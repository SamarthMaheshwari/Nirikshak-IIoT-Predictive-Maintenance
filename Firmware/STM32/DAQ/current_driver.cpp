#include "current_driver.h"
#include <math.h>

// ===== CONFIG =====
static uint8_t _adcPin;

static const float ADC_REF = 3.3;
static const int ADC_MAX = 4095;
static const int SAMPLES = 2000;
static const float NOISE_THRESHOLD = 0.01;

// ===== CALIBRATION =====
static float calibrationFactor = 29.4;
static float offset = 1.65;

void Current_Init(uint8_t adcPin)
{
    _adcPin = adcPin;

    analogReadResolution(12); 
}

void Current_SetCalibration(float factor, float offs)
{
    calibrationFactor = factor;
    offset = offs;
}

float Current_ReadRMS(void)
{
    float sumSq = 0;

    for (int i = 0; i < SAMPLES; i++)
    {
        int raw = analogRead(_adcPin);
        float voltage = (raw * ADC_REF) / ADC_MAX;
        float ac = voltage - offset;
        sumSq += ac * ac;
        delayMicroseconds(200);
    }

    float rmsV = sqrt(sumSq / SAMPLES);

    if (rmsV < NOISE_THRESHOLD)
        return 0.0;

    return rmsV * calibrationFactor;
}
