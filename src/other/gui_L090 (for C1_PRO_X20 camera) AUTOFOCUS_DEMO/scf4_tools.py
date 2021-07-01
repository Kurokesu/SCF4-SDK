import serial
import time

def send_command(ser, cmd, echo=False):
    ser.write(bytes(cmd+"\n", 'utf8'))
    data_in = ser.readline().decode('utf-8').strip()
    if echo:
        print("> "+cmd)
        print("< "+data_in)
        print("")
    return data_in

# Status returns 9 arguments. Internal position counter, PI status and movement status
def parse_status(status_string):
    temp = status_string.split(",")
    ret = []
    for t in temp:
        ret.append(int(t.strip()))
    return ret

def wait_homing(ser, initial_status, axis):
    for i in range(10000):
        status_str = send_command(ser, "!1")
        status = parse_status(status_str)
        #print(status[axis])
        #print(status)
        time.sleep(0.01)
        if initial_status != status[axis]:
            break
    time.sleep(0.1)
    