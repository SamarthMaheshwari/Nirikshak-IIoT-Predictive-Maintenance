#ifndef CURRENT_DRIVER_H
#define CURRENT_DRIVER_H

#include <Arduino.h>

// ===== API =====
void Current_Init(uint8_t adcPin);
void Current_SetCalibration(float factor, float offset);
float Current_ReadRMS(void);

#endif
