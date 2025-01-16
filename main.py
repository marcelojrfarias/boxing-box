from machine import Pin, SoftI2C, Timer
from neopixel import NeoPixel
from MPU6050 import MPU6050
from tm1637 import TM1637
import time
from DebouncedInput import DebouncedInput

# ==== Configuração dos dispositivos ====
CLK_PIN = Pin(13)
DIO_PIN = Pin(14)
display = TM1637(clk=CLK_PIN, dio=DIO_PIN)

LED_PIN = Pin(27, Pin.OUT)
NUM_LEDS = 12
leds = NeoPixel(LED_PIN, NUM_LEDS)

i2c = SoftI2C(scl=Pin(22), sda=Pin(21))
mpu = MPU6050()

# Variáveis globais
selected_time = 60
menu_active = True
increment_timer = Timer(-1)
decrement_timer = Timer(-1)
# countdown_timer = Timer(-1)
golpe_timer = Timer(-1)
press_start_time = {}
MAX_TIME = 999
countdown_started = False
colors = [(0, 255, 0), (0, 0, 255), (255, 0, 0)]
count_cyles = 0
min_magnitude = 30

# Controle de golpes
current_golpes = 0
last_golpe_time = time.ticks_ms()  # Para controle da amostragem

# ==== Funções Auxiliares ====
def set_leds_color(leds, color):
    for i in range(NUM_LEDS):
        leds[i] = color
    leds.write()

def cycle_leds(leds, delay):
    global colors
    for color in colors:
        set_leds_color(leds, color)
        time.sleep(delay)
    set_leds_color(leds, (0, 0, 0))  # Apagar LEDs


def update_display(time_val):
    display.number(time_val)

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
    global colors
    for i in [3, 2, 1]:
        update_display(i)
        set_leds_color(leds, colors[i-1])  # Apagar LEDs
        time.sleep(1)
    
    display.write([0, 0, 0, 0])  # Apaga o display por 500ms
    set_leds_color(leds, (0, 0, 0))  # Apagar LEDs
    
    update_display(selected_time)

    # countdown_timer.init(mode=Timer.PERIODIC, period=1000, callback=decrement_time)
    golpe_timer.init(mode=Timer.PERIODIC, period=50, callback=detect_golpe)

def decrement_time(timer=None):
    global selected_time
    
    if selected_time > 0: 
        selected_time -= 1
        update_display(selected_time)
    else:
        # countdown_timer.deinit()  
        golpe_timer.deinit()
        increment_timer.deinit()  
        decrement_timer.deinit()
        show_golpes()  # Chama a função para exibir os golpes

def detect_golpe(timer=None):
    global current_golpes, last_golpe_time, colors, selected_time, count_cyles

    count_cyles += 1
    
    accel_data = mpu.read_accel_data()
    magnitude = (accel_data['x']**2 + accel_data['y']**2 + accel_data['z']**2) ** 0.5
    
    # Se a magnitude for maior que 20 e a amostragem for adequada
    if magnitude > min_magnitude and time.ticks_ms() - last_golpe_time > 200:
        set_leds_color(leds, colors[current_golpes%3])  # Apagar LEDs
        if current_golpes < 999:  # Limite de golpes
            current_golpes += 1
            last_golpe_time = time.ticks_ms()
    
    if selected_time > 0 and count_cyles >= 20: 
        selected_time -= 1
        count_cyles = 0
        update_display(selected_time)
    elif selected_time > 0:
        count_cyles
    else:
        golpe_timer.deinit()
        increment_timer.deinit()  
        decrement_timer.deinit()
        show_golpes()  # Chama a função para exibir os golpes

def show_golpes():
    # Pisca os pontos decimais por 3 segundos (6 piscadas em 500ms)
    display.write([127, 127, 127, 127])
    time.sleep(2)
    display.write([0, 0, 0, 0])
    time.sleep(1)

    # Exibe o número de golpes no display
    update_display(current_golpes) 

    # Pisca a exibição 5 vezes
    for _ in range(5):  # Pisca 5 vezes
        time.sleep(0.5)
        display.write([0, 0, 0, 0])
        time.sleep(0.5)
        update_display(current_golpes)  # Exibe novamente

    # Espera por um botão pressionado para voltar ao menu de ajuste de tempo
    while True:
        if BUTTON_1.pin.value() == 0 or BUTTON_2.pin.value() == 0:  # Verifica se algum botão foi pressionado
            return_to_menu()  # Retorna ao menu
            break  # Sai do loop e reinicia o processo

def return_to_menu():
    global menu_active, current_golpes, selected_time
    menu_active = True
    selected_time = 60
    current_golpes = 0  # Reseta o contador de golpes
    print("Retornando ao menu de ajuste de tempo...")
    set_leds_color(leds, (0, 0, 0))  # Apagar LEDs
    display.write([0, 0, 0, 0])  # Limpa o display antes de qualquer outra coisa
    update_display(selected_time)

# Inicialização do sistema
BUTTON_1 = DebouncedInput(pin_num=18, callback=button_callback, pin_pull=Pin.PULL_UP, pin_logic_pressed=False)
BUTTON_2 = DebouncedInput(pin_num=19, callback=button_callback, pin_pull=Pin.PULL_UP, pin_logic_pressed=False)

# 1. Display pisca todos os segmentos
display.write([127, 127, 127, 127])
time.sleep(1)

# 1. Limpar o display
display.write([0, 0, 0, 0])  # Limpa o display antes de qualquer outra coisa
time.sleep(0.5)  # Aguarda meio segundo (opcional)

# 2. Ajustar brilho do display
display.brightness(4)

# 3. Mostrar 'OLA!' no display
display.show("OLA")

# 4. Piscar LEDs nas cores Verde, Azul e Vermelho
cycle_leds(leds, 0.5)

# 5. Configurar o MPU6050
mpu.set_accel_range(0x18)  # Define o alcance do acelerômetro para 16g
accel_data = mpu.read_accel_data()
print(f"Magnitude: {(accel_data['x']**2 + accel_data['y']**2 + accel_data['z']**2) ** 0.5}")

# 6. Apagar LEDs
set_leds_color(leds, (0, 0, 0))

# 7. Menu de Seleção de Tempo
update_display(selected_time)

# Loop principal
while menu_active:
    check_buttons_simultaneous()
    # detect_golpe()  # Detecção de golpes
    time.sleep(0.05)  # Intervalo para detecção de golpes a cada 50ms

if countdown_started:
    # Apaga o display por 1 segundo antes de iniciar a contagem de 3, 2, 1
    display.write([0, 0, 0, 0])
    time.sleep(1)
    start_countdown()

print("Sistema finalizado com sucesso!")