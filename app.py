import mysql.connector
import datetime
import ttkbootstrap as ttk
from ttkbootstrap import DateEntry
from ttkbootstrap.constants import *
from tkinter import messagebox, END, W, NW, LEFT, BOTH, X, CENTER

# =========================
# GLOBAL STATE 
# =========================
user_logged_in = None
notifikasi_deadline_sudah = False

combo_matkul_jadwal = None
combo_matkul_tugas = None
combo_matkul_dosen = None

matkul_map = {}
dosen_map = {}

# ============================================
# CONNECT TO MYSQL
# ============================================
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",          
    database="jadwal_kuliah"
)
cursor = conn.cursor()

# ============================================
# FUNGSI DATABASE
# ============================================
def ada_dosen():
    cursor.execute(
        "SELECT COUNT(*) FROM dosen WHERE user_id=%s",
        (user_logged_in,)
    )
    return cursor.fetchone()[0] > 0

def kunci_form_jadwal():
    widgets = (ttk.Entry, ttk.Combobox)

    if ada_dosen():
        state = "normal"
    else:
        state = "disabled"

    for w in frm_input_jadwal.winfo_children():
        if isinstance(w, widgets):
            w.configure(state=state)

def tampilkan_home():
    for w in frame_home.winfo_children():
        w.destroy()

    hari_ini = datetime.datetime.now().strftime("%A")

    ttk.Label(
        frame_home,
        text=f"📅 Jadwal Hari Ini — {hari_ini}",
        font=("Comic Sans MS", 14, "bold"),
        bootstyle="info"
    ).pack(pady=8)

    cursor.execute("""
        SELECT 
            mk.nama AS mata_kuliah,
            d.nama AS nama_dosen,
            j.jam
        FROM jadwal j
        JOIN mata_kuliah mk ON j.mata_kuliah_id = mk.id
        LEFT JOIN dosen d ON j.dosen_id = d.id
        WHERE j.user_id=%s AND j.hari=%s
        ORDER BY j.jam
    """, (user_logged_in, hari_ini))

    rows = cursor.fetchall()

    if rows:
        for mk, dosen, jam in rows:
            dosen_text = dosen if dosen else "Belum ada dosen"
            ttk.Label(
                frame_home,
                text=f"• {mk} — {dosen_text} ({jam})",
                font=("Comic Sans MS", 11)
            ).pack(anchor=W, padx=10, pady=2)
    else:
        ttk.Label(
            frame_home,
            text="Tidak ada jadwal hari ini 🎉",
            font=("Comic Sans MS", 11, "italic")
        ).pack(pady=6)

def tampilkan_jadwal():
    for row in tree_jadwal.get_children():
        tree_jadwal.delete(row)
    cursor.execute("""
    SELECT 
    j.id,
    j.hari,
    mk.nama,
    CONCAT(d.kode, ' - ', d.nama),
    j.jam
    FROM jadwal j
    JOIN mata_kuliah mk ON j.mata_kuliah_id = mk.id
    LEFT JOIN dosen d ON j.dosen_id = d.id
    WHERE j.user_id=%s
    ORDER BY j.hari, j.jam
""", (user_logged_in,))
    for row in cursor.fetchall():
        tree_jadwal.insert("", "end", values=row)

def tampilkan_tugas():
    for row in tree_tugas.get_children():
        tree_tugas.delete(row)
    cursor.execute("SELECT id, mata_kuliah, deskripsi, deadline, status FROM tugas WHERE user_id=%s ORDER BY deadline",
               (user_logged_in,))
    for row in cursor.fetchall():
        tag = "selesai" if row[4] == "Selesai" else "belum"
        tree_tugas.insert("", "end", values=row, tags=(tag,))
    tree_tugas.tag_configure("selesai", background="#d4edda")
    tree_tugas.tag_configure("belum", background="#f8d7da")

def get_mata_kuliah():
    cursor.execute(
        "SELECT id, nama FROM mata_kuliah WHERE user_id=%s ORDER BY nama",
        (user_logged_in,)
    )
    return cursor.fetchall()

def tampilkan_semua():
    tampilkan_home()
    tampilkan_jadwal()
    tampilkan_tugas()

# ============================================
# GLOBAL MAP & DROPDOWN LOADER
# ============================================

matkul_map = {}   # nama_mata_kuliah -> id_mata_kuliah

def load_matkul_dropdown(*combos):
    matkul_map.clear()
    data = get_mata_kuliah()
    values = []

    for id_mk, nama in data:
        values.append(nama)
        matkul_map[nama] = id_mk

    for cb in combos:
        cb["values"] = values
        if values:
            cb.set("")

