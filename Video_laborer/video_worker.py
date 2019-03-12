import cv2
import numpy as np


class Video:

    def __init__(self, source):
        self.cap = cv2.VideoCapture(source)

    def __enter__(self):
        print('Starting computer camera')

    def camera_vision(self):
        while True:
            """Capture frame-by-frame"""
            ret, frame = self.cap.read()
            # Our operations on the frame come here
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            """Display the resulting frame"""
            cv2.imshow('frame', gray)

            """Press 'q' for exit"""
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    def __exit__(self, exc_type, exc_val, exc_tb):
        """When everything done, release the capture"""
        self.cap.release()
        cv2.destroyAllWindows()
