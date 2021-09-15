import cv2
import os
import serial
import sys
import scf4_tools
import time
import threading
import camera
import numpy as np
from scipy.interpolate import interp1d
from tqdm import tqdm

CHB_MOVE    = 7
CHA_MOVE    = 6
CHB_PI      = 4
CHA_PI      = 3



def parse_data(data):
    out_x = []
    out_y = []

    for i in data:
        p2 = i.split("	")
        out_x.append(int(p2[0]))
        out_y.append(int(p2[1]))

    return out_x, out_y


def scale(val, src, dst):
    return ((val - src[0]) / (src[1]-src[0])) * (dst[1]-dst[0]) + dst[0]








ser = serial.Serial()
ser.port = 'COM231'             # Controller com port
ser.baudrate = 115200           # BAUD rate when connected over CDC USB is not important
ser.timeout = 5                 # max timeout to wait for command response

print("Open COM port:", ser.port)
ser.open()
ser.flushInput()
ser.flushOutput()








c = camera.Cam()
print("Starting cam")
c.start()

print("Waiting for camera")
while c.fps == 0:
    time.sleep(0.1) # should be implemented with queue/signals but good enough for testing
print("Cam is operational")

c.set_cam_text("Prepare")
print("Read controller version strings")
scf4_tools.send_command(ser, "$S", echo=True)

print("Initialize controller")
scf4_tools.send_command(ser, "$B2", echo=True)

print("# Set motion to forced mode")
scf4_tools.send_command(ser, "M231 A", echo=True)

print("Set stepping mode")
scf4_tools.send_command(ser, "M243 C6", echo=True)

print("Set normal move")
scf4_tools.send_command(ser, 'M230', echo=True)

print("Set to rel movement mode")
scf4_tools.send_command(ser, 'G91', echo=True)

print("Energize PI leds")
scf4_tools.send_command(ser, "M238", echo=True)

print("Set motor power")
scf4_tools.send_command(ser, "M234 A190 B190 C190 D90", echo=True)

print("Set motor sleep power")
scf4_tools.send_command(ser, "M235 A120 B120 C120", echo=True)

print("Set motor drive speed")
scf4_tools.send_command(ser, "M240 A600 B600 C600", echo=True)

print("Set PI low/high detection voltage")
scf4_tools.send_command(ser, "M232 A400 B400 C400 E700 F700 G700", echo=True)

print("Filter = VIS")
scf4_tools.send_command(ser, "M7", echo=True)








c.set_cam_text("Homing A")
print()
print("Home axis A")
print("Get status")
status_str = scf4_tools.send_command(ser, "!1")
status = scf4_tools.parse_status(status_str)
print(status_str)

if status[3] == 0:
    print("Dir 1")
    scf4_tools.send_command(ser, "G91")
    scf4_tools.send_command(ser, "M231 A")          # Set motion to forced mode
    scf4_tools.send_command(ser, "G0 A+100")
    scf4_tools.wait_homing(ser, status[CHA_PI], CHA_PI)
else:
    print("Dir 2")
    scf4_tools.send_command(ser, "G91")
    scf4_tools.send_command(ser, "M231 A")          # Set motion to forced mode
    scf4_tools.send_command(ser, "G0 A-100")
    scf4_tools.wait_homing(ser, status[CHA_PI], CHA_PI)     # Wait until homing is over

print("Motor normal mode")
scf4_tools.send_command(ser, "M230 A")          # Set motion back to normal mode
scf4_tools.send_command(ser, "G0 A-200")
scf4_tools.wait_homing(ser, 1, CHA_MOVE) # Wait until homing is over

print("Motor forced mode")
scf4_tools.send_command(ser, "G91")
scf4_tools.send_command(ser, "M231 A")          # Set motion to forced mode
scf4_tools.send_command(ser, "G0 A+100")
scf4_tools.wait_homing(ser, status[CHA_PI], CHA_PI)     # Wait until homing is over

print("Set current coordinate as middle")
scf4_tools.send_command(ser, "G92 A32000")          # set current coordinate to 32000
scf4_tools.send_command(ser, "M230 A")          # Set motion back to normal mode
scf4_tools.send_command(ser, "G90")






c.set_cam_text("Homing B")
print()
print("Home axis B")
print("Get status")
status_str = scf4_tools.send_command(ser, "!1")
status = scf4_tools.parse_status(status_str)
print(status_str)

if status[4] == 0:
    print("Dir 1")
    scf4_tools.send_command(ser, "G91")
    scf4_tools.send_command(ser, "M231 B")          # Set motion to forced mode
    scf4_tools.send_command(ser, "G0 B+100")
    scf4_tools.wait_homing(ser, status[CHB_PI], CHB_PI)
else:
    print("Dir 2")

    scf4_tools.send_command(ser, "G91")
    scf4_tools.send_command(ser, "M231 B")          # Set motion to forced mode
    scf4_tools.send_command(ser, "G0 B-100")
    scf4_tools.wait_homing(ser, status[CHB_PI], CHB_PI)     # Wait until homing is over


print("Motor normal mode")
scf4_tools.send_command(ser, "M230 B")          # Set motion back to normal mode
scf4_tools.send_command(ser, "G0 B-200")
scf4_tools.wait_homing(ser, 1, CHB_MOVE)        # Wait until homing is over

print("Motor forced mode")
scf4_tools.send_command(ser, "G91")
scf4_tools.send_command(ser, "M231 B")          # Set motion to forced mode
scf4_tools.send_command(ser, "G0 B+100")
scf4_tools.wait_homing(ser, status[CHB_PI], CHB_PI)     # Wait until homing is over

print("Set current coordinate as middle")
scf4_tools.send_command(ser, "G92 B32000")          # set current coordinate to 32000
scf4_tools.send_command(ser, "M230 B")          # Set motion back to normal mode
scf4_tools.send_command(ser, "G90")










with open('line_inf2.txt') as f:
    lines = f.readlines()

x, y = parse_data(lines)

x, y = parse_data(lines)

xi = np.linspace(min(x), max(x), num=max(x)-min(x), endpoint=True)
yi = interp1d(x, y, kind='cubic')




new_list2 = []
for i in range(min(x), max(x), 10):
    y = float(np.asarray(yi(i)))
    new_list2.append((i, y))

# reverse motion directon (from wide to narrow)
new_list2 = new_list2[::-1]






print("Set motor drive speed")
scf4_tools.send_command(ser, "M240 A500 B500 C500", echo=True)

c.set_cam_text("Moving to wide angle")

(x, y) = new_list2[0]

scf4_tools.send_command(ser, "G0 A"+str(x))
scf4_tools.wait_homing(ser, 1, CHA_MOVE)        # Wait until homing is over

scf4_tools.send_command(ser, "G0 B"+str(y))
scf4_tools.wait_homing(ser, 1, CHB_MOVE)        # Wait until homing is over

print("Done")
time.sleep(1)


for i in tqdm(range(len(new_list2))):
    (x, y) = new_list2[i]

    zoom = round(scale(x, (39800, 22600), (5.5, 95)), 1)
    c.set_cam_text("Focal length: "+str(zoom)+"mm")
    scf4_tools.send_command(ser, "G0 A"+str(x)+ " B"+str(y))
    time.sleep(0.001)

c.set_cam_text("Sleeping 10s")
time.sleep(10)




f.close()


time.sleep(10)
c.stop()
