#include "../gcode.h"
#include <src/feature/drlcd/drlcd.h>
#include <src/module/planner.h>
#include <src/module/motion.h>
#include <src/gcode/parser.h>

void measureAndReportTSL2561() {
    auto value = DR_LCD.readTSL2561();
    SERIAL_ECHO(value);
    SERIAL_ECHO("\n");
}

void measureAndReport(int sensorType) {
    switch (sensorType) {
        case 0:
            measureAndReportTSL2561();
            break;
        default:
            SERIAL_ECHO("Unknown sensor specified\n");
    }
}

void reportMeasurementMiss() {
    SERIAL_ECHO("Missed\n");
}

/**
 * Makes a line move and performs measurements using a specified
 * sensor along the movement without stopping. It reports
 *
 * - P specifies the sensor:
 *   - 0 = TSL2561
 * - S specifies the number of samples (including start and end point)
 */
void GcodeSuite::M6000() {
    planner.synchronize();

    xy_pos_t startPoint = current_position;

    get_destination_from_command();
    int samples = parser.intval('S');
    int sensor = parser.intval('P');

    xy_pos_t direction = destination - startPoint;
    float length = direction.magnitude();
    float step = length / samples;
    float half_step = step / 2.0f;
    float step_inv = 1.0f / step;

    // We start the movement and wait for it to finish:
    prepare_line_to_destination();

    int lastMeasurement = 0;
    while (lastMeasurement < samples) {
        idle();
        get_cartesian_from_steppers();
        xy_pos_t current = cartes;
        float progress = (current - startPoint).magnitude();
        int measurementNo = (progress + half_step) * step_inv;
        int measurementAdv = measurementNo - lastMeasurement;
        if (measurementAdv > 1) {
            for (int i = 0; i != measurementAdv; i++)
                reportMeasurementMiss();
        } else if (measurementAdv == 1) {
            measureAndReport(sensor);
        }
        lastMeasurement = measurementNo;
    }

    planner.synchronize();
}
