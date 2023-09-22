import os
import shutil
import cv2
import threading
from datetime import datetime
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

# Authenticate and create the PyDrive client
gauth = GoogleAuth()
gauth.LocalWebserverAuth()
drive = GoogleDrive(gauth)

# Create a folder in Google Drive to store the recorded videos
folder_name = "Recorded Videos " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
folder = drive.CreateFile({'title': folder_name, 'mimeType': 'application/vnd.google-apps.folder'})
folder.Upload()
folder_id = folder['id']

# Set up OpenCV video capture
cam = cv2.VideoCapture(0)

# Set up utility variables and functions
if  os.path.exists('recorded_videos'):
     shutil.rmtree('recorded_videos')
     
if not os.path.exists('recorded_videos'):
    os.makedirs('recorded_videos')


body_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_fullbody.xml')
font2 = cv2.FONT_HERSHEY_DUPLEX
fourcc = cv2.VideoWriter_fourcc(*'XIVD')

#  This is a common size for video frames, and it can help to reduce the size of the video file.
def record_clip(rec_frame, out):
    rec_frame = cv2.resize(rec_frame, (640, 480))    # resize original frame
    out.write(rec_frame)
    



def relaunch(video_count):
    print("System relaunch #" + str(video_count))
    out = cv2.VideoWriter("recorded_videos/rec_" + str(video_count) +".mp4",  fourcc, 20.0, (640,  480))
    print("* * * * * * * * VIDEO complete * * * * * ")
    return out

def analysis():
    some_motion = False
    video_count = 0
    count = 0
    out = relaunch(video_count)

    while True:
        _, frame1 = cam.read()
        _, frame2 = cam.read()
        # cv2.imshow('Difference Image', frame1)

        y = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame1, "TIME:  " + str(y), (50, 50), font2, 1, (255, 255, 255), 2)
        
        # Motion analysis
        diff = cv2.absdiff(frame1, frame2)
        gray = cv2.cvtColor(diff, cv2.COLOR_RGB2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)

        _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)

        dilated = cv2.dilate(thresh, None, iterations=3)
        contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        # Display the result
        for c in contours:
            if cv2.contourArea(c) > 2000:
                some_motion = True
                print("[!] Motion triggered")
                x, y, w, h = cv2.boundingRect(c)
                cv2.rectangle(frame1, (x, y), (x+w, y+h), (0, 255, 0), 2)

        if some_motion == True:
            if count < 150:
                record_clip(frame1, out)
                count = count + 1
            else:
                print("[DONE] Recording Done")
                some_motion = False
                count = 0
                video_count = video_count + 1
                new_out = relaunch(video_count)
                out = new_out
                    
        cv2.imshow('Transmit frame', frame1)
       
        if cv2.waitKey(10) == ord('q'):
            out.release()  # release the video writer
            cv2.destroyAllWindows() 
            for i in range(video_count+1):
                file = drive.CreateFile({'title': 'rec_' + str(i) + '.MP4', 'parents': [{'id': folder_id}]})
                file.SetContentFile("recorded_videos/rec_" + str(i) + ".mp4")
                file.Upload()
            break

thread_motion_detection = threading.Thread(target=analysis)
thread_motion_detection.start()