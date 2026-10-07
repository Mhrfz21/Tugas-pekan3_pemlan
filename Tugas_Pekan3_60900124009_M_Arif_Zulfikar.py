#!/usr/bin/env python
# coding: utf-8

# # 🏛️ Laboratorium Rekayasa Perangkat Lunak & Sistem Informasi
# ## Fakultas Sains dan Teknologi — UIN Alauddin Makassar
# ### Tugas Terstruktur & Praktikum Pekan 03: Prinsip SOLID & Dependency Injection untuk Refactoring Aman
# **Mata Kuliah:** Pemrograman Lanjut (SIN442430) • **Bobot:** 4 SKS (2 SKS Teori + 2 SKS Praktik)  
# **Capaian Pembelajaran:** Sub-CPMK-2.1 (Menerapkan SOLID dan Dependency Injection untuk Refactoring, Taksonomi Bloom: C6)  
# **Bobot Penilaian:** 4% Penilaian OBE (Tugas Terstruktur 3% + Partisipasi Lab 1%)
# 
# ---
# 
# ### 📝 Lembar Identitas Mahasiswa
# * **Nama Lengkap:** `M Arif Zulfikar`
# * **NIM:** `60900124009`
# * **Kelas:** `A`
# * **Tanggal Pengerjaan:** `2026-09-30`
# * **Tautan GitHub Repositori:** `https://github.com/...`
# 
# ---
# 
# ### 🎯 Tujuan Pembelajaran
# Setelah menyelesaikan tugas praktikum ini, mahasiswa diharapkan mampu:
# 1. **Mendiagnosis Code Smells:** Mengidentifikasi pelanggaran prinsip SOLID (*Rigidity, Fragility, Immobility*) pada kode warisan (*legacy code*).
# 2. **Membangun Safety Net:** Merancang *Characterization Unit Tests* sebelum melakukan restrukturisasi kode.
# 3. **Menerapkan 5 Prinsip SOLID (S-O-L-I-D):**
#    - **SRP:** Memisahkan *God Class* menjadi kelas-kelas dengan tanggung jawab tunggal.
#    - **OCP:** Merancang pipeline validasi berbasis abstraksi sehingga penambahan syarat baru tidak mengubah kode lama.
#    - **LSP:** Memastikan seluruh subtipe mematuhi kontrak antarmuka tanpa efek samping liar (*no unexpected exceptions*).
#    - **ISP:** Menolak *fat interface* dan memecah kontrak menjadi *role protocols* via `typing.Protocol`.
#    - **DIP:** Membalik arah ketergantungan modul bisnis agar bergantung pada abstraksi, bukan detail database/vendor.
# 4. **Menerapkan Constructor Dependency Injection:** Menyuntikkan dependensi kolaborator secara eksplisit sehingga modul 100% *testable* secara terisolasi.
# 5. **Mengeksekusi Baby Steps Refactoring:** Mengubah struktur kode langkah demi langkah dengan perlindungan *automated test suite*.
# 

# ## 🏢 Skenario Studi Kasus: Sistem Pengajuan Beasiswa FST UINAM (SIAKAD-Scholarship)
# 
# Bayangkan Anda baru saja diterima sebagai **Junior Software Architect** di Pusat Teknologi Informasi dan Pangkalan Data (PTIPD) UIN Alauddin Makassar. Anda diberi tugas memodernisasi modul **Layanan Pendaftaran dan Seleksi Beasiswa Internal FST**.
# 
# Pengembang sebelumnya meninggalkan sebuah kelas raksasa (*God Class*) bernama `LegacyScholarshipManager`. Kelas ini berjalan, tetapi memiliki reputasi buruk:
# * **Kaku & Rapuh:** Setiap kali ada SK Rektor baru mengenai skema beasiswa baru, pengembang harus membongkar ratusan baris percabangan `if/elif`.
# * **Sulit Diuji:** Logika kelayakan tidak bisa dites tanpa menyalakan database SQLite fisik dan pulsa API WhatsApp gateway.
# * **Tercampur Aduk:** Logika kalkulasi, query SQL database, pengiriman pesan notifikasi WhatsApp, dan pencetakan bukti terpadu dalam satu kelas raksasa 250 baris.
# 
# ### 📋 Aturan Bisnis Beasiswa Kampus UINAM:
# 1. **Syarat Umum:** Mahasiswa harus aktif pada **Semester 3 sampai Semester 8**. Mahasiswa semester 1, 2, atau semester 9 ke atas tidak berhak mendaftar.
# 2. **Skema Beasiswa Tahfidz Al-Qur'an:**
#    - Minimal IPK: **>= 3.25**
#    - Hafalan minimal: **>= 10 Juz** (dibuktikan dengan sertifikat sah).
# 3. **Skema Beasiswa Prestasi Akademik/Sains:**
#    - Minimal IPK: **>= 3.50**
#    - Sertifikat: Juara Lomba Tingkat Nasional atau Internasional.
# 4. **Skema Beasiswa KIP-Kuliah (Afirmasi):**
#    - Minimal IPK: **>= 3.00**
#    - Surat Keterangan Tidak Mampu (SKTM) dari Kelurahan/Desa terverifikasi.
# 5. **Pencatatan & Notifikasi:**
#    - Jika permohonan **LOLOS**: status disimpan ke database dan dikirimi pesan WhatsApp konfirmasi jadwal wawancara.
#    - Jika permohonan **DITOLAK**: pesan penolakan beserta rincian alasan kegagalan dikirimkan ke nomor WhatsApp mahasiswa.
# 

