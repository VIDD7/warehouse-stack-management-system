import tkinter as tk
from tkinter import messagebox, ttk
from firebase_admin import credentials, initialize_app, db
import datetime

ref = None
ref_riwayat = None

try:
    cred = credentials.Certificate('stack-barang-gudang-firebase-adminsdk-fbsvc-4bca36991c.json')
    initialize_app(cred, { 
        'databaseURL': 'https://stack-barang-gudang-default-rtdb.firebaseio.com/'
    })
    ref = db.reference('tumpukan_barang')
    ref_riwayat = db.reference('riwayat_barang')
except Exception as e:
    print(f"Koneksi ke firebase gagal: {e}")

class stok_gudang:
    def __init__(self):
        # List 'items' digunakan untuk menyimpan tumpukan barangnya
        self.items = []
        # List 'riwayat' digunakan untuk menyimpan log riwayat barang keluar
        self.riwayat = []
        self.muat_data_dari_firebase()
    
    def muat_data_dari_firebase(self):
        """Mengambil data tumpukan barang dan riwayat terbaru dari Firebase"""
        if ref:
            try:
                data = ref.get()
                if data:
                    if isinstance(data, list):
                        # Membersihkan nilai None jika ada indeks kosong di database
                        self.items = [item for item in data if item is not None]
                    elif isinstance(data, dict):
                        self.items = list(data.values())
                else:
                    self.items = []
            except Exception as e:
                print(f"Gagal mengambil tumpukan barang: {e}")
                self.items = []

        if ref_riwayat:
            try:
                data_riwayat = ref_riwayat.get()
                if data_riwayat:
                    if isinstance(data_riwayat, list):
                        self.riwayat = [item for item in data_riwayat if item is not None]
                    elif isinstance(data_riwayat, dict):
                        self.riwayat = list(data_riwayat.values())
                else:
                    self.riwayat = []
            except Exception as e:
                print(f"Gagal mengambil riwayat: {e}")
                self.riwayat = []

    def sinkronisasi_ke_firebase(self):
        """Menyimpan kondisi tumpukan barang terbaru ke Firebase"""
        if ref:
            try:
                ref.set(self.items)
            except Exception as e:
                print(f"Gagal sinkronisasi tumpukan barang ke Firebase: {e}")

    def sinkronisasi_riwayat_ke_firebase(self):
        """Menyimpan kondisi riwayat barang terbaru ke Firebase"""
        if ref_riwayat:
            try:
                ref_riwayat.set(self.riwayat)
            except Exception as e:
                print(f"Gagal sinkronisasi riwayat ke Firebase: {e}")

    def is_empty(self):
        """Memeriksa apakah tumpukan barang kosong. True jika kosong, False jika ada isinya."""
        return len(self.items) == 0

    def push(self, barang):
        """PUSH: Menambahkan barang baru ke posisi paling atas (Top) tumpukan"""    
        self.items.append(barang)
        self.sinkronisasi_ke_firebase()

    def pop(self):
        """POP: Mengambil dan menghapus barang teratas (LIFO - Last In First Out)"""
        if not self.is_empty():
            barang_keluar = self.items.pop()
            self.sinkronisasi_ke_firebase()
            
            # Catat ke riwayat
            waktu_sekarang = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            log_riwayat = f"{barang_keluar} | Keluar: {waktu_sekarang}"
            self.riwayat.append(log_riwayat)
            self.sinkronisasi_riwayat_ke_firebase()
            
            return barang_keluar
        return None

    def peek(self):
        """PEEK: Mengintip/melihat barang paling atas (Top) tanpa menghapusnya"""
        if not self.is_empty():
            return self.items[-1]
        return None

    def size(self):
        """Mendapatkan jumlah total barang yang ada di dalam tumpukan"""
        return len(self.items)

    def reset(self):
        """RESET: Mengosongkan seluruh tumpukan barang di gudang"""
        self.items = []
        self.sinkronisasi_ke_firebase()

    def reset_riwayat(self):
        """RESET: Mengosongkan seluruh riwayat barang keluar"""
        self.riwayat = []
        self.sinkronisasi_riwayat_ke_firebase()


# ==========================================
# INISIALISASI OBJEK STACK UTAMA
# ==========================================
gudang_stack = stok_gudang()

# ==========================================
# FUNGSI-FUNGSI AKSI UTAMA GUI
# ==========================================

