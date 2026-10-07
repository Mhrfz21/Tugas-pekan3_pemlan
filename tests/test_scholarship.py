import sqlite3
from typing import Dict, Any, List, Optional

class LegacyScholarshipManager:
    """
    PERINGATAN: Kodingan ini sengaja dirancang buruk sebagai bahan latihan refactoring!
    Mengandung berbagai 'Code Smells' dan melanggar prinsip SOLID.
    """

    def __init__(self, db_path: str='beasiswa_legacy.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self._setup_db()

    def _setup_db(self):
        cursor = self.conn.cursor()
        cursor.execute('\n            CREATE TABLE IF NOT EXISTS beasiswa (\n                id INTEGER PRIMARY KEY AUTOINCREMENT,\n                nim TEXT,\n                nama TEXT,\n                jenis TEXT,\n                ipk REAL,\n                semester INTEGER,\n                status TEXT,\n                catatan TEXT\n            )\n        ')
        self.conn.commit()

    def submit_application(self, data: Dict[str, Any]) -> Dict[str, Any]:
        nim = data.get('nim', '')
        nama = data.get('nama', '')
        ipk = float(data.get('ipk', 0.0))
        semester = int(data.get('semester', 1))
        jenis_beasiswa = data.get('jenis', '').lower()
        hafalan_juz = int(data.get('hafalan_juz', 0))
        punya_prestasi_nasional = bool(data.get('prestasi_nasional', False))
        punya_sktm = bool(data.get('sktm', False))
        reasons = []
        if semester < 3 or semester > 8:
            reasons.append(f'Semester {semester} di luar batas yang diizinkan (syarat: Semester 3 s.d 8)')
        if jenis_beasiswa == 'tahfidz':
            if ipk < 3.25:
                reasons.append(f'IPK {ipk} belum memenuhi standar Tahfidz (minimal 3.25)')
            if hafalan_juz < 10:
                reasons.append(f'Hafalan {hafalan_juz} Juz belum mencukupi (minimal 10 Juz)')
        elif jenis_beasiswa == 'prestasi':
            if ipk < 3.5:
                reasons.append(f'IPK {ipk} belum memenuhi standar Beasiswa Prestasi (minimal 3.50)')
            if not punya_prestasi_nasional:
                reasons.append('Tidak memiliki bukti sertifikat juara tingkat nasional/internasional')
        elif jenis_beasiswa == 'kip-kuliah':
            if ipk < 3.0:
                reasons.append(f'IPK {ipk} belum memenuhi batas KIP-Kuliah (minimal 3.00)')
            if not punya_sktm:
                reasons.append('Tidak melampirkan Surat Keterangan Tidak Mampu (SKTM) yang valid')
        else:
            reasons.append(f"Jenis beasiswa '{jenis_beasiswa}' tidak dikenali oleh sistem UINAM")
        is_approved = len(reasons) == 0
        cursor = self.conn.cursor()
        status_str = 'DISETUJUI' if is_approved else 'DITOLAK'
        catatan_str = 'Memenuhi kriteria seleksi berkas' if is_approved else ' | '.join(reasons)
        cursor.execute('INSERT INTO beasiswa (nim, nama, jenis, ipk, semester, status, catatan) VALUES (?, ?, ?, ?, ?, ?, ?)', (nim, nama, jenis_beasiswa, ipk, semester, status_str, catatan_str))
        self.conn.commit()
        if is_approved:
            pesan = f"Selamat sdr/i {nama} (NIM: {nim}), berkas beasiswa '{jenis_beasiswa.upper()}' Anda DISETUJUI!"
        else:
            pesan = f'Mohon maaf sdr/i {nama}, berkas beasiswa Anda DITOLAK karena: ' + ', '.join(reasons)
        self._send_whatsapp(nim, pesan)
        return {'nim': nim, 'nama': nama, 'jenis': jenis_beasiswa, 'disetujui': is_approved, 'alasan': reasons}

    def _send_whatsapp(self, nim: str, teks: str):
        print(f'[WA GATEWAY -> {nim}]: {teks}')
import unittest

class TestLegacyScholarshipSafetyNet(unittest.TestCase):

    def setUp(self):
        self.manager = LegacyScholarshipManager(db_path=':memory:')

    def test_mahasiswa_tahfidz_valid_harus_disetujui(self):
        data = {'nim': '60200122010', 'nama': 'Muhammad Fajar', 'ipk': 3.75, 'semester': 4, 'jenis': 'tahfidz', 'hafalan_juz': 15}
        hasil = self.manager.submit_application(data)
        self.assertTrue(hasil['disetujui'])
        self.assertEqual(len(hasil['alasan']), 0)

    def test_mahasiswa_semester_akhir_harus_ditolak(self):
        data = {'nim': '60200119099', 'nama': 'Rina Safitri', 'ipk': 3.9, 'semester': 9, 'jenis': 'prestasi', 'prestasi_nasional': True}
        hasil = self.manager.submit_application(data)
        self.assertFalse(hasil['disetujui'])
        self.assertTrue(any(('Semester' in a for a in hasil['alasan'])))

    def test_beasiswa_prestasi_ipk_kurang_harus_ditolak(self):
        data = {'nim': '60200122088', 'nama': 'Budi Santoso', 'ipk': 3.3, 'semester': 5, 'jenis': 'prestasi', 'prestasi_nasional': True}
        hasil = self.manager.submit_application(data)
        self.assertFalse(hasil['disetujui'])
        self.assertTrue(any(('IPK' in a for a in hasil['alasan'])))
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
from typing import Protocol, Tuple, Optional

class ScholarshipRule(Protocol):
    """Interface Segregation: Setiap aturan validasi hanya punya 1 fungsi evaluasi."""

    def evaluate(self, application: ScholarshipApplication) -> Tuple[bool, Optional[str]]:
        """
        Returns:
            Tuple (is_valid, error_message_if_invalid)
        """
        ...

class ScholarshipRepositoryPort(Protocol):

    def save(self, application: ScholarshipApplication) -> None:
        ...

    def find_by_nim(self, nim: str) -> Optional[ScholarshipApplication]:
        ...

class NotificationPort(Protocol):

    def send(self, recipient: str, title: str, message: str) -> bool:
        ...

class SemesterEligibilityRule:
    """Aturan Umum UINAM: Mahasiswa harus aktif pada Semester 3 s.d 8."""

    def evaluate(self, application: ScholarshipApplication) -> Tuple[bool, Optional[str]]:
        sem = application.student.semester
        if sem < 3 or sem > 8:
            return (False, f'Semester {sem} di luar batas yang diizinkan (syarat: Semester 3 s.d 8)')
        return (True, None)

class TahfidzEligibilityRule:
    """Syarat Beasiswa Tahfidz: IPK >= 3.25 dan Hafalan >= 10 Juz."""

    def evaluate(self, application: ScholarshipApplication) -> Tuple[bool, Optional[str]]:
        if application.jenis_beasiswa != 'tahfidz':
            return (True, None)
        student = application.student
        if student.ipk < 3.25:
            return (False, f'IPK {student.ipk} belum memenuhi standar Tahfidz (minimal 3.25)')
        if student.hafalan_juz < 10:
            return (False, f'Hafalan {student.hafalan_juz} Juz belum mencukupi (minimal 10 Juz)')
        return (True, None)

class PrestasiAkademikRule:
    """Syarat Beasiswa Prestasi: IPK >= 3.50 dan Punya Sertifikat Nasional."""

    def evaluate(self, application: ScholarshipApplication) -> Tuple[bool, Optional[str]]:
        if application.jenis_beasiswa != 'prestasi':
            return (True, None)
        student = application.student
        if student.ipk < 3.5:
            return (False, f'IPK {student.ipk} belum memenuhi standar Beasiswa Prestasi (minimal 3.50)')
        if not student.prestasi_nasional:
            return (False, 'Tidak memiliki bukti sertifikat juara tingkat nasional/internasional')
        return (True, None)

class KIPKuliahEligibilityRule:

    def evaluate(self, application: ScholarshipApplication) -> Tuple[bool, Optional[str]]:
        if application.jenis_beasiswa != 'kip-kuliah':
            return (True, None)
        student = application.student
        if student.ipk < 3.0:
            return (False, f'IPK {student.ipk} belum memenuhi batas KIP-Kuliah (minimal 3.00)')
        if not student.sktm_valid:
            return (False, 'Tidak melampirkan Surat Keterangan Tidak Mampu (SKTM) yang valid')
        return (True, None)

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
        print(f'[WHATSAPP -> {recipient}] {title}: {message}')
        return True

class EmailNotificationAdapter:

    def send(self, recipient: str, title: str, message: str) -> bool:
        print(f'[EMAIL -> {recipient}@uin-alauddin.ac.id] {title}: {message}')
        return True

class ScholarshipService:
    """
    Application Use Case Service yang mematuhi SOLID:
    - SRP: Hanya fokus pada orkestrasi alur seleksi beasiswa.
    - OCP: Pipeline rules dapat ditambah/dikurangi sesuka hati dari luar.
    - DIP: Hanya bergantung pada abstraksi Ports via Constructor Dependency Injection.
    """

    def __init__(self, repository: ScholarshipRepositoryPort, rules: List[ScholarshipRule], notifier: NotificationPort):
        self._repo = repository
        self._rules = rules
        self._notifier = notifier

    def process_application(self, application: ScholarshipApplication) -> Dict[str, Any]:
        student = application.student
        for rule in self._rules:
            is_valid, reason = rule.evaluate(application)
            if not is_valid and reason:
                application.add_rejection_reason(reason)
        is_approved = application.is_eligible
        self._repo.save(application)
        title = f'PENGUMUMAN BEASISWA {application.jenis_beasiswa.upper()} UINAM'
        if is_approved:
            pesan = f'Selamat sdr/i {student.nama}, berkas beasiswa Anda dinyatakan LENGKAP & DISETUJUI.'
        else:
            pesan = f'Yth. sdr/i {student.nama}, berkas beasiswa Anda DITOLAK: ' + '; '.join(application.catatan_kegagalan)
        delivered = self._notifier.send(student.nim, title, pesan)
        return {'nim': student.nim, 'nama': student.nama, 'jenis': application.jenis_beasiswa, 'disetujui': is_approved, 'alasan': application.catatan_kegagalan, 'notifikasi_terkirim': delivered}

class MockNotifier:

    def __init__(self):
        self.sent_messages = []

    def send(self, recipient: str, title: str, message: str) -> bool:
        self.sent_messages.append({'recipient': recipient, 'title': title, 'message': message})
        return True

class TestRefactoredScholarshipService(unittest.TestCase):

    def setUp(self):
        self.repo = InMemoryScholarshipRepository()
        self.notifier = MockNotifier()
        self.rules = [SemesterEligibilityRule(), TahfidzEligibilityRule(), PrestasiAkademikRule(), KIPKuliahEligibilityRule()]
        self.service = ScholarshipService(repository=self.repo, rules=self.rules, notifier=self.notifier)

    def test_tahfidz_eligible_success(self):
        student = StudentProfile(nim='60200122001', nama='Ahmad Hidayat', ipk=3.8, semester=5, hafalan_juz=30)
        app = ScholarshipApplication(student=student, jenis_beasiswa='tahfidz')
        result = self.service.process_application(app)
        self.assertTrue(result['disetujui'])
        self.assertEqual(len(result['alasan']), 0)
        self.assertEqual(len(self.notifier.sent_messages), 1)
        self.assertIn('DISETUJUI', self.notifier.sent_messages[0]['message'])
        self.assertIsNotNone(self.repo.find_by_nim('60200122001'))

    def test_semester_invalid_rejected(self):
        student = StudentProfile(nim='60200119099', nama='Rina', ipk=3.9, semester=9, prestasi_nasional=True)
        app = ScholarshipApplication(student=student, jenis_beasiswa='prestasi')
        result = self.service.process_application(app)
        self.assertFalse(result['disetujui'])
        self.assertTrue(any(('Semester' in a for a in result['alasan'])))
        self.assertIn('DITOLAK', self.notifier.sent_messages[0]['message'])

    def test_prestasi_gpa_low_rejected(self):
        student = StudentProfile(nim='60200122088', nama='Budi', ipk=3.3, semester=5, prestasi_nasional=True)
        app = ScholarshipApplication(student=student, jenis_beasiswa='prestasi')
        result = self.service.process_application(app)
        self.assertFalse(result['disetujui'])
        self.assertTrue(any(('IPK' in a for a in result['alasan'])))

    def test_kip_kuliah_rule_works_without_sktm(self):
        student = StudentProfile(nim='60200122077', nama='Siti', ipk=3.4, semester=3, sktm_valid=False)
        app = ScholarshipApplication(student=student, jenis_beasiswa='kip-kuliah')
        result = self.service.process_application(app)
        self.assertFalse(result['disetujui'])
        self.assertTrue(any(('SKTM' in a for a in result['alasan'])))
