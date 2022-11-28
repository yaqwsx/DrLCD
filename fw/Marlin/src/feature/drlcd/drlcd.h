#pragma once

#include <variant.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_TSL2561_U.h>
#include <Adafruit_AS7341.h>



class DrLcd {
private:
    TwoWire _wire = TwoWire(PIN_SENSOR_SDA, PIN_SENSOR_SCL);
    Adafruit_TSL2561_Unified _tsl2561 = Adafruit_TSL2561_Unified(TSL2561_ADDR_HIGH);
    Adafruit_AS7341 _as7341 = Adafruit_AS7341();
public:
    void init() {
        _wire.begin();
        _wire.setClock(400000);

        _tsl2561.begin(&_wire);
        _tsl2561.setGain(TSL2561_GAIN_1X);
        _tsl2561.setIntegrationTime(TSL2561_INTEGRATIONTIME_13MS);

        _as7341.begin(AS7341_I2CADDR_DEFAULT, &_wire);
        _as7341.setATIME(100);
        _as7341.setASTEP(100);
        _as7341.setGain(AS7341_GAIN_16X);
    }

    int readTSL2561() {
        // We want to avoid float, so we have to recreate
        // what getEvent does

        uint16_t broadband, ir;
        _tsl2561.getLuminosity(&broadband, &ir);
        return _tsl2561.calculateLux(broadband, ir);
    }

    std::array< uint16_t, 12 > readAS7341() {
        _as7341.readAllChannels();
        std::array< uint16_t, 12 > values;
        for ( int channel = AS7341_CHANNEL_415nm_F1; channel <= AS7341_CHANNEL_NIR; channel++ ) {
            values[ channel ] = _as7341.getChannel( static_cast< as7341_color_channel_t >( channel ) );
        }
        return values;
    }
};

extern DrLcd DR_LCD;
