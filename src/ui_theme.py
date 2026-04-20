from PyQt6.QtWidgets import QApplication


APP_STYLESHEET = """
QMainWindow#mainWindow,
QMainWindow#loginWindow,
QDialog {
    background-color: #f4f7fb;
    color: #1f2a37;
}

QWidget#mainContent,
QWidget#mailPanelContent,
QWidget#loginContent {
    background: transparent;
    color: #1f2a37;
}

QLabel {
    color: #334155;
}

QLabel#screenTitle {
    color: #16314f;
    font-size: 18px;
    font-weight: 600;
}

QLabel#statusLabel {
    color: #45627f;
    font-size: 12px;
}

QLabel#resultCountLabel {
    color: #1d4ed8;
    font-weight: 600;
}

QLineEdit,
QTextEdit,
QTextBrowser {
    background: #ffffff;
    border: 1px solid #cfdae8;
    border-radius: 10px;
    color: #1f2a37;
    padding: 8px 10px;
    selection-background-color: #2f6fed;
    selection-color: #ffffff;
}

QLineEdit:focus,
QTextEdit:focus,
QTextBrowser:focus {
    border: 1px solid #2f6fed;
    background: #fdfefe;
}

QLineEdit[inputRole="minutes"] {
    background: #f8fbff;
    padding: 6px 8px;
    border-radius: 8px;
    font-weight: 600;
}

QPushButton {
    background: #f9fbff;
    color: #27415a;
    border: 1px solid #cfdae8;
    border-radius: 10px;
    padding: 5px 10px;
    font-weight: 600;
}

QPushButton:hover {
    background: #eff5ff;
    border-color: #b9cde7;
}

QPushButton:pressed {
    background: #e5eefc;
}

QPushButton:disabled {
    background: #edf2f7;
    color: #8fa1b5;
    border-color: #d7e0ea;
}

QPushButton[buttonRole="primary"] {
    background: #2f6fed;
    color: #ffffff;
    border: 1px solid #2459c8;
}

QPushButton[buttonRole="primary"]:hover {
    background: #255fd1;
    border-color: #1f4faa;
}

QPushButton[buttonRole="primary"]:pressed {
    background: #1f53b9;
}

QPushButton[buttonRole="toggle"] {
    background: #f6f9fe;
}

QPushButton[buttonRole="toggle"]:checked {
    background: #dce9ff;
    color: #18407d;
    border: 1px solid #7aa5f7;
}

QPushButton[buttonRole="danger"] {
    background: #fff6f5;
    color: #9f2d2d;
    border: 1px solid #efc7c4;
}

QPushButton[buttonRole="danger"]:hover {
    background: #ffeaea;
    border-color: #e7b2ae;
}

QGroupBox#filtersPanel {
    background: #ffffff;
    border: 1px solid #d7e1ee;
    border-radius: 16px;
    margin-top: 14px;
    color: #16314f;
    font-weight: 600;
}

QGroupBox#filtersPanel::title {
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 8px;
    color: #1d4ed8;
}

QFrame#controlPanel {
    background: #ffffff;
    border: 1px solid #d7e1ee;
    border-radius: 16px;
}

QScrollArea#mailPanelArea {
    background: #ffffff;
    border: 1px solid #d7e1ee;
    border-radius: 18px;
}

QWidget#mailPanelViewport {
    background: transparent;
}

QScrollArea#mailPanelArea[panelRole="breakdown"] {
    background: #fdfefe;
}

QScrollArea#mailPanelArea[panelRole="found"] {
    background: #fbfdff;
}

QFrame#mailCard {
    background: #f8fbff;
    border: 1px solid #dbe5f3;
    border-radius: 14px;
}

QFrame#mailCard[panelRole="breakdown"] {
    background: #f6faff;
    border-color: #d4e1f7;
}

QFrame#mailCard[panelRole="found"] {
    background: #fbfdff;
}

QLabel#mailText {
    color: #24384d;
    line-height: 1.35;
}

QDialog QTextEdit#descriptionEditor,
QDialog QTextBrowser#mailViewer {
    background: #ffffff;
    border-radius: 12px;
}

QScrollBar:vertical {
    background: transparent;
    width: 11px;
    margin: 6px 0 6px 0;
}

QScrollBar::handle:vertical {
    background: #c4d6ee;
    border-radius: 5px;
    min-height: 28px;
}

QScrollBar::handle:vertical:hover {
    background: #9db9e5;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical,
QScrollBar:horizontal,
QScrollBar::handle:horizontal,
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {
    background: transparent;
    border: none;
    height: 0px;
    width: 0px;
}
"""


def aplicar_tema_compartido():
    app = QApplication.instance()
    if app is None:
        return
    app.setStyleSheet(APP_STYLESHEET)


def aplicar_rol_de_boton(boton, rol):
    boton.setProperty("buttonRole", rol)
    _repolish(boton)


def aplicar_rol_visual(widget, nombre, valor):
    widget.setProperty(nombre, valor)
    _repolish(widget)


def _repolish(widget):
    style = widget.style()
    if style is not None:
        style.unpolish(widget)
        style.polish(widget)
    widget.update()
