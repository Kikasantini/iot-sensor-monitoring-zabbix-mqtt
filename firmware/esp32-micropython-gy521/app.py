import gc
import uasyncio as asyncio
import urequests as requests
from dd_web import WebApp, jsonify, writeHTML
import usocket
from ssid_info import ARDUINO_WEATHER_URL

# ======================================================= MPU 6050 / GY 512 :
from time import sleep_ms
from machine import SoftI2C, Pin
import mpu6050

i2c = SoftI2C(scl=Pin(22), sda=Pin(21))     #initializing the I2C method for ESP32
accelerometer = mpu6050.accel(i2c)

# ======================================================= Watchdog :
"""
from time import sleep
from machine import WDT
from time import ticks_ms

useWDT = Pin(4, Pin.IN, Pin.PULL_UP) # placer un fil entre G et D2 (se for no ESP 8266) ou D4 (se for no ESP 32) pour prévenir le lancement du WatchDog

if useWDT.value():
    wdt = WDT(timeout=5000) # par defaclut, si on ne especifie pas, c'est 5 secondes 
    
i = 0
"""
# ======================================================= Touch sensor :
from machine import TouchPad

TRIGGER = 300
touch0 = TouchPad(Pin(15)) # D15
touch0.config(600)
touch0_lect = 0

# ======================================================= NTP :
from time import localtime
from ntptime import settime

def heure():
    hour = localtime()[3] - 4
    if hour < 0:
        hour += 24
    settime()
    return '{:02d}:{:02d}:{:02d} '.format(hour, localtime()[4], localtime()[5])

# ================================================================
TEST_SERVER = 'https://one.one.one.one'
webapp = WebApp()

def is_connected(hostname):
    try:
        s = requests.get(TEST_SERVER)
        return True
    except OSError:
        print("timeout")
        pass
    return False

@webapp.route('/', method='GET')
def index(request, response):
    gc.collect()
    yield from webapp.sendfile(response, '/index.html')
    
@webapp.route('/jsonGY521', method='GET')
def jsonGY521(request, response):
    global accelerometer
    
    val = accelerometer.get_values()
    message = '{"body":{"gy512":{"GyZ": ' + str(val["GyZ"]) + ', "GyY": ' + str(val["GyY"]) + ', "GyX": ' + str(val["GyX"]) + ', "Tmp": ' + str(val["Tmp"]) + ', "AcZ": ' + str(val["AcZ"]) + ', "AcY": ' + str(val["AcY"]) + ', "AcX": ' + str(val["AcX"]) + '}}}'

    gc.collect()
    yield from writeHTML(response, message)

async def tache_bme280():
    '''
    Cette fonction cherche la string Json dans mon Web Serveur Arduino C++
    Elle prend aussi l'heure exacte à partir du protocole NTP
    Et elle montre dans la console
    '''
    while True:
        
        try:
            site = requests.get("ARDUINO_WEATHER_URL") # adresse serveur microcontroleur 1
            print("")
            print("JSON bme280 : " + site.text + " - " + str(heure()))
            print("")
            
        except OSError:
            print("timeout")
            pass
        gc.collect()
        await asyncio.sleep(5)

async def tache_watchdog():
    global i
    
    while True:
        if useWDT.value():
            wdt.feed()
        print(i, end = " ")
        i += 0.1
        await asyncio.sleep(3)

async def tache_touch():
    global TRIGGER
    global touch0
    global touch0_lect
    global accelerometer
    
    while True:
        touch0_lect = touch0.read()
        
        if touch0_lect < TRIGGER:
            val = accelerometer.get_values()
            print(str(val) + " - " + str(heure()))
            
        await asyncio.sleep(1)
            

def main():
    """
    Met en place les tâches et crée la boucle
    """
    print(is_connected(TEST_SERVER))
    loop = asyncio.get_event_loop()
    loop.create_task(asyncio.start_server(webapp.handle, '0.0.0.0', 80))
    loop.create_task(tache_bme280())
    loop.create_task(tache_touch())
    #loop.create_task(tache_watchdog())
    print("Taches crées")
    
    gc.collect()
    loop.run_forever()

if __name__ == "__main__":
    main()