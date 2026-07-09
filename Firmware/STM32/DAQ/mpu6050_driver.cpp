#include "mpu6050_driver.h"
#include <math.h>

static MPU6050 mpu;

void MPU6050_Init(void)
{
    // IMPORTANT: STM32 default I2C pins (PB6 SCL, PB7 SDA)
    Wire.begin();

    mpu.initialize();

    // Force ±2g range so 16384 LSB/g is correct
    mpu.setFullScaleAccelRange(MPU6050_ACCEL_FS_2);
}

void MPU6050_Read(MPU6050_Data_t *data)
{
    int16_t ax, ay, az;
    mpu.getAcceleration(&ax, &ay, &az);

    // Convert to g
    data->ax = ax / 16384.0;
    data->ay = ay / 16384.0;
    data->az = az / 16384.0;

    // Acceleration magnitude
    float mag = sqrt(
        data->ax * data->ax +
        data->ay * data->ay +
        data->az * data->az
    );

    // Vibration = deviation from gravity (DC removed)
    data->vibration = fabs(mag - 1.0);
}
