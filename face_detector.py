import cv2
import pickle
import numpy as np
import os

video = cv2.VideoCapture(0)     # cv2.VideoCapture() is a function that returns a video capture object
                                # cv2.VideoCapture() takes one argument, the camera index
                                # 0 is the default camera index, it is the index of the default camera
                                # 0 is the index of the default camera on most of the systems
                                
face_detect = cv2.CascadeClassifier('haarcascade_frontalface_default.xml') 
                                # cv2.CascadeClassifier() is a function that returns a cascade classifier object
                                # cv2.CascadeClassifier() takes one argument, the path of the cascade classifier
                                # 'haarcascade_frontalface_default.xml' is a pre-trained cascade classifier for detecting faces
                                
faces_data = []                 

i = 0 

name = input("Enter your name: ")

while True:                     
    
    ret , frame = video.read()  # ret is a boolean value that returns true if the frame is available 
                                # and frame is the image array
                                # video.read() returns two values, ret and frame
                                
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                                # cv2.cvtColor() is a function that converts the color of the image
                                # cv2.cvtColor() takes two arguments, the image array and the color conversion code
                                # cv2.COLOR_BGR2GRAY is a color conversion code to convert the image to grayscale
                                
    faces = face_detect.detectMultiScale(gray, 1.3, 5)
                                # face_detect.detectMultiScale() is a function that detects objects in the image
                                # face_detect.detectMultiScale() takes three arguments, the image array, the scale factor and the minimum neighbors
                                # gray is the image array
                                # 1.3 is the scale factor, it compensates for the faces that are closer to the camera
                                # 5 is the minimum neighbors, it specifies how many neighbors each candidate rectangle should have
                                # face_detect.detectMultiScale() returns the coordinates of the detected faces
                                # the coordinates are stored in the faces variable
                                # faces is a list of lists, each list contains the coordinates of a face
                                # each list contains four values, the x-coordinate, the y-coordinate, the width and the height
                                # faces = [[x1, y1, w1, h1], [x2, y2, w2, h2], [x3, y3, w3, h3], ...]
                                # x1, y1, w1, h1 are the coordinates of the first face
                                
    for (x,y,w,h) in faces:
                                # A for loop that iterates over the faces
                                # faces is a list of lists, each list contains the coordinates of a face
                                # each list contains four values, the x-coordinate, the y-coordinate, the width and the height
                                # for (x,y,w,h) in faces: iterates over the faces
                                # x,y,w,h are the coordinates of the face
                                
                
                crop_img = frame[y:y+h, x:x+w, :]
                                # frame[y:y+h, x:x+w, :] is used to crop the face from the frame
                                # frame is the image array
                                # y:y+h is the y-coordinate and the height of the face
                                # x:x+w is the x-coordinate and the width of the face
                                # [:] is used to crop all the channels of the image
                                # crop_img is the cropped face (numpy array that contains the face)
                
                resized_img = cv2.resize(crop_img,(50,50))
                
                if len(faces_data)<=100 and i%10==0:        
                                # if the length of faces_data is less than or equal to 100 and i is divisible by 10
                                # then append the resized_img to faces_data
                                
                        faces_data.append(resized_img)
                                # faces_data is a list that contains the resized images of the faces
                                
                i = i+1         
                                # increment the value of i by 1
                                # i is used to keep track of the number of frames processed
                
                cv2.putText(frame, str(len(faces_data)), (50,50), cv2.FONT_HERSHEY_SIMPLEX, 1, (50,50,255), 2)
                                # cv2.putText() is used to write text on the frame\
                                # cv2.putText() takes eight arguments, the image array, the text, the position, the font, the font scale, the color, the thickness and the line type
                                # frame is the image array
                                # str(len(faces_data)) is the text to be written on the frame
                                # (50,50) is the position of the text
                                # cv2.FONT_HERSHEY_SIMPLEX is the font of the text
                                # 1 is the font scale
                                # (50,50,255) is the color of the text, it is in BGR format
                                # 2 is the thickness of the text
                
                cv2.rectangle(frame, (x,y),(x+w,y+h), (0,255,0), 2)
                                # cv2.rectangle() is used to draw a bounding box around the detected face
                                # cv2.rectangle() takes five arguments, the image array, the top-left corner, the bottom-right corner, the color and the thickness
                                # frame is the image array
                                # (x,y) is the top-left corner of the rectangle
                                # (x+w,y+h) is the bottom-right corner of the rectangle
                                # (0,255,0) is the color of the rectangle, it is in BGR format
                                # 1 is the thickness of the rectangle

                                        
    cv2.imshow("Frame",frame)   # Display the frame
                                # cv2.imshow() takes two arguments, the first one is the name of the window
                                # and the second one is the image array
                                # cv2.imshow() displays the image in a window
                                # cv2.imshow() is a blocking function, it will block the execution of the program
                                # until the window is closed
                                
    k = cv2.waitKey(1)          # cv2.waitkey() is a function that waits for a key press
                                # cv2.waitkey() takes one argument, the time in milliseconds
                                # cv2.waitkey() returns the key value
                                # cv2.waitkey() is used to control the frame rate of the video
                                # cv2.waitkey(1) waits for 1 millisecond
                                # cv2.waitkey(0) waits indefinitely
                                # cv2.waitkey(1000) waits for 1 second
                                # cv2.waitkey(1000) is used to control the frame rate of the video
                                
    if k == ord("q") or len(faces_data) == 100:           
                                # ord() is a function that returns the ASCII value of a character
                                # ord() takes one argument, the character
            break               # ord("q") returns the ASCII value of the character "q"
                                # ord("q") returns 113
                                # ord("q") is used to check if the key pressed is "q"
                                # if the key pressed is "q" or the length of faces_data is equal to 100
                                # then break the loop
                            
