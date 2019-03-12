import cv2
import numpy as np


class Imager:

    def __init__(self, image):
        self.img = cv2.imread(image)

    def __enter__(self):
        print("Start working on image")

    def image_to_pixels_list(self):
        """This function will read given image/frame and return it as pixels list,
        note every three following numbers are pixel"""
        for row in self.img:
            img_in_pix = []
            for pixel in row:
                img_in_pix.extend(pixel)
            return img_in_pix

    def display_image(self):
        """This function will display image"""
        cv2.imshow('image', self.img)
        cv2.waitKey(0)

    @staticmethod
    def save_image(image, image_name):
        """Saving image to new file"""
        cv2.imwrite(f'{image_name}.jpg', image)

    def __exit__(self, exc_type, exc_val, exc_tb):
        cv2.destroyAllWindows()
