import cv2
import pickle
import numpy as np
import os
import csv
from datetime import datetime, timedelta
import time
import pyttsx3  # Untuk text to speech

# Cek apakah folder 'data/' sudah ada
if not os.path.exists("data"):
    os.makedirs("data")

# Inisialisasi Kamera
video = cv2.VideoCapture(0)
if not video.isOpened():
    print("Kamera tidak dapat dibuka! Pastikan tidak digunakan oleh aplikasi lain.")
    exit()

# Load Haarcascade untuk deteksi wajah
facedetect = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

faces_data = []
total_capture = 100

# Data Input
name = ""
absen_clicked = False
absen_done = False  # Status apakah absen sudah dilakukan

# Lokasi penyimpanan file absensi
csv_file = "data/absensi.csv"

# Durasi scan 10 detik akumulasi wajah
scan_duration = timedelta(seconds=10)
face_accum = timedelta(0)
last_loop = None

# Inisialisasi TTS Offline dengan pyttsx3
tts_engine = pyttsx3.init()
voices = tts_engine.getProperty('voices')

# Set voice cowok (biasanya index 0), sesuaikan dengan daftar voice di komputermu
tts_engine.setProperty('voice', voices[0].id)
tts_engine.setProperty('rate', 150)

# Flag untuk suara agar hanya diputar sekali saat input nama muncul
voice_played = False

# Fungsi menyimpan data ke CSV
def save_to_csv(name):
    current_date = datetime.now().strftime("%Y-%m-%d")
    current_time = datetime.now().strftime("%H:%M:%S")
    file_exists = os.path.isfile(csv_file)
    try:
        with open(csv_file, mode="a", newline="") as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(["Nama", "Tanggal", "Waktu"])
            writer.writerow([name, current_date, current_time])
        print(f"✅ Data absen {name} berhasil disimpan ke CSV!")
    except Exception as e:
        print(f"❌ Error menyimpan data absensi ke CSV: {e}")

