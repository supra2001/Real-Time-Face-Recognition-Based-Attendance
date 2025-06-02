import cv2
import numpy as np
import face_recognition
import os
from datetime import datetime
import pyttsx3
import time
import logging
import mysql.connector
import threading

# -------------------- Configuration --------------------
IMAGES_PATH = 'Images'
ATTENDANCE_FOLDER = 'Attendance'
BACKGROUND_IMAGE = 'Background.jpg'
ACTIVE_IMAGE = 'active.png'
DEFAULT_PHOTO_PATH = os.path.join(IMAGES_PATH, 'default.png')
THRESHOLD = 0.46
UNAUTHORIZED_TIMEOUT = 7
FAILSAFE_TIMEOUT = 20

# -------------------- Logging Setup --------------------
logging.basicConfig(filename='attendance_system.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# -------------------- TTS Setup --------------------
engine = pyttsx3.init()
engine.setProperty('rate', 160)
engine.setProperty('voice', 'english')
engine.setProperty('volume', 1.0)  
engine_lock = threading.Lock()

# -------------------- Load Known Faces --------------------
def load_known_faces():
    images, classnames = [], []
    for filename in os.listdir(IMAGES_PATH):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            path = os.path.join(IMAGES_PATH, filename)
            img = cv2.imread(path)
            if img is not None:
                images.append(img)
                classnames.append(os.path.splitext(filename)[0])
    return images, classnames

def find_encodings(images):
    encode_list = []
    for img in images:
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(rgb_img)
        if encodings:
            encode_list.append(encodings[0])
    return encode_list

images, classnames = load_known_faces()
encode_list_known = find_encodings(images)
print(f"[INFO] Loaded and encoded {len(encode_list_known)} known faces.")

# -------------------- Attendance --------------------
def mark_attendance(student_id, name):
    now = datetime.now()
    date_str = now.strftime('%Y-%m-%d')
    dt_string = now.strftime('%Y-%m-%d %H:%M:%S')
    os.makedirs(ATTENDANCE_FOLDER, exist_ok=True)
    filename = os.path.join(ATTENDANCE_FOLDER, f"{date_str}.csv")

    if os.path.exists(filename):
        with open(filename, 'r') as f:
            if name in f.read():
                print(f"[INFO] {name}'s attendance already marked today.")
                return

    with open(filename, 'a') as f:
        f.write(f"{student_id},{name},{dt_string}\n")
    logging.info(f"Marked attendance: {name} (ID: {student_id})")

    speak(f"Attendance marked for {name}. Good morning and have a great day.")

# -------------------- Database --------------------
def fetch_user_data(name):
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="2001supra2127",
            database="face_attendance"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT student_id, major, photo_path FROM students WHERE name = %s", (name,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result if result else ("N/A", "N/A", DEFAULT_PHOTO_PATH)
    except mysql.connector.Error as err:
        logging.error(f"Database error: {err}")
        return ("DB-ERR", "DB-ERR", DEFAULT_PHOTO_PATH)

# -------------------- Display Helpers --------------------
def draw_pretty_box(img, x1, y1, x2, y2, color=(0, 255, 0), thickness=3):
    cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)

def show_marked_image(background):
    active_img = cv2.imread(ACTIVE_IMAGE)
    if active_img is not None:
        active_img = cv2.resize(active_img, (250, 350))
        background[10:360, 10:260] = active_img

def show_user_data(background, student_id, major, photo_path):
    try:
        user_img = cv2.imread(photo_path)
        if user_img is not None:
            user_img = cv2.resize(user_img, (214, 213))
            background[177:390, 905:1119] = user_img

        cv2.putText(background, str(student_id), (1006, 493), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        cv2.putText(background, str(major), (1006, 550), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    except Exception as e:
        logging.error(f"Error displaying user data: {e}")

# -------------------- TTS Helper --------------------
def speak(message):
    # Avoid multiple threads attempting to speak at the same time
    with engine_lock:
        t = threading.Thread(target=_speak, args=(message,))
        t.start()

def _speak(message):
    engine.say(message)
    engine.runAndWait()

# -------------------- Main Recognition --------------------
def start_recognition():
    cap = cv2.VideoCapture(0)
    greeted_names = {}
    marked_names = set()
    unauthorized_start = None
    first_known_name = None
    first_seen_time = None

    while True:
        ret, frame = cap.read()
        frame = cv2.flip(frame, 1)  
        if not ret:
            break

        background = cv2.imread(BACKGROUND_IMAGE)
        if background is None:
            logging.error("Background image not found.")
            break

        resized_frame = cv2.resize(frame, (640, 480))
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        background[162:642, 55:695] = resized_frame

        faces_cur_frame = face_recognition.face_locations(rgb_small_frame)
        encodes_cur_frame = face_recognition.face_encodings(rgb_small_frame, faces_cur_frame)

        match_found = False

        for encodeFace, faceLoc in zip(encodes_cur_frame, faces_cur_frame):
            face_dis = face_recognition.face_distance(encode_list_known, encodeFace)
            if not face_dis.size:
                continue

            min_dist = np.min(face_dis)
            best_match_index = np.argmin(face_dis)

            if min_dist < THRESHOLD:
                name = classnames[best_match_index]
                match_found = True
                unauthorized_start = None

                if first_known_name is None:
                    first_known_name = name
                    first_seen_time = time.time()

                y1, x2, y2, x1 = [v * 4 for v in faceLoc]
                x1 += 55; x2 += 55; y1 += 162; y2 += 162
                draw_pretty_box(background, x1, y1, x2, y2)
                cv2.putText(background, name, (x1, y2 + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

                if name not in greeted_names:
                    greeted_names[name] = time.time()
                    speak(f"Good morning {name}. Have a great day.")

                elif time.time() - greeted_names[name] > 12 and name not in marked_names:
                    user_data = fetch_user_data(name)
                    mark_attendance(user_data[0], name)
                    marked_names.add(name)
                    
                    speak(f"Attendance marked for {name}. Take care. See you next day!")

                    show_user_data(background, *user_data)
                    show_marked_image(background)

                    cv2.imshow("Face Recognition Attendance", background)
                    cv2.waitKey(9000)
                    cap.release()
                    cv2.destroyAllWindows()
                    return

        if not match_found and encodes_cur_frame:
            if unauthorized_start is None:
                unauthorized_start = time.time()
            elif time.time() - unauthorized_start >= UNAUTHORIZED_TIMEOUT:
                speak("Unauthorized access detected. You are not in our database.")
                logging.warning("Unauthorized face detected.")

                cv2.putText(background, "Unauthorized access detected!", (100, 300), cv2.FONT_HERSHEY_SIMPLEX,
                            1.0, (0, 0, 255), 3)
                cv2.imshow("Face Recognition Attendance", background)
                cv2.waitKey(7000)

                cap.release()
                cv2.destroyAllWindows()
                return
        else:
            unauthorized_start = None

        if first_known_name and first_known_name not in marked_names:
            if time.time() - first_seen_time >= FAILSAFE_TIMEOUT:
                msg = f"Sorry, attendance failed for {first_known_name} on {datetime.now().strftime('%d %B %Y')}."
                speak(msg)

                cv2.putText(background, msg, (40, 460), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 3)
                cv2.imshow("Face Recognition Attendance", background)
                cv2.waitKey(7000)
                cap.release()
                cv2.destroyAllWindows()
                return

        cv2.imshow("Face Recognition Attendance", background)
        if cv2.waitKey(1) == ord('q'):  
            break

    cap.release()
    cv2.destroyAllWindows()

# -------------------- Run --------------------
if __name__ == '__main__':
    start_recognition()
