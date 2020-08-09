import sys
import os
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5 import sip
from PyQt5.QtCore import Qt, QTimer, QThread
import queue
import utils
import hw_serial
import gui
import version

if sys.platform == 'win32':
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)


SETTINGS_FILE = 'settings.json'
MOVE_REL      = 0
MOVE_ABS      = 1

# print(sys.version)

if os.name == 'nt':
    from serial.tools.list_ports_windows import *
elif sys.platform == 'darwin':
    from serial.tools.list_ports_osx import *
    from serial.tools.list_ports_vid_pid_osx_posix import *
elif os.name == 'posix':
    from serial.tools.list_ports_posix import *
    from serial.tools.list_ports_vid_pid_osx_posix import *
else:
    raise ImportError("Serial error: no implementation for your platform ('%s') available" % (os.name,))

ser = serial.Serial()
q = queue.Queue()
q_labels = queue.Queue()

running = True


class MyWindowClass(QtWidgets.QMainWindow, gui.Ui_MainWindow):
    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        self.setupUi(self)

        self.original_window_name = self.windowTitle()
        self.setWindowTitle(self.original_window_name + " (" + version.__version__ + ")")


        self.config = {}
        self.config = utils.json_boot_routine(SETTINGS_FILE)
        self.feedback = []
        self.controls_enabled = False
        self.move_mode = MOVE_REL

        # get available com ports
        self.combo_ports.clear()
        com_ports = sorted(comports())
        for port, desc, hwid in com_ports:
            self.combo_ports.addItem(port.strip())

        # set last selected com port
        self.combo_ports.setCurrentIndex(self.combo_ports.findText(self.config["port"]))

        # setup serial class
        self.hw = hw_serial.SerialComm()
        self.thread_serial = QThread()
        self.hw.strStatus.connect(self.serStatus)
        self.hw.strVersion.connect(self.serVersion)
        self.hw.strVoltage.connect(self.serVoltage)
        self.hw.feedback.connect(self.serFeedback)
        self.hw.moveToThread(self.thread_serial)
        self.thread_serial.started.connect(self.hw.serial_worker)
        self.thread_serial.start()

        self.slider_a_speed.setMinimum(self.config["speed_min"])
        self.slider_a_speed.setMaximum(self.config["speed_max"])
        self.slider_a_speed.setValue(self.config["speed_default"])
        self.slider_a_speed.valueChanged.connect(self.slider_a_speed_changed)

        self.slider_b_speed.setMinimum(self.config["speed_min"])
        self.slider_b_speed.setMaximum(self.config["speed_max"])
        self.slider_b_speed.setValue(self.config["speed_default"])
        self.slider_b_speed.valueChanged.connect(self.slider_b_speed_changed)

        self.slider_c_speed.setMinimum(self.config["speed_min"])
        self.slider_c_speed.setMaximum(self.config["speed_max"])
        self.slider_c_speed.setValue(self.config["speed_default"])
        self.slider_c_speed.valueChanged.connect(self.slider_c_speed_changed)

        # buttons
        self.btn_connect.clicked.connect(self.btn_connect_clicked)
        self.btn_disconnect.clicked.connect(self.btn_disconnect_clicked)
        self.btn_dn1.clicked.connect(self.btn_dn1_clicked)
        self.btn_dn2.clicked.connect(self.btn_dn2_clicked)
        self.btn_aux_on.clicked.connect(self.btn_aux_on_clicked)
        self.btn_aux_off.clicked.connect(self.btn_aux_off_clicked)

        self.btn_a_left.clicked.connect(self.btn_a_left_clicked)
        self.btn_a_right.clicked.connect(self.btn_a_right_clicked)
        self.btn_b_left.clicked.connect(self.btn_b_left_clicked)
        self.btn_b_right.clicked.connect(self.btn_b_right_clicked)
        self.btn_c_left.clicked.connect(self.btn_c_left_clicked)
        self.btn_c_right.clicked.connect(self.btn_c_right_clicked)
        self.btn_a_left_fine.clicked.connect(self.btn_a_left_fine_clicked)
        self.btn_a_right_fine.clicked.connect(self.btn_a_right_fine_clicked)
        self.btn_b_left_fine.clicked.connect(self.btn_b_left_fine_clicked)
        self.btn_b_right_fine.clicked.connect(self.btn_b_right_fine_clicked)
        self.btn_c_left_fine.clicked.connect(self.btn_c_left_fine_clicked)
        self.btn_c_right_fine.clicked.connect(self.btn_c_right_fine_clicked)

        self.btn_a_0.clicked.connect(self.btn_a_0_clicked)
        self.btn_b_0.clicked.connect(self.btn_b_0_clicked)
        self.btn_c_0.clicked.connect(self.btn_c_0_clicked)

        self.btn_a_stop.clicked.connect(self.btn_a_stop_clicked)
        self.btn_b_stop.clicked.connect(self.btn_b_stop_clicked)
        self.btn_c_stop.clicked.connect(self.btn_c_stop_clicked)

        self.btn_a_seek.clicked.connect(self.btn_a_seek_clicked)
        self.btn_b_seek.clicked.connect(self.btn_b_seek_clicked)
        self.btn_c_seek.clicked.connect(self.btn_c_seek_clicked)

        self.push_pr1_set.clicked.connect(self.push_pr1_set_clicked)
        self.push_pr2_set.clicked.connect(self.push_pr2_set_clicked)
        self.push_pr3_set.clicked.connect(self.push_pr3_set_clicked)
        self.push_pr4_set.clicked.connect(self.push_pr4_set_clicked)
        self.push_pr5_set.clicked.connect(self.push_pr5_set_clicked)

        self.push_pr1_go.clicked.connect(self.push_pr1_go_clicked)
        self.push_pr2_go.clicked.connect(self.push_pr2_go_clicked)
        self.push_pr3_go.clicked.connect(self.push_pr3_go_clicked)
        self.push_pr4_go.clicked.connect(self.push_pr4_go_clicked)
        self.push_pr5_go.clicked.connect(self.push_pr5_go_clicked)

        self.btn_pi_led_on.clicked.connect(self.btn_pi_led_on_clicked)
        self.btn_pi_led_off.clicked.connect(self.btn_pi_led_off_clicked)

        # Load presets
        self.label_pr1_a.setText(str(self.config["presets"]["1"]["A"]))
        self.label_pr1_b.setText(str(self.config["presets"]["1"]["B"]))
        self.label_pr1_c.setText(str(self.config["presets"]["1"]["C"]))
        self.label_pr2_a.setText(str(self.config["presets"]["2"]["A"]))
        self.label_pr2_b.setText(str(self.config["presets"]["2"]["B"]))
        self.label_pr2_c.setText(str(self.config["presets"]["2"]["C"]))
        self.label_pr3_a.setText(str(self.config["presets"]["3"]["A"]))
        self.label_pr3_b.setText(str(self.config["presets"]["3"]["B"]))
        self.label_pr3_c.setText(str(self.config["presets"]["3"]["C"]))
        self.label_pr4_a.setText(str(self.config["presets"]["4"]["A"]))
        self.label_pr4_b.setText(str(self.config["presets"]["4"]["B"]))
        self.label_pr4_c.setText(str(self.config["presets"]["4"]["C"]))
        self.label_pr5_a.setText(str(self.config["presets"]["5"]["A"]))
        self.label_pr5_b.setText(str(self.config["presets"]["5"]["B"]))
        self.label_pr5_c.setText(str(self.config["presets"]["5"]["C"]))

        self.slider_a.sliderReleased.connect(self.slider_a_released)
        self.slider_b.sliderReleased.connect(self.slider_b_released)
        self.slider_c.sliderReleased.connect(self.slider_c_released)

        self.slider_a.valueChanged.connect(self.slider_a_changed)
        self.slider_b.valueChanged.connect(self.slider_b_changed)
        self.slider_c.valueChanged.connect(self.slider_c_changed)

    def slider_a_speed_changed(self, val):
        self.label_a_speed.setText(str(val))
        self.hw.send("M240 A" + str(val) + "\r\n")
        self.config["current"]["A"]["speed"] = val

    def slider_b_speed_changed(self, val):
        self.label_b_speed.setText(str(val))
        self.hw.send("M240 B" + str(val) + "\r\n")
        self.config["current"]["B"]["speed"] = val

    def slider_c_speed_changed(self, val):
        self.label_c_speed.setText(str(val))
        self.hw.send("M240 C" + str(val) + "\r\n")
        self.config["current"]["C"]["speed"] = val

    def slider_a_changed(self, val):
        self.label_a_setpos.setText(str(val))

    def slider_b_changed(self, val):
        self.label_b_setpos.setText(str(val))

    def slider_c_changed(self, val):
        self.label_c_setpos.setText(str(val))

    def slider_a_released(self):
        pos = self.slider_a.value()
        self.set_move_mode(MOVE_ABS)
        self.hw.send("G0 A" + str(pos) + "\r\n")

    def slider_b_released(self):
        pos = self.slider_b.value()
        self.set_move_mode(MOVE_ABS)
        self.hw.send("G0 B" + str(pos) + "\r\n")

    def slider_c_released(self):
        pos = self.slider_c.value()
        self.set_move_mode(MOVE_ABS)
        self.hw.send("G0 C" + str(pos) + "\r\n")

    def btn_pi_led_on_clicked(self):
        self.hw.send("M238\r\n")

    def btn_pi_led_off_clicked(self):
        self.hw.send("M239\r\n")

    def btn_aux_on_clicked(self):
        self.hw.send("M246\r\n")

    def btn_aux_off_clicked(self):
        self.hw.send("M245\r\n")

    def set_move_mode(self, mode):
        self.move_mode = mode
        if self.move_mode == MOVE_ABS:
            self.hw.send("G90\r\n")
        if self.move_mode == MOVE_REL:
            self.hw.send("G91\r\n")

    def controls_enable(self, status):
        # not enabled and instructed to enable
        if not self.controls_enabled and status:
            self.group_a.setEnabled(True)
            self.group_b.setEnabled(True)
            #self.group_c.setEnabled(True)
            self.group_d.setEnabled(True)
            #self.group_aux.setEnabled(True)
            self.group_pi.setEnabled(True)
            self.group_p1.setEnabled(True)
            self.group_p2.setEnabled(True)
            self.group_p3.setEnabled(True)
            self.group_p4.setEnabled(True)
            self.group_p5.setEnabled(True)
            self.controls_enabled = True

        # enabled and instructed to disable
        if self.controls_enabled and not status:
            self.group_a.setEnabled(False)
            self.group_b.setEnabled(False)
            #self.group_c.setEnabled(False)
            self.group_d.setEnabled(False)
            #self.group_aux.setEnabled(False)
            self.group_pi.setEnabled(False)
            self.group_p1.setEnabled(False)
            self.group_p2.setEnabled(False)
            self.group_p3.setEnabled(False)
            self.group_p4.setEnabled(False)
            self.group_p5.setEnabled(False)
            self.controls_enabled = False

    def set_controls(self, data):
        self.progress_a.setValue(data[0])
        self.progress_b.setValue(data[1])
        self.progress_c.setValue(data[2])

        self.label_a_pos.setText(str(data[0]))
        self.label_b_pos.setText(str(data[1]))
        self.label_c_pos.setText(str(data[2]))

        self.label_a_limitsw.setText(str(data[3]))
        self.label_b_limitsw.setText(str(data[4]))
        self.label_c_limitsw.setText(str(data[5]))

        self.label_a_status.setText(str(data[6]))
        self.label_b_status.setText(str(data[7]))
        self.label_c_status.setText(str(data[8]))

        self.config["current"]["A"]["pos"] = data[0]
        self.config["current"]["B"]["pos"] = data[1]
        self.config["current"]["C"]["pos"] = data[2]

    def btn_connect_clicked(self):
        self.config["port"] = self.combo_ports.currentText()
        self.hw.connect(self.config["port"], 115200, self.config["seek_timeout"])

    def btn_disconnect_clicked(self):
        self.hw.disconnect()

    def btn_dn1_clicked(self):
        self.hw.send("M8\r\n")

    def btn_dn2_clicked(self):
        self.hw.send("M7\r\n")

    def btn_a_left_clicked(self):
        self.set_move_mode(MOVE_REL)
        self.hw.send("G0 A-" + str(self.config["defaults"]["A"]["jog_steps"]) + "\r\n")

    def btn_a_right_clicked(self):
        self.set_move_mode(MOVE_REL)
        self.hw.send("G0 A" + str(self.config["defaults"]["A"]["jog_steps"]) + "\r\n")

    def btn_b_left_clicked(self):
        self.set_move_mode(MOVE_REL)
        self.hw.send("G0 B-" + str(self.config["defaults"]["B"]["jog_steps"]) + "\r\n")

    def btn_b_right_clicked(self):
        self.set_move_mode(MOVE_REL)
        self.hw.send("G0 B" + str(self.config["defaults"]["B"]["jog_steps"]) + "\r\n")

    def btn_c_left_clicked(self):
        self.set_move_mode(MOVE_REL)
        self.hw.send("G0 C-" + str(self.config["defaults"]["C"]["jog_steps"]) + "\r\n")

    def btn_c_right_clicked(self):
        self.set_move_mode(MOVE_REL)
        self.hw.send("G0 C" + str(self.config["defaults"]["C"]["jog_steps"]) + "\r\n")

    def btn_a_left_fine_clicked(self):
        self.set_move_mode(MOVE_REL)
        self.hw.send("G0 A-" + str(self.config["defaults"]["A"]["jog_steps_fine"]) + "\r\n")

    def btn_a_right_fine_clicked(self):
        self.set_move_mode(MOVE_REL)
        self.hw.send("G0 A" + str(self.config["defaults"]["A"]["jog_steps_fine"]) + "\r\n")

    def btn_b_left_fine_clicked(self):
        self.set_move_mode(MOVE_REL)
        self.hw.send("G0 B-" + str(self.config["defaults"]["B"]["jog_steps_fine"]) + "\r\n")

    def btn_b_right_fine_clicked(self):
        self.set_move_mode(MOVE_REL)
        self.hw.send("G0 B" + str(self.config["defaults"]["B"]["jog_steps_fine"]) + "\r\n")

    def btn_c_left_fine_clicked(self):
        self.set_move_mode(MOVE_REL)
        self.hw.send("G0 C-" + str(self.config["defaults"]["C"]["jog_steps_fine"]) + "\r\n")

    def btn_c_right_fine_clicked(self):
        self.set_move_mode(MOVE_REL)
        self.hw.send("G0 C" + str(self.config["defaults"]["C"]["jog_steps_fine"]) + "\r\n")

    def btn_a_0_clicked(self):
        self.hw.send("G92 A0\r\n")

    def btn_b_0_clicked(self):
        self.hw.send("G92 B0\r\n")

    def btn_c_0_clicked(self):
        self.hw.send("G92 C0\r\n")

    def btn_a_stop_clicked(self):
        self.hw.send("M0 A\r\n")

    def btn_b_stop_clicked(self):
        self.hw.send("M0 B\r\n")

    def btn_c_stop_clicked(self):
        self.hw.send("M0 C\r\n")

    def btn_a_seek_clicked(self):
        self.hw.action_recipe.put("seek_a")

    def btn_b_seek_clicked(self):
        self.hw.action_recipe.put("seek_b")

    def btn_c_seek_clicked(self):
        self.hw.action_recipe.put("seek_c")

    def push_pr1_set_clicked(self):
        self.config["presets"]["1"]["A"] = self.config["current"]["A"]["pos"]
        self.config["presets"]["1"]["B"] = self.config["current"]["B"]["pos"]
        self.config["presets"]["1"]["C"] = self.config["current"]["C"]["pos"]

        self.label_pr1_a.setText(str(self.config["presets"]["1"]["A"]))
        self.label_pr1_b.setText(str(self.config["presets"]["1"]["B"]))
        self.label_pr1_c.setText(str(self.config["presets"]["1"]["C"]))

    def push_pr2_set_clicked(self):
        self.config["presets"]["2"]["A"] = self.config["current"]["A"]["pos"]
        self.config["presets"]["2"]["B"] = self.config["current"]["B"]["pos"]
        self.config["presets"]["2"]["C"] = self.config["current"]["C"]["pos"]

        self.label_pr2_a.setText(str(self.config["presets"]["2"]["A"]))
        self.label_pr2_b.setText(str(self.config["presets"]["2"]["B"]))
        self.label_pr2_c.setText(str(self.config["presets"]["2"]["C"]))

    def push_pr3_set_clicked(self):
        self.config["presets"]["3"]["A"] = self.config["current"]["A"]["pos"]
        self.config["presets"]["3"]["B"] = self.config["current"]["B"]["pos"]
        self.config["presets"]["3"]["C"] = self.config["current"]["C"]["pos"]

        self.label_pr3_a.setText(str(self.config["presets"]["3"]["A"]))
        self.label_pr3_b.setText(str(self.config["presets"]["3"]["B"]))
        self.label_pr3_c.setText(str(self.config["presets"]["3"]["C"]))

    def push_pr4_set_clicked(self):
        self.config["presets"]["4"]["A"] = self.config["current"]["A"]["pos"]
        self.config["presets"]["4"]["B"] = self.config["current"]["B"]["pos"]
        self.config["presets"]["4"]["C"] = self.config["current"]["C"]["pos"]

        self.label_pr4_a.setText(str(self.config["presets"]["4"]["A"]))
        self.label_pr4_b.setText(str(self.config["presets"]["4"]["B"]))
        self.label_pr4_c.setText(str(self.config["presets"]["4"]["C"]))

    def push_pr5_set_clicked(self):
        self.config["presets"]["5"]["A"] = self.config["current"]["A"]["pos"]
        self.config["presets"]["5"]["B"] = self.config["current"]["B"]["pos"]
        self.config["presets"]["5"]["C"] = self.config["current"]["C"]["pos"]

        self.label_pr5_a.setText(str(self.config["presets"]["5"]["A"]))
        self.label_pr5_b.setText(str(self.config["presets"]["5"]["B"]))
        self.label_pr5_c.setText(str(self.config["presets"]["5"]["C"]))

    def push_pr1_go_clicked(self):
        self.set_move_mode(MOVE_ABS)
        self.hw.send("G0 A" + str(self.config["presets"]["1"]["A"]) + " B" + str(self.config["presets"]["1"]["B"]) + " C" + str(self.config["presets"]["1"]["C"]) + "\r\n")

    def push_pr2_go_clicked(self):
        self.set_move_mode(MOVE_ABS)
        self.hw.send("G0 A" + str(self.config["presets"]["2"]["A"]) + " B" + str(self.config["presets"]["2"]["B"]) + " C" + str(self.config["presets"]["2"]["C"]) + "\r\n")

    def push_pr3_go_clicked(self):
        self.set_move_mode(MOVE_ABS)
        self.hw.send("G0 A" + str(self.config["presets"]["3"]["A"]) + " B" + str(self.config["presets"]["3"]["B"]) + " C" + str(self.config["presets"]["3"]["C"]) + "\r\n")

    def push_pr4_go_clicked(self):
        self.set_move_mode(MOVE_ABS)
        self.hw.send("G0 A" + str(self.config["presets"]["4"]["A"]) + " B" + str(self.config["presets"]["4"]["B"]) + " C" + str(self.config["presets"]["4"]["C"]) + "\r\n")

    def push_pr5_go_clicked(self):
        self.set_move_mode(MOVE_ABS)
        self.hw.send("G0 A" + str(self.config["presets"]["5"]["A"]) + " B" + str(self.config["presets"]["5"]["B"]) + " C" + str(self.config["presets"]["5"]["C"]) + "\r\n")

    def closeEvent(self, event):
        global config
        global running
        utils.json_exit_routine(SETTINGS_FILE, self.config)
        running = False

    def serStatus(self, text):
        self.label_ser_status.setText(text)
        if text == "Connected":
            self.combo_ports.setEnabled(False)
            self.btn_connect.setEnabled(False)
            self.btn_disconnect.setEnabled(True)
            self.hw.action_recipe.put("init")
            self.hw.action_recipe.put("version")
            self.hw.action_recipe.put("status1")
            self.hw.action_recipe.put("voltage")

        if text == "Disconnected":
            self.combo_ports.setEnabled(True)
            self.btn_connect.setEnabled(True)
            self.btn_disconnect.setEnabled(False)
            self.controls_enable(False)

    def serVersion(self, text):
        self.label_ser_version.setText(text)

    def serVoltage(self, text):
        if text.find("ADC") >= 0:
            v = (float)(text.split("=")[1])
            v = v/4096.0*3.3/0.5

            #self.label_voltage.setText(str(round(v, 2)).format(2))
            self.label_voltage.setText('VUSB={0:01.1f}V'.format(v))

    def serFeedback(self, data):
        if len(data) == 9:
            self.controls_enable(True)
            self.feedback = data
            self.set_controls(data)


app = QtWidgets.QApplication(sys.argv)
myWindow = MyWindowClass(None)
myWindow.show()
app.exec_()