# ============================================
# CRUD FUNGSIONAL
# ============================================
def tambah_jadwal():
    hari = combo_hari.get().strip()
    matkul_nama = combo_matkul_jadwal.get().strip()
    dosen_label = combo_dosen_jadwal.get().strip()
    jam = entry_jam.get().strip()

    if not (hari and matkul_nama and dosen_label and jam):
        messagebox.showwarning("Peringatan", "Semua field harus diisi!")
        return

    matkul_id = matkul_map.get(matkul_nama)
    dosen_id = dosen_map.get(dosen_label)

    cursor.execute("""
        INSERT INTO jadwal (hari, mata_kuliah_id, dosen_id, jam, user_id)
        VALUES (%s, %s, %s, %s, %s)
    """, (hari, matkul_id, dosen_id, jam, user_logged_in))

    conn.commit()
    tampilkan_jadwal()
    messagebox.showinfo("Sukses", "Jadwal berhasil ditambahkan!")

def hapus_jadwal():
    sel = tree_jadwal.selection()
    if not sel:
        messagebox.showwarning("Peringatan", "Pilih jadwal yang mau dihapus.")
        return
    id_hapus = tree_jadwal.item(sel[0])["values"][0]

    cursor.execute(
    "DELETE FROM jadwal WHERE id=%s AND user_id=%s",
    (id_hapus, user_logged_in)
)
    conn.commit()
    tampilkan_home()
    tampilkan_jadwal()
    messagebox.showinfo("Sukses", "Jadwal terhapus.")

def edit_jadwal():
    sel = tree_jadwal.selection()
    if not sel:
        messagebox.showwarning("Peringatan", "Pilih jadwal yang mau diedit.")
        return

    id_jadwal, hari_lama, matkul_lama, dosen_lama, jam_lama = tree_jadwal.item(sel[0])["values"]

    win = ttk.Toplevel(root)
    win.title("Edit Jadwal")
    win.geometry("420x350")
    win.transient(root)
    win.grab_set()

    frm = ttk.Frame(win, padding=12)
    frm.pack(fill=BOTH, expand=True)

    ttk.Label(frm, text="Mata Kuliah:").pack(anchor=W)
    c_matkul = ttk.Combobox(frm, state="readonly")
    c_matkul.pack(fill=X, pady=4)
    load_matkul_dropdown(c_matkul)
    c_matkul.set(matkul_lama)

    ttk.Label(frm, text="Dosen:").pack(anchor=W)
    c_dosen = ttk.Combobox(frm, state="readonly")
    c_dosen.pack(fill=X, pady=4)

    load_dosen_dropdown(c_dosen)
    c_dosen.set(dosen_lama)

    ttk.Label(frm, text="Hari:").pack(anchor=W)
    c_hari = ttk.Combobox(
        frm,
        values=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    )
    c_hari.set(hari_lama)
    c_hari.pack(fill=X, pady=4)

    ttk.Label(frm, text="Jam:").pack(anchor=W)
    e_jam = ttk.Entry(frm)
    e_jam.insert(0, jam_lama)
    e_jam.pack(fill=X, pady=4)

    def simpan_edit():
        hari = c_hari.get().strip()
        matkul_id = matkul_map.get(c_matkul.get())
        dosen_id = dosen_map.get(c_dosen.get())
        jam = e_jam.get().strip()

        if not (hari and matkul_id and dosen_id and jam):
            messagebox.showwarning("Peringatan", "Semua field wajib diisi")
            return

        cursor.execute("""
            UPDATE jadwal
            SET hari=%s, mata_kuliah_id=%s, dosen_id=%s, jam=%s
            WHERE id=%s AND user_id=%s
        """, (hari, matkul_id, dosen_id, jam, id_jadwal, user_logged_in))

        conn.commit()
        tampilkan_jadwal()
        win.destroy()

    ttk.Button(frm, text="Simpan", bootstyle="success", command=simpan_edit)\
        .pack(fill=X, pady=10)

def load_dosen_dropdown(combo):
    dosen_map.clear()
    cursor.execute("""
        SELECT id, kode, nama 
        FROM dosen 
        WHERE user_id=%s
        ORDER BY nama
    """, (user_logged_in,))
    rows = cursor.fetchall()

    values = []
    for i, k, n in rows:
        label = f"{k} - {n}"
        values.append(label)
        dosen_map[label] = i

    combo["values"] = values
    combo.set("")

def tambah_tugas():
    matkul = combo_matkul_tugas.get().strip()
    deskripsi = entry_tugas_desc.get().strip()
    deadline = entry_tugas_deadline.entry.get().strip()

    if not (matkul and deadline):
        messagebox.showwarning("Peringatan", "Mata kuliah dan deadline wajib diisi!")
        return

    cursor.execute(
    "INSERT INTO tugas (mata_kuliah, deskripsi, deadline, status, user_id) VALUES (%s, %s, %s, %s, %s)",
    (matkul, deskripsi, deadline, "Belum Selesai", user_logged_in)
    )
    conn.commit()
    tampilkan_tugas()
    combo_matkul_tugas.set("")
    entry_tugas_desc.delete(0, END)
    messagebox.showinfo("Sukses", "Tugas berhasil ditambahkan!")

