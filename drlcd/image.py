import math
from typing import List
import plotly.graph_objects as go
import click
import json
import numpy as np
import cv2 as cv
import itertools
from scipy.ndimage.filters import gaussian_filter
from .ui_common import Resolution

def replacePeaks(arr: np.array, threshold: float, windowSize: int):
    """
    Given an array and threshold, replace peaks with local average of
    windowSize×windowSize.
    """
    result = np.copy(arr)
    height, width = arr.shape

    halfWindow = windowSize // 2

    for i in range(halfWindow, height - halfWindow):
        for j in range(halfWindow, width - halfWindow):
            if arr[i, j] > threshold:
                localWindow = arr[i - halfWindow: i + halfWindow + 1, j - halfWindow: j + halfWindow + 1]
                localWindowWithoutPeak = localWindow[localWindow != arr[i, j]]
                localAverage = np.mean(localWindowWithoutPeak)
                result[i, j] = localAverage

    return result


def normalizeData(data: List[List[float]], lowThreshold=0) -> List[List[float]]:
    npArray = np.array(data)

    # There are often faulty peaks in the source data, let's filter them out
    mean = np.mean(npArray)
    npArray = replacePeaks(npArray, 1.5 * mean, 3)

    max = np.max(npArray)
    npArray = np.clip(npArray, lowThreshold, max)
    npArray[npArray == lowThreshold] = None

    return npArray.tolist()

@click.command()
@click.argument("input", type=click.Path())
@click.argument("output", type=click.Path())
@click.option("--title", type=str, default="Display measurement",
    help="Plot title")
@click.option("--show", type=bool, is_flag=True,
    help="Immediately show")
@click.option("--threshold", type=int, default=0,
    help="Minimal value to crop")
def visualize(input, output, title, show, threshold):
    with open(input) as f:
        measurement = json.load(f)
    data = normalizeData(measurement["measurements"], lowThreshold=threshold)
    fig = go.Figure(data=[go.Surface(z=data)])
    fig.update_layout(title=title, autosize=True,
                  scene_aspectmode="manual", scene_aspectratio=dict(x=1, y=measurement["resolution"][1]/measurement["resolution"][0], z=0.1))
    fig.write_html(output)
    if show:
        fig.show()

def lineIntersection(line1, line2):
    """
    Finds the intersection of two lines given in Hesse normal form.

    Returns closest integer pixel locations.
    See https://stackoverflow.com/a/383527/5087436
    """
    rho1, theta1 = line1
    rho2, theta2 = line2
    A = np.array([
        [np.cos(theta1), np.sin(theta1)],
        [np.cos(theta2), np.sin(theta2)]
    ])
    b = np.array([[rho1], [rho2]])
    try:
        x0, y0 = np.linalg.solve(A, b)
    except np.linalg.LinAlgError:
        return None
    x0, y0 = int(np.round(x0)), int(np.round(y0))
    return (x0, y0)

def locateScreenAutomatic(image, threshold):
    npImg = np.array(image)
    ret, thresholded = cv.threshold(npImg, threshold, 255, cv.THRESH_BINARY)
    thresholded = np.uint8(thresholded)

    contours, hierarchy = cv.findContours(thresholded, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

    # We draw contours to find lines in the using Hough transform
    countoursImg = np.zeros((len(image), len(image[0])), dtype=np.uint8)
    cv.drawContours(countoursImg, contours, 0, 255,  1)

    # Detect the lines
    lines = cv.HoughLines(countoursImg, 0.5, np.pi / 360, len(image[0]) // 5, None, 0, 0, 0, 3 / 4 * np.pi)
    dbgImg1 = cv.cvtColor(countoursImg, cv.COLOR_GRAY2RGB)

    def thetaClose(a, b):
        return abs(a - b) < np.pi / 40

    def rhoClose(a, b):
        return abs(a - b) < 10

    if lines is not None:
        # Find strong lines
        strongLines = []
        for line in lines:
            rho, theta = line[0][0], line[0][1]
            if any(rhoClose(rho, l[0]) and thetaClose(theta, l[1]) for l in strongLines):
                continue
            strongLines.append((rho, theta))

        # Draw lines into dbg image:
        for line in strongLines:
            rho, theta = line[0], line[1]
            a = math.cos(theta)
            b = math.sin(theta)
            x0 = a * rho
            y0 = b * rho
            pt1 = (int(x0 + 1000*(-b)), int(y0 + 1000*(a)))
            pt2 = (int(x0 - 1000*(-b)), int(y0 - 1000*(a)))
            cv.line(dbgImg1, pt1, pt2, (255,0,255), 1, cv.LINE_AA)

    intersections = [lineIntersection(l1, l2) for l1, l2 in itertools.product(strongLines, strongLines) if l1 != l2]
    fitsInImage = lambda p: p[0] > 0 and p[0] <= len(image[0]) and p[1] > 0 and p[1] <= len(image)
    corners = list(set([x for x in intersections if x is not None and fitsInImage(x)]))
    return corners

def originDistance(point):
    return point[0] ** 2 + point[1] ** 2

def cropToScreen(image, corners, screenSize):
    assert len(corners) == 4

    npImg = np.array(image)

    sortedCorners = sorted(corners, key=originDistance)
    expected = sorted([(0, 0), (0, screenSize[1]), (screenSize[0], 0), screenSize],
                      key=originDistance)

    perspTransform = cv.getPerspectiveTransform(np.float32(sortedCorners), np.float32(expected))
    return cv.warpPerspective(npImg, perspTransform, screenSize)

@click.command()
@click.argument("output", type=click.Path())
@click.option("--measurement", type=click.Path(exists=True, file_okay=True, dir_okay=False),
    required=True,
    help="The full-screen measurement JSON file")
@click.option("--min", type=int, required=True,
    help="The minimal brightness to compensate for")
@click.option("--max", type=int, default=None,
    help="The maximal brightness to compensate for")
@click.option("--by", type=int, required=True,
    help="Amount of brightness to compensate by (0-255)")
@click.option("--cutoff", type=int, default=50,
    help="The value considered as out of screen")
@click.option("--screen", type=Resolution(), required=True,
    help="The screen resolution in pixels")
@click.option("--manual", is_flag=True,
    help="Locate screen manually")
def compensate(output, measurement, min, max, by, cutoff, screen, manual):
    """
    Build a compensation mask for a given LCD. Provide a full-screen measurement
    and screen resolution to build a PNG compensation mask that you can load
    into UVTools and apply it.
    """
    with open(measurement) as f:
        measurement = json.load(f)
    data = normalizeData(measurement["measurements"])

    corners = []
    if not manual:
        corners = locateScreenAutomatic(data, cutoff)
    if len(corners) != 4 or manual:
        from .manual_crop import locateScreenManually
        corners = locateScreenManually(data)

    map = cropToScreen(data, corners, screen)
    if max is None:
        max = np.max(map)
    map = np.clip(map - min, 0, max - min) * by / (max - min)
    map = cv.rotate(map, cv.ROTATE_180)
    cv.imwrite(output, map)


