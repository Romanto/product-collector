import cv2
import numpy as np


class ImageFrame:

    def __init__(self, images):
        self.img = []
        self.img.extend([cv2.imread(img, -1) for img in images])

    def __enter__(self):
        print("Start working on image")

    @staticmethod
    def ident_object_by_color(frame, color):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        # define range of blue color in HSV
        colors = {
                  'red': [[0, 50, 50], [20, 255, 255]],
                  'yellow': [[20, 50, 50], [50, 255, 255]],
                  'green': [[50, 50, 50], [100, 255, 255]],
                  'blue': [[100, 50, 50], [130, 255, 255]],
                  'white': [[0, 0, 230], [255, 30, 255]],
                  'all': [[0, 0, 0], [360, 255, 255]]
                  }
        mask = cv2.inRange(hsv, np.array(colors[color][0]), np.array(colors[color][1]))
        # Bitwise-AND mask and original image
        res = cv2.bitwise_and(frame, frame, mask=mask)
        return ImageFrame.draw_contours(res, mask)
        # cv2.imshow('frame', frame)
        # cv2.imshow('mask', mask)
        # cv2.imshow('res', res)
        # cv2.destroyAllWindows()

    @staticmethod
    def draw_contours(frame, mask):
        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        cv2.drawContours(frame, contours, -1, (0, 255, 0), 3)
        return frame

    def image_to_pixels_list(self):
        """This function will read given image/frame and return it as pixels list,
        note every three following numbers are pixel"""
        for row in self.img:
            img_in_pix = []
            for pixel in row:
                img_in_pix.extend(pixel)
            return img_in_pix

    @staticmethod
    def display_image(img):
        """This function will display image"""
        cv2.namedWindow('image', cv2.WINDOW_NORMAL)
        cv2.imshow('image', img)
        cv2.moveWindow('image', 100, 100)
        cv2.waitKey(0) & 0xFF

    @staticmethod
    def save_image(image, image_name):
        """Saving image to new file"""
        cv2.imwrite(f'{image_name}.jpg', image)

    def compare2images(self):
        if self.img[0].shape == self.img[1].shape:
            print("The images have same size and channels")
            difference = cv2.subtract(self.img[0], self.img[1])
            b, g, r = cv2.split(difference)

            if cv2.countNonZero(b) == 0 and cv2.countNonZero(g) == 0 and cv2.countNonZero(r) == 0:
                print("The images are completely Equal")
            else:
                print("The images are not Equal")
            ImageFrame.display_image(self.img[0])
            ImageFrame.display_image(self.img[1])
            cv2.waitKey(0)
            cv2.destroyAllWindows()

    def __exit__(self, exc_type, exc_val, exc_tb):
        cv2.destroyAllWindows()