def hapus_tugas():
    sel = tree_tugas.selection()
    if not sel:
        messagebox.showwarning("Peringatan", "Pilih tugas yang mau dihapus.")
        return
    id_hapus = tree_tugas.item(sel[0])["values"][0]

    cursor.execute(
    "DELETE FROM tugas WHERE id=%s AND user_id=%s",
    (id_hapus, user_logged_in)
)
    conn.commit()
    tampilkan_tugas()
    messagebox.showinfo("Sukses", "Tugas terhapus.")

def edit_tugas():
    sel = tree_tugas.selection()
    if not sel:
        messagebox.showwarning("Peringatan", "Pilih tugas yang mau diedit.")
        return

    id_tugas, matkul_lama, desc_lama, deadline_lama, _ = tree_tugas.item(sel[0])["values"]

    win = ttk.Toplevel(root)
    win.title("Edit Tugas")
    win.geometry("420x350")
    win.transient(root)
    win.grab_set()

    frm = ttk.Frame(win, padding=12)
    frm.pack(fill=BOTH, expand=True)

    ttk.Label(frm, text="Mata Kuliah:").pack(anchor=W)
    e_matkul = ttk.Entry(frm)
    e_matkul.insert(0, matkul_lama)
    e_matkul.pack(fill=X, pady=4)

    ttk.Label(frm, text="Deadline:").pack(anchor=W)
    e_deadline = DateEntry(frm, bootstyle="warning", dateformat="%Y-%m-%d")
    e_deadline.set_date(deadline_lama)
    e_deadline.pack(fill=X, pady=4)

    ttk.Label(frm, text="Deskripsi:").pack(anchor=W)
    e_desc = ttk.Entry(frm)
    e_desc.insert(0, desc_lama)
    e_desc.pack(fill=X, pady=4)

    def simpan_edit():
        matkul = e_matkul.get().strip()
        deadline = e_deadline.entry.get().strip()
        desc = e_desc.get().strip()

        if not (matkul and deadline):
            messagebox.showwarning("Peringatan", "Mata kuliah dan deadline wajib diisi!")
            return

        cursor.execute("""
            UPDATE tugas
            SET mata_kuliah=%s, deskripsi=%s, deadline=%s
            WHERE id=%s AND user_id=%s
        """, (matkul, desc, deadline, id_tugas, user_logged_in))
        conn.commit()

        win.destroy()
        tampilkan_tugas()
        messagebox.showinfo("Sukses", "Tugas berhasil diperbarui.")

    ttk.Button(frm, text="Simpan", bootstyle="success", command=simpan_edit)\
        .pack(fill=X, pady=10)

def ubah_status_tugas():
    sel = tree_tugas.selection()
    if not sel:
        messagebox.showwarning("Peringatan", "Pilih tugas yang mau ditandai selesai.")
        return

    id_tugas = tree_tugas.item(sel[0])["values"][0]
    cursor.execute(
    "UPDATE tugas SET status='Selesai' WHERE id=%s AND user_id=%s",
    (id_tugas, user_logged_in)
)
    conn.commit()
    tampilkan_tugas()
    messagebox.showinfo("Sukses", "Status tugas diubah menjadi selesai.")

def cek_tugas_deadline():
    global notifikasi_deadline_sudah
    if notifikasi_deadline_sudah:
        return
    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)

    cursor.execute("""
        SELECT mata_kuliah, deadline 
        FROM tugas 
        WHERE status='Belum Selesai' AND user_id=%s
    """, (user_logged_in,))
    rows = cursor.fetchall()

    urgent = []

    for mata, dl in rows:
        # FIX 1: pastikan deadline jadi date
        if isinstance(dl, datetime.date):
            dt = dl
        else:
            try:
                dt = datetime.datetime.strptime(str(dl), "%Y-%m-%d").date()
            except ValueError:
                continue  # skip data rusak

        if dt <= today:
            urgent.append((mata, dt, "Deadline hari ini atau sudah lewat!"))
        elif dt == tomorrow:
            urgent.append((mata, dt, "Deadline besok!"))

    if urgent:
        pesan = "Pengingat Tugas:\n\n"
        for m, dt, note in urgent:
            pesan += f"- {m} (Deadline: {dt}) — {note}\n"

        messagebox.showinfo("Pengingat Tugas", pesan)
        notifikasi_deadline_sudah = True

# ============================================
# CRUD DOSEN
# ============================================
def tampilkan_dosen():
    for row in tree_dosen.get_children():
        tree_dosen.delete(row)

    cursor.execute("""
    SELECT d.id, d.kode, d.nama, m.nama
    FROM dosen d
    JOIN mata_kuliah m ON d.mata_kuliah_id = m.id
    WHERE d.user_id=%s
    ORDER BY d.kode
""", (user_logged_in,))
    for row in cursor.fetchall():
        tree_dosen.insert("", "end", values=row)

def tampilkan_mata_kuliah():
    for row in tree_matkul.get_children():
        tree_matkul.delete(row)

    cursor.execute("""
    SELECT id, nama
    FROM mata_kuliah
    WHERE user_id=%s
    ORDER BY nama
""", (user_logged_in,))
    for row in cursor.fetchall():
        tree_matkul.insert("", "end", values=row)

