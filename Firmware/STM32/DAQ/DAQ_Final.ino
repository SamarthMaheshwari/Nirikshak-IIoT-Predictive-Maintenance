#include <Wire.h>
#include <I2Cdev.h>
#include <MPU6050.h>

#include <OneWire.h>
#include <DallasTemperature.h>

#include "sensor_manager.h"

SensorData_t sensorData;

void setup()
{
    // UART to ESP32 (USART1 → PA9 TX, PA10 RX)
    Serial1.begin(115200);

    // Initialize all sensors
    SensorManager_Init();

    Serial1.println("DAQ_START");
}

void loop()
{
    SensorManager_ReadAll(&sensorData);

    // ===== FORMAT EXPECTED BY ESP32 =====
    Serial1.print("TEMP:");
    Serial1.print(sensorData.temperature, 1);
    Serial1.print(",");

    Serial1.print("CUR:");
    Serial1.print(sensorData.current, 2);
    Serial1.print(",");

    Serial1.print("VOLT:");
    Serial1.print(sensorData.voltage, 1);
    Serial1.print(",");

    Serial1.print("RPM:");
    Serial1.print(sensorData.rpm);
    Serial1.print(",");

    Serial1.print("VIB:");
    Serial1.println(sensorData.vibration, 4);

    delay(1000);
}
