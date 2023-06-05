'''Given video path, extract frames for all videos. Check if frames exist first.'''

import os
import argparse
from pathlib import Path
import cv2
from tqdm import tqdm
import sys

if __name__ == '__main__':
    root_path = sys.argv[1]
    video_path = os.path.join(root_path, 'PSI_Videos/videos')
    frames_path = os.path.join(root_path, 'frames')

    #create 'data/frames' folder
    if not os.path.exists(frames_path):
        os.makedirs(frames_path)
        print("Created 'frames' folder.")
        
    for video in tqdm(sorted(os.listdir(video_path))):
        name = video.split('.mp4')[0]
        video_target = os.path.join(video_path, video)
        frames_target = os.path.join(frames_path, name)

        if not os.path.exists(frames_target):
            os.makedirs(frames_target)
            print(f'Created frames folder for video {name}')

        try:
            vidcap = cv2.VideoCapture(video_target)
            if not vidcap.isOpened():
                raise Exception(f'Cannot open file {video}')
        except Exception as e:
            raise e

        success, frame = vidcap.read()
        cur_frame = 0
        while(success):
            frame_num = str(cur_frame).zfill(3)
            cv2.imwrite(os.path.join(frames_target, f'{frame_num}.jpg'), frame)
            success, frame = vidcap.read()
            cur_frame += 1
        vidcap.release()
        # break

