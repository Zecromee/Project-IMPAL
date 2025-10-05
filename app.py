import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import sqlite3
import datetime
import os

# --- Tentukan folder penyimpanan database ---
base_dir = os.path.expanduser("~/OneDrive/Dokumen/project_jadwal/data")
os.makedirs(base_dir, exist_ok=True)  # buat folder kalau belum ada
db_path = os.path.join(base_dir, "jadwal_kuliah.db")
print("Database disimpan di:", db_path)

# --- Koneksi Database ---
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# --- Buat tabel jadwal ---
cursor.execute("""
CREATE TABLE IF NOT EXISTS jadwal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hari TEXT,
    mata_kuliah TEXT,
    jam TEXT
)
""")

# --- Buat tabel tugas ---
cursor.execute("""
CREATE TABLE IF NOT EXISTS tugas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mata_kuliah TEXT,
    deskripsi TEXT,
    deadline TEXT,
    status TEXT DEFAULT 'Belum Selesai'
)
""")
conn.commit()

# --- Fungsi ---
def tampilkan_home():
    for widget in frame_home.winfo_children():
        widget.destroy()

    hari_ini = datetime.datetime.now().strftime("%A")  # ex: Monday
    label_home = tk.Label(frame_home, text=f"Jadwal Hari Ini ({hari_ini})", font=("Arial", 14, "bold"))
    label_home.pack(pady=10)

    cursor.execute("SELECT mata_kuliah, jam FROM jadwal WHERE hari=?", (hari_ini,))
    data = cursor.fetchall()

    if data:
        for row in data:
            tk.Label(frame_home, text=f"{row[0]} - {row[1]}").pack()
    else:
        tk.Label(frame_home, text="Tidak ada jadwal hari ini").pack()

def tambah_jadwal():
    hari = combo_hari.get()
    matkul = entry_matkul.get()
    jam = entry_jam.get()

    if hari and matkul and jam:
        cursor.execute("INSERT INTO jadwal (hari, mata_kuliah, jam) VALUES (?, ?, ?)", (hari, matkul, jam))
        conn.commit()
        tampilkan_jadwal()
    else:
        messagebox.showwarning("Peringatan", "Semua field harus diisi!")

def tampilkan_jadwal():
    for row in tree_jadwal.get_children():
        tree_jadwal.delete(row)
    cursor.execute("SELECT id, hari, mata_kuliah, jam FROM jadwal")
    for row in cursor.fetchall():
        tree_jadwal.insert("", "end", values=row)

def hapus_jadwal():
    selected = tree_jadwal.selection()
    if not selected:
        return
    item = tree_jadwal.item(selected[0])
    id_hapus = item["values"][0]
    cursor.execute("DELETE FROM jadwal WHERE id=?", (id_hapus,))
    conn.commit()
    tampilkan_jadwal()

def tambah_tugas():
    matkul = entry_tugas_matkul.get()
    deskripsi = entry_tugas_desc.get()
    deadline = entry_tugas_deadline.get_date().strftime("%Y-%m-%d")

    if matkul and deadline:
        cursor.execute("INSERT INTO tugas (mata_kuliah, deskripsi, deadline, status) VALUES (?, ?, ?, ?)",
                       (matkul, deskripsi, deadline, "Belum Selesai"))
        conn.commit()
        tampilkan_tugas()
    else:
        messagebox.showwarning("Peringatan", "Field mata kuliah dan deadline wajib diisi!")

def tampilkan_tugas():
    for row in tree_tugas.get_children():
        tree_tugas.delete(row)
    cursor.execute("SELECT id, mata_kuliah, deskripsi, deadline, status FROM tugas")
    for row in cursor.fetchall():
        tree_tugas.insert("", "end", values=row)

def hapus_tugas():
    selected = tree_tugas.selection()
    if not selected:
        return
    item = tree_tugas.item(selected[0])
    id_hapus = item["values"][0]
    cursor.execute("DELETE FROM tugas WHERE id=?", (id_hapus,))
    conn.commit()
    tampilkan_tugas()

