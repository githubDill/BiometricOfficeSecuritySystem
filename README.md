# WeSellYourData
IOT Smart security system with R503 fingerprint sensor, Rpi and AWS hosted website

Promotional Website Link: https://edsincorporated.my.canva.site/

Promotional Video Link: https://www.canva.com/design/DAHA6rBFxmY/HbClBqIMdlqYh2hrnYzwwA/watch?utm_content=DAHA6rBFxmY&utm_campaign=designshare&utm_medium=link2&utm_source=uniquelinks&utlId=h9b4d1e56d2

RPI Code can be found under raspberricode->main(finalversion)
- temp.py contains the code for i2c sensor Si7021 for temp and humidity
- main.py imports Si7021 sensor code to be used and also has its own code for fingerprint sensor -> this sensor uses uart so we used the fingerprint library, in main.py MQTT is also established
- config.yaml contains the topics for MQTT
- devices.yaml is a list of id and names stored on the fingerprint sensor
- there was a plan to do lock and unlocking in rpi however it was scrapped, with lambda functions on AWS handling the logic

tests folder contains test scripts used to ensure functionality

Main website which shows all the data from the sensors can be found in websiteSC->wesellyourdata.html, it is run with VS code extension "Live Servers"

System flow:
Fingerprint Sensor & (Si7021 sensor) -> MQTT/Iot Core -> Iot Rule -> DynamoB -> Lamba Functions -> API Gateway -> Website