def refresh_tampilan_gudang():
    """Memperbarui tampilan tumpukan barang dan riwayat di GUI"""
    # Bersihkan daftar listbox lama
    listbox_visual_tumpukan.delete(0, tk.END)
    
    if gudang_stack.is_empty():
        listbox_visual_tumpukan.insert(tk.END, "  [ GUDANG KOSONG / TIDAK ADA BARANG ]")
        label_status_top.config(text="Barang Teratas (TOP): -", fg="grey")
    else:
        # Menampilkan barang dari posisi teratas (TOP) ke bawah (LIFO)
        tumpukan_terbalik = list(reversed(gudang_stack.items))
        for indeks, barang in enumerate(tumpukan_terbalik):
            if indeks == 0:
                listbox_visual_tumpukan.insert(tk.END, f"[TOP] -> {barang}")
            else:
                listbox_visual_tumpukan.insert(tk.END, f"  └─ {barang}")
                
        label_status_top.config(text=f"Barang Teratas (TOP): {gudang_stack.peek()}", fg="black")
        
    # Perbarui info total barang
    label_total_barang.config(text=f"Total Barang: {gudang_stack.size()} Unit")

    # Refresh riwayat listbox
    listbox_riwayat.delete(0, tk.END)
    if not hasattr(gudang_stack, 'riwayat') or not gudang_stack.riwayat:
        listbox_riwayat.insert(tk.END, "  [ BELUM ADA RIWAYAT BARANG KELUAR ]")
    else:
        # Menampilkan riwayat dari yang paling baru dikeluarkan (teratas)
        riwayat_terbalik = list(reversed(gudang_stack.riwayat))
        for indeks, log in enumerate(riwayat_terbalik):
            listbox_riwayat.insert(tk.END, f" {indeks + 1}. {log}")
            
    # Perbarui label total riwayat
    total_riwayat_count = len(gudang_stack.riwayat) if hasattr(gudang_stack, 'riwayat') else 0
    label_total_riwayat.config(text=f"Total Riwayat: {total_riwayat_count} Item")

def tambah_barang_masuk():
    """Operasi PUSH: Menambahkan barang baru ke tumpukan teratas"""
    nama_barang = entry_nama_barang.get().strip()
    kategori = combo_kategori.get()
    
    # Validasi jika nama barang kosong
    if nama_barang == "":
        messagebox.showwarning("Input Kosong", "Harap isi nama barang terlebih dahulu!")
        return
        
    # Format identitas barang yang disimpan nama dan kategori
    identitas_barang = f"{nama_barang.upper()} [{kategori.upper()}]"
    
    # Lakukan Push ke stack (otomatis tersimpan ke Firebase)
    gudang_stack.push(identitas_barang)
    messagebox.showinfo("Push Sukses", f"Barang '{identitas_barang}' berhasil ditumpuk ke gudang.")
    
    # Bersihkan kolom input nama barang dan tampilkan barangnya
    entry_nama_barang.delete(0, tk.END)
    refresh_tampilan_gudang()

def ambil_barang_keluar():
    """Operasi POP: Mengambil barang dari puncak tumpukan"""
    if gudang_stack.is_empty():
        messagebox.showwarning("Gudang Kosong", "Tidak ada barang untuk diambil!")
        return
        
    # Lakukan Pop dari stack (otomatis terhapus di Firebase)
    barang_diambil = gudang_stack.pop()
    messagebox.showinfo("Pop Sukses", f"Barang '{barang_diambil}' dari puncak tumpukan resmi diambil.")
    refresh_tampilan_gudang()

def lihat_barang_teratas():
    """Operasi PEEK: Melihat barang teratas tanpa mengambilnya"""
    if gudang_stack.is_empty():
        messagebox.showwarning("Gudang Kosong", "Tumpukan barang kosong!")
        return
        
    # Lakukan Peek untuk mengambil nilai teratas
    barang_teratas = gudang_stack.peek()
    messagebox.showinfo("Peek (Barang Teratas)", f"Barang yang berada di puncak tumpukan (TOP) saat ini:\n\n👉 {barang_teratas}")

def kosongkan_gudang_handler():
    """Operasi RESET: Mengosongkan seluruh tumpukan barang di rak gudang"""
    if gudang_stack.is_empty():
        messagebox.showinfo("Informasi", "Gudang sudah kosong.")
        return
        
    # Konfirmasi sebelum menghapus semua data
    tanya = messagebox.askyesno("Konfirmasi", "Apakah Anda yakin ingin mengosongkan seluruh rak gudang?")
    if tanya:
        gudang_stack.reset()
        messagebox.showinfo("Reset Sukses", "Seluruh tumpukan barang telah dikosongkan.")
        refresh_tampilan_gudang()

def hapus_riwayat_handler():
    """Operasi RESET RIWAYAT: Mengosongkan seluruh riwayat barang keluar"""
    if not hasattr(gudang_stack, 'riwayat') or len(gudang_stack.riwayat) == 0:
        messagebox.showinfo("Informasi", "Riwayat barang keluar sudah kosong.")
        return
        
    tanya = messagebox.askyesno("Konfirmasi Hapus Riwayat", "Apakah Anda yakin ingin menghapus semua riwayat barang keluar?")
    if tanya:
        gudang_stack.reset_riwayat()
        messagebox.showinfo("Reset Sukses", "Seluruh riwayat barang keluar telah dihapus.")
        refresh_tampilan_gudang()


