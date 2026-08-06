from string import Template

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication


ZOOM_DE_FUENTE = 1.0
ZOOM_MINIMO_DE_FUENTE = 0.5
ZOOM_MAXIMO_DE_FUENTE = 2.5
PASO_DE_ZOOM_DE_FUENTE = 0.1
_FUENTE_BASE_DE_APP = None


def _tamanio_de_fuente(base):
    return max(1, round(base * ZOOM_DE_FUENTE))


def _limitar_zoom_de_fuente(zoom):
    return round(max(ZOOM_MINIMO_DE_FUENTE, min(ZOOM_MAXIMO_DE_FUENTE, zoom)), 2)


def _stylesheet():
    return Template("""
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
    font-size: ${fuente_normal}px;
}

QLabel#screenTitle {
    color: #16314f;
    font-size: ${fuente_titulo}px;
    font-weight: 600;
}

QLabel#statusLabel {
    color: #45627f;
    font-size: ${fuente_estado}px;
}

QLabel#resultCountLabel {
    color: #1d4ed8;
    font-size: ${fuente_normal}px;
    font-weight: 600;
}

QLineEdit,
QComboBox,
QTextEdit,
QTextBrowser {
    background: #ffffff;
    border: 1px solid #cfdae8;
    border-radius: 10px;
    color: #1f2a37;
    font-size: ${fuente_normal}px;
    padding: 8px 10px;
    selection-background-color: #2f6fed;
    selection-color: #ffffff;
}

QLineEdit:focus,
QComboBox:focus,
QTextEdit:focus,
QTextBrowser:focus {
    border: 1px solid #2f6fed;
    background: #fdfefe;
}

QComboBox {
    font-size: ${fuente_normal}px;
    padding: 5px 28px 5px 10px;
    font-weight: 600;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
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
    font-size: ${fuente_normal}px;
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

QPushButton[buttonRole="filterToggle"] {
    background: transparent;
    color: #45627f;
    border: none;
    border-radius: 8px;
    padding: 4px 6px;
    font-weight: 600;
}

QPushButton[buttonRole="filterToggle"]:hover {
    background: #eff5ff;
    color: #1d4ed8;
    border: none;
}

QPushButton[buttonRole="filterToggle"]:pressed {
    background: #e5eefc;
    border: none;
}

QPushButton[buttonRole="filterToggle"]:focus {
    outline: none;
    border: 1px solid #b9cde7;
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
    margin-top: 0px;
    color: #16314f;
    font-size: ${fuente_normal}px;
    font-weight: 600;
}

QGroupBox#filtersPanel::title {
    subcontrol-origin: margin;
    left: 0px;
    padding: 0px;
    color: transparent;
    width: 0px;
    height: 0px;
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

QFrame#mailCard[matchRole="subject"] {
    border: 2px solid #22a06b;
}

QLabel#mailText {
    color: #24384d;
    font-size: ${fuente_normal}px;
    line-height: 1.35;
}

QDialog QTextEdit#descriptionEditor,
QDialog QTextBrowser#mailViewer {
    background: #ffffff;
    border-radius: 12px;
    font-size: ${fuente_normal}px;
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
""").substitute(
        fuente_normal=_tamanio_de_fuente(13),
        fuente_titulo=_tamanio_de_fuente(18),
        fuente_estado=_tamanio_de_fuente(12),
    )


def _aplicar_fuente_base_con_zoom(app):
    global _FUENTE_BASE_DE_APP

    if _FUENTE_BASE_DE_APP is None:
        _FUENTE_BASE_DE_APP = QFont(app.font())

    fuente = QFont(_FUENTE_BASE_DE_APP)
    tamanio_base = fuente.pointSizeF()
    if tamanio_base > 0:
        fuente.setPointSizeF(max(1.0, tamanio_base * ZOOM_DE_FUENTE))
    app.setFont(fuente)


def aplicar_tema_compartido():
    app = QApplication.instance()
    if app is None:
        return
    _aplicar_fuente_base_con_zoom(app)
    app.setStyleSheet(_stylesheet())


def posicionar_ventana_en_mitad_izquierda(ventana):
    _posicionar_ventana_en_mitad_de_pantalla(ventana, "izquierda")


def posicionar_ventana_en_mitad_derecha(ventana):
    _posicionar_ventana_en_mitad_de_pantalla(ventana, "derecha")


def _posicionar_ventana_en_mitad_de_pantalla(ventana, lado):
    pantalla = ventana.screen()
    if pantalla is None:
        app = QApplication.instance()
        pantalla = app.primaryScreen() if app is not None else None
    if pantalla is None:
        return

    disponible = pantalla.availableGeometry()
    ancho_izquierdo = disponible.width() // 2
    ancho_derecho = disponible.width() - ancho_izquierdo

    if lado == "derecha":
        inicio_x = disponible.x() + ancho_izquierdo
        ancho_zona = ancho_derecho
    else:
        inicio_x = disponible.x()
        ancho_zona = ancho_izquierdo

    x = inicio_x + (ancho_zona - ventana.width()) // 2
    y = disponible.y() + (disponible.height() - ventana.height()) // 2
    x = _limitar(x, disponible.left(), disponible.right() - ventana.width() + 1)
    y = _limitar(y, disponible.top(), disponible.bottom() - ventana.height() + 1)
    ventana.move(x, y)


def _limitar(valor, minimo, maximo):
    if maximo < minimo:
        return minimo
    return max(minimo, min(maximo, valor))


def establecer_zoom_de_fuente(zoom):
    global ZOOM_DE_FUENTE

    ZOOM_DE_FUENTE = _limitar_zoom_de_fuente(zoom)
    aplicar_tema_compartido()
    return ZOOM_DE_FUENTE


def aumentar_zoom_de_fuente():
    return establecer_zoom_de_fuente(ZOOM_DE_FUENTE + PASO_DE_ZOOM_DE_FUENTE)


def reducir_zoom_de_fuente():
    return establecer_zoom_de_fuente(ZOOM_DE_FUENTE - PASO_DE_ZOOM_DE_FUENTE)


def obtener_zoom_de_fuente():
    return ZOOM_DE_FUENTE


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