def ubah_status_tugas():
    selected = tree_tugas.selection()
    if not selected:
        return
    item = tree_tugas.item(selected[0])
    id_tugas = item["values"][0]
    current_status = item["values"][4]

    if current_status == "Selesai":
        messagebox.showinfo("Info", "Tugas ini sudah selesai.")
        return

    cursor.execute("UPDATE tugas SET status='Selesai' WHERE id=?", (id_tugas,))
    conn.commit()
    tampilkan_tugas()

# --- Notifikasi Tugas ---
def cek_tugas_deadline():
    cursor.execute("SELECT mata_kuliah, deadline FROM tugas WHERE status='Belum Selesai'")
    tugas = cursor.fetchall()
    if tugas:
        pesan = "Tugas belum selesai:\n"
        for t in tugas:
            pesan += f"- {t[0]} (Deadline: {t[1]})\n"
        messagebox.showinfo("Pengingat Tugas", pesan)

# --- GUI ---
root = tk.Tk()
root.title("Aplikasi Jadwal Kuliah & Tugas")
root.geometry("650x500")

notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill="both")

# --- Frame Home ---
frame_home = tk.Frame(notebook)
notebook.add(frame_home, text="Home")
tampilkan_home()

# --- Frame Jadwal ---
frame_jadwal = tk.Frame(notebook)
notebook.add(frame_jadwal, text="Jadwal Kuliah")

tk.Label(frame_jadwal, text="Hari:").pack()
combo_hari = ttk.Combobox(frame_jadwal, values=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"])
combo_hari.pack()
tk.Label(frame_jadwal, text="Mata Kuliah:").pack()
entry_matkul = tk.Entry(frame_jadwal)
entry_matkul.pack()
tk.Label(frame_jadwal, text="Jam:").pack()
entry_jam = tk.Entry(frame_jadwal)
entry_jam.pack()
tk.Button(frame_jadwal, text="Tambah Jadwal", command=tambah_jadwal).pack(pady=5)

tree_jadwal = ttk.Treeview(frame_jadwal, columns=("ID","Hari","Mata Kuliah","Jam"), show="headings")
for col in ("ID","Hari","Mata Kuliah","Jam"):
    tree_jadwal.heading(col, text=col)
tree_jadwal.pack()
tk.Button(frame_jadwal, text="Hapus Jadwal", command=hapus_jadwal).pack(pady=5)

# --- Frame Tugas ---
frame_tugas = tk.Frame(notebook)
notebook.add(frame_tugas, text="Tugas Kuliah")

tk.Label(frame_tugas, text="Mata Kuliah:").pack()
entry_tugas_matkul = tk.Entry(frame_tugas)
entry_tugas_matkul.pack()
tk.Label(frame_tugas, text="Deskripsi:").pack()
entry_tugas_desc = tk.Entry(frame_tugas)
entry_tugas_desc.pack()
tk.Label(frame_tugas, text="Deadline:").pack()
entry_tugas_deadline = DateEntry(frame_tugas, date_pattern="yyyy-mm-dd")
entry_tugas_deadline.pack()

tk.Button(frame_tugas, text="Tambah Tugas", command=tambah_tugas).pack(pady=5)
tree_tugas = ttk.Treeview(frame_tugas, columns=("ID","Mata Kuliah","Deskripsi","Deadline","Status"), show="headings")
for col in ("ID","Mata Kuliah","Deskripsi","Deadline","Status"):
    tree_tugas.heading(col, text=col)
tree_tugas.pack()
tk.Button(frame_tugas, text="Hapus Tugas", command=hapus_tugas).pack(pady=5)
tk.Button(frame_tugas, text="Tandai Selesai", command=ubah_status_tugas).pack(pady=5)

# --- Jalankan ---
cek_tugas_deadline()
tampilkan_jadwal()
tampilkan_tugas()
root.mainloop()
