from Video_laborer import video_worker, Config
import numpy as np
import cv2

# Create a black image
img = np.zeros((512,512,3), np.uint8)
cv2.imshow('image', img)
# Draw a diagonal blue line with thickness of 5 px
img = cv2.line(img,(0,0),(511,511),(255,0,0),5)
cv2.imshow('image', img)
m=0
obj = video_worker.Video(Config.Video)
obj.camera_vision()


