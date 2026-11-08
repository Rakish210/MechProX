def create_sample_widget(context) -> object:
    from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget
    w = QWidget()
    lay = QVBoxLayout(w)
    lay.addWidget(QLabel("Sample Module"))
    lay.addWidget(QLabel("Registered via ModuleRegistry"))
    return w
