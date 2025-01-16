from machine import Pin, SoftI2C, Timer
from MPU6050 import MPU6050
from tm1637 import TM1637
from neopixel import NeoPixel
import time
from DebouncedInput import DebouncedInput
import random

# ==== Configuração dos dispositivos ====
CLK_PIN = Pin(13)
DIO_PIN = Pin(14)
tm = TM1637(clk=CLK_PIN, dio=DIO_PIN)

LED_PIN = Pin(27, Pin.OUT)
NUM_LEDS = 12
leds = NeoPixel(LED_PIN, NUM_LEDS)

i2c = SoftI2C(scl=Pin(22), sda=Pin(21))
mpu = MPU6050()

selected_time = 60
menu_active = True
increment_timer = Timer(-1)
decrement_timer = Timer(-1)
press_start_time = {}
MAX_TIME = 999  # Ajustado para 999 segundos
countdown_timer = Timer(-1)
countdown_started = False

# Variáveis para contabilizar golpes
golpes_contados = 0

# ==== Funções Auxiliares ====
def set_leds_color(leds, color):
    for i in range(NUM_LEDS):
        leds[i] = color
    leds.write()

def blink_leds(leds, colors, delay):
    for color in colors:
        set_leds_color(leds, color)
        time.sleep(delay)
    set_leds_color(leds, (0, 0, 0))  # Apagar LEDs

def display_all_segments(tm, duration):
    tm.write([127, 127, 127, 127])
    time.sleep(duration)
    tm.write([0, 0, 0, 0])

def update_display(time_val):
    """Atualiza o display com o valor atual de tempo ou golpes."""
    tm.number(time_val)

def adjust_time(delta):
    global selected_time
    selected_time = max(0, min(MAX_TIME, selected_time + delta))
    update_display(selected_time)

def handle_long_press(pin_num):
    global press_start_time
    elapsed = time.ticks_ms() - press_start_time[pin_num]
    if elapsed > 3000:
        adjust_time(5 if pin_num == 19 else -5)
    else:
        adjust_time(1 if pin_num == 19 else -1)

def button_callback(pin_num, pressed, duration):
    global press_start_time, increment_timer, decrement_timer
    if not menu_active:
        return
    if pressed:
        press_start_time[pin_num] = time.ticks_ms()
        if pin_num == 18:
            decrement_timer.init(mode=Timer.PERIODIC, period=200, callback=lambda t: handle_long_press(18))
        elif pin_num == 19:
            increment_timer.init(mode=Timer.PERIODIC, period=200, callback=lambda t: handle_long_press(19))
    else:
        press_duration = time.ticks_ms() - press_start_time[pin_num]
        if 25 <= press_duration < 500:
            adjust_time(-1 if pin_num == 18 else 1)
        if pin_num == 18:
            decrement_timer.deinit()
        elif pin_num == 19:
            increment_timer.deinit()

def check_buttons_simultaneous():
    global menu_active, countdown_started
    if not BUTTON_1.pin.value() and not BUTTON_2.pin.value():
        menu_active = False
        countdown_started = True
        time.sleep(0.5)

def start_countdown():
    for i in [3, 2, 1]:
        update_display(i)
        time.sleep(1)
    
    # Piscar o display após a contagem de 3, 2, 1
    for _ in range(3):
        update_display(0)
        time.sleep(0.5)
        update_display(selected_time)
        time.sleep(0.5)
    
    tm.write([0, 0, 0, 0])
    time.sleep(1)
    
    update_display(selected_time)
    countdown_timer.init(mode=Timer.PERIODIC, period=1000, callback=decrement_time)

def decrement_time(timer=None):
    global selected_time, golpes_contados
    if selected_time > 0:
        selected_time -= 1
        update_display(selected_time)
        # Verificar os dados do MPU para contar os golpes
        accel_data = mpu.read_accel_data()
        magnitude = (accel_data['x']**2 + accel_data['y']**2 + accel_data['z']**2)**0.5
        if magnitude > 20:
            golpes_contados += 1
            # Piscar LEDs em uma cor aleatória por 100ms
            random_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            blink_leds(leds, [random_color], 0.1)
    else:
        countdown_timer.deinit()
        # Apresentar a quantidade de golpes com "G" no dígito mais à esquerda
        tm.write([ord('G'), golpes_contados // 10, golpes_contados % 10, 127])
        # Piscar o número de golpes 5 vezes com intervalo de 500ms
        for _ in range(5):
            update_display(golpes_contados)
            time.sleep(0.5)
            tm.write([0, 0, 0, 0])
            time.sleep(0.5)
        # Deixar o valor fixo na tela
        update_display(golpes_contados)
        # Aguardar pressionamento de qualquer botão para voltar ao menu
        while True:
            if BUTTON_1.pin.value() == 0 or BUTTON_2.pin.value() == 0:
                menu_active = True
                break
        print("Contagem finalizada!")

BUTTON_1 = DebouncedInput(pin_num=18, callback=button_callback, pin_pull=Pin.PULL_UP, pin_logic_pressed=False)
BUTTON_2 = DebouncedInput(pin_num=19, callback=button_callback, pin_pull=Pin.PULL_UP, pin_logic_pressed=False)

# Inicialização do Sistema
print("Inicializando o sistema...")
display_all_segments(tm, 1)
tm.brightness(4)
tm.show("OLA")
colors = [(0, 255, 0), (0, 0, 255), (255, 0, 0)]
blink_leds(leds, colors, 0.5)
print(f"Temperatura: {mpu.read_temperature():.2f} °C")
accel_data = mpu.read_accel_data()
print(f"Aceleração: X={accel_data['x']:.2f} m/s², Y={accel_data['y']:.2f} m/s², Z={accel_data['z']:.2f} m/s²")

set_leds_color(leds, (0, 0, 0))
print("Iniciando o menu de seleção de tempo...")
update_display(selected_time)

# Loop Principal
while menu_active:
    check_buttons_simultaneous()
    time.sleep(0.1)

if countdown_started:
    start_countdown()

print(f"Tempo final selecionado: {selected_time} segundos")
tm.number(selected_time)
print("Sistema finalizado com sucesso!")