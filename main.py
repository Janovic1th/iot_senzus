#Version '1.4 beta'
from machine import Pin, PWM
from time import sleep
from machine import RTC
import dht
import network
import time
import json
from umqtt.simple import MQTTClient

#sensor = dht.DHT22(Pin(7))
sensor = dht.DHT11(Pin(5))
led = Pin(15, Pin.OUT)
buzzer = PWM(Pin(14))
rtc = RTC()

MQTT_BROKER = '147.232.34.254'
PORT = 1883
MQTT_USERNAME = 'maker'
MQTT_PASSWORD = 'this.is.mqtt'

MQTT_TOPIC_TEMPERATURE = 'gateway/temperature/111101'
MQTT_TOPIC_HUMIDITY = 'gateway/humidity/111102'

CLIENT_ID = 'Janko'

MQTT_TOPIC_TEMPERATURE_SET = 'gateway/temperature/111101/set'
MQTT_TOPIC_LED_SET = 'gateway/lamp/111105/set'

delay = 3
led_state = False
# def do_connect(ssid, password):
#     import network
#     wlan = network.WLAN(network.STA_IF)
#     wlan.active(True)
#     if not wlan.isconnected():
#         print('connecting to network...')
#         wlan.connect(ssid, password)
#         while not wlan.isconnected():
#             pass
#     print('network config:', wlan.ifconfig())
#     
    
# Connect to MQTT Broker
def connect_mqtt():
    client = MQTTClient(CLIENT_ID, MQTT_BROKER, PORT, MQTT_USERNAME, MQTT_PASSWORD)
    return client

# Send Data to MQTT Broker
def send_mqtt(client, message, TOPIC):
    client.publish(TOPIC, message)
    print(f'Sent to MQTT Broker: {message}')
    
def measure():
    try:
        ts = time.mktime(time.localtime())
        rtc_time = rtc.datetime()
        datetime_str = "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}.{:06d}Z".format(
            rtc_time[0], rtc_time[1], rtc_time[2], rtc_time[4], rtc_time[5], rtc_time[6], rtc_time[7])
        sensor.measure()
        temp = sensor.temperature()
        hum = sensor.humidity()
        temperature_data = {
            "name": "MariaDB teplomer",
            "ts": ts,
            #"dt": datetime_str,
            "temperature": temp,
            "battery": 100
        }

        humidity_data = {
            "name": "MariaDB humiditymeter",
            "ts": ts,
            #"dt": datetime_str,
            "humidity": hum,
            "battery": 100
        }
        return temperature_data, humidity_data
    
    except OSError as e:
        return "ERROR MEASURING!"
    
    
def subscribe_callback(topic, message):
    global delay
    global led_state
    try:
        topic = topic.decode('utf-8')
        message = message.decode('utf-8')
        
        data = json.loads(message)
        if 'delay' in data:
            delay = data['delay']
        if 'led1' in data:
            led_state = data['led1']
    except ValueError as e:
        # In case the payload is not a valid JSON
        print(f"Error parsing JSON: {e}")    
    print(message)
    
def play_sound():
    buzzer.freq(500)
    buzzer.duty_u16(1000)
    sleep(0.1)
    buzzer.duty_u16(0)
#do_connect('raspberry', '123456789')
    
# do_connect('vulcan-things', 'welcome.to.the.vulcan')
led.value(False)
mqtt_client = connect_mqtt()

mqtt_client.set_callback(subscribe_callback)

mqtt_client.connect()
mqtt_client.subscribe(MQTT_TOPIC_TEMPERATURE_SET)
mqtt_client.subscribe(MQTT_TOPIC_LED_SET)

while True:
    mqtt_client.check_msg()
    led.value(led_state)
    temperature_json, humidity_json = measure()

    temperature_json_str = json.dumps(temperature_json)
    humidity_json_str = json.dumps(humidity_json)
    send_mqtt(mqtt_client, temperature_json_str, MQTT_TOPIC_TEMPERATURE)
    send_mqtt(mqtt_client, humidity_json_str, MQTT_TOPIC_HUMIDITY)
    play_sound()
    sleep(delay)
