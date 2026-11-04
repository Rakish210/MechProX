import sys
import random
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget,
                             QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QComboBox, QSpinBox, QLineEdit, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class StyledTab(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(12)


class DashboardTab(StyledTab):
    def __init__(self):
        super().__init__()
        title = QLabel("Goster Paneli")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.layout.addWidget(title)

        stats = QHBoxLayout()
        for name, val in [("Toplam Poz", "42"), ("Malzeme", "18"), ("Blok", "7"), ("Modul", "1 (Sihhi)")]:
            card = QFrame()
            card.setStyleSheet("background:#1e293b; border-radius:8px; padding:12px;")
            cl = QVBoxLayout(card)
            cl.addWidget(QLabel(name))
            v = QLabel(val)
            v.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
            v.setStyleSheet("color:#38bdf8;")
            cl.addWidget(v)
            stats.addWidget(card)
        self.layout.addLayout(stats)

        self.layout.addWidget(QLabel("Son islemler:"))
        log = QTableWidget(5, 3)
        log.setHorizontalHeaderLabels(["Tarih", "Islem", "Durum"])
        log.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        data = [("2026-11-04", "BOM import", "OK"), ("2026-11-03", "PDF rapor", "OK"),
                ("2026-11-02", "DXF export", "OK"), ("2026-11-01", "SQLite init", "OK"),
                ("2026-10-31", "UI scaffold", "OK")]
        for i, row in enumerate(data):
            for j, v in enumerate(row):
                log.setItem(i, j, QTableWidgetItem(v))
        self.layout.addWidget(log)
        self.layout.addStretch()


class BomTab(StyledTab):
    def __init__(self):
        super().__init__()
        title = QLabel("BOM / BOQ")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.layout.addWidget(title)

        ctrl = QHBoxLayout()
        ctrl.addWidget(QLabel("Proje:"))
        combo = QComboBox()
        combo.addItems(["Proje 1", "Proje 2", "Yeni Proje"])
        ctrl.addWidget(combo)
        ctrl.addStretch()
        btn_add = QPushButton("+ Poz Ekle")
        btn_add.setStyleSheet("background:#2563eb; color:white; padding:6px 12px; border-radius:4px;")
        ctrl.addWidget(btn_add)
        btn_export = QPushButton("Excel Export")
        btn_export.setStyleSheet("background:#16a34a; color:white; padding:6px 12px; border-radius:4px;")
        ctrl.addWidget(btn_export)
        self.layout.addLayout(ctrl)

        table = QTableWidget(8, 6)
        table.setHorizontalHeaderLabels(["Poz No", "Malzeme", "Birim", "Miktar", "Birim Fiyat", "Toplam"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        sample = [("1.1", "Boru DN50", "m", "10", "45.50", "455.00"),
                  ("1.2", "Vana DN50", "adet", "2", "120.00", "240.00"),
                  ("2.1", "Radyator 1000", "adet", "5", "350.00", "1750.00")]
        for i, row in enumerate(sample):
            for j, v in enumerate(row):
                table.setItem(i, j, QTableWidgetItem(v))
        self.layout.addWidget(table)

        total = QLabel("Toplam: 2.445,00 TL")
        total.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        total.setStyleSheet("color:#38bdf8;")
        self.layout.addWidget(total)
        self.layout.addStretch()


class HesapTab(StyledTab):
    def __init__(self):
        super().__init__()
        title = QLabel("Sihhi Tesisat Hesabi")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.layout.addWidget(title)

        form = QHBoxLayout()
        form.addWidget(QLabel("Debi (l/s):"))
        self.debi = QSpinBox()
        self.debi.setRange(1, 100)
        self.debi.setValue(5)
        form.addWidget(self.debi)
        form.addWidget(QLabel("Boru capi (mm):"))
        self.cap = QComboBox()
        self.cap.addItems(["20", "25", "32", "40", "50", "63"])
        form.addWidget(self.cap)
        form.addStretch()
        btn = QPushButton("Hesapla")
        btn.setStyleSheet("background:#2563eb; color:white; padding:6px 12px; border-radius:4px;")
        btn.clicked.connect(self.hesapla)
        form.addWidget(btn)
        self.layout.addLayout(form)

        self.sonuc = QLabel("Sonuc: -")
        self.sonuc.setFont(QFont("Segoe UI", 14))
        self.layout.addWidget(self.sonuc)
        self.layout.addStretch()

    def hesapla(self):
        debi = self.debi.value()
        cap = int(self.cap.currentText())
        hiz = debi * 1000 / (3.14159 * (cap / 2) ** 2) / 1000
        self.sonuc.setText("Debi: %d l/s | Cap: %d mm | Hiz: %.2f m/s" % (debi, cap, hiz))


class AyarlarTab(StyledTab):
    def __init__(self):
        super().__init__()
        title = QLabel("Ayarlar")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.layout.addWidget(title)

        self.layout.addWidget(QLabel("Tema:"))
        tema = QComboBox()
        tema.addItems(["Koyu (Varsayilan)", "Acik"])
        self.layout.addWidget(tema)

        self.layout.addWidget(QLabel("Dil:"))
        dil = QComboBox()
        dil.addItems(["Turkce", "English", "Russkiy"])
        self.layout.addWidget(dil)

        self.layout.addWidget(QLabel("Proje konumu:"))
        path = QLineEdit("/opt/data/Alfred_Projeler/MechPro")
        self.layout.addWidget(path)

        btn = QPushButton("Kaydet")
        btn.setStyleSheet("background:#16a34a; color:white; padding:6px 12px; border-radius:4px;")
        self.layout.addWidget(btn)
        self.layout.addStretch()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MechPro - Faz 0 MVP")
        self.resize(1000, 700)

        tabs = QTabWidget()
        tabs.addTab(DashboardTab(), "Goster Paneli")
        tabs.addTab(BomTab(), "BOM / BOQ")
        tabs.addTab(HesapTab(), "Sihhi Tesisat")
        tabs.addTab(AyarlarTab(), "Ayarlar")
        self.setCentralWidget(tabs)

        self.setStyleSheet("""
            QMainWindow { background: #0f172a; }
            QWidget { background: #0f172a; color: #e2e8f0; font-family: Segoe UI; font-size: 13px; }
            QTabWidget::pane { border: 1px solid #334155; border-radius: 4px; }
            QTabBar::tab { background: #1e293b; color: #94a3b8; padding: 8px 16px; margin-right: 2px; border-radius: 4px 4px 0 0; }
            QTabBar::tab:selected { background: #334155; color: #f1f5f9; }
            QTableWidget { background: #1e293b; gridline-color: #334155; }
            QHeaderView::section { background: #334155; color: #f1f5f9; padding: 4px; border: none; }
            QLineEdit, QComboBox, QSpinBox { background: #1e293b; border: 1px solid #475569; border-radius: 4px; padding: 4px; color: #f1f5f9; }
            QPushButton { background: #334155; color: #f1f5f9; border: none; padding: 6px 12px; border-radius: 4px; }
            QPushButton:hover { background: #475569; }
            QLabel { color: #e2e8f0; }
            QFrame { border: none; }
        """)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