def tambah_dosen():
    kd = entry_kode_dosen.get().strip()
    nm = entry_nama_dosen.get().strip()
    matkul_nama = combo_matkul_dosen.get().strip()

    if not (kd and nm and matkul_nama):
        messagebox.showwarning("Peringatan", "Semua field wajib diisi!")
        return

    # ambil ID mata kuliah
    matkul_id = matkul_map.get(matkul_nama)
    if not matkul_id:
        messagebox.showerror("Error", "Mata kuliah tidak valid")
        return

    # cek duplikat kode dosen
    cursor.execute(
        "SELECT COUNT(*) FROM dosen WHERE kode=%s AND user_id=%s",
        (kd, user_logged_in)
    )
    if cursor.fetchone()[0] > 0:
        messagebox.showwarning("Duplikat", "Kode dosen sudah ada")
        return

    cursor.execute(
        """
        INSERT INTO dosen (kode, nama, mata_kuliah_id, user_id)
        VALUES (%s, %s, %s, %s)
        """,
        (kd, nm, matkul_id, user_logged_in)
    )
    conn.commit()

    tampilkan_dosen()

    load_dosen_dropdown(combo_dosen_jadwal)
    kunci_form_jadwal()

    # reset input
    entry_kode_dosen.delete(0, END)
    entry_nama_dosen.delete(0, END)
    combo_matkul_dosen.set("")

    messagebox.showinfo("Sukses", "Dosen berhasil ditambahkan!")


def hapus_dosen():
    sel = tree_dosen.selection()
    if not sel:
        messagebox.showwarning("Peringatan", "Pilih dosen yang ingin dihapus!")
        return

    id_hapus = tree_dosen.item(sel[0])["values"][0]

    cursor.execute(
    "DELETE FROM dosen WHERE id=%s AND user_id=%s",
    (id_hapus, user_logged_in)
)
    conn.commit()

    tampilkan_dosen()
    load_dosen_dropdown(combo_dosen_jadwal)
    kunci_form_jadwal()
    messagebox.showinfo("Sukses", "Dosen berhasil dihapus!")

def edit_dosen():
    sel = tree_dosen.selection()
    if not sel:
        messagebox.showwarning("Peringatan", "Pilih dosen yang mau diedit.")
        return

    data = tree_dosen.item(sel[0])["values"]
    id_dosen, kode_lama, nama_lama, mk_lama = data

    win = ttk.Toplevel(root)
    win.title("Edit Dosen")
    win.geometry("420x420")
    win.transient(root)
    win.grab_set()

    # FRAME + CANVAS
    container = ttk.Frame(win)
    container.pack(fill=BOTH, expand=True)

    canvas = ttk.Canvas(container)
    canvas.pack(side=LEFT, fill=BOTH, expand=True)

    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    scrollbar.pack(side=RIGHT, fill=Y)

    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    frm = ttk.Frame(canvas, padding=12)
    canvas.create_window((0, 0), window=frm, anchor="nw")

    # -------------- INPUT ----------------
    ttk.Label(frm, text="Kode Dosen:").pack(anchor=W)
    e_kode = ttk.Entry(frm)
    e_kode.insert(0, kode_lama)
    e_kode.pack(fill=X, pady=4)

    ttk.Label(frm, text="Nama Dosen:").pack(anchor=W)
    e_nama = ttk.Entry(frm)
    e_nama.insert(0, nama_lama)
    e_nama.pack(fill=X, pady=4)

    ttk.Label(frm, text="Mata Kuliah:").pack(anchor=W)
    c_mk = ttk.Combobox(frm, state="readonly")
    c_mk.pack(fill=X, pady=4)

    load_matkul_dropdown(c_mk)
    c_mk.set(mk_lama)

    def simpan_edit(event=None):
        mk_nama = c_mk.get().strip()
        mk_id = matkul_map.get(mk_nama)

        if not mk_id:
            messagebox.showerror("Error", "Mata kuliah tidak valid")
            return

        cursor.execute("""
            UPDATE dosen
            SET kode=%s, nama=%s, mata_kuliah_id=%s
            WHERE id=%s AND user_id=%s
        """, (
            e_kode.get().strip(),
            e_nama.get().strip(),
            mk_id,
            id_dosen,
            user_logged_in
        ))
        conn.commit()

        win.destroy()
        tampilkan_dosen()
        messagebox.showinfo("Sukses", "Data dosen berhasil diperbarui.")

    ttk.Button(
        frm,
        text="Simpan Perubahan",
        bootstyle="success",
        command=simpan_edit
    ).pack(fill=X, pady=12)

def tambah_mata_kuliah():
    nama = entry_matkul_baru.get().strip()
    if not nama:
        messagebox.showwarning("Peringatan", "Nama mata kuliah wajib diisi")
        return

    cursor.execute(
        "SELECT COUNT(*) FROM mata_kuliah WHERE nama=%s AND user_id=%s",
        (nama, user_logged_in)
    )
    if cursor.fetchone()[0] > 0:
        messagebox.showwarning("Duplikat", "Mata kuliah sudah ada")
        return

    cursor.execute(
        "INSERT INTO mata_kuliah (nama, user_id) VALUES (%s, %s)",
        (nama, user_logged_in)
    )
    conn.commit()

    entry_matkul_baru.delete(0, END)
    refresh_matkul_dropdowns()
    tampilkan_mata_kuliah()
    messagebox.showinfo("Sukses", "Mata kuliah ditambahkan!")

