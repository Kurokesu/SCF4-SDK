import serial
import time

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
#send_command(ser, "G91")

#send_command(ser, "M234 D20")
#send_command(ser, "M8")
#send_command(ser, "G4 P500")
#send_command(ser, "M7")
#send_command(ser, "G4 P500")

#send_command(ser, "$B3")
#send_command(ser, "!1")

send_command(ser, "M240 C400")  # Set motor drive speed

send_command(ser, "M241 C0")    
send_command(ser, "M242 C142")  
send_command(ser, "M243 C6")    # stepping (should be set 64 by default)
send_command(ser, "M244 C0")    
send_command(ser, "M234 C100")  # set motor power
send_command(ser, "M235 C50")    # set motor sleep power

#send_command(ser, "G0 C3200")   
#send_command(ser, "G4 P1000")
#send_command(ser, "!1")

#send_command(ser, "G0 C-3200")
#send_command(ser, "G4 P2000")

send_command(ser, "G0 C64000") # 20 turns, ar galima didinti apsisukimo skaiciu???
#send_command(ser, "G4 P2000")

'''
total_steps = 3200
step_size = 1
for i in range(int(total_steps / step_size)):
    send_command(ser, "G0 C"+str(step_size))
    #send_command(ser, "G4 P1")

'''
