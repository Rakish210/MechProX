import sys
import os
import random
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, QStackedWidget,
                             QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QComboBox, QSpinBox, QLineEdit, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap


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
            card.setStyleSheet("background:#1e293b; border-radius:8px; padding:12px; border:1px solid #334155;")
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
        btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add.setStyleSheet("background:#2563eb; color:white; padding:6px 12px; border-radius:4px;")
        ctrl.addWidget(btn_add)
        btn_export = QPushButton("Excel Export")
        btn_export.setCursor(Qt.CursorShape.PointingHandCursor)
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
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
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
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("background:#16a34a; color:white; padding:6px 12px; border-radius:4px;")
        self.layout.addWidget(btn)
        self.layout.addStretch()


class Sidebar(QWidget):
    def __init__(self, on_select):
        super().__init__()
        self.setFixedWidth(200)
        self.setStyleSheet("background:#1e293b; border-right:1px solid #334155;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(8)

        logo_label = QLabel()
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.jpg")
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            logo_label.setPixmap(pixmap.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo_label)

        app_name = QLabel("MechPro")
        app_name.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        app_name.setStyleSheet("color:#f1f5f9;")
        app_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(app_name)

        layout.addSpacing(16)

        modules = [("Goster Paneli", 0), ("BOM / BOQ", 1), ("Sihhi Tesisat", 2), ("Ayarlar", 3)]
        self.buttons = []
        for name, idx in modules:
            btn = QPushButton(name)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("text-align:left; padding:8px 12px; border-radius:4px; background:transparent; color:#94a3b8; border:none;")
            btn.clicked.connect(lambda checked, i=idx: on_select(i))
            self.buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch()

        self.active_idx = 0
        self._highlight(0)

    def _highlight(self, idx):
        for i, btn in enumerate(self.buttons):
            if i == idx:
                btn.setStyleSheet("text-align:left; padding:8px 12px; border-radius:4px; background:#334155; color:#f1f5f9; font-weight:bold;")
            else:
                btn.setStyleSheet("text-align:left; padding:8px 12px; border-radius:4px; background:transparent; color:#94a3b8;")
        self.active_idx = idx


class Header(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(50)
        self.setStyleSheet("background:#1e293b; border-bottom:1px solid #334155;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)

        title = QLabel("MechPro - Faz 0 MVP")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet("color:#f1f5f9;")
        layout.addWidget(title)
        layout.addStretch()

        user_label = QLabel("Kullanici: Sef")
        user_label.setStyleSheet("color:#94a3b8;")
        layout.addWidget(user_label)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MechPro - Faz 0 MVP")
        self.resize(1100, 700)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = Sidebar(self._on_module_select)
        main_layout.addWidget(self.sidebar)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        header = Header()
        right_layout.addWidget(header)

        self.stack = QStackedWidget()
        self.stack.addWidget(DashboardTab())
        self.stack.addWidget(BomTab())
        self.stack.addWidget(HesapTab())
        self.stack.addWidget(AyarlarTab())
        right_layout.addWidget(self.stack)

        main_layout.addWidget(right)

        self.setStyleSheet("""
            QMainWindow { background: #0f172a; }
            QWidget { background: #0f172a; color: #e2e8f0; font-family: Segoe UI; font-size: 13px; }
            QTableWidget { background: #1e293b; gridline-color: #334155; }
            QHeaderView::section { background: #334155; color: #f1f5f9; padding: 4px; border: none; }
            QLineEdit, QComboBox, QSpinBox { background: #1e293b; border: 1px solid #475569; border-radius: 4px; padding: 4px; color: #f1f5f9; }
            QPushButton { background: #334155; color: #f1f5f9; border: none; padding: 6px 12px; border-radius: 4px; }
            QPushButton:hover { background: #475569; }
            QPushButton:pressed { background: #1d4ed8; }
            QTableWidget::item:hover { background: #334155; }
            QTableWidget::item:selected { background: #2563eb; color: #ffffff; }
            QFrame:hover { background: #263548; }
            QLabel { color: #e2e8f0; }
            QFrame { border: none; }
        """)


    def _on_module_select(self, idx):
        self.stack.setCurrentIndex(idx)
        self.sidebar._highlight(idx)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
