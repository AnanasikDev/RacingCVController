import vgamepad as vg
import time
import math

gamepad = vg.VDS4Gamepad()

gamepad.reset()
time.sleep(2)


def angle_to_joystick(angle):
    global gamepad
    # Convert angle to radians
    angle_rad = math.radians(angle)

    # Calculate joystick coordinates
    cs = math.cos(angle_rad)
    sign = 1 if cs >= 0 else -1
    x = math.pow(abs(cs), 0.4) * sign

    gamepad.left_joystick_float(x_value_float=x, y_value_float=0)
    gamepad.update()


def pull_gas(value):

    #print("Gas:", value)

    gamepad.right_trigger_float(value)
    gamepad.update()