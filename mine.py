# Import necessary libraries
import cv2  # For image and video processing
import numpy as np  # For numerical operations
import face_recognition  # For face recognition
import os  # For directory and file operations
from datetime import datetime  # For time-related operations
import pyttsx3  # For text-to-speech functionality
import time  # For timing events
import logging  # For logging system events
import mysql.connector  # For connecting to MySQL database
import threading  # For handling threads (used in TTS)

# -------------------- Configuration --------------------
# Define paths and settings for the system
IMAGES_PATH = 'Images'  # Folder containing known face images
ATTENDANCE_FOLDER = 'Attendance'  # Folder to save attendance records
BACKGROUND_IMAGE = 'Background.jpg'  # Background template image
ACTIVE_IMAGE = 'active.png'  # Image shown when attendance is marked
DEFAULT_PHOTO_PATH = os.path.join(IMAGES_PATH, 'default.png')  # Default photo if not found
THRESHOLD = 0.46  # Face match threshold (lower means stricter)
UNAUTHORIZED_TIMEOUT = 7  # Time before warning for unknown face
FAILSAFE_TIMEOUT = 30  # Time before timeout if attendance fails

# -------------------- Logging Setup --------------------
# Setup for saving system logs to a file
logging.basicConfig(filename='attendance_system.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# -------------------- TTS Setup --------------------
# Initialize text-to-speech engine
engine = pyttsx3.init()
engine.setProperty('rate', 160)  # Speed of speech
engine.setProperty('voice', 'english')  # Voice type
engine.setProperty('volume', 1.0)  # Volume (0.0 to 1.0)
engine_lock = threading.Lock()  # Lock for preventing overlap in speech

# -------------------- Load Known Faces --------------------
# Function to load all images and names from the known folder
def load_known_faces():
    images, classnames = [], []
    for filename in os.listdir(IMAGES_PATH):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):  # Only image files
            path = os.path.join(IMAGES_PATH, filename)
            img = cv2.imread(path)
            if img is not None:
                images.append(img)
                classnames.append(os.path.splitext(filename)[0])  # Name without file extension
    return images, classnames

# Function to find encodings (numerical representation of faces)
def find_encodings(images):
    encode_list = []
    for img in images:
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB
        encodings = face_recognition.face_encodings(rgb_img)
        if encodings:
            encode_list.append(encodings[0])  # Add only first face encoding
    return encode_list

# Load images and compute encodings
images, classnames = load_known_faces()
encode_list_known = find_encodings(images)
print(f"[INFO] Loaded and encoded {len(encode_list_known)} known faces.")

# -------------------- Attendance --------------------
# Function to mark attendance by writing to a CSV file
def mark_attendance(student_id, name):
    now = datetime.now()
    date_str = now.strftime('%Y-%m-%d')  # Format as YYYY-MM-DD
    dt_string = now.strftime('%Y-%m-%d %H:%M:%S')  # Full timestamp
    os.makedirs(ATTENDANCE_FOLDER, exist_ok=True)
    filename = os.path.join(ATTENDANCE_FOLDER, f"{date_str}.csv")

    # Check if attendance already marked
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            if name in f.read():
                print(f"[INFO] {name}'s attendance already marked today.")
                return

    # Write attendance entry to file
    with open(filename, 'a') as f:
        f.write(f"{student_id},{name},{dt_string}\n")
    logging.info(f"Marked attendance: {name} (ID: {student_id})")

    # Speak confirmation
    speak(f"Attendance marked for {name}. Good morning and have a great day.")

# -------------------- Database --------------------
# Fetch user details from MySQL database
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
# Draw a styled rectangle (face box)
def draw_pretty_box(img, x1, y1, x2, y2, color=(0, 255, 0), thickness=3):
    cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)

# Display image after attendance is marked
def show_marked_image(background):
    active_img = cv2.imread(ACTIVE_IMAGE)
    if active_img is not None:
        active_img = cv2.resize(active_img, (250, 350))
        background[10:360, 10:260] = active_img

# Show user photo, ID, and major on the screen
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
# Thread-safe way to call text-to-speech
def speak(message):
    with engine_lock:
        t = threading.Thread(target=_speak, args=(message,))
        t.start()

# Actual TTS function
def _speak(message):
    engine.say(message)
    engine.runAndWait()

# -------------------- Main Recognition --------------------
# This is the main function where video feed and recognition takes place
def start_recognition():
    cap = cv2.VideoCapture(0)  # Start webcam
    greeted_names = {}  # Track who was greeted
    marked_names = set()  # Track whose attendance was marked
    unauthorized_start = None
    first_known_name = None
    first_seen_time = None

    while True:
        ret, frame = cap.read()  # Capture a frame
        if not ret:
            break

        background = cv2.imread(BACKGROUND_IMAGE)  # Load background template
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
                cv2.putText(background, name, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 3)

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

        # Handle unauthorized faces
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

        # If timeout occurs without marking attendance
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

        # Show the window
        cv2.imshow("Face Recognition Attendance", background)
        if cv2.waitKey(1) == ord('q'):  # Press 'q' to quit
            break

    cap.release()
    cv2.destroyAllWindows()

# -------------------- Run --------------------
# Start the recognition process
if __name__ == '__main__':
    start_recognition()
