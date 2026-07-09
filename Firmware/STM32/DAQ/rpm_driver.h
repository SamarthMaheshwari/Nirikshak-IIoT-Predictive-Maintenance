#ifndef RPM_DRIVER_H
#define RPM_DRIVER_H

#include <Arduino.h>

// ===== API =====
void RPM_Init(uint8_t pin, uint8_t pulsesPerRev);
float RPM_Read(void);

#endif
