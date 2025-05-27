import cv2
import numpy as np
import os
import time
from datetime import datetime, timedelta
import pyttsx3
import mysql.connector
import csv
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont
import ctypes

# --- FUNGSI ICON WINDOW ---
def create_icon_png(output_path="icon.png"):
    img_size = (256, 256)
    background_color = (255, 255, 255, 0)
    text_color = (0, 0, 0)
    font_size = 64

    img = Image.new("RGBA", img_size, background_color)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()

    text = "MK LOG"
    bbox = draw.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pos = ((img_size[0] - w) // 2, (img_size[1] - h) // 2)
    draw.text(pos, text, fill=text_color, font=font)
    img.save(output_path)

def convert_png_to_ico(png_path="icon.png", ico_path="icon.ico"):
    img = Image.open(png_path)
    img.save(ico_path, format="ICO")

def set_window_icon(window_name, icon_path="icon.ico"):
    if os.name == 'nt' and os.path.exists(icon_path):
        hwnd = ctypes.windll.user32.FindWindowW(None, window_name)
        if hwnd:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("MK.LOG.Icon")
            ctypes.windll.user32.SendMessageW(
                hwnd, 0x80, 0,
                ctypes.windll.user32.LoadImageW(0, icon_path, 1, 0, 0, 0x00000010)
            )

# --- DATA LOGIN BUAT SISWA ---
credentials = {"akbar": "ganteng", "zidan": "ganteng"}

def login_gui():
    def attempt_login():
        u = username_entry.get().strip()
        p = password_entry.get().strip()
        if u in credentials and credentials[u] == p:
            messagebox.showinfo("Login Berhasil", f"Selamat datang, {u}!")
            root.destroy()
        else:
            messagebox.showerror("Login Gagal", "Username atau Password salah!")

    root = tk.Tk()
    root.title("Login - MK LOG")
    root.geometry("400x300")
    root.configure(bg="#f2f2f2")
    root.resizable(False, False)

    frame = tk.Frame(root, bg="white", bd=2, relief="ridge")
    frame.place(relx=0.5, rely=0.5, anchor="center", width=300, height=250)

    lp = os.path.join(os.path.dirname(__file__), "logo.png")
    if os.path.exists(lp):
        img = Image.open(lp).resize((50,50))
        logo = ImageTk.PhotoImage(img)
        lbl = tk.Label(frame, image=logo, bg="white")
        lbl.image = logo
        lbl.pack(pady=(10,5))

    tk.Label(frame, text="Login MK LOG", font=("Helvetica",16,"bold"),
             bg="white", fg="#333").pack(pady=(5,15))
    tk.Label(frame, text="Username", font=("Helvetica",10),
             bg="white", anchor="w").pack(fill="x", padx=20)
    username_entry = tk.Entry(frame, font=("Helvetica",11), bd=1, relief="solid")
    username_entry.pack(fill="x", padx=20, pady=(0,10))
    username_entry.focus()

    tk.Label(frame, text="Password", font=("Helvetica",10),
             bg="white", anchor="w").pack(fill="x", padx=20)
    password_entry = tk.Entry(frame, font=("Helvetica",11), bd=1,
                              relief="solid", show="*")
    password_entry.pack(fill="x", padx=20, pady=(0,15))

    tk.Button(frame, text="Login", font=("Helvetica",11,"bold"),
              bg="#4CAF50", fg="white", bd=0, height=2,
              command=attempt_login, activebackground="#45a049",
              cursor="hand2").pack(fill="x", padx=60)

    root.mainloop()

login_gui()

# --- KONFIGURASI DB ---
config = {"host": "localhost", "user": "root", "password": "", "database": "absensi_db"}

def create_db_and_table():
    conn = mysql.connector.connect(
        host=config['host'], user=config['user'], password=config['password'])
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

create_db_and_table()

def save_to_csv(name):
    today = datetime.now().date()
    now = datetime.now().time().replace(microsecond=0)
    path = os.path.join("absensi_csv", "absensi.csv")
    file_exists = os.path.isfile(path)
    with open(path, "a", newline="") as f:
        w = csv.writer(f)
        if not file_exists:
            w.writerow(["Nama","Tanggal","Waktu"])
        w.writerow([name, today, now])

def save_to_db(name):
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        today = datetime.now().date()
        now = datetime.now().time().replace(microsecond=0)
        sql = "INSERT INTO absensi (nama, tanggal, waktu) VALUES (%s,%s,%s)"
        cursor.execute(sql, (name, today, now))
        conn.commit()
        conn.close()
        save_to_csv(name)
    except Exception as e:
        print("DB Error:", e)

# --- INISIALISASI CV, TTS ---
video = cv2.VideoCapture(0)
if not video.isOpened():
    raise RuntimeError("Kamera tidak bisa diakses.")

facedetect = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
tts = pyttsx3.init()
tts.setProperty('rate', 150)

def get_face_histogram(gray, coords):
    x, y, w, h = coords
    face = gray[y:y+h, x:x+w]
    face = cv2.resize(face, (100,100))
    hist = cv2.calcHist([face],[0],None,[256],[0,256])
    cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)
    return hist

