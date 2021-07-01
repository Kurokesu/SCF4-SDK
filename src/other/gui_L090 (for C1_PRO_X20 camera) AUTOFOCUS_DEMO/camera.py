import threading
import cv2
import time

class Cam():

    def __init__(self, q_frame = None, scale=0.4, cam_width=1920, cam_height=1080, cam_fps=30, preview=True):
        self.running = False
        
        self.fps = 0
        self.q_frame = q_frame
        self.q_len = 10

        self.cam_width = cam_width
        self.cam_height = cam_height
        self.cam_fps = cam_fps
        self.scale = scale
        self.preview = preview
        self.focus_traker_enabled = False

        self.roi_x0 = 0
        self.roi_x1 = 0
        self.roi_y0 = 0
        self.roi_y1 = 0
        self.roi_size = 0
        self.focus_val = 0

        self.mouseX = 0 
        self.mouseY = 0
        self.mouse_clicked = False
        self.cam_text = ""

    def focus_tracker(self, enabled, x, y, size=100):
        self.roi_size = size
        
        # --fix: check min/max ranges
        self.roi_x0 = int(x-self.roi_size)
        self.roi_x1 = int(x+self.roi_size)
        self.roi_y0 = int(y-self.roi_size)
        self.roi_y1 = int(y+self.roi_size)

        self.focus_traker_enabled = enabled

    def set_cam_text(self, text):
        self.cam_text = text

    def eval_focus(self, img):
        # get ROI and calcualte Laplacian transformation        
        roi = img[self.roi_y0:self.roi_y1, self.roi_x0:self.roi_x1]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        fm = cv2.Laplacian(gray, cv2.CV_64F).var()
        return fm, roi

    def start(self, nr=0):
        self.run = True
        self.capture_thread = None
        self.nr = nr

        self.capture_thread = threading.Thread(target=self.worker)
        self.capture_thread.start()


    def get_mouse_pos(self, event, x, y, flags, param):
        #if event == cv2.EVENT_LBUTTONDBLCLK:
        if event == cv2.EVENT_LBUTTONDOWN:
            #cv2.circle(img,(x,y),100,(255,0,0),-1)
            self.mouseX, self.mouseY = x, y
            self.mouse_clicked = True
            self.focus_tracker(True, int(self.mouseX/self.scale), int(self.mouseY/self.scale))

    def stop(self):
        self.run = False
        
        try:
            self.capture_thread.join()
        except:
            pass
        
        while self.running:
            time.sleep(0.1)


    def set(self, param=None, value=None):
        self.capture.set(param, value)


    def get(self, param=None):
        self.capture.get(param)


    def worker(self):
        cv2.namedWindow('image')
        cv2.setMouseCallback('image', self.get_mouse_pos)

        self.running = True
        self.capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.capture.set(cv2.CAP_PROP_FPS, self.cam_fps)
        self.capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('m','j','p','g'))
        self.capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('M','J','P','G'))
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)


        start = time.time()
        while(self.run):
            self.capture.grab()
            ret_video = {}

            end = time.time()
            _, img = self.capture.retrieve(0)
            elapsed = end-start

            if elapsed > 0:
                self.fps = 1 / (elapsed)
            else:
                self.fps = 0
            start = end
            
            if self.focus_traker_enabled:
                self.focus_val, _ = self.eval_focus(img)

            if self.preview:
                if self.cam_text:
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    org = (50, 50)
                    fontScale = 1
                    thickness = 2
                    color = (255, 255, 255)
                    img = cv2.putText(img, self.cam_text, org, font, fontScale, color, thickness, cv2.LINE_AA)

                if self.focus_traker_enabled:
                    img = cv2.rectangle(img, (self.roi_x0, self.roi_y0), (self.roi_x1, self.roi_y1), (255,255,255), 2)

                img_r = cv2.resize(img, None, fx=self.scale, fy=self.scale, interpolation=cv2.INTER_CUBIC)
               
                cv2.imshow("image", img_r)
                k = cv2.waitKey(1) & 0xff
                if k == 27:
                    break

        self.capture.release()
        self.running = False



if __name__ == "__main__":
    c = Cam()

    print("Starting cam")
    c.start()

    c.focus_tracker(True, 1920/2, 1080/2)
  
    print("Waiting for camera")
    while c.fps == 0:
        time.sleep(0.1) # should be implemented with queue/signals but good enough for testing

    print("Cam is operational")
    while True:
        time.sleep(0.1)
        print(round(c.fps, 2), round(c.focus_val, 2))
        if not c.running:
            break

    print("Stopping camera")
    c.stop()
