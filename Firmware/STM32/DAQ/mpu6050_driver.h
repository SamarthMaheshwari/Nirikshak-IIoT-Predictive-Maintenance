#ifndef MPU6050_DRIVER_H
#define MPU6050_DRIVER_H

#include <MPU6050.h>

typedef struct
{
    float ax;
    float ay;
    float az;
    float vibration;
} MPU6050_Data_t;

void MPU6050_Init(void);
void MPU6050_Read(MPU6050_Data_t *data);

#endif