def edit_mata_kuliah():
    sel = tree_matkul.selection()
    if not sel:
        messagebox.showwarning("Peringatan", "Pilih mata kuliah yang mau diedit.")
        return

    id_matkul, nama_lama = tree_matkul.item(sel[0])["values"]

    win = ttk.Toplevel(root)
    win.title("Edit Mata Kuliah")
    win.geometry("400x200")
    win.transient(root)
    win.grab_set()

    frm = ttk.Frame(win, padding=12)
    frm.pack(fill=BOTH, expand=True)

    ttk.Label(frm, text="Nama Mata Kuliah:").pack(anchor=W)
    e_nama = ttk.Entry(frm)
    e_nama.insert(0, nama_lama)
    e_nama.pack(fill=X, pady=4)

    def simpan_edit():
        nama_baru = e_nama.get().strip()
        if not nama_baru:
            messagebox.showwarning("Peringatan", "Nama mata kuliah wajib diisi")
            return

        # Check for duplicates
        cursor.execute(
            "SELECT COUNT(*) FROM mata_kuliah WHERE nama=%s AND user_id=%s AND id!=%s",
            (nama_baru, user_logged_in, id_matkul)
        )
        if cursor.fetchone()[0] > 0:
            messagebox.showwarning("Duplikat", "Mata kuliah sudah ada")
            return

        cursor.execute(
            "UPDATE mata_kuliah SET nama=%s WHERE id=%s AND user_id=%s",
            (nama_baru, id_matkul, user_logged_in)
        )
        conn.commit()

        win.destroy()
        refresh_matkul_dropdowns()
        tampilkan_mata_kuliah()
        messagebox.showinfo("Sukses", "Mata kuliah berhasil diperbarui.")

    ttk.Button(frm, text="Simpan", bootstyle="success", command=simpan_edit)\
        .pack(fill=X, pady=10)

def hapus_mata_kuliah():
    sel = tree_matkul.selection()
    if not sel:
        messagebox.showwarning("Peringatan", "Pilih mata kuliah yang mau dihapus.")
        return

    id_hapus = tree_matkul.item(sel[0])["values"][0]

    # Check if mata kuliah is used in jadwal or dosen
    cursor.execute(
        "SELECT COUNT(*) FROM jadwal WHERE mata_kuliah_id=%s AND user_id=%s",
        (id_hapus, user_logged_in)
    )
    if cursor.fetchone()[0] > 0:
        messagebox.showwarning("Tidak Dapat Dihapus", "Mata kuliah ini masih digunakan dalam jadwal.")
        return

    cursor.execute(
        "SELECT COUNT(*) FROM dosen WHERE mata_kuliah_id=%s AND user_id=%s",
        (id_hapus, user_logged_in)
    )
    if cursor.fetchone()[0] > 0:
        messagebox.showwarning("Tidak Dapat Dihapus", "Mata kuliah ini masih digunakan oleh dosen.")
        return

    cursor.execute(
        "DELETE FROM mata_kuliah WHERE id=%s AND user_id=%s",
        (id_hapus, user_logged_in)
    )
    conn.commit()

    refresh_matkul_dropdowns()
    tampilkan_mata_kuliah()
    messagebox.showinfo("Sukses", "Mata kuliah terhapus.")

# ============================================
# LOGIN & REGISTER
# ============================================
def switch_to_register():
    login_frame.pack_forget()
    register_frame.pack(fill=BOTH, expand=True)

def switch_to_login():
    register_frame.pack_forget()
    login_frame.pack(fill=BOTH, expand=True)

def register_user():
    user = reg_username.get().strip()
    pwd = reg_password.get().strip()

    if not user or not pwd:
        messagebox.showwarning("Peringatan", "Isi semua field!")
        return

    try:
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (user, pwd)
        )
        conn.commit()
        messagebox.showinfo("Sukses", "Akun berhasil dibuat!")
        switch_to_login()

    except mysql.connector.errors.IntegrityError:
        messagebox.showerror("Error", "Username sudah digunakan!")

def try_login():
    global user_logged_in
    global notifikasi_deadline_sudah
    notifikasi_deadline_sudah = False
    user = entry_username.get().strip()
    pwd = entry_password.get().strip()

    cursor.execute(
        "SELECT id, username FROM users WHERE username=%s AND password=%s",
        (user, pwd)
    )
    result = cursor.fetchone()

    if result:
        user_logged_in = result[0]     
        show_main_frames()
    else:
        messagebox.showerror("Login Gagal", "Username atau password salah!")