# Fungsi untuk menggambar UI input nama
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
        cv2.putText(bg, "Nama:", (50, 160),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        cv2.rectangle(bg, (50, 180), (450, 220), (0, 0, 0), 2)
        cv2.putText(bg, name, (60, 210),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
    if show_button:
        button_text = "ABSEN"
        btn_w, btn_h = cv2.getTextSize(button_text, cv2.FONT_HERSHEY_DUPLEX, 0.7, 2)[0]
        btn_x = (bg.shape[1] - btn_w) // 2
        btn_y = 415
        cv2.rectangle(bg,
                      (btn_x - 20, btn_y - 30),
                      (btn_x + btn_w + 20, btn_y + 10),
                      (255, 255, 255), -1)
        cv2.rectangle(bg,
                      (btn_x - 20, btn_y - 30),
                      (btn_x + btn_w + 20, btn_y + 10),
                      (0, 0, 0), 2)
        cv2.putText(bg, button_text, (btn_x, btn_y),
                    cv2.FONT_HERSHEY_DUPLEX, 0.7, (0, 0, 0), 2)
    return bg

# Fungsi splash screen dengan background dinamis
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

# Fungsi layar perantara (loading screen) sebelum absen wajah
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

# Proses klik tombol absen
def on_mouse(event, x, y, flags, param):
    global absen_clicked
    if event == cv2.EVENT_LBUTTONDOWN:
        button_text = "ABSEN"
        btn_w, _ = cv2.getTextSize(button_text, cv2.FONT_HERSHEY_DUPLEX, 0.7, 2)[0]
        btn_x = (500 - btn_w) // 2
        btn_y = 415
        if btn_x - 20 <= x <= btn_x + btn_w + 20 and btn_y - 30 <= y <= btn_y + 10:
            absen_clicked = True

# Fungsi tampilan berhasil absen dengan tulisan dan ceklis
def show_success_screen(name, duration=3, window_size=(500, 500)):
    cv2.namedWindow("Berhasil Absen", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Berhasil Absen", window_size[0], window_size[1])

    start_time = time.time()
    while True:
        bg = np.ones((window_size[1], window_size[0], 3), dtype=np.uint8) * 255

        # Tulisan "Selamat Anda sudah absen"
        text = f"Selamat {name},\nAnda sudah absen!"
        y0, dy = 180, 50
        for i, line in enumerate(text.split('\n')):
            y = y0 + i * dy
            cv2.putText(bg, line, (50, y), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 128, 0), 3)

        # Gambar ceklis (simple tanda centang)
        pts = np.array([[200, 350], [250, 400], [350, 300]], np.int32)
        pts = pts.reshape((-1, 1, 2))
        cv2.polylines(bg, [pts], False, (0, 200, 0), thickness=10, lineType=cv2.LINE_AA)

        elapsed = time.time() - start_time
        if cv2.waitKey(100) == ord('q') or elapsed >= duration:
            break

        cv2.imshow("Berhasil Absen", bg)

    cv2.destroyWindow("Berhasil Absen")

# --- MULAI PROGRAM ---

# Tampilkan splash screen mk.png sebelum input nama
splash_screen(duration=3, bg_image_path="mk.png")

# Tampilan input nama dengan background.png
cv2.namedWindow("Tampilan Awal", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Tampilan Awal", 500, 500)
cv2.setMouseCallback("Tampilan Awal", on_mouse)

while True:
    ui = draw_ui(use_background=True, show_button=True, show_title=False, show_name_input=True, bg_image_path="background.png")
    cv2.imshow("Tampilan Awal", ui)

    # Putar suara hanya setelah UI input nama sudah tampil (hanya sekali)
    if not voice_played:
        tts_engine.say("Selamat datang di MK LOG. Silakan masukan nama untuk melakukan kehadiran.")
        tts_engine.runAndWait()
        voice_played = True

    key = cv2.waitKey(1) & 0xFF
    if 48 <= key <= 57 or 65 <= key <= 90 or 97 <= key <= 122 or key == 32:
        name += chr(key)
    elif key == 8:
        name = name[:-1]
    elif key == 13 and name.strip():  # Enter dan nama tidak kosong
        absen_clicked = True

    if absen_clicked and name.strip():
        break

# Tampilkan layar perantara loading sebelum ke absensi wajah
loading_screen(name)

# Persiapkan loop scan wajah
face_accum = timedelta(0)
last_loop = datetime.now()

cv2.namedWindow("Absensi Wajah", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Absensi Wajah", 720, 540)

i = 0  # Reset counter untuk penomoran wajah dan pengambilan data wajah
while True:
    now = datetime.now()
    dt = now - last_loop
    last_loop = now

    ret, frame = video.read()
    if not ret:
        print("Gagal membaca frame dari kamera!")
        break

    frame_resized = cv2.resize(frame, (720, 540))

    # Buat background UI (kosong putih)
    ui_frame = draw_ui(use_background=True, show_button=False, show_title=False, show_name_input=False, window_size=(720, 540))
    bg_copy = ui_frame.copy()

    # Letakkan frame kamera di background UI
    bg_copy[0:540, 0:720] = frame_resized

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = facedetect.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50))

    # Jika ada wajah, akumulasikan waktu dt
    if len(faces) > 0:
        face_accum += dt

    # Gambar kotak wajah dan simpan gambar wajah secara berkala
    for (x, y, w, h) in faces:
        cv2.rectangle(bg_copy, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(bg_copy, f"ID {i+1}", (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        crop_img = frame[y:y+h, x:x+w]
        resized_img = cv2.resize(crop_img, (w, h))
        # Simpan wajah tiap 10 frame hingga max total_capture
        if len(faces_data) < total_capture and i % 10 == 0:
            faces_data.append(resized_img)
        i += 1

    # Hitung detik tersisa dari 10s akumulasi
    remaining = max(0, scan_duration.seconds - int(face_accum.total_seconds()))
    cv2.putText(bg_copy, f"Scan berakhir dalam: {remaining}s",
                (20, 520), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (50, 50, 255), 2)

    cv2.imshow("Absensi Wajah", bg_copy)

    # Jika akumulasi >= 10 detik dan ada wajah, simpan absen
    if face_accum >= scan_duration and len(faces) > 0 and not absen_done:
        save_to_csv(name)
        absen_done = True

    if cv2.waitKey(1) == ord('q') or absen_done:
        break

video.release()
cv2.destroyAllWindows()

# Tampilkan layar berhasil absen
if absen_done:
    show_success_screen(name)
