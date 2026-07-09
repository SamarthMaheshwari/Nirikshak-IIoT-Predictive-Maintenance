#include "ds18b20_driver.h"

static OneWire *oneWire;
static DallasTemperature *sensors;

void DS18B20_Init(uint8_t pin)
{
    oneWire = new OneWire(pin);
    sensors = new DallasTemperature(oneWire);
    sensors->begin();
}

float DS18B20_Read(void)
{
    sensors->requestTemperatures();
    return sensors->getTempCByIndex(0);
}