def show_main_frames():
    login_frame.pack_forget()
    register_frame.pack_forget()
    main_frame.pack(fill=BOTH, expand=True)

    refresh_matkul_dropdowns()

    if combo_dosen_jadwal is not None:
        load_dosen_dropdown(combo_dosen_jadwal)

    tampilkan_semua()
    cek_tugas_deadline()
    tampilkan_dosen()
    tampilkan_mata_kuliah()

    kunci_form_jadwal()

def refresh_matkul_dropdowns():
    combos = []
    if combo_matkul_jadwal is not None:
        combos.append(combo_matkul_jadwal)
    if combo_matkul_tugas is not None:
        combos.append(combo_matkul_tugas)
    if combo_matkul_dosen is not None:
        combos.append(combo_matkul_dosen)

    if combos:
        load_matkul_dropdown(*combos)

def logout_user():
    tanya = messagebox.askyesno(
        "Konfirmasi Logout",
        "Apakah Anda yakin ingin logout?"
    )

    if tanya:
        global user_logged_in
        user_logged_in = None

        main_frame.pack_forget()
        login_frame.pack(fill=BOTH, expand=True)

        entry_username.delete(0, END)
        entry_password.delete(0, END)

        messagebox.showinfo("Logout", "Anda berhasil logout.")
    else:
        return

# ============================================
# UI APLIKASI
# ============================================
root = ttk.Window(title="Jadwal Kuliah & Pengingat Tugas", themename="morph")
root.geometry("900x650")

# LOGIN FRAME
login_frame = ttk.Frame(root, padding=20)
login_frame.pack(fill=BOTH, expand=True)

ttk.Label(login_frame, text="🔐 Login", font=("Comic Sans MS", 20, "bold"),
          bootstyle="info").pack(pady=(10,20))

frm_login_box = ttk.Frame(login_frame, padding=12)
frm_login_box.pack(pady=10)

ttk.Label(frm_login_box, text="Username:").grid(row=0, column=0, sticky=W, pady=6)
entry_username = ttk.Entry(frm_login_box, width=30)
entry_username.grid(row=0, column=1, padx=8)
entry_username.focus_set()

ttk.Label(frm_login_box, text="Password:").grid(row=1, column=0, sticky=W, pady=6)
entry_password = ttk.Entry(frm_login_box, width=30, show="*")
entry_password.grid(row=1, column=1, padx=8)
entry_username.bind("<Return>", lambda event: entry_password.focus_set())
entry_password.bind("<Return>", lambda event: try_login())
entry_username.focus_set()

ttk.Button(frm_login_box, text="Masuk", bootstyle="success-outline", command=try_login)\
    .grid(row=2, column=1, sticky="e", pady=12)

ttk.Button(login_frame, text="Buat Akun Baru", bootstyle="info-link",
           command=switch_to_register).pack(pady=8)

# REGISTER FRAME
register_frame = ttk.Frame(root, padding=20)
ttk.Label(register_frame, text="🆕 Buat Akun Baru", font=("Comic Sans MS", 20, "bold"),
          bootstyle="primary").pack(pady=(10,20))

frm_reg_box = ttk.Frame(register_frame, padding=12)
frm_reg_box.pack(pady=10)

ttk.Label(frm_reg_box, text="Username:").grid(row=0, column=0, sticky=W, pady=6)
reg_username = ttk.Entry(frm_reg_box, width=30)
reg_username.grid(row=0, column=1, padx=8)

ttk.Label(frm_reg_box, text="Password:").grid(row=1, column=0, sticky=W, pady=6)
reg_password = ttk.Entry(frm_reg_box, width=30, show="*")
reg_password.grid(row=1, column=1, padx=8)
reg_password.bind("<Return>", lambda event: register_user())
reg_username.bind("<Return>", lambda event: reg_password.focus_set())
reg_username.focus_set()

ttk.Button(frm_reg_box, text="Daftar", bootstyle="success-outline",
           command=register_user).grid(row=2, column=1, sticky="e", pady=12)

ttk.Button(register_frame, text="Kembali ke Login", bootstyle="secondary-link",
           command=switch_to_login).pack(pady=5)

# MAIN FRAME
main_frame = ttk.Frame(root)
header = ttk.Frame(main_frame)
header.pack(fill=X, padx=12, pady=8)

ttk.Label(header, text="🎓 Jadwal Kuliah & Pengingat Tugas",
          font=("Comic Sans MS", 18, "bold"),
          bootstyle="success").pack(side=LEFT)

ttk.Button(
    header,
    text="Logout",
    bootstyle="danger-outline",
    command=logout_user
).pack(side=RIGHT, padx=10)

notebook = ttk.Notebook(main_frame, bootstyle="info")
notebook.pack(fill=BOTH, expand=True, padx=12, pady=6)

# HOME TAB
frame_home = ttk.Frame(notebook, padding=12)
notebook.add(frame_home, text="🏠 Home")

# JADWAL TAB
frame_jadwal = ttk.Frame(notebook, padding=12)
notebook.add(frame_jadwal, text="📚 Jadwal Kuliah")

