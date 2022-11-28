import math
from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame
import numpy as np

LINE_COLOR = (255, 0, 0)
LINE_WIDTH = 3

CORNER_COLOR = (255, 0, 0)
CORNER_RADIUS = 10

class ManualScreenLocator:
    """
    The user can select image corners via simple GUI
    """
    def __init__(self, image, windowWidth=1024):
        pygame.init()

        self._srcImg = image
        self._srcSize = (len(image[0]), len(image))
        self._windowSize = (windowWidth,
                            windowWidth / self._srcSize[0] * self._srcSize[1])
        self._img = self._prepareImg(self._srcImg)
        self._corners = self._prepareCorners(self._windowSize)
        self._activeCornerIdx = None

        self._window = pygame.display.set_mode(self._windowSize)

    def _prepareImg(self, image):
        """
        Given a raw measurement image, convert it into pygame surface
        """
        npImg = np.transpose(np.array(image))
        npImg = (255 * npImg) / np.nanmax(npImg)
        w, h = npImg.shape
        rgbImg = np.empty((w, h, 3), dtype=np.uint8)
        rgbImg[:, :, 2] = rgbImg[:, :, 1] = rgbImg[:, :, 0] = npImg

        surface = pygame.surfarray.make_surface(rgbImg)
        return pygame.transform.scale(surface, self._windowSize)

    def _prepareCorners(self, windowSize):
        OFFSET = 20
        return [
            (OFFSET, OFFSET),
            (windowSize[0] - OFFSET, OFFSET),
            (windowSize[0] - OFFSET, windowSize[1] - OFFSET),
            (OFFSET, windowSize[1] - OFFSET)
        ]

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                running = running and self._handleEvent(event)
            self._redraw()
            pygame.display.flip()
        pygame.quit()

    def _redraw(self):
        self._window.fill((0, 0, 0))
        self._window.blit(self._img, (0, 0))

        pygame.draw.lines(self._window, LINE_COLOR, True, self._corners, LINE_WIDTH)
        for corner in self._corners:
            pygame.draw.circle(self._window, CORNER_COLOR, corner, CORNER_RADIUS, 1)

    def _handleEvent(self, event):
        if self._isQuitEvent(event):
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._onDragStart(event.pos)
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._onDragEnd(event.pos)
        if event.type == pygame.MOUSEMOTION:
            self._onDrag(event.pos)
        return True

    def _onDragStart(self, pos):
        for i, corner in enumerate(self._corners):
            if math.sqrt((pos[0] - corner[0]) ** 2 + (pos[1] - corner[1]) ** 2 ) < CORNER_RADIUS:
                self._activeCornerIdx = i
                return

    def _onDragEnd(self, pos):
        self._activeCornerIdx = None

    def _onDrag(self, pos):
        if self._activeCornerIdx is None:
            return
        self._corners[self._activeCornerIdx] = pos

    @staticmethod
    def _isQuitEvent(event):
        return event.type == pygame.QUIT or \
               (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE) or \
               (event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN)

    @property
    def corners(self):
        ratio = (self._srcSize[0] / self._windowSize[0], self._srcSize[1] / self._windowSize[1])
        return [(x * ratio[0], y * ratio[1]) for x, y in self._corners]

def locateScreenManually(image):
    print("Select the screen and press ENTER")
    s = ManualScreenLocator(image)
    s.run()
    return s.corners
