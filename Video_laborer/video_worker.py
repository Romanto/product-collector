import cv2
import numpy as np
from Image_laborer.img_worker import *


class Video:
    def __init__(self, source):
        self.cap = cv2.VideoCapture(source)

    def __enter__(self):
        print('Starting computer camera')
        return self

    def video_object_detection(self, color):
        img = ImageFrame([])
        while True:
            _, frame = self.cap.read()
            res = img.ident_object_by_color(frame, color)
            cv2.imshow("FRAME", res)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        self.cap.release()
        cv2.destroyAllWindows()

    def draw_contours_by_color(self):
        while True:
            _, frame = self.cap.read()
            blurred_frame = cv2.GaussianBlur(frame, (5, 5), 0)
            hsv = cv2.cvtColor(blurred_frame, cv2.COLOR_BGR2HSV)
            lower_blue = np.array([38, 86, 0])
            upper_blue = np.array([121, 255, 255])
            mask = cv2.inRange(hsv, lower_blue, upper_blue)
            contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
            cv2.drawContours(frame, contours, -1, (0, 255, 0), 2)
            cv2.imshow("Frame", frame)
            cv2.imshow("Mask", mask)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        self.cap.release()
        cv2.destroyAllWindows()

    def camera_vision(self):
        while True:
            firs_frame = self.cap.read()[1]
            second_frame = self.cap.read()[1]
            delta_frames = cv2.absdiff(cv2.cvtColor(firs_frame, cv2.COLOR_BGR2GRAY), cv2.cvtColor(second_frame, cv2.COLOR_BGR2GRAY))
            blurred_frame = cv2.GaussianBlur(delta_frames, (5, 5), 0)
            ret_thres_value, thres_frame = cv2.threshold(blurred_frame, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
            contours, _ = cv2.findContours(thres_frame, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
            temp_contours = [cnt for cnt in contours if ret_thres_value > 5.0]
            cv2.drawContours(firs_frame, temp_contours, -1, (0, 255, 0), 2)
            cv2.imshow("Frame", firs_frame)
            """Press 'q' for exit"""
            if cv2.waitKey(7) & 0xFF == ord('q'):
                break
        self.cap.release()
        cv2.destroyAllWindows()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """When everything done, release the capture"""
        print('Exit')