frm_input_jadwal = ttk.Labelframe(
    frame_jadwal,
    text="Tambah Jadwal",
    padding=10,
    bootstyle="info"
)
frm_input_jadwal.pack(fill=X, padx=6, pady=6)

# =========================
# TABEL JADWAL (WAJIB ADA)
# =========================
tree_jadwal = ttk.Treeview(
    frame_jadwal,
    columns=("ID", "Hari", "Mata Kuliah", "Dosen", "Jam"),
    show="headings",
    height=10
)

for col, text, w in [
    ("ID", "ID", 40),
    ("Hari", "Hari", 100),
    ("Mata Kuliah", "Mata Kuliah", 220),
    ("Dosen", "Dosen", 180),
    ("Jam", "Jam", 80)
]:
    tree_jadwal.heading(col, text=text)
    tree_jadwal.column(col, width=w, anchor=W)

tree_jadwal.pack(fill=BOTH, expand=True, padx=6, pady=6)

# --- FRAME UNTUK TOMBOL EDIT/HAPUS JADWAL ---
btn_frame_jadwal = ttk.Frame(frame_jadwal)
btn_frame_jadwal.pack(fill=X, padx=6, pady=6)

ttk.Button(btn_frame_jadwal, text="Edit Jadwal",
           bootstyle="warning", command=edit_jadwal)\
    .pack(side=LEFT, padx=4)

ttk.Button(btn_frame_jadwal, text="Hapus Jadwal"),
ttk.Label(frm_input_jadwal, text="Mata Kuliah:")\
    .grid(row=0, column=0, sticky=W, pady=6)

combo_matkul_jadwal = ttk.Combobox(
    frm_input_jadwal,
    state="readonly",
    width=34
)
combo_matkul_jadwal.grid(row=0, column=1, padx=8)


# === Dosen ===
ttk.Label(frm_input_jadwal, text="Dosen:")\
    .grid(row=1, column=0, sticky=W, pady=6)

combo_dosen_jadwal = ttk.Combobox(
    frm_input_jadwal,
    state="readonly",
    width=34
)
combo_dosen_jadwal.grid(row=1, column=1, padx=8)


# === Hari ===
ttk.Label(frm_input_jadwal, text="Hari:")\
    .grid(row=2, column=0, sticky=W, pady=6)

combo_hari = ttk.Combobox(
    frm_input_jadwal,
    values=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],
    width=34
)
combo_hari.grid(row=2, column=1, padx=8)


# === Jam ===
ttk.Label(frm_input_jadwal, text="Jam (08:30):")\
    .grid(row=3, column=0, sticky=W, pady=6)

entry_jam = ttk.Entry(frm_input_jadwal, width=36)
entry_jam.grid(row=3, column=1, padx=8)


# === Tombol ===
ttk.Button(
    frm_input_jadwal,
    text="Tambah Jadwal",
    bootstyle="success",
    command=tambah_jadwal
).grid(row=4, column=1, sticky="e", pady=10)

# TUGAS TAB
frame_tugas = ttk.Frame(notebook, padding=12)
notebook.add(frame_tugas, text="📝 Tugas Kuliah")

frm_input_tugas = ttk.Labelframe(frame_tugas, text="Tambah Tugas",
                                 padding=10, bootstyle="info")
frm_input_tugas.pack(fill=X, padx=6, pady=6)

ttk.Label(frm_input_tugas, text="Mata Kuliah:").grid(row=0, column=0, sticky=W, pady=6)
combo_matkul_tugas = ttk.Combobox(
    frm_input_tugas,
    state="readonly",
    width=38
)
combo_matkul_tugas.grid(row=0, column=1, padx=8)

ttk.Label(frm_input_tugas, text="Deadline (YYYY-MM-DD):").grid(row=1, column=0, sticky=W, pady=6)
entry_tugas_deadline = DateEntry(frm_input_tugas, bootstyle="warning", dateformat="%Y-%m-%d")
entry_tugas_deadline.grid(row=1, column=1, padx=8)

ttk.Label(frm_input_tugas, text="Deskripsi:").grid(row=2, column=0, sticky=NW, pady=6)
entry_tugas_desc = ttk.Entry(frm_input_tugas, width=60)
entry_tugas_desc.grid(row=2, column=1, padx=8)

ttk.Button(frm_input_tugas, text="Tambah Tugas",
           bootstyle="success", command=tambah_tugas)\
    .grid(row=3, column=1, sticky="e", pady=8)

# --- FRAME UNTUK TOMBOL EDIT/HAPUS/LIST TUGAS ---
btn_frame = ttk.Frame(frame_tugas)
btn_frame.pack(pady=10)

ttk.Button(btn_frame, text="Edit Tugas",
           bootstyle="warning", command=edit_tugas)\
    .pack(side=LEFT, padx=4)

tree_tugas = ttk.Treeview(frame_tugas,
                          columns=("ID","Mata Kuliah","Deskripsi","Deadline","Status"),
                          show="headings", height=10)
