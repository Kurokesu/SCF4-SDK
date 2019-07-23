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

# move zoom back, wait 0.5s, move forward and wait 0.5 again
send_command(ser, "G0 A-1000")
send_command(ser, "G4 P500")
send_command(ser, "G0 A1000")
send_command(ser, "G4 P500")

# move focus back, wait 0.5s, move forward and wait 0.5 again
send_command(ser, "G0 B-1000")
send_command(ser, "G4 P500")
send_command(ser, "G0 B1000")
send_command(ser, "G4 P500")

# move iris back, wait 0.5s, move forward and wait 0.5 again
send_command(ser, "G0 C-1000")
send_command(ser, "G4 P500")
send_command(ser, "G0 C1000")
send_command(ser, "G4 P500")

# Set Day/Night fiter IR+VIS, wait 0.5s, move to VIS, wait 0.5s again
send_command(ser, "M8")
send_command(ser, "G4 P500")
send_command(ser, "M7")
send_command(ser, "G4 P500")
