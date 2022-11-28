#include "../gcode.h"
#include <src/feature/drlcd/drlcd.h>

void GcodeSuite::M5500() {
    float value = DR_LCD.readTSL2561();
    SERIAL_ECHOPAIR_F("Data: ", value);
    SERIAL_ECHO("\n");
}

void GcodeSuite::M5501() {
    auto values = DR_LCD.readAS7341();
    SERIAL_ECHO("Data: ");
    for (auto value : values) {
        SERIAL_ECHOPAIR_F(" ", float(value));
    }
    SERIAL_ECHO("\n");
}