# ==========================================
# TATA LETAK & ANTARMUKA GUI (TKINTER)
# ==========================================

# Palet warna
warna_bg_utama = "#2C3E50"      # Dark Slate Blue (Background utama)
warna_bg_header = "#1A252F"     # Deep Dark Blue (Header)
warna_bg_panel = "#ECF0F1"      # Abu-abu Terang (Latar panel input)
warna_tombol_push = "#2ECC71"   # Hijau Emerald
warna_tombol_pop = "#E67E22"    # Orange Labu
warna_tombol_peek = "#3498DB"   # Biru Peter River
warna_tombol_reset = "#E74C3C"  # Merah Alizarin
warna_tombol_reset_riwayat = "#7F8C8D" # Abu-abu Flat (Reset Riwayat)

root = tk.Tk()
root.title("Sistem Tumpukan Barang Gudang (Stack - LIFO)")
root.geometry("980x600")
root.configure(bg=warna_bg_utama)

# Bagian Header Aplikasi
frame_header = tk.Frame(root, bg=warna_bg_header, height=60)
frame_header.pack(fill="x", side="top")
frame_header.pack_propagate(False)

label_judul = tk.Label(
    frame_header, 
    text="WAREHOUSE STACK MANAGEMENT SYSTEM", 
    bg=warna_bg_header, 
    fg="white", 
    font=("Helvetica", 12, "bold")
)
label_judul.pack(expand=True)

# Panel Form Input Barang
frame_input = tk.LabelFrame(
    root, 
    text=" Input Barang Baru", 
    bg=warna_bg_panel, 
    fg="#2C3E50", 
    font=("Arial", 10, "bold"), 
    padx=15, 
    pady=10
)
frame_input.pack(fill="x", padx=30, pady=15)

label_nama = tk.Label(frame_input, text="Nama Barang :", bg=warna_bg_panel, fg="#2C3E50", font=("Arial", 9, "bold"))
label_nama.grid(row=0, column=0, sticky="w", pady=5)

# Fungsi untuk membatasi panjang karakter input nama barang (maksimal 30 karakter)
def limit_karakter(P):
    return len(P) <= 30

vcmd = root.register(limit_karakter)

entry_nama_barang = tk.Entry(
    frame_input, 
    width=32, 
    font=("Arial", 10),
    validate="key",
    validatecommand=(vcmd, '%P')
)
entry_nama_barang.grid(row=0, column=1, padx=10, pady=5)

label_kategori = tk.Label(frame_input, text="Kategori Barang :", bg=warna_bg_panel, fg="#2C3E50", font=("Arial", 9, "bold"))
label_kategori.grid(row=1, column=0, sticky="w", pady=5)

combo_kategori = ttk.Combobox(
    frame_input, 
    values=["Elektronik", "ATK", "Pakaian", "Peralatan", "Lainnya"], 
    state="readonly", 
    width=30, 
    font=("Arial", 10)
)
combo_kategori.grid(row=1, column=1, padx=10, pady=5)
combo_kategori.set("Elektronik") # Pilihan default awal

# Baris Tombol Kontrol Operasi Stack
frame_tombol = tk.Frame(root, bg=warna_bg_utama)
frame_tombol.pack(fill="x", padx=30, pady=(0, 15))

# Atur kolom tombol agar terbagi rata menjadi 5 kolom
for col_idx in range(5):
    frame_tombol.columnconfigure(col_idx, weight=1)

btn_push = tk.Button(frame_tombol, text="Push (Tambah)", bg=warna_tombol_push, fg="white", font=("Arial", 10, "bold"), pady=8, command=tambah_barang_masuk)
btn_push.grid(row=0, column=0, padx=3, sticky="ew")

btn_pop = tk.Button(frame_tombol, text="Pop (Ambil)", bg=warna_tombol_pop, fg="white", font=("Arial", 10, "bold"), pady=8, command=ambil_barang_keluar)
btn_pop.grid(row=0, column=1, padx=3, sticky="ew")

btn_peek = tk.Button(frame_tombol, text="Peek (Lihat TOP)", bg=warna_tombol_peek, fg="white", font=("Arial", 10, "bold"), pady=8, command=lihat_barang_teratas)
btn_peek.grid(row=0, column=2, padx=3, sticky="ew")

btn_reset = tk.Button(frame_tombol, text="Reset Barang", bg=warna_tombol_reset, fg="white", font=("Arial", 10, "bold"), pady=8, command=kosongkan_gudang_handler)
btn_reset.grid(row=0, column=3, padx=3, sticky="ew")

