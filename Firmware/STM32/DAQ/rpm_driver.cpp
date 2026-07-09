#include "rpm_driver.h"

// ===== INTERNAL STATE =====
static uint8_t rpmPin;
static uint8_t pulsesPerRev;

static volatile uint32_t pulseCount = 0;
static unsigned long lastTime = 0;
static float rpmValue = 0;

// ===== ISR (STM32 SAFE) =====
static void pulseISR()
{
    pulseCount++;
}

// ===== INIT =====
void RPM_Init(uint8_t pin, uint8_t ppr)
{
    rpmPin = pin;
    pulsesPerRev = ppr;

    pinMode(rpmPin, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(rpmPin), pulseISR, FALLING);

    lastTime = millis();
}

// ===== READ RPM =====
float RPM_Read(void)
{
    if (millis() - lastTime >= 1000)
    {
        noInterrupts();
        uint32_t pulses = pulseCount;
        pulseCount = 0;
        interrupts();

        rpmValue = (pulses * 60.0) / pulsesPerRev;
        lastTime = millis();
    }

    return rpmValue;
}
