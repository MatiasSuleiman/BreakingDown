from datetime import datetime
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QGroupBox, QGridLayout, QLabel, QLineEdit, QSizePolicy


class Barra_de_fecha(QLineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        font = self.font()
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2.0)
        self.setFont(font)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        posicion = self.cursorPositionAt(event.position().toPoint())
        self.setCursorPosition(self.inicio_de_seccion(posicion))

    def inicio_de_seccion(self, posicion):
        if posicion < 2:
            return 0
        if posicion < 5:
            return 3
        return 6




class Mostrador_de_condiciones:

    @classmethod
    def en(self, master, anchura, altura, x, y, sistema):
        return self(master, anchura, altura, x, y, sistema)

    def __init__(self, master, anchura, altura, x, y, sistema):
        self.sistema = sistema
        self.caja_filtros = QGroupBox("", master)
        self.caja_filtros.setObjectName("filtersPanel")
        self.caja_filtros.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.inicializar_contenidos()

    def inicializar_contenidos(self):
        layout = QGridLayout(self.caja_filtros)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(10)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(3, 1)

        layout.addWidget(QLabel("Enviado por:"), 0, 0)
        self.barra_de_emisor = QLineEdit()
        layout.addWidget(self.barra_de_emisor, 0, 1)

        layout.addWidget(QLabel("Enviado a:"), 0, 2)
        self.barra_de_receptor = QLineEdit()
        layout.addWidget(self.barra_de_receptor, 0, 3)

        layout.addWidget(QLabel("Enviado antes de:"), 1, 0)
        self.barra_de_enviado_antes_de = Barra_de_fecha()
        self.barra_de_enviado_antes_de.setInputMask("00/00/0000")
        self.barra_de_enviado_antes_de.setPlaceholderText("DD/MM/AAAA")
        layout.addWidget(self.barra_de_enviado_antes_de, 1, 1)

        layout.addWidget(QLabel("Enviado despues de:"), 1, 2)
        self.barra_de_enviado_despues_de = Barra_de_fecha()
        self.barra_de_enviado_despues_de.setInputMask("00/00/0000")
        self.barra_de_enviado_despues_de.setPlaceholderText("DD/MM/AAAA")
        layout.addWidget(self.barra_de_enviado_despues_de, 1, 3)

        layout.addWidget(QLabel("Conteniendo:"), 2, 0)
        self.barra_de_cuerpo = QLineEdit()
        layout.addWidget(self.barra_de_cuerpo, 2, 1, 1, 3)



    def parse_fecha(self, texto):
        texto = texto.strip()
        if not texto or "_" in texto:
            return None
        partes = texto.split("/")
        if len(partes) != 3:
            return None
        try:
            dia, mes, anio = [int(p) for p in partes]
            return datetime(anio, mes, dia)
        except ValueError:
            return None

    def aplicar_condiciones_a(self, sistema):
        emisor = self.barra_de_emisor.text().strip()
        receptor = self.barra_de_receptor.text().strip()
        cuerpo = self.barra_de_cuerpo.text().strip()
        fecha_antes = self.parse_fecha(self.barra_de_enviado_antes_de.text())
        fecha_despues = self.parse_fecha(self.barra_de_enviado_despues_de.text())

        sistema.limpiar_condiciones()
        sistema.agregar_condicion_de_emisor(emisor)
        sistema.agregar_condicion_de_receptor(receptor)
        sistema.agregar_condicion_de_enviado_antes_de(fecha_antes)
        sistema.agregar_condicion_de_enviado_despues_de(fecha_despues)
        sistema.agregar_condicion_de_cuerpo(cuerpo)
