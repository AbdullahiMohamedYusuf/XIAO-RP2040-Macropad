import time
import microcontroller
import digitalio
import keypad
import rotaryio
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode

# Initialize USB Devices
keyboard = Keyboard(usb_hid.devices)
cc = ConsumerControl(usb_hid.devices)

# --- Fixed Pin Mapping ---
row_pins = (
    microcontroller.pin.GPIO7,   # ROW1 (D5) - Top
    microcontroller.pin.GPIO6,   # ROW2 (D4) - Middle
    microcontroller.pin.GPIO29,  # ROW3 (D3) - Bottom
)

col_pins = (
    microcontroller.pin.GPIO28,  # COL1 (D2) - Left
    microcontroller.pin.GPIO27,  # COL2 (D1) - Middle
    microcontroller.pin.GPIO26,  # COL3 (D0) - Right
)

# Rotary Encoder Setup
encoder = rotaryio.IncrementalEncoder(microcontroller.pin.GPIO2, microcontroller.pin.GPIO1)  # ROTA = D8, ROTB = D7

rot_sw = digitalio.DigitalInOut(microcontroller.pin.GPIO4)  # ROTSW = D9
rot_sw.direction = digitalio.Direction.INPUT
rot_sw.pull = digitalio.Pull.UP

matrix = keypad.KeyMatrix(row_pins, col_pins)

# --- Mode Configurations ---
MODE_NAMES = ["YouTube", "KiCad Schematic"]
current_mode = 0

keymaps = [
    # Mode 0: YouTube
    [
        Keycode.J,            Keycode.K,            Keycode.L,             # Top Left | Top Mid | Top Right
        Keycode.M,            Keycode.F,            Keycode.C,             # Mid Left | Mid Mid | Mid Right
        Keycode.LEFT_ARROW,   Keycode.SPACE,        Keycode.RIGHT_ARROW    # Bot Left | Bot Mid | Bot Right
    ],
    # Mode 1: KiCad Schematic
    [
        Keycode.A,            Keycode.W,            Keycode.L,             # Top Left (A) | Top Mid (W) | Top Right (L)
        Keycode.P,            Keycode.Q,            Keycode.R,             # Mid Left (P) | Mid Mid (Q) | Mid Right (R)
        Keycode.E,            Keycode.DELETE,       Keycode.ESCAPE  # Bot Left | Bot Mid | Bot Right
    ]
]

last_sw_state = True
last_encoder_pos = encoder.position

print(f"Macropad Ready! Active Mode: {MODE_NAMES[current_mode]}")

def trigger_key(key_def, is_pressed):
    if isinstance(key_def, tuple):
        if is_pressed:
            for k in key_def:
                keyboard.press(k)
        else:
            for k in reversed(key_def):
                keyboard.release(k)
    else:
        if is_pressed:
            keyboard.press(key_def)
        else:
            keyboard.release(key_def)

while True:
    # 1. Rotary Switch Press -> Change Mode
    current_sw_state = rot_sw.value
    if last_sw_state and not current_sw_state:
        current_mode = (current_mode + 1) % len(keymaps)
        print("Switched Mode ->", MODE_NAMES[current_mode])
        time.sleep(0.05)
    last_sw_state = current_sw_state

    # 2. Rotary Encoder Rotation -> Volume Control
    current_pos = encoder.position
    if current_pos != last_encoder_pos:
        diff = current_pos - last_encoder_pos
        last_encoder_pos = current_pos

        if diff > 0:
            for _ in range(abs(diff)):
                cc.send(ConsumerControlCode.VOLUME_INCREMENT)
        else:
            for _ in range(abs(diff)):
                cc.send(ConsumerControlCode.VOLUME_DECREMENT)

    # 3. Key Matrix Scanning
    matrix_event = matrix.events.get()
    if matrix_event:
        selected_key = keymaps[current_mode][matrix_event.key_number]
        trigger_key(selected_key, matrix_event.pressed)     
