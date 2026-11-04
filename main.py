import sys
import random
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('MechPro - Faz 0')
        self.resize(400, 300)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self.label = QLabel('Sayi: -')
        layout.addWidget(self.label)

        btn = QPushButton('Rastgele Sayi Uret (1-10)')
        btn.clicked.connect(self.generate_number)
        layout.addWidget(btn)

    def generate_number(self):
        num = random.randint(1, 10)
        self.label.setText(f'Sayi: {num}')


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