# ---
# ## 🔍 BAGIAN 1: Observasi & Diagnosis Masalah (15 Poin)
# 
# Mari kita amati kode warisan `LegacyScholarshipManager` di bawah ini. Jalankan cell berikut untuk melihat bagaimana sistem saat ini memproses data pengajuan beasiswa.
# 

# In[1]:


# ============================================================================
# KODE WARISAN (LEGACY CODE) - CONTOH ANTI-PATTERN & PELANGGARAN SOLID
# ============================================================================
import sqlite3
from typing import Dict, Any, List, Optional

class LegacyScholarshipManager:
    """
    PERINGATAN: Kodingan ini sengaja dirancang buruk sebagai bahan latihan refactoring!
    Mengandung berbagai 'Code Smells' dan melanggar prinsip SOLID.
    """
    def __init__(self, db_path: str = "beasiswa_legacy.db"):
        self.db_path = db_path
        # PELANGGARAN DIP: Hardcoded database SQLite langsung di konstruktor
        self.conn = sqlite3.connect(self.db_path)
        self._setup_db()

    def _setup_db(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS beasiswa (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nim TEXT,
                nama TEXT,
                jenis TEXT,
                ipk REAL,
                semester INTEGER,
                status TEXT,
                catatan TEXT
            )
        """)
        self.conn.commit()

    def submit_application(self, data: Dict[str, Any]) -> Dict[str, Any]:
        nim = data.get("nim", "")
        nama = data.get("nama", "")
        ipk = float(data.get("ipk", 0.0))
        semester = int(data.get("semester", 1))
        jenis_beasiswa = data.get("jenis", "").lower()
        hafalan_juz = int(data.get("hafalan_juz", 0))
        punya_prestasi_nasional = bool(data.get("prestasi_nasional", False))
        punya_sktm = bool(data.get("sktm", False))

        reasons = []

        # 1. ATURAN UMUM SEMESTER (PELANGGARAN SRP & OCP)
        if semester < 3 or semester > 8:
            reasons.append(f"Semester {semester} di luar batas yang diizinkan (syarat: Semester 3 s.d 8)")

        # 2. ATURAN SPESIFIK JENIS BEASISWA (PELANGGARAN OCP: Rantai if/elif panjang)
        if jenis_beasiswa == "tahfidz":
            if ipk < 3.25:
                reasons.append(f"IPK {ipk} belum memenuhi standar Tahfidz (minimal 3.25)")
            if hafalan_juz < 10:
                reasons.append(f"Hafalan {hafalan_juz} Juz belum mencukupi (minimal 10 Juz)")

        elif jenis_beasiswa == "prestasi":
            if ipk < 3.50:
                reasons.append(f"IPK {ipk} belum memenuhi standar Beasiswa Prestasi (minimal 3.50)")
            if not punya_prestasi_nasional:
                reasons.append("Tidak memiliki bukti sertifikat juara tingkat nasional/internasional")

        elif jenis_beasiswa == "kip-kuliah":
            if ipk < 3.00:
                reasons.append(f"IPK {ipk} belum memenuhi batas KIP-Kuliah (minimal 3.00)")
            if not punya_sktm:
                reasons.append("Tidak melampirkan Surat Keterangan Tidak Mampu (SKTM) yang valid")

        else:
            reasons.append(f"Jenis beasiswa '{jenis_beasiswa}' tidak dikenali oleh sistem UINAM")

        is_approved = len(reasons) == 0

        # 3. PENYIMPANAN SQL DATABASE (PELANGGARAN SRP: Mengurusi query database)
        cursor = self.conn.cursor()
        status_str = "DISETUJUI" if is_approved else "DITOLAK"
        catatan_str = "Memenuhi kriteria seleksi berkas" if is_approved else " | ".join(reasons)
        cursor.execute(
            "INSERT INTO beasiswa (nim, nama, jenis, ipk, semester, status, catatan) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (nim, nama, jenis_beasiswa, ipk, semester, status_str, catatan_str)
        )
        self.conn.commit()

        # 4. PENGIRIMAN NOTIFIKASI WHATSAPP (PELANGGARAN SRP & DIP: Hardcoded vendor)
        if is_approved:
            pesan = f"Selamat sdr/i {nama} (NIM: {nim}), berkas beasiswa '{jenis_beasiswa.upper()}' Anda DISETUJUI!"
        else:
            pesan = f"Mohon maaf sdr/i {nama}, berkas beasiswa Anda DITOLAK karena: " + ", ".join(reasons)

        self._send_whatsapp(nim, pesan)

        return {
            "nim": nim,
            "nama": nama,
            "jenis": jenis_beasiswa,
            "disetujui": is_approved,
            "alasan": reasons
        }

    def _send_whatsapp(self, nim: str, teks: str):
        # Simulasi pemanggilan API eksternal
        print(f"[WA GATEWAY -> {nim}]: {teks}")

# Uji Coba Eksekusi Kode Warisan:
manager = LegacyScholarshipManager(db_path=":memory:")
demo_mhs = {
    "nim": "60200122001",
    "nama": "Ahmad Hidayat",
    "ipk": 3.80,
    "semester": 5,
    "jenis": "tahfidz",
    "hafalan_juz": 30
}
hasil_demo = manager.submit_application(demo_mhs)
print("\nHasil Pengajuan Demo:", hasil_demo)


# ### 📝 Tugas 1.1: Lembar Audit Pelanggaran SOLID (15 Poin)
# 
# Analisis kode `LegacyScholarshipManager` di atas secara kritis, lalu **isi tabel evaluasi berikut** dengan mengidentifikasi pelanggaran pada masing-masing prinsip SOLID:
# 
# | Huruf | Prinsip SOLID | Letak Pelanggaran di Kode Warisan | Dampak Negatif Arsitektural / Code Smell |
# | :---: | :--- | :--- | :--- |
# | **S** | **Single Responsibility Principle** | `LegacyScholarshipManager` mengurus koneksi dan pembuatan tabel (`__init__`, `_setup_db`, baris 12–32), validasi beasiswa (`submit_application`, baris 34–72), penyimpanan SQL (baris 74–82), serta pengiriman WhatsApp (`_send_whatsapp`, baris 84–102). | Satu kelas memiliki banyak alasan untuk berubah. Perubahan aturan seleksi, skema database, atau penyedia notifikasi berisiko memengaruhi bagian lain. Hal ini meningkatkan coupling, menyulitkan pemeliharaan, dan membuat pengujian unit harus berhadapan dengan banyak tanggung jawab sekaligus (*God Class*). |
# | **O** | **Open/Closed Principle** | Percabangan `if/elif` berdasarkan `jenis_beasiswa` pada baris 50–70, khususnya cabang `tahfidz`, `prestasi`, dan `kip-kuliah`. | Penambahan beasiswa baru, misalnya Atlet PON, mengharuskan modifikasi metode lama dan menambah cabang kondisi. Semakin banyak jenis beasiswa, semakin besar risiko regresi pada aturan yang sudah ada. Sistem tidak terbuka untuk ekstensi tanpa mengubah kode yang telah stabil. |
# | **L** | **Liskov Substitution Principle** | Kode warisan belum memiliki hierarki subclass atau kontrak aturan yang dapat diuji; karena itu pelanggaran LSP belum tampak sebagai baris tertentu. Jika aturan dipisah menjadi subclass, setiap implementasi harus tetap memenuhi kontrak `evaluate` yang sama. | Substitusi implementasi aturan yang mengembalikan tipe atau makna hasil berbeda, atau melempar exception yang tidak diharapkan, dapat merusak pemanggil. Kontrak yang konsisten (pasangan status valid dan pesan kesalahan) memungkinkan setiap aturan dipakai secara bergantian tanpa mengubah perilaku service. |
# | **I** | **Interface Segregation Principle** | `LegacyScholarshipManager` mencampurkan kebutuhan validasi, database, dan notifikasi dalam satu kelas. Tidak ada interface terpisah; pemanggil yang hanya ingin menguji validasi tetap harus membuat manager yang menginisialisasi SQLite melalui `__init__` (baris 12–16). | Klien dan test bergantung pada kemampuan yang tidak dibutuhkannya. Pengujian menjadi lebih berat karena perlu menyiapkan database dan efek samping lain. Kontrak peran yang kecil—aturan, repository, dan notifier—membuat mock lebih sederhana dan mengurangi ketergantungan yang tidak perlu. |
# | **D** | **Dependency Inversion Principle** | `sqlite3.connect(self.db_path)` pada baris 15 mengikat kelas langsung ke SQLite. Pemanggilan `_send_whatsapp` pada baris 90 dan implementasinya pada baris 100–102 mengikat alur bisnis ke mekanisme notifikasi tertentu. | Logika bisnis bergantung pada detail infrastruktur, bukan abstraksi. Pengujian terisolasi menjadi sulit karena kelas membuat koneksi database sendiri dan mengirim notifikasi secara langsung. Mengganti SQLite atau WhatsApp juga memaksa perubahan pada kelas bisnis; dependency injection melalui port memungkinkan repository dan notifier palsu saat pengujian. |
# 
# > 💡 **Petunjuk:** Berikan jawaban yang tajam, teknis, dan mengaitkan dampaknya terhadap kemudahan perawatan (*maintainability*) dan pengujian (*testability*).

# ---
# ## 🎪 BAGIAN 2: Jaring Pengaman (Characterization Testing) (20 Poin)
# 
# > **Hukum Emas Refactoring:** *"Jangan pernah menyentuh atau merefaktor satu baris pun kode lama sebelum Anda memiliki Unit Test otomatis yang HIJAU (Passed)!"*
# 
# Sebelum kita merombak kode `LegacyScholarshipManager`, kita harus membuat **Characterization Tests** (Pengujian Karakterisasi) untuk mengunci perilaku sistem saat ini. Jika nanti saat kita merefaktor ada test yang mendadak **MERAH (Failed)**, berarti kita telah melakukan kesalahan regresi!
# 
# ### Instruksi Tugas 2:
# Lengkapi kelas `TestLegacyScholarshipSafetyNet` di bawah ini untuk menguji minimal 3 skenario penting:
# 1. **Skenario Lolos (Happy Path):** Mahasiswa Tahfidz dengan IPK 3.80, 30 Juz, Semester 5 -> Harus Disetujui (`disetujui == True`).
# 2. **Skenario Pelanggaran Semester:** Mahasiswa semester 9 (melebihi batas semester 8) -> Harus Ditolak (`disetujui == False`).
# 3. **Skenario Pelanggaran Syarat Khusus:** Mahasiswa Beasiswa Prestasi tapi IPK hanya 3.30 (< 3.50) -> Harus Ditolak.
# 

# In[2]:


import unittest

class TestLegacyScholarshipSafetyNet(unittest.TestCase):
    def setUp(self):
        # Gunakan database in-memory agar pengujian aman dan bersih
        self.manager = LegacyScholarshipManager(db_path=":memory:")

    def test_mahasiswa_tahfidz_valid_harus_disetujui(self):
        data = {
            "nim": "60200122010",
            "nama": "Muhammad Fajar",
            "ipk": 3.75,
            "semester": 4,
            "jenis": "tahfidz",
            "hafalan_juz": 15
        }
        hasil = self.manager.submit_application(data)

        # Assertion: pengajuan valid disetujui tanpa alasan penolakan.
        self.assertTrue(hasil["disetujui"])
        self.assertEqual(len(hasil["alasan"]), 0)

    def test_mahasiswa_semester_akhir_harus_ditolak(self):
        data = {
            "nim": "60200119099",
            "nama": "Rina Safitri",
            "ipk": 3.90,
            "semester": 9, # Melanggar batas semester <= 8
            "jenis": "prestasi",
            "prestasi_nasional": True
        }
        hasil = self.manager.submit_application(data)

        # Assertion: pengajuan ditolak dan alasan menyebut semester.
        self.assertFalse(hasil["disetujui"])
        self.assertTrue(any("Semester" in a for a in hasil["alasan"]))

    def test_beasiswa_prestasi_ipk_kurang_harus_ditolak(self):
        data = {
            "nim": "60200122088",
            "nama": "Budi Santoso",
            "ipk": 3.30, # Kurang dari 3.50
            "semester": 5,
            "jenis": "prestasi",
            "prestasi_nasional": True
        }
        hasil = self.manager.submit_application(data)

        # Assertion: pengajuan ditolak dan alasan menyebut IPK.
        self.assertFalse(hasil["disetujui"])
        self.assertTrue(any("IPK" in a for a in hasil["alasan"]))

# Jalankan Test Suite Safety Net
suite = unittest.TestLoader().loadTestsFromTestCase(TestLegacyScholarshipSafetyNet)
runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)
assert result.wasSuccessful(), "❌ Safety net test gagal! Perbaiki test Anda sebelum lanjut ke Bagian 3."
print("\n✅ SAFETY NET TERPASANG SEMPURNA! Kita siap melakukan refactoring dengan aman.")


# ---
# ## 🏗️ BAGIAN 3: Refactoring Bertahap Berbasis SOLID (45 Poin)
# 
# Sekarang kita akan merestrukturisasi sistem menggunakan arsitektur bersih (*Clean / Layered Architecture*) yang mematuhi **5 Prinsip SOLID**.
# 
# Kita akan membagi sistem menjadi 4 lapisan terisolasi:
# ```text
# ┌──────────────────────────────────────────────────────────────┐
# │  1. DOMAIN LAYER (models.py)                                 │
# │     - StudentProfile & ScholarshipApplication (Pure Entity)  │
# ├──────────────────────────────────────────────────────────────┤
# │  2. PORTS / CONTRACTS LAYER (interfaces.py)                  │
# │     - ScholarshipRule(Protocol)                              │
# │     - ScholarshipRepositoryPort(Protocol)                    │
# │     - NotificationPort(Protocol)                             │
# ├──────────────────────────────────────────────────────────────┤
# │  3. ADAPTERS LAYER (infrastructure.py)                       │
# │     - Concrete Rules (TahfidzRule, PrestasiRule, SKTMRule)   │
# │     - InMemoryScholarshipRepository, WhatsAppNotifier        │
# ├──────────────────────────────────────────────────────────────┤
# │  4. APPLICATION SERVICE LAYER (service.py)                   │
# │     - ScholarshipService (Constructor Dependency Injection)  │
# └──────────────────────────────────────────────────────────────┘
# ```
# 
# Mari kita selesaikan langkah demi langkah!
# 

# ### 📦 Langkah 3.1: Lapisan Domain (Single Responsibility Principle)
# Entitas domain hanya bertugas merepresentasikan **data dan aturan bisnis intrinsik**, tanpa mengetahui apa itu database SQL, JSON, atau WhatsApp.
# 

# In[3]:


from dataclasses import dataclass, field
from typing import List, Optional

@dataclass(frozen=True)
class StudentProfile:
    nim: str
    nama: str
    ipk: float
    semester: int
    hafalan_juz: int = 0
    prestasi_nasional: bool = False
    sktm_valid: bool = False

@dataclass
class ScholarshipApplication:
    student: StudentProfile
    jenis_beasiswa: str
    catatan_kegagalan: List[str] = field(default_factory=list)

    @property
    def is_eligible(self) -> bool:
        """Pengajuan dianggap layak jika tidak ada catatan kegagalan aturan."""
        return len(self.catatan_kegagalan) == 0

    def add_rejection_reason(self, reason: str) -> None:
        self.catatan_kegagalan.append(reason)

# Tes Cepat Entitas Domain
mhs_test = StudentProfile(nim="602001", nama="Fajar", ipk=3.8, semester=5, hafalan_juz=30)
app_test = ScholarshipApplication(student=mhs_test, jenis_beasiswa="tahfidz")
assert app_test.is_eligible == True
app_test.add_rejection_reason("Contoh penolakan")
assert app_test.is_eligible == False
print("✅ Langkah 3.1 (Domain Layer) Berhasil!")


# ### 🔌 Langkah 3.2: Lapisan Ports & Contracts (ISP & DIP)
# Gunakan `typing.Protocol` untuk mendefinisikan antarmuka peran (*Role Interfaces*). Ingat prinsip ISP: **kontrak harus ramping dan terfokus pada peran masing-masing**.
# 

# In[4]:


from typing import Protocol, Tuple, Optional

# 1. KONTRAK ATURAN SELEKSI (OCP & LSP)
class ScholarshipRule(Protocol):
    """Interface Segregation: Setiap aturan validasi hanya punya 1 fungsi evaluasi."""
    def evaluate(self, application: ScholarshipApplication) -> Tuple[bool, Optional[str]]:
        """
        Returns:
            Tuple (is_valid, error_message_if_invalid)
        """
        ...

# 2. KONTRAK PENYIMPANAN DATA (ISP & DIP)
class ScholarshipRepositoryPort(Protocol):
    def save(self, application: ScholarshipApplication) -> None:
        ...

    def find_by_nim(self, nim: str) -> Optional[ScholarshipApplication]:
        ...

# 3. KONTRAK PENGIRIMAN NOTIFIKASI (ISP & DIP)
class NotificationPort(Protocol):
    def send(self, recipient: str, title: str, message: str) -> bool:
        ...

print("✅ Langkah 3.2 (Ports/Interfaces Protocol) Berhasil Didefinisikan!")


# ### 🛠️ Langkah 3.3: Lapisan Adapters & Rules (OCP & LSP in Action!)
# Setiap kriteria seleksi dibuat sebagai **class validator independen**. Jika besok ada beasiswa baru, kita cukup menambah class baru tanpa memodifikasi class lain!
# 

# In[5]:


# ============================================================================
# CONCRETE VALIDATION RULES (MEMATUHI OCP & LSP)
# ============================================================================

class SemesterEligibilityRule:
    """Aturan Umum UINAM: Mahasiswa harus aktif pada Semester 3 s.d 8."""
    def evaluate(self, application: ScholarshipApplication) -> Tuple[bool, Optional[str]]:
        sem = application.student.semester
        if sem < 3 or sem > 8:
            return False, f"Semester {sem} di luar batas yang diizinkan (syarat: Semester 3 s.d 8)"
        return True, None

class TahfidzEligibilityRule:
    """Syarat Beasiswa Tahfidz: IPK >= 3.25 dan Hafalan >= 10 Juz."""
    def evaluate(self, application: ScholarshipApplication) -> Tuple[bool, Optional[str]]:
        if application.jenis_beasiswa != "tahfidz":
            return True, None # Bukan domain aturan ini, lewati

        student = application.student
        if student.ipk < 3.25:
            return False, f"IPK {student.ipk} belum memenuhi standar Tahfidz (minimal 3.25)"
        if student.hafalan_juz < 10:
            return False, f"Hafalan {student.hafalan_juz} Juz belum mencukupi (minimal 10 Juz)"
        return True, None

class PrestasiAkademikRule:
    """Syarat Beasiswa Prestasi: IPK >= 3.50 dan Punya Sertifikat Nasional."""
    def evaluate(self, application: ScholarshipApplication) -> Tuple[bool, Optional[str]]:
        if application.jenis_beasiswa != "prestasi":
            return True, None

        student = application.student
        if student.ipk < 3.50:
            return False, f"IPK {student.ipk} belum memenuhi standar Beasiswa Prestasi (minimal 3.50)"
        if not student.prestasi_nasional:
            return False, "Tidak memiliki bukti sertifikat juara tingkat nasional/internasional"
        return True, None

# TODO 3.3: IMPLEMENTASIKAN ATURAN BARU (BUKTI OCP):
# Buatlah class KIPKuliahEligibilityRule di bawah ini:
# Syarat: jenis_beasiswa == 'kip-kuliah' -> IPK >= 3.00 dan sktm_valid == True
class KIPKuliahEligibilityRule:
    def evaluate(self, application: ScholarshipApplication) -> Tuple[bool, Optional[str]]:
        if application.jenis_beasiswa != "kip-kuliah":
            return True, None

        student = application.student
        if student.ipk < 3.00:
            return False, f"IPK {student.ipk} belum memenuhi batas KIP-Kuliah (minimal 3.00)"
        if not student.sktm_valid:
            return False, "Tidak melampirkan Surat Keterangan Tidak Mampu (SKTM) yang valid"
        return True, None

# ============================================================================
# CONCRETE ADAPTERS: IN-MEMORY DATABASE & NOTIFIERS
# ============================================================================

class InMemoryScholarshipRepository:
    """Adapter repository in-memory untuk pengujian kilat tanpa database SQLite nyata."""
    def __init__(self):
        self._db: Dict[str, ScholarshipApplication] = {}

    def save(self, application: ScholarshipApplication) -> None:
        self._db[application.student.nim] = application

    def find_by_nim(self, nim: str) -> Optional[ScholarshipApplication]:
        return self._db.get(nim)

class WhatsAppNotificationAdapter:
    def send(self, recipient: str, title: str, message: str) -> bool:
        print(f"[WHATSAPP -> {recipient}] {title}: {message}")
        return True

class EmailNotificationAdapter:
    def send(self, recipient: str, title: str, message: str) -> bool:
        print(f"[EMAIL -> {recipient}@uin-alauddin.ac.id] {title}: {message}")
        return True

print("✅ Langkah 3.3 (Rules & Adapters) Berhasil Dibuat!")


# ### 🧠 Langkah 3.4: Application Service (DIP & Constructor Injection)
# Kelas `ScholarshipService` bertugas mengorkestrasi proses pengajuan beasiswa. Perhatikan bahwa kelas ini **hanya menerima dependensi melalui `__init__` (Constructor Injection)** dan sama sekali tidak tahu detail SQLite maupun vendor WhatsApp!
# 

# In[6]:


class ScholarshipService:
    """
    Application Use Case Service yang mematuhi SOLID:
    - SRP: Hanya fokus pada orkestrasi alur seleksi beasiswa.
    - OCP: Pipeline rules dapat ditambah/dikurangi sesuka hati dari luar.
    - DIP: Hanya bergantung pada abstraksi Ports via Constructor Dependency Injection.
    """
    def __init__(
        self,
        repository: ScholarshipRepositoryPort,
        rules: List[ScholarshipRule],
        notifier: NotificationPort
    ):
        # Injeksi Dependensi Konstruktor
        self._repo = repository
        self._rules = rules
        self._notifier = notifier

    def process_application(self, application: ScholarshipApplication) -> Dict[str, Any]:
        student = application.student

        # 1. Jalankan Seluruh Aturan Validasi (OCP Pipeline)
        for rule in self._rules:
            is_valid, reason = rule.evaluate(application)
            if not is_valid and reason:
                application.add_rejection_reason(reason)

        is_approved = application.is_eligible

        # 2. Simpan Riwayat Pengajuan ke Repositori (DIP)
        self._repo.save(application)

        # 3. Susun Pesan & Kirimkan Notifikasi via Notifier (Strategy)
        title = f"PENGUMUMAN BEASISWA {application.jenis_beasiswa.upper()} UINAM"
        if is_approved:
            pesan = f"Selamat sdr/i {student.nama}, berkas beasiswa Anda dinyatakan LENGKAP & DISETUJUI."
        else:
            pesan = f"Yth. sdr/i {student.nama}, berkas beasiswa Anda DITOLAK: " + "; ".join(application.catatan_kegagalan)

        delivered = self._notifier.send(student.nim, title, pesan)

        return {
            "nim": student.nim,
            "nama": student.nama,
            "jenis": application.jenis_beasiswa,
            "disetujui": is_approved,
            "alasan": application.catatan_kegagalan,
            "notifikasi_terkirim": delivered
        }

print("✅ Langkah 3.4 (ScholarshipService) Berhasil Dirakit!")


# ---
# ## 🧪 BAGIAN 4: Verifikasi & Uji Refactoring Aman (20 Poin)
# 
# Sekarang saatnya membuktikan bahwa kode hasil refactoring:
# 1. **Mempertahankan Perilaku Asli 100%:** Seluruh skenario pengujian lama tetap lulus.
# 2. **100% Terisolasi & Kilat:** Menggunakan *Mock Notifier* dan *In-Memory Repository*, pengujian berjalan dalam **0.001 detik** tanpa memerlukan database file ataupun jaringan internet.
# 3. **Membuktikan Fleksibilitas (OCP & DIP):** Kita bisa menambah aturan KIP-Kuliah dan menukar adapter notifikasi dengan sangat mudah.
# 
# Jalankan cell pengujian di bawah ini!
# 

# In[7]:


class MockNotifier:
    def __init__(self):
        self.sent_messages = []

    def send(self, recipient: str, title: str, message: str) -> bool:
        self.sent_messages.append({"recipient": recipient, "title": title, "message": message})
        return True

class TestRefactoredScholarshipService(unittest.TestCase):
    def setUp(self):
        self.repo = InMemoryScholarshipRepository()
        self.notifier = MockNotifier()
        self.rules = [
            SemesterEligibilityRule(),
            TahfidzEligibilityRule(),
            PrestasiAkademikRule(),
            KIPKuliahEligibilityRule() # Aturan baru yang kita buat!
        ]
        # Dependency Injection
        self.service = ScholarshipService(
            repository=self.repo,
            rules=self.rules,
            notifier=self.notifier
        )

    def test_tahfidz_eligible_success(self):
        student = StudentProfile(nim="60200122001", nama="Ahmad Hidayat", ipk=3.80, semester=5, hafalan_juz=30)
        app = ScholarshipApplication(student=student, jenis_beasiswa="tahfidz")

        result = self.service.process_application(app)

        self.assertTrue(result["disetujui"])
        self.assertEqual(len(result["alasan"]), 0)
        self.assertEqual(len(self.notifier.sent_messages), 1)
        self.assertIn("DISETUJUI", self.notifier.sent_messages[0]["message"])
        self.assertIsNotNone(self.repo.find_by_nim("60200122001"))

    def test_semester_invalid_rejected(self):
        student = StudentProfile(nim="60200119099", nama="Rina", ipk=3.90, semester=9, prestasi_nasional=True)
        app = ScholarshipApplication(student=student, jenis_beasiswa="prestasi")

        result = self.service.process_application(app)

        self.assertFalse(result["disetujui"])
        self.assertTrue(any("Semester" in a for a in result["alasan"]))
        self.assertIn("DITOLAK", self.notifier.sent_messages[0]["message"])

    def test_prestasi_gpa_low_rejected(self):
        student = StudentProfile(nim="60200122088", nama="Budi", ipk=3.30, semester=5, prestasi_nasional=True)
        app = ScholarshipApplication(student=student, jenis_beasiswa="prestasi")

        result = self.service.process_application(app)

        self.assertFalse(result["disetujui"])
        self.assertTrue(any("IPK" in a for a in result["alasan"]))

    def test_kip_kuliah_rule_works_without_sktm(self):
        # Mahasiswa KIP tapi tidak punya SKTM
        student = StudentProfile(nim="60200122077", nama="Siti", ipk=3.40, semester=3, sktm_valid=False)
        app = ScholarshipApplication(student=student, jenis_beasiswa="kip-kuliah")

        result = self.service.process_application(app)

        self.assertFalse(result["disetujui"])
        self.assertTrue(any("SKTM" in a for a in result["alasan"]))

# Jalankan Test Suite Arsitektur Baru
suite2 = unittest.TestLoader().loadTestsFromTestCase(TestRefactoredScholarshipService)
runner2 = unittest.TextTestRunner(verbosity=2)
result2 = runner2.run(suite2)

if result2.wasSuccessful():
    print("\n" + "=" * 70)
    print("🎉 SELAMAT! SELURUH TEST BERHASIL LULUS (100% GREEN)!")
    print("Arsitektur Anda kini mematuhi 5 Prinsip SOLID & mudah diuji secara kilat.")
    print("=" * 70)
else:
    print("\n❌ Masih ada test yang gagal. Silakan periksa kembali implementasi rule Anda.")


# ---
# ## 📝 BAGIAN 5: Refleksi & Rubrik Penilaian OBE (Sub-CPMK 2.1)
# 
# Jawablah 3 pertanyaan refleksi di bawah ini sebagai pertanggungjawaban desain arsitektur Anda:
# 
# ### 1. Refleksi Testability:
# > **Pertanyaan:** Apa perbedaan paling signifikan yang Anda rasakan saat menguji kode di Bagian 2 (kode warisan) dibandingkan menguji kode di Bagian 4 (kode hasil refactoring SOLID)?  
# > **Jawaban:** Pada kode warisan, pengujian dilakukan melalui `LegacyScholarshipManager` yang sekaligus mengelola validasi, SQLite, dan notifikasi. Walaupun database in-memory dapat digunakan agar pengujian lebih aman, kelas tersebut tetap memiliki ketergantungan langsung pada SQLite dan mekanisme notifikasi. Pada hasil refactoring, `ScholarshipService` menerima repository, daftar aturan, dan notifier melalui constructor (*Dependency Injection*). Karena itu pengujian dapat memakai `InMemoryScholarshipRepository` dan `MockNotifier`, tanpa file database maupun jaringan. Test juga dapat memeriksa hasil seleksi, penyimpanan, dan pesan notifikasi secara terpisah sehingga kegagalan lebih mudah dilokalisasi.
# 
# ### 2. Refleksi Ekstensibilitas (OCP):
# > **Pertanyaan:** Jika besok Rektor UIN Alauddin Makassar mengeluarkan SK Beasiswa baru: *"Beasiswa Juara MTQ Internasional"*, jelaskan file/kelas apa saja yang perlu Anda buat atau ubah? Apakah `ScholarshipService` perlu dimodifikasi?  
# > **Jawaban:** Saya akan membuat class aturan baru, misalnya `JuaraMTQInternasionalEligibilityRule`, pada lapisan adapters/rules. Class tersebut mengimplementasikan kontrak `ScholarshipRule` melalui method `evaluate` dan memeriksa kriteria khusus beasiswa MTQ. Kemudian instance aturan baru ditambahkan ke daftar `rules` saat `ScholarshipService` dirakit (composition root atau bagian konfigurasi/pemanggil). `ScholarshipService` tidak perlu dimodifikasi karena sudah menjalankan semua aturan yang diinjeksi melalui pipeline. Jika kelak ada kebutuhan menyimpan atribut mahasiswa baru yang belum tersedia, model `StudentProfile` dan pemetaan data pada lapisan pemanggil mungkin perlu diperluas; perubahan itu bergantung pada kriteria resmi beasiswa.
# 
# ### 3. Refleksi Trade-offs Arsitektur:
# > **Pertanyaan:** Tidak ada solusi tanpa kompromi (*No Silver Bullet*). Sebutkan minimal 2 trade-off atau konsekuensi biaya (biaya kognitif, jumlah file, indirection) yang timbul akibat menerapkan prinsip SOLID pada kasus ini!  
# > **Jawaban:**
# > 1. **Jumlah class dan berkas bertambah.** Aturan seleksi, kontrak, repository, notifier, dan service dipisahkan. Struktur ini membuat tanggung jawab lebih jelas, tetapi pengembang perlu membuka beberapa class/berkas untuk memahami satu alur pengajuan. Untuk proyek kecil, pemisahan ini dapat terasa berlebihan.
# > 2. **Indirection dan biaya kognitif meningkat.** Pemanggilan melewati port dan dependency injection, sehingga alur dependensi tidak selalu terlihat langsung dari satu fungsi. Pengembang perlu memahami `Protocol`, adapter, dan proses perakitan dependency sebelum menelusuri eksekusi.
# > 3. **Konfigurasi dan pemeliharaan pipeline menjadi tanggung jawab tambahan.** Aturan baru harus didaftarkan pada komposisi service agar dijalankan. Jika aturan terlupa didaftarkan, class sudah ada tetapi tidak berpengaruh pada proses seleksi. Di sisi lain, pola ini mengurangi kebutuhan mengubah service inti saat menambah aturan.
