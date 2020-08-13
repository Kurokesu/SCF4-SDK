from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
import serial
import time
import queue


IDLE_TIMEOUT = 100
CHC_MOVE     = 8
CHB_MOVE     = 7
CHA_MOVE     = 6
CHC_PI       = 5
CHB_PI       = 4
CHA_PI       = 3
CHC_POS      = 2
CHB_POS      = 1
CHA_POS      = 0


class SerialComm(QObject):
    strStatus = pyqtSignal(str)
    strVersion = pyqtSignal(str)
    strVoltage = pyqtSignal(str)
    feedback = pyqtSignal(list)

    port = None
    commands = queue.Queue()
    action_connect = queue.Queue()
    action_disconnect = queue.Queue()
    action_recipe = queue.Queue()

    def connect(self, port, baudrate, seek_timeout):
        self.port = port
        self.baudrate = baudrate
        self.action_connect.put(True)
        self.seek_timeout = seek_timeout

    def disconnect(self):
        self.action_disconnect.put(True)

    def send(self, data):
        self.commands.put(data)

    def __ser_send(self, ser, data):
        ser.write(bytes(data+'\r\n', 'utf8'))
        r = ser.readline().decode("utf-8").strip()
        return r

    def __parse_status(self, status_string):
        temp = status_string.split(",")
        ret = []
        for t in temp:
            ret.append(int(t.strip()))
        return ret

    def __wait_till_stop(self, ser, initial_status, axis, timeout=5):
        elapsed_time = 0
        start_time = time.time()
        while elapsed_time < timeout:
            elapsed_time = time.time() - start_time
            status_str = self.__ser_send(ser, "!1")
            status = self.__parse_status(status_str)
            self.feedback.emit(status)
            time.sleep(0.05)
            if initial_status != status[axis]:
                return elapsed_time
        return -1


    @pyqtSlot()
    def serial_worker(self):
        idle_counter = 0
        status_version = ""

        while True:
            try:
                stay_connected = True
                #self.strStatus.emit("Idle")
                self.action_connect.get()  # in general - wait until connect button is pressed
                #self.action_connect.clear()

                self.strStatus.emit("Connecting...")
                ser = serial.Serial()
                ser.port = str(self.port)
                ser.baudrate = int(self.baudrate)
                ser.timeout = 1

                res = ser.open()
                ser.flushInput()
                ser.flushOutput()

                self.strStatus.emit("Connected")

                while stay_connected:
                    if not self.action_disconnect.empty():
                        self.action_disconnect.get()
                        #self.action_disconnect.clear()
                        stay_connected = False

                    # some commands require certain seqence and testing, these are put into recipes
                    if not self.action_recipe.empty():
                        rec = self.action_recipe.get()
                        #self.action_recipe.clear()

                        if rec == "init":
                            self.__ser_send(ser, '$B2')
                            self.__ser_send(ser, "M243 C6")                   # stepping (should be set 64 by default)
                            self.__ser_send(ser, "M243 A2")                   # stepping (should be set 64 by default)
                            self.__ser_send(ser, "M243 B2")                   # stepping (should be set 64 by default)
                            self.__ser_send(ser, 'M230')                      # set normal move
                            self.__ser_send(ser, 'G91')                       # set to rel movement mode (just in case it is not set yet)
                            self.__ser_send(ser, "M238")                      # Energize PI leds
                            self.__ser_send(ser, "M234 A180 B180 C180 D90")                  # set motor power
                            self.__ser_send(ser, "M235 A50 B50 C90")             # set motor sleep power
                            self.__ser_send(ser, "M240 A5000 B5000 C5000")                 # Set motor drive speed #TODO: remove and use use config settings from main
                            self.__ser_send(ser, "M232 A2000 B2000 C2000 E3000 F3000 G3000")  # Set PI low/high detection voltage

                            idle_counter = 0

                        if rec == "version":
                            ser.write(bytes('$S\r\n', 'utf8'))
                            r = ser.readline().decode("utf-8").strip()
                            self.strVersion.emit(r)
                            idle_counter = 0

                        if rec == "status1":
                            status_version = "status1"
                            ser.write(bytes('!1\r\n', 'utf8'))
                            r = ser.readline().decode("utf-8").strip()
                            st = []
                            for i in r.split(","):
                                st.append(int(i.strip()))
                            self.feedback.emit(st)
                            idle_counter = 0

                        if rec == "status2":
                            status_version = "status2"
                            ser.write(bytes('!1\r\n', 'utf8'))
                            r = ser.readline().decode("utf-8").strip()
                            st = []
                            for i in r.split(","):
                                st.append(int(i.strip()))
                            self.feedback.emit(st)
                            idle_counter = 0

                            ser.write(bytes('M247\r\n', 'utf8'))
                            r = ser.readline().decode("utf-8").strip()
                            self.strVoltage.emit(r)
                            idle_counter = 0



                        if rec == "seek_a":
                            self.__ser_send(ser, "G91")
                            self.__ser_send(ser, "M230 A")          # Set motion back to normal mode
                            self.__ser_send(ser, "G0 A13000")       # move forward (and move back to find PI to eliminate hysteresis)
                            self.__wait_till_stop(ser, 1, CHA_MOVE) # Wait until homing is over

                            status_str = self.__ser_send(ser, "!1")
                            status = self.__parse_status(status_str)

                            self.__ser_send(ser, "M231 A")          # Set motion to forced mode
                            self.__ser_send(ser, "G0 A-100")
                            self.__wait_till_stop(ser, status[CHA_PI], CHA_PI)     # Wait until homing is over

                            self.__ser_send(ser, "M230 A")          # Set motion back to normal mode
                            self.__ser_send(ser, "G92 A0")          # set current coordinate to 0
                            self.__ser_send(ser, "G0 A-8900")       # still using relative coordinate system move a bit
                            self.__wait_till_stop(ser, 1, CHA_MOVE) # Wait until homing is over
                            self.__ser_send(ser, "G92 A0")          # set current coordinate to 0
                            self.__ser_send(ser, "G90")
                            idle_counter = 0

                        if rec == "seek_b":
                            self.__ser_send(ser, "G91")
                            self.__ser_send(ser, "M230 B")          # Set motion back to normal mode
                            self.__ser_send(ser, "G0 B10000")        # move forward (and move back to find PI to eliminate hysteresis)
                            self.__wait_till_stop(ser, 1, CHB_MOVE) # Wait until homing is over

                            status_str = self.__ser_send(ser, "!1")
                            status = self.__parse_status(status_str)

                            self.__ser_send(ser, "M231 B")          # Set motion to forced mode
                            self.__ser_send(ser, "G0 B-100")        # move lens until PI toggles
                            self.__wait_till_stop(ser, status[CHB_PI], CHB_PI)     # Wait until homing is over

                            self.__ser_send(ser, "M230 B")          # Set motion back to normal mode
                            self.__ser_send(ser, "G92 B0")          # set current coordinate to 0
                            self.__ser_send(ser, "G0 B-5000")       # still using relative coordinate system move a bit
                            self.__wait_till_stop(ser, 1, CHB_MOVE) # Wait until homing is over
                            self.__ser_send(ser, "G92 B0")          # set current coordinate to 0
                            self.__ser_send(ser, "G90")
                            idle_counter = 0

                        if rec == "seek_c":
                            self.__ser_send(ser, "G91")
                            self.__ser_send(ser, "M230 C")          # Set motion back to normal mode
                            self.__ser_send(ser, "G0 C5500")        # move forward (and move back to find PI to eliminate hysteresis)
                            self.__wait_till_stop(ser, 1, CHC_MOVE) # Wait until homing is over

                            status_str = self.__ser_send(ser, "!1")
                            status = self.__parse_status(status_str)

                            self.__ser_send(ser, "M231 C")          # Set motion to forced mode
                            self.__ser_send(ser, "G0 C-100")        # move lens until PI toggles
                            self.__wait_till_stop(ser, status[CHC_PI], CHC_PI)     # Wait until homing is over

                            self.__ser_send(ser, "M230 C")          # Set motion back to normal mode
                            self.__ser_send(ser, "G92 C0")          # set current coordinate to 0
                            self.__ser_send(ser, "G0 C-5000")       # still using relative coordinate system move a bit
                            self.__wait_till_stop(ser, 1, CHC_MOVE) # Wait until homing is over
                            self.__ser_send(ser, "G92 C0")          # set current coordinate to 0
                            self.__ser_send(ser, "G90")
                            idle_counter = 0


                    # read bare command
                    if not self.commands.empty():
                        f = self.commands.get()
                        # got it - clean queue????
                        #print(f)
                        ser.write(bytes(f, 'utf8'))
                        r = ser.readline().decode("utf-8").strip()
                        #print(f, r)
                        idle_counter = 0

                    if len(status_version) > 1:
                        if idle_counter >= IDLE_TIMEOUT:
                            idle_counter = 0
                            self.action_recipe.put(status_version)

                    # count few cycles with no delay
                    idle_counter += 1

                    # if delay count > xxx add delay
                    # if delay count > yyy add put recipe status

                ser.close()
                self.strStatus.emit("Disconnected")

            except Exception as e:
                self.strStatus.emit("Error:"+str(e))
                time.sleep(1)

            self.strStatus.emit("Disconnected")
