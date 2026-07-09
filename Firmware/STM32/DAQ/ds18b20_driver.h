#ifndef DS18B20_DRIVER_H
#define DS18B20_DRIVER_H

#include <Arduino.h>
#include <OneWire.h>
#include <DallasTemperature.h>

// API
void DS18B20_Init(uint8_t pin);
float DS18B20_Read(void);

#endif