video.release()                 # video.release() is a function that releases the video capture object
                                # video.release() is used to close the camera
                                
cv2.destroyAllWindows()         # cv2.destroyAllWindows() is a function that closes all the windows


faces_data = np.asarray(faces_data)
                                # np.asarray() is a function that converts the input to an array
                                # np.asarray() takes one argument, the input
                                # faces_data is a list that contains the resized images of the faces
                                # np.asarray(faces_data) converts the list to a numpy array
                                # faces_data is now a numpy array that contains the resized images of the faces
                            
faces_data = faces_data.reshape(100,-1)
                                # faces_data.reshape() takes two arguments, the number of rows and the number of columns
                                # 100 is the number of rows
                                # -1 is the number of columns
                                # -1 is used to automatically calculate the number of columns
                                # faces_data is reshaped to a 2D array with 100 rows and -1 columns
                                # faces_data is now a 2D array that contains the resized images of the faces
                                # each row contains the resized image of a face
                                
if 'names.pkl' not in os.listdir('data'):
    names = [name] * 100
    with open ('data/names.pkl','wb') as f:
        pickle.dump(names, f)
else:
    with open ('data/names.pkl','rb') as f:
        names = pickle.load(f)
    names = names + [name] * 100
    with open ('data/names.pkl','wb') as f:
        pickle.dump(names, f)    
                                # if 'names.pkl' is not in the list of files in the data directory
                                # then create a list of 100 elements with the name as the element
                                # and save the list to 'names.pkl'
                                # else load the list from 'names.pkl'
                                # append the name to the list 100 times
                                # and save the list to 'names.pkl'
        

if 'faces_data.pkl' not in os.listdir('data'):
    with open ('data/faces_data.pkl','wb') as f:
        pickle.dump(faces_data, f)
else:
    with open ('data/faces_data.pkl','rb') as f:
        faces = pickle.load(f)
    faces = np.append(faces, faces_data, axis=0)
    with open ('data/faces_data.pkl','wb') as f:
        pickle.dump(faces, f)
                                # if 'faces_data.pkl' is not in the list of files in the data directory
                                # then save the faces_data to 'faces_data.pkl'
                                # else load the faces_data from 'faces_data.pkl'
                                # append the faces_data to faces
                                # and save the faces to 'faces_data.pkl'
                                
                                        

                                
                            


                                
        
                         
    
    
                                
