#ifndef VOLTAGE_DRIVER_H
#define VOLTAGE_DRIVER_H

#include <Arduino.h>

// ===== API =====
void Voltage_Init(uint8_t adcPin);
void Voltage_SetCalibration(float factor, float offset);
float Voltage_ReadRMS(void);

#endif
