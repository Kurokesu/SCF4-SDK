import cv2
import os
import serial
import sys
import scf4_tools
import time
import threading
import camera

CHC_MOVE    = 8
CHB_MOVE    = 7
CHA_MOVE    = 6
CHC_PI      = 5
CHB_PI      = 4
CHA_PI      = 3
CHC_POS     = 2
CHB_POS     = 1
CHA_POS     = 0

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

# define ROI center of the frame
roi_size = 100
x0 = int(1920/2-roi_size)
x1 = int(1920/2+roi_size)
y0 = int(1080/2-roi_size)
y1 = int(1080/2+roi_size)
#c.focus_tracker(True, x0, x1, y0, y1)


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

print("Get bus voltage")
adc = scf4_tools.send_command(ser, "M247", echo=True)
adc = (float)(adc.split("=")[1])
volts = adc/4096.0*3.3/0.5
print("  V(bus)=", round(volts, 2), "V")





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



print("Get status")
status_str = scf4_tools.send_command(ser, "!1")
status = scf4_tools.parse_status(status_str)
print(status_str)



# A:17850...38650
# B:28500...38000
c.set_cam_text("Moving to preset position")
print()
print("Move to zoom preset position")
#scf4_tools.send_command(ser, "G0 A17850")
scf4_tools.send_command(ser, "G0 A30000")
#scf4_tools.send_command(ser, "G0 A38000")
scf4_tools.wait_homing(ser, 1, CHA_MOVE)        # Wait until homing is over

scf4_tools.send_command(ser, "G0 B35020")
scf4_tools.wait_homing(ser, 1, CHB_MOVE)        # Wait until homing is over

#c.set_cam_text("Done")



print("Done")
time.sleep(1)
#c.set_cam_text("")


#TODO: sweep full focus range and measure focus table
#TODO: go to best focus position


while True:
    c.set_cam_text("Click mouse on the image to autofocus")
    time.sleep(0.1)

    if c.mouse_clicked:
        c.mouse_clicked = False
        focus_table = []
    
        c.set_cam_text("Moving to MIN foxus point")
        scf4_tools.send_command(ser, "G0 B29000")
        scf4_tools.wait_homing(ser, 1, CHB_MOVE)

        scf4_tools.send_command(ser, "M240 B5000")    # make motor move slower
        c.set_cam_text("Searching for best focus position (full range)")
        scf4_tools.send_command(ser, "G0 B38000")

        for i in range(10000):
            status_str = scf4_tools.send_command(ser, "!1")
            status = scf4_tools.parse_status(status_str)
            #print(status[1], c.focus_val)
            focus_table.append([status[1], c.focus_val])
            time.sleep(0.01)
            if 1 != status[CHB_MOVE]:
                break
        time.sleep(0.1)

        focus_peak_val = -1
        focus_peak_pos = -1

        for f in focus_table:
            if f[1] > focus_peak_val:
                focus_peak_pos= f[0]
                focus_peak_val = f[1]
        
        print()
        print("Best focus pos:", focus_peak_pos)
        print("Best focus val:", focus_peak_val)
        
        # experimental offset value. due to camera frame and motor mismatch
        focus_peak_pos -= 100
        scf4_tools.send_command(ser, "M240 B600")    # make motor move normal

        c.set_cam_text("Moving to best position")
        scf4_tools.send_command(ser, "G0 B"+str(focus_peak_pos))
        scf4_tools.wait_homing(ser, 1, CHB_MOVE)


    if not c.running:
        break

print("Stopping camera")

c.stop()

