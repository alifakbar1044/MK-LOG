import cv2
import pickle
import numpy as np
import os
import csv
from datetime import datetime

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

# Fungsi menyimpan data ke CSV
def save_to_csv(name):
    current_date = datetime.now().strftime("%Y-%m-%d")
    current_time = datetime.now().strftime("%H:%M:%S")

    file_exists = os.path.isfile(csv_file)

    try:
        with open(csv_file, mode="a", newline="") as file:
            writer = csv.writer(file)
            
            # Jika file baru dibuat, tambahkan header
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
        bg_copy = np.ones((window_size[1], window_size[0], 3), dtype=np.uint8) * 255  # Ukuran dinamis
    else:
        background_path = os.path.join(os.path.dirname(__file__), "background.png")  # Path relatif
        background = cv2.imread(background_path)
        if background is None:
            bg_copy = np.ones((window_size[1], window_size[0], 3), dtype=np.uint8) * 255  # Background putih jika gambar tidak ditemukan
        else:
            bg_copy = cv2.resize(background, (window_size[0], window_size[1]))  # Resize background ke ukuran dinamis
    
    if show_name_input:
        cv2.putText(bg_copy, "Nama:", (50, 160),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        cv2.rectangle(bg_copy, (50, 180), (450, 220), (0, 0, 0), 2)
        cv2.putText(bg_copy, name, (60, 210),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
    
    if show_button:
        button_text = "ABSEN"
        button_size = cv2.getTextSize(button_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
        button_x = (bg_copy.shape[1] - button_size[0]) // 2
        button_y = 415
        cv2.rectangle(bg_copy, (button_x - 20, button_y - 30), (button_x + button_size[0] + 20, button_y + 10), (0, 255, 0), -1)
        cv2.putText(bg_copy, button_text, (button_x, button_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    return bg_copy

# Proses klik tombol absen
def on_mouse(event, x, y, flags, param):
    global absen_clicked
    if event == cv2.EVENT_LBUTTONDOWN:
        button_text = "ABSEN"
        button_size = cv2.getTextSize(button_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
        button_x = (500 - button_size[0]) // 2  # Ukuran 500x500 untuk input nama
        button_y = 415
        if button_x - 20 <= x <= button_x + button_size[0] + 20 and button_y - 30 <= y <= button_y + 10:
            print("Tombol ABSEN ditekan!")
            absen_clicked = True

# Menampilkan tampilan awal dengan background
cv2.namedWindow("Tampilan Awal", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Tampilan Awal", 500, 500)  # Ukuran jendela input nama 500x500
while True:
    ui_frame = draw_ui(use_background=True, show_button=True, show_title=False, show_name_input=True)
    cv2.imshow("Tampilan Awal", ui_frame)
    key = cv2.waitKey(1) & 0xFF

    if 48 <= key <= 57 or 65 <= key <= 90 or 97 <= key <= 122 or key == 32:
        name += chr(key)
    elif key == 8:
        name = name[:-1]
    elif key == 13 and name:
        absen_clicked = True

    if absen_clicked:
        break

# Setelah jendela "Tampilan Awal" dibuka, sekarang set callback untuk mouse
cv2.setMouseCallback("Tampilan Awal", on_mouse)

# Proses Absensi Wajah (Jendela kedua untuk kamera)
cv2.namedWindow("Absensi Wajah", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Absensi Wajah", 720, 540)  # Ukuran jendela kamera sedikit lebih kecil 720x540
while True:
    ui_frame = draw_ui(use_background=True, show_button=False, show_title=False, show_name_input=False, window_size=(720, 540))
    cv2.imshow("Absensi Wajah", ui_frame)

    ret, frame = video.read()
    if not ret:
        print("Gagal membaca frame dari kamera!")
        break

    frame_resized = cv2.resize(frame, (720, 540))  # Sesuaikan frame dengan ukuran 720x540
    bg_copy = ui_frame.copy()
    bg_copy[0:540, 0:720] = frame_resized  # Tempatkan frame di atas background

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = facedetect.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50))

    for (x, y, w, h) in faces:
        cv2.rectangle(bg_copy, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(bg_copy, f"ID {i+1}", (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        crop_img = frame[y:y+h, x:x+w]
        resized_img = cv2.resize(crop_img, (w, h))
        if len(faces_data) < total_capture and i % 10 == 0:
            faces_data.append(resized_img)
        i += 1

    cv2.putText(bg_copy, f"Captured: {len(faces_data)}/{total_capture}", (20, 520), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (50, 50, 255), 2)
    cv2.imshow("Absensi Wajah", bg_copy)

    if len(faces_data) >= total_capture and not absen_done:
        save_to_csv(name)
        absen_done = True

    if cv2.waitKey(1) == ord('q') or absen_done:
        break

video.release()
cv2.destroyAllWindows()
