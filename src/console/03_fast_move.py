__author__      = "Saulius Lukse"
__copyright__   = "Copyright 2019, Kurokesu"
__license__     = "MIT"


import serial

def send_command(ser, cmd, echo=True):
    ser.write(bytes(cmd+"\n", 'utf8'))
    data_in = ser.readline().decode('utf-8').strip()
    if echo:
        print("")
        print("> "+cmd)
        print("< "+data_in)
    return data_in


ser = serial.Serial()
ser.port = 'COM21'              # Controller com port
ser.baudrate = 115200           # BAUD rate when connected over CDC USB is not important
ser.timeout = 5                 # max timeout to wait for command response

ser.open()
ser.flushInput()
ser.flushOutput()


# Read controller version strings
send_command(ser, "$S")

# Initialize controller
send_command(ser, "$B2")

send_command(ser, "G0 A-1000")
send_command(ser, "G4 P100")
send_command(ser, "G0 A1000")
send_command(ser, "G4 P100")

send_command(ser, "G0 A-1000")
send_command(ser, "G4 P100")
send_command(ser, "G0 A1000")
send_command(ser, "G4 P500")



send_command(ser, "G0 A-4000")
send_command(ser, "G4 P200")

send_command(ser, "G0 A-1000")
send_command(ser, "G4 P100")
send_command(ser, "G0 A1000")
send_command(ser, "G4 P100")

send_command(ser, "G0 A01000")
send_command(ser, "G4 P100")
send_command(ser, "G0 A-1000")
send_command(ser, "G4 P100")
send_command(ser, "G0 A01000")
send_command(ser, "G4 P100")
send_command(ser, "G0 A-1000")
send_command(ser, "G4 P500")

send_command(ser, "G0 A4000")
send_command(ser, "G4 P200")
