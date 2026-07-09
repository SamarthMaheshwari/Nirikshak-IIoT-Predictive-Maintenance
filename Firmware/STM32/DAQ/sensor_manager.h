#ifndef SENSOR_MANAGER_H
#define SENSOR_MANAGER_H

typedef struct
{
    float temperature;
    float current;
    float voltage;
    int   rpm;
    float vibration;
} SensorData_t;

void SensorManager_Init(void);
void SensorManager_ReadAll(SensorData_t *data);

#endif
