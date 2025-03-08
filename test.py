from sklearn.neighbors import KNeighborsClassifier
import cv2
import pickle
import numpy as np
import os
import csv
import time
from datetime import datetime

from win32com.client import Dispatch

def Speaking(str):
    speak = Dispatch('SAPI.SpVoice')
    speak.Speak(str)
    
if not os.path.exists('data'):
    os.makedirs('data')

video = cv2.VideoCapture(0)
face_detect = cv2.CascadeClassifier('haarcascade_frontalface_default.xml') 

with open ('data/names.pkl','rb') as f:
        LABELS = pickle.load(f)
        
with open ('data/faces_data.pkl','rb') as f:
        FACES = pickle.load(f)
        
KNN = KNeighborsClassifier(n_neighbors=5)
KNN.fit(FACES,LABELS)

image_background = cv2.imread('background.png')

COLUMN_NAMES = ['NAME','TIME']

while True:  
    
    ret , frame = video.read()
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    faces = face_detect.detectMultiScale(gray, 1.3, 5)

    for (x,y,w,h) in faces:
        crop_img = frame[y:y+h, x:x+w, :]
        resized_img = cv2.resize(crop_img,(50,50)).flatten().reshape(1,-1)
        output = KNN.predict(resized_img)
        
        ts = time.time()
        date = datetime.fromtimestamp(ts).strftime("%d-%m-%Y")
        timestamp = datetime.fromtimestamp(ts).strftime("%H:%M-%S")
        
        exist=os.path.isfile("Attendance/Attendance_" + date + ".csv")
        
        cv2.rectangle(frame, (x,y),(x+w,y+h), (255,0,0), 1)
        cv2.putText(frame, str(output[0]), (x,y-15), cv2.FONT_HERSHEY_COMPLEX, 1, (0,0,255), 2)
        
        attendance = [str(output[0]), str(timestamp)]
    
    image_background[162:162 + 480, 55:55 + 640] = frame
    cv2.imshow("Frame",image_background)
    
    k = cv2.waitKey(1)
    
    if k == ord("o"):
        
        Speaking("Attendance Marked")
        time.sleep(5)
        
        if exist:
            with open ("Attendance/Attendance_" + date + ".csv","+a") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(attendance)
            csvfile.close()

        else:
            with open ("Attendance/Attendance_" + date + ".csv","+a") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(COLUMN_NAMES)
                writer.writerow(attendance)
            csvfile.close()
    
    if k == ord("q") :
        break
    
video.release()
cv2.destroyAllWindows()

