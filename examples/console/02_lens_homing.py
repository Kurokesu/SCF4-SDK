import os
import serial
import sys
import scf4_tools
import time

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
ser.port = 'COM21'              # Controller com port
ser.baudrate = 115200           # BAUD rate when connected over CDC USB is not important
ser.timeout = 5                 # max timeout to wait for command response

ser.open()
ser.flushInput()
ser.flushOutput()



# Read controller version strings
scf4_tools.send_command(ser, "$S")

# Initialize controller
scf4_tools.send_command(ser, "$B2")


# Energize PI leds
scf4_tools.send_command(ser, "M238")
# Set motion to forced mode
scf4_tools.send_command(ser, "M231 A")

# read status
status_str = scf4_tools.send_command(ser, "!1")
status = scf4_tools.parse_status(status_str)

# For particular lens if PI is 1, we shoud move backwards
print("!!", status[CHA_PI])
if status[CHA_PI] == 0:
    # move lens axis back, until PI changes status
    scf4_tools.send_command(ser, "G0 A100")
else:
    # move lens axis back, until PI changes status
    scf4_tools.send_command(ser, "G0 A-100")

# Wait until homing is over
scf4_tools.wait_homing(ser, status[CHA_PI], CHA_PI)
# sleep a bit! why???
scf4_tools.send_command(ser, "G4 P100")
# set motion to back normal
scf4_tools.send_command(ser, "M230 A")
# stil using relative coordinate system move a bit
scf4_tools.send_command(ser, "G0 A-1000")

print()
for i in range(30):
    status_str = scf4_tools.send_command(ser, "!1")
    status = scf4_tools.parse_status(status_str)
    print(status)
    time.sleep(0.01)

# De-energize PI leds
scf4_tools.send_command(ser, "M239")
