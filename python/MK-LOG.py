import cv2
import numpy as np
import os
import time
from datetime import datetime, timedelta
import pyttsx3
import mysql.connector
import csv

# --- KONFIGURASI DATABASE MYSQL ---
config = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "absensi_db"
}

def create_db_and_table():
    conn = mysql.connector.connect(
        host=config['host'],
        user=config['user'],
        password=config['password']
    )
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config['database']}")
    conn.close()

    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS absensi (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nama VARCHAR(100) NOT NULL,
            tanggal DATE NOT NULL,
            waktu TIME NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    print("Database dan tabel absensi sudah siap!")

def save_to_csv(name):
    current_date = datetime.now().date()
    current_time = datetime.now().time().replace(microsecond=0)
    csv_path = os.path.join("data", "absensi.csv")
    file_exists = os.path.isfile(csv_path)
    with open(csv_path, mode="a", newline="") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Nama", "Tanggal", "Waktu"])
        writer.writerow([name, current_date, current_time])
    print(f"Data absensi untuk '{name}' juga disimpan ke file CSV di folder 'data'.")

def save_to_db(name):
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        current_date = datetime.now().date()
        current_time = datetime.now().time().replace(microsecond=0)
        sql = "INSERT INTO absensi (nama, tanggal, waktu) VALUES (%s, %s, %s)"
        cursor.execute(sql, (name, current_date, current_time))
        conn.commit()
        conn.close()
        print(f"Data absensi untuk '{name}' berhasil disimpan ke database.")
        save_to_csv(name)
    except Exception as e:
        print(f"Gagal menyimpan data ke database: {e}")

# --- Mulai kode absensi dengan kamera dan UI ---
if not os.path.exists("data"):
    os.makedirs("data")

video = cv2.VideoCapture(0)
if not video.isOpened():
    print("Kamera tidak dapat dibuka! Pastikan tidak digunakan aplikasi lain.")
    exit()

facedetect = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

faces_data = []
total_capture = 100
name = ""
absen_clicked = False
absen_done = False

scan_duration = timedelta(seconds=10)
face_accum = timedelta(0)
last_loop = None

tts_engine = pyttsx3.init()
voices = tts_engine.getProperty('voices')
tts_engine.setProperty('voice', voices[0].id)
tts_engine.setProperty('rate', 150)
voice_played = False

def draw_ui(use_background=False, show_button=True, show_title=True, show_name_input=True, window_size=(500, 500), bg_image_path=None):
    global name
    if not use_background:
        bg = np.ones((window_size[1], window_size[0], 3), dtype=np.uint8) * 255
    else:
        if bg_image_path:
            background_path = os.path.join(os.path.dirname(__file__), bg_image_path)
            background = cv2.imread(background_path)
        else:
            background_path = os.path.join(os.path.dirname(__file__), "background.png")
            background = cv2.imread(background_path)

        if background is None:
            bg = np.ones((window_size[1], window_size[0], 3), dtype=np.uint8) * 255
        else:
            bg = cv2.resize(background, (window_size[0], window_size[1]))

    if show_name_input:
        cv2.putText(bg, "Nama:", (50, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        cv2.rectangle(bg, (50, 180), (450, 220), (0, 0, 0), 2)
        cv2.putText(bg, name, (60, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
    if show_button:
        button_text = "ABSEN"
        btn_w, btn_h = cv2.getTextSize(button_text, cv2.FONT_HERSHEY_DUPLEX, 0.7, 2)[0]
        btn_x = (bg.shape[1] - btn_w) // 2
        btn_y = 415
        cv2.rectangle(bg, (btn_x - 20, btn_y - 30), (btn_x + btn_w + 20, btn_y + 10), (255, 255, 255), -1)
        cv2.rectangle(bg, (btn_x - 20, btn_y - 30), (btn_x + btn_w + 20, btn_y + 10), (0, 0, 0), 2)
        cv2.putText(bg, button_text, (btn_x, btn_y), cv2.FONT_HERSHEY_DUPLEX, 0.7, (0, 0, 0), 2)
    return bg

def splash_screen(duration=3, window_size=(500, 500), bg_image_path="mk.png"):
    cv2.namedWindow("Splash Screen", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Splash Screen", window_size[0], window_size[1])
    background_path = os.path.join(os.path.dirname(__file__), bg_image_path)
    background = cv2.imread(background_path)
    if background is None:
        bg = np.ones((window_size[1], window_size[0], 3), dtype=np.uint8) * 255
    else:
        bg = cv2.resize(background, (window_size[0], window_size[1]))
    start_time = time.time()
    while True:
        cv2.imshow("Splash Screen", bg)
        if cv2.waitKey(100) == ord('q') or (time.time() - start_time) >= duration:
            break
    cv2.destroyWindow("Splash Screen")

def loading_screen(name, duration=3):
    cv2.namedWindow("Persiapan Absensi", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Persiapan Absensi", 500, 500)
    start_time = time.time()
    while True:
        bg = np.ones((500, 500, 3), dtype=np.uint8) * 255
        text = f"Halo {name},\npersiapkan wajah Anda\nuntuk absensi..."
        y0, dy = 180, 40
        for i, line in enumerate(text.split('\n')):
            y = y0 + i*dy
            cv2.putText(bg, line, (50, y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
        elapsed = time.time() - start_time
        remaining = max(0, int(duration - elapsed))
        cv2.putText(bg, f"Mulai dalam: {remaining}s", (150, 450), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.imshow("Persiapan Absensi", bg)
        if cv2.waitKey(100) == ord('q') or elapsed >= duration:
            break
    cv2.destroyWindow("Persiapan Absensi")

def on_mouse(event, x, y, flags, param):
    global absen_clicked
    if event == cv2.EVENT_LBUTTONDOWN:
        button_text = "ABSEN"
        btn_w, _ = cv2.getTextSize(button_text, cv2.FONT_HERSHEY_DUPLEX, 0.7, 2)[0]
        btn_x = (500 - btn_w) // 2
        btn_y = 415
        if btn_x - 20 <= x <= btn_x + btn_w + 20 and btn_y - 30 <= y <= btn_y + 10:
            absen_clicked = True

def show_success_screen(name, duration=3, window_size=(500, 500)):
    cv2.namedWindow("Berhasil Absen", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Berhasil Absen", window_size[0], window_size[1])
    start_time = time.time()
    while True:
        bg = np.ones((window_size[1], window_size[0], 3), dtype=np.uint8) * 255
        text = f"Selamat {name},\nAnda sudah absen!"
        y0, dy = 180, 50
        for i, line in enumerate(text.split('\n')):
            y = y0 + i * dy
            cv2.putText(bg, line, (50, y), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 128, 0), 3)
        pts = np.array([[200, 350], [250, 400], [350, 300]], np.int32)
        pts = pts.reshape((-1, 1, 2))
        cv2.polylines(bg, [pts], False, (0, 200, 0), thickness=10, lineType=cv2.LINE_AA)
        elapsed = time.time() - start_time
        if cv2.waitKey(100) == ord('q') or elapsed >= duration:
            break
        cv2.imshow("Berhasil Absen", bg)
    cv2.destroyWindow("Berhasil Absen")

# --- MULAI PROGRAM ---
create_db_and_table()
splash_screen(duration=3, bg_image_path="mk.png")

cv2.namedWindow("Tampilan Awal", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Tampilan Awal", 500, 500)
cv2.setMouseCallback("Tampilan Awal", on_mouse)

while True:
    ui = draw_ui(use_background=True, show_button=True, show_title=False, show_name_input=True, bg_image_path="background.png")
    cv2.imshow("Tampilan Awal", ui)

    if not voice_played:
        tts_engine.say("Selamat datang di MK LOG. Silakan masukan nama untuk melakukan kehadiran.")
        tts_engine.runAndWait()
        voice_played = True

    key = cv2.waitKey(1) & 0xFF
    if 48 <= key <= 57 or 65 <= key <= 90 or 97 <= key <= 122 or key == 32:
        name += chr(key)
    elif key == 8:
        name = name[:-1]
    elif key == 13 and name.strip():
        absen_clicked = True

    if absen_clicked and name.strip():
        break

loading_screen(name)

face_accum = timedelta(0)
last_loop = datetime.now()

cv2.namedWindow("Absensi Wajah", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Absensi Wajah", 720, 540)

i = 0
while True:
    now = datetime.now()
    dt = now - last_loop
    last_loop = now

    ret, frame = video.read()
    if not ret:
        print("Gagal membaca frame dari kamera!")
        break

    frame_resized = cv2.resize(frame, (720, 540))
    ui_frame = draw_ui(use_background=True, show_button=False, show_title=False, show_name_input=False, window_size=(720, 540))
    bg_copy = ui_frame.copy()
    bg_copy[0:540, 0:720] = frame_resized

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = facedetect.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50))

    if len(faces) > 0:
        face_accum += dt

    for (x, y, w, h) in faces:
        cv2.rectangle(bg_copy, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(bg_copy, f"ID {i+1}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        crop_img = frame[y:y+h, x:x+w]
        resized_img = cv2.resize(crop_img, (w, h))
        if len(faces_data) < total_capture and i % 10 == 0:
            faces_data.append(resized_img)
        i += 1

    cv2.putText(bg_copy, f"Deteksi wajah: {len(faces)}", (10, 500), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
    cv2.putText(bg_copy, f"Waktu deteksi: {face_accum.seconds} detik", (10, 530), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

    cv2.imshow("Absensi Wajah", bg_copy)

    if face_accum >= scan_duration:
        save_to_db(name)
        show_success_screen(name)
        absen_done = True
        break

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

video.release()
cv2.destroyAllWindows()
    