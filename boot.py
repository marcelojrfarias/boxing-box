# boot.py -- run on boot-up
import network

def connect_wifi():
    ssid = 'Farias IoT'
    password = 'IoT@Farias'

    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('Conectando à rede Wi-Fi...')
        sta_if.active(True)
        sta_if.connect(ssid, password)
        while not sta_if.isconnected():
            pass
    print('Conectado! Meu endereço IP é:', sta_if.ifconfig()[0])

def boot():
        print('Olá! :)')
        print('Bem vindo ao Boxing Box!')

boot()
