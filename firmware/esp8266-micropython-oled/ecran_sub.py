from umqttsimple import MQTTClient
import machine
import ubinascii
from machine import Pin, ADC
import SSD1306
import time
import os

# ================================================================= Écran SSD1306 :
i2c = machine.I2C(machine.Pin(5), machine.Pin(4))
oled = SSD1306.SSD1306_I2C(128, 64, i2c,addr=0x3c)


# Initialisation des timers :
millis = time.ticks_ms()
millisPrec = millis


# Variables globales :
INTERVAL = 3000
start_timer = False
starting = False
first_step = False
second_step = False

DEBUG = True
mqtt_server = MQTT_SERVER
client_id = ubinascii.hexlify(machine.unique_id())
topic_sub = b'bme280'
from ssid_info import MQTT_SERVER, MQTT_USER, MQTT_PASSWORD



def show_on_screen(msg):
    oled.fill(0)
    oled.text("Nouvelle lecture", 0, 2)

    values = (str(msg)).split(" ")
    
    values[0] = values[0].replace("b'", "")
    values[3] = values[3].replace("'", "")
    
    oled.text("T : " + str(values[0]) + " dC", 0, 25)
    oled.text("P : " + str(values[1]) + " hPa", 0, 35)
    oled.text("A : " + str(values[2]) + " m", 0, 45)
    oled.text("H : " + str(values[3]) + " %", 0, 55)
    oled.show()

def sub_cb(topic, msg):
    global start_timer
    global starting
    
    print((topic, msg))
    show_on_screen(msg)
    start_timer = True
    starting = True

def connect_and_subscribe():
    global client_id, mqtt_server, topic_sub
    if DEBUG:
        print("client_id = " + str(client_id))
        print("mqtt_server = " + str(mqtt_server))
        print("topic_sub = " + str(topic_sub))
    client = MQTTClient(client_id, mqtt_server, user=MQTT_USER, password=MQTT_PASSWORD)
    client.set_callback(sub_cb)
    client.connect()
    client.subscribe(topic_sub)
    print('Connected to %s MQTT broker, subscribed to %s topic' % (mqtt_server, topic_sub))
    return client

def restart_and_reconnect():
  print('Failed to connect to MQTT broker. Reconnecting...')
  time.sleep(10)
  machine.reset()


def main():
    
    global INTERVAL
    global millis
    global millisPrec
    global start_timer
    global starting
    global first_step
    global second_step
    
    try:
        client = connect_and_subscribe()
    except OSError as e:
        if DEBUG: print(e)
        restart_and_reconnect()
    
    while True:   
        millis = time.ticks_ms()
        
        try:
            client.check_msg()
        except OSError as e:
            if DEBUG: print(e)
            restart_and_reconnect()
            
            
        if start_timer == True:
            if starting == True:
                oled.poweron()
                oled.contrast(255)
                millisPrec = millis
                starting = False
                first_step = True
            else:
                if millis > (millisPrec + INTERVAL) and first_step == True:
                    first_step = False
                    second_step = True
                    millisPrec = millis
                    oled.contrast(20)
                    
                if millis > (millisPrec + INTERVAL + 2000) and second_step == True:
                    start_timer = False
                    second_step = False
                    start_timer = False
                    oled.poweroff()
            
            


if __name__ == "__main__":
    main()