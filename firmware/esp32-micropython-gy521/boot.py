# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
import uos, machine
INTERNET = 1


if INTERNET:
    ##########################
    # pour connecter le WiFi #
    ##########################
    from network import WLAN, STA_IF, AP_IF
    from ssid_info import SSID, PASSWORD


    mywifi = WLAN(STA_IF)
    mywifi.active(False) #Désactive et 
    mywifi.active(True)  #Réactive le client pour prévenir certains problèmes intermittants
    ap=WLAN(AP_IF)
    ap.active(False) #Désactive le point d'accès pour ne pas publier le SSID
    mywifi.connect(SSID, PASSWORD)
    while not mywifi.isconnected():
        pass
    print()
    print("connecté à : " + mywifi.config('essid') + " avec l'adresse IP : " + mywifi.ifconfig()[0])
    ##########################
    # pour connecter le WiFi #
    ##########################

#uos.dupterm(None, 1) # disable REPL on UART(0)
import gc
#import webrepl
#webrepl.start()
gc.collect()