for col, text, w in [
    ("ID","ID",50),
    ("Mata Kuliah","Mata Kuliah",220),
    ("Deskripsi","Deskripsi",260),
    ("Deadline","Deadline",110),
    ("Status","Status",100)
]:
    tree_tugas.heading(col, text=text)
    tree_tugas.column(col, width=w,
                      anchor=CENTER if col in ("ID","Deadline","Status") else W)
tree_tugas.pack(fill=BOTH, expand=True, padx=6, pady=6)

btn_frame = ttk.Frame(frame_tugas)
btn_frame.pack(fill=X, padx=6, pady=6)

ttk.Button(btn_frame, text="Hapus Tugas",
           bootstyle="danger", command=hapus_tugas)\
    .pack(side=LEFT, padx=4)

ttk.Button(btn_frame, text="Tandai Selesai",
           bootstyle="info", command=ubah_status_tugas)\
    .pack(side=LEFT, padx=4)

# DOSEN TAB
frame_dosen = ttk.Frame(notebook, padding=12)
notebook.add(frame_dosen, text="👨‍🏫 Dosen")

frm_input_dosen = ttk.Labelframe(frame_dosen, text="Tambah Dosen",
                                 padding=10, bootstyle="info")
frm_input_dosen.pack(fill=X, padx=6, pady=6)

ttk.Label(frm_input_dosen, text="Kode Dosen (inisial):").grid(row=0, column=0, sticky=W, pady=6)
entry_kode_dosen = ttk.Entry(frm_input_dosen, width=40)
entry_kode_dosen.grid(row=0, column=1, padx=8)

ttk.Label(frm_input_dosen, text="Nama Lengkap Dosen:").grid(row=1, column=0, sticky=W, pady=6)
entry_nama_dosen = ttk.Entry(frm_input_dosen, width=40)
entry_nama_dosen.grid(row=1, column=1, padx=8)

ttk.Label(frm_input_dosen, text="Mata Kuliah:").grid(row=2, column=0, sticky=W, pady=6)
combo_matkul_dosen = ttk.Combobox(
    frm_input_dosen,
    state="readonly",
    width=38
)
combo_matkul_dosen.grid(row=2, column=1, padx=8)

ttk.Button(frm_input_dosen, text="Tambah Dosen",
           bootstyle="success", command=tambah_dosen)\
    .grid(row=3, column=1, sticky="e", pady=8)

ttk.Button(frame_dosen, text="Edit Dosen",
           bootstyle="info", command=edit_dosen)\
    .pack(pady=4)

tree_dosen = ttk.Treeview(frame_dosen,
                          columns=("ID","Kode","Nama","Matkul"),
                          show="headings", height=10)
for col, text, w in [
    ("ID","ID",40),
    ("Kode","Kode",80),
    ("Nama","Nama Lengkap",240),
    ("Matkul","Mata Kuliah",200)
]:
    tree_dosen.heading(col, text=text)
    tree_dosen.column(col, width=w, anchor=W)
tree_dosen.pack(fill=BOTH, expand=True, padx=6, pady=6)

ttk.Button(frame_dosen, text="Hapus Dosen",
           bootstyle="danger", command=hapus_dosen)\
    .pack(pady=6)

frame_matkul = ttk.Frame(notebook, padding=12)
notebook.add(frame_matkul, text="📘 Mata Kuliah")

# Treeview for Mata Kuliah
tree_matkul = ttk.Treeview(
    frame_matkul,
    columns=("ID", "Nama"),
    show="headings",
    height=10
)

for col, text, w in [
    ("ID", "ID", 50),
    ("Nama", "Nama Mata Kuliah", 400)
]:
    tree_matkul.heading(col, text=text)
    tree_matkul.column(col, width=w, anchor=W)

tree_matkul.pack(fill=BOTH, expand=True, padx=6, pady=6)

# Frame for buttons
btn_frame_matkul = ttk.Frame(frame_matkul)
btn_frame_matkul.pack(fill=X, padx=6, pady=6)

ttk.Button(btn_frame_matkul, text="Edit Mata Kuliah",
           bootstyle="warning", command=edit_mata_kuliah)\
    .pack(side=LEFT, padx=4)

ttk.Button(btn_frame_matkul, text="Hapus Mata Kuliah",
           bootstyle="danger", command=hapus_mata_kuliah)\
    .pack(side=LEFT, padx=4)

# Input section
frm_input_matkul = ttk.Labelframe(frame_matkul, text="Tambah Mata Kuliah",
                                 padding=10, bootstyle="info")
frm_input_matkul.pack(fill=X, padx=6, pady=6)

ttk.Label(frm_input_matkul, text="Nama Mata Kuliah:").pack(anchor=W, pady=6)
entry_matkul_baru = ttk.Entry(frm_input_matkul, width=40)
entry_matkul_baru.pack(pady=4)

ttk.Button(
    frm_input_matkul,
    text="Tambah Mata Kuliah",
    bootstyle="success",
    command=tambah_mata_kuliah
).pack(pady=6)

# TUTUP APP
def on_close():
    try:
        conn.commit()
        conn.close()
    except:
        pass
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)
root.mainloop()
