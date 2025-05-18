import cv2
import pickle
import numpy as np
import os
import csv
from datetime import datetime, timedelta  # tambah timedelta

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
i = 0
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

# Fungsi untuk menggambar UI
def draw_ui(use_background=False, show_button=True, show_title=True, show_name_input=True, window_size=(500, 500)):
    global name
    if not use_background:
        bg = np.ones((window_size[1], window_size[0], 3), dtype=np.uint8) * 255
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

# Tampilan awal (input nama)
cv2.namedWindow("Tampilan Awal", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Tampilan Awal", 500, 500)
cv2.setMouseCallback("Tampilan Awal", on_mouse)
while True:
    ui = draw_ui(use_background=True, show_button=True, show_title=False, show_name_input=True)
    cv2.imshow("Tampilan Awal", ui)
    key = cv2.waitKey(1) & 0xFF
    if 48 <= key <= 57 or 65 <= key <= 90 or 97 <= key <= 122 or key == 32:
        name += chr(key)
    elif key == 8:
        name = name[:-1]
    elif key == 13 and name:
        absen_clicked = True
    if absen_clicked:
        break

# Persiapkan loop scan wajah
face_accum = timedelta(0)
last_loop = datetime.now()

cv2.namedWindow("Absensi Wajah", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Absensi Wajah", 720, 540)
while True:
    now = datetime.now()
    dt = now - last_loop
    last_loop = now

    ret, frame = video.read()
    if not ret:
        print("Gagal membaca frame dari kamera!")
        break

    # Kamera non-mirror
    # Jika butuh mirror: uncomment berikut
    # frame = cv2.flip(frame, 1)

    frame_resized = cv2.resize(frame, (720, 540))
    ui_frame = draw_ui(use_background=True, show_button=False, show_title=False, show_name_input=False, window_size=(720, 540))
    bg_copy = ui_frame.copy()
    bg_copy[0:540, 0:720] = frame_resized

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = facedetect.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50))

    # Jika ada wajah, akumulasikan waktu dt
    if len(faces) > 0:
        face_accum += dt

    # Gambar kotak dan ID jika terdeteksi
    for (x, y, w, h) in faces:
        cv2.rectangle(bg_copy, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(bg_copy, f"ID {i+1}", (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        crop_img = frame[y:y+h, x:x+w]
        resized_img = cv2.resize(crop_img, (w, h))
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
