#include "sensor_manager.h"

// Drivers
#include "mpu6050_driver.h"
#include "ds18b20_driver.h"
#include "current_driver.h"
#include "voltage_driver.h"
#include "rpm_driver.h"

// ===== PIN DEFINITIONS =====
#define DS18B20_PIN     PA8
#define CURRENT_ADC    PA0
#define VOLTAGE_ADC    PA1
#define RPM_PIN        PA6
#define RPM_PPR        1

static MPU6050_Data_t mpuData;

void SensorManager_Init(void)
{
    MPU6050_Init();

    DS18B20_Init(DS18B20_PIN);

    Current_Init(CURRENT_ADC);
    Current_SetCalibration(32.2, 1.65);

    Voltage_Init(VOLTAGE_ADC);
    Voltage_SetCalibration(230.0, 1.65);

    RPM_Init(RPM_PIN, RPM_PPR);
}

void SensorManager_ReadAll(SensorData_t *data)
{
    MPU6050_Read(&mpuData);

    data->temperature = DS18B20_Read();
    data->current     = Current_ReadRMS();
    data->voltage     = Voltage_ReadRMS();
    data->rpm         = RPM_Read();
    data->vibration   = mpuData.vibration;
}