def draw_ui(bg_size, name="", show_input=True, show_button=True, bg_path=None):
    w, h = bg_size
    bg = np.full((h,w,3),255, dtype=np.uint8)
    if bg_path:
        p = os.path.join(os.path.dirname(__file__), bg_path)
        img = cv2.imread(p)
        if img is not None:
            bg = cv2.resize(img, (w,h))
    if show_input:
        cv2.putText(bg, "Nama:", (50,160),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,0), 2)
        cv2.rectangle(bg,(50,180),(w-50,220),(0,0,0),2)
        cv2.putText(bg, name, (60,210),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,0), 2)
    if show_button:
        text = "ABSEN"
        tw,_ = cv2.getTextSize(text, cv2.FONT_HERSHEY_DUPLEX,0.7,2)[0]
        bx = (w - tw)//2
        by = h - 85
        cv2.rectangle(bg,(bx-20,by-30),(bx+tw+20,by+10),(255,255,255),-1)
        cv2.rectangle(bg,(bx-20,by-30),(bx+tw+20,by+10),(0,0,0),2)
        cv2.putText(bg, text, (bx,by),
                    cv2.FONT_HERSHEY_DUPLEX,0.7,(0,0,0),2)
    return bg

def splash(duration=5, size=(500,500), img="mk.png"):
    cv2.namedWindow("Splash", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Splash", *size)
    bg = draw_ui(size, show_input=False, show_button=False, bg_path=img)
    start = time.time()
    while time.time() - start < duration:
        cv2.imshow("Splash", bg)
        if cv2.waitKey(100) == ord('q'):
            break
    cv2.destroyWindow("Splash")

def loading(name, duration=3):
    cv2.namedWindow("Loading", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Loading", 500, 500)
    start = time.time()
    while True:
        bg = np.full((500,500,3),255, dtype=np.uint8)
        lines = [f"Halo {name},", "persiapkan wajah Anda", "untuk absensi..."]
        for i,l in enumerate(lines):
            cv2.putText(bg, l, (50,180+i*40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,0), 2)
        rem = max(0, int(duration - (time.time() - start)))
        cv2.putText(bg, f"Mulai dalam: {rem}s", (150,450),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)
        cv2.imshow("Loading", bg)
        if cv2.waitKey(100) == ord('q') or time.time() - start >= duration:
            break
    cv2.destroyWindow("Loading")

def success(name, duration=3, size=(500,500)):
    cv2.namedWindow("Sukses", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Sukses", *size)
    start = time.time()
    while time.time() - start < duration:
        bg = np.full((size[1],size[0],3),255, dtype=np.uint8)
        cv2.putText(bg, f"Selamat {name},", (50,180),
                    cv2.FONT_HERSHEY_SIMPLEX,1,(0,128,0),3)
        cv2.putText(bg, "Anda sudah absen!", (50,240),
                    cv2.FONT_HERSHEY_SIMPLEX,1,(0,128,0),3)
        cv2.imshow("Sukses", bg)
        if cv2.waitKey(100) == ord('q'):
            break
    cv2.destroyWindow("Sukses")

# ---- UBAH DI SINI: Folder bukti absen ----
def save_face_photo(frame, coords, name):
    os.makedirs("bukti_absen", exist_ok=True)
    x, y, w, h = coords
    face_img = frame[y:y+h, x:x+w]
    filename = f"{name.replace(' ', '_')}.jpg"
    cv2.imwrite(os.path.join("bukti_absen", filename), face_img)

# --- JALANKAN SPLASH & WINDOW UTAMA ---
create_icon_png("icon.png")
convert_png_to_ico("icon.png", "icon.ico")
splash()
cv2.namedWindow("MK LOG", cv2.WINDOW_NORMAL)
cv2.resizeWindow("MK LOG", 500, 500)
set_window_icon("MK LOG", "icon.ico")

name = ""
voice_played = False
known_face_hist = None

# Input nama
while True:
    frame = draw_ui((500,500), name=name, show_button=True, bg_path="background.png")
    cv2.imshow("MK LOG", frame)
    if not voice_played:
        tts.say("Selamat datang di MK LOG. Silakan masukan nama untuk melakukan kehadiran.")
        tts.runAndWait()
        voice_played = True
    key = cv2.waitKey(1) & 0xFF
    if 32 <= key <= 126:
        name += chr(key)
    elif key == 8:
        name = name[:-1]
    elif key == 13 and name.strip():
        break
    elif key == ord('q'):
        video.release()
        cv2.destroyAllWindows()
        exit()

loading(name)

# Proses deteksi & absensi (tanpa penolakan wajah)
cv2.namedWindow("Absensi Wajah", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Absensi Wajah", 720, 540)
accum = timedelta(0)
last = datetime.now()

while True:
    now = datetime.now()
    dt = now - last
    last = now

    ret, frame = video.read()
    if not ret:
        break
    frame = cv2.resize(frame, (720,540))
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    ui = draw_ui((720,540), show_input=False, show_button=False)
    ui[:540,:720] = frame

    faces = facedetect.detectMultiScale(gray, 1.1, 5, minSize=(50,50))
    if len(faces) == 0:
        cv2.putText(ui, "Wajah tidak terdeteksi", (20,60),
                    cv2.FONT_HERSHEY_SIMPLEX,0.9,(0,0,255),2)
        cv2.imshow("Absensi Wajah", ui)
        if cv2.waitKey(1) == ord('q'):
            break
        continue

    x, y, w, h = faces[0]
    if known_face_hist is None:
        known_face_hist = get_face_histogram(gray, (x,y,w,h))

    accum += dt

    for idx, (xx,yy,ww,hh) in enumerate(faces):
        cv2.rectangle(ui,(xx,yy),(xx+ww,yy+hh),(0,255,0),2)
        cv2.putText(ui, f"ID {idx+1}", (xx,yy-10),
                    cv2.FONT_HERSHEY_SIMPLEX,0.8,(0,255,0),2)

    cv2.putText(ui, f"Deteksi wajah: {len(faces)}", (10,500),
                cv2.FONT_HERSHEY_SIMPLEX,0.7,(255,0,0),2)
    cv2.putText(ui, f"Waktu: {accum.seconds}s", (10,530),
                cv2.FONT_HERSHEY_SIMPLEX,0.7,(255,0,0),2)
    cv2.imshow("Absensi Wajah", ui)

    if accum.seconds >= 10:
        save_to_db(name)
        save_face_photo(frame, (x, y, w, h), name)
        success(name)
        break

    if cv2.waitKey(1) == ord('q'):
        break

video.release()
cv2.destroyAllWindows()