btn_reset_riwayat = tk.Button(frame_tombol, text="Reset Riwayat", bg=warna_tombol_reset_riwayat, fg="white", font=("Arial", 10, "bold"), pady=8, command=hapus_riwayat_handler)
btn_reset_riwayat.grid(row=0, column=4, padx=3, sticky="ew")

# Panel Visualisasi Tumpukan Fisik Gudang
# Panel Utama Monitor (Container untuk Rak & Riwayat)
frame_monitor_container = tk.Frame(root, bg=warna_bg_utama)
frame_monitor_container.pack(fill="both", expand=True, padx=30, pady=(0, 20))

# Mengatur agar kedua kolom di dalam kontainer selalu memiliki lebar yang sama (50% - 50%)
frame_monitor_container.columnconfigure(0, weight=1, uniform="equal_cols")
frame_monitor_container.columnconfigure(1, weight=1, uniform="equal_cols")
frame_monitor_container.rowconfigure(0, weight=1)

# Panel Visualisasi Tumpukan Fisik Gudang (Kiri)
frame_monitor = tk.LabelFrame(
    frame_monitor_container, 
    text=" Visualisasi Tumpukan Fisik Rak (LIFO) ", 
    bg=warna_bg_panel, 
    fg="#2C3E50", 
    font=("Arial", 10, "bold"), 
    padx=15, 
    pady=15
)
frame_monitor.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

# Status Barang Teratas saat ini
label_status_top = tk.Label(
    frame_monitor, 
    text="Barang Teratas (TOP): -", 
    bg=warna_bg_panel, 
    font=("Arial", 10, "bold"), 
    fg="#2C3E50",
    wraplength=400,
    justify="left"
)
label_status_top.pack(anchor="w", pady=(0, 5))

# Frame untuk Listbox & Scrollbar Rak
frame_listbox_tumpukan = tk.Frame(frame_monitor)
frame_listbox_tumpukan.pack(fill="both", expand=True, pady=5)

listbox_visual_tumpukan = tk.Listbox(frame_listbox_tumpukan, font=("Consolas", 11, "bold"), bg="white", fg="#2C3E50", bd=2, relief="solid")
listbox_visual_tumpukan.pack(side="left", fill="both", expand=True)

scrollbar_tumpukan = tk.Scrollbar(frame_listbox_tumpukan, orient="vertical", command=listbox_visual_tumpukan.yview)
scrollbar_tumpukan.pack(side="right", fill="y")
listbox_visual_tumpukan.config(yscrollcommand=scrollbar_tumpukan.set)

# Informasi Total Barang di Bagian Bawah
frame_info_bawah_barang = tk.Frame(frame_monitor, bg=warna_bg_panel)
frame_info_bawah_barang.pack(fill="x", pady=(10, 0))

label_total_barang = tk.Label(frame_info_bawah_barang, text="Total Barang: 0 Unit", bg=warna_bg_panel, fg="#2C3E50", font=("Arial", 10, "bold"))
label_total_barang.pack(side="left")


# Panel Riwayat Barang Keluar (Kanan)
frame_riwayat = tk.LabelFrame(
    frame_monitor_container, 
    text=" Riwayat Barang Keluar ", 
    bg=warna_bg_panel, 
    fg="#2C3E50", 
    font=("Arial", 10, "bold"), 
    padx=15, 
    pady=15
)
frame_riwayat.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

# Status Riwayat saat ini
label_status_riwayat = tk.Label(frame_riwayat, text="Daftar Barang yang Telah Diambil:", bg=warna_bg_panel, font=("Arial", 10, "bold"), fg="#2C3E50")
label_status_riwayat.pack(anchor="w", pady=(0, 5))

# Frame untuk Listbox & Scrollbar Riwayat
frame_listbox_riwayat = tk.Frame(frame_riwayat)
frame_listbox_riwayat.pack(fill="both", expand=True, pady=5)

listbox_riwayat = tk.Listbox(frame_listbox_riwayat, font=("Consolas", 9, "bold"), bg="white", fg="#2C3E50", bd=2, relief="solid")
listbox_riwayat.pack(side="left", fill="both", expand=True)

scrollbar_riwayat = tk.Scrollbar(frame_listbox_riwayat, orient="vertical", command=listbox_riwayat.yview)
scrollbar_riwayat.pack(side="right", fill="y")
listbox_riwayat.config(yscrollcommand=scrollbar_riwayat.set)    

# Informasi Total Riwayat di Bagian Bawah
frame_info_bawah_riwayat = tk.Frame(frame_riwayat, bg=warna_bg_panel)
frame_info_bawah_riwayat.pack(fill="x", pady=(10, 0))

label_total_riwayat = tk.Label(frame_info_bawah_riwayat, text="Total Riwayat: 0 Item", bg=warna_bg_panel, fg="#2C3E50", font=("Arial", 10, "bold"))
label_total_riwayat.pack(side="left")

refresh_tampilan_gudang()
root.mainloop()