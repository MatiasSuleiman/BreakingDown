from functools import partial
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIntValidator
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

try:
    from src.buscador_adapter import normalizar_datetime_naive
    from src.ui_theme import aplicar_rol_de_boton, aplicar_rol_visual
except ModuleNotFoundError:
    from buscador_adapter import normalizar_datetime_naive
    from ui_theme import aplicar_rol_de_boton, aplicar_rol_visual


class Mostrador_de_mails():

    @classmethod
    def en(self, master ,altura, anchura, x, y, user_interface):
        return self(master ,altura, anchura, x, y, user_interface)


    def __init__(self, master ,altura, anchura, x, y, user_interface):

        self.user_interface = user_interface
        self.mails = []

        self.area = QScrollArea(master)
        self.area.setObjectName("mailPanelArea")
        self.area.setWidgetResizable(True)
        self.area.setFrameShape(QFrame.Shape.NoFrame)
        self.area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.area.setMinimumHeight(360)
        aplicar_rol_visual(self.area, "panelRole", self.panel_role())
        self.area.viewport().setObjectName("mailPanelViewport")

        self.contenedor_de_mails = QWidget()
        self.contenedor_de_mails.setObjectName("mailPanelContent")
        aplicar_rol_visual(self.contenedor_de_mails, "panelRole", self.panel_role())

        self.layout = QVBoxLayout(self.contenedor_de_mails)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.layout.setContentsMargins(16, 16, 16, 16)
        self.layout.setSpacing(14)
        self.contenedor_de_mails.setLayout(self.layout)

        self.area.setWidget(self.contenedor_de_mails)

    def panel_role(self):
        raise NotImplementedError("subclass should have overriden panel_role")


    def limpiar_mostrador(self):

        while self.layout.count() > 0: 
            item = self.layout.takeAt(0)  
            widget = item.widget()  
            
            if widget:  
                widget.deleteLater()
        self.mails = []

    def ordenar_por_mas_recientes(self, mails):
        return sorted(mails, key=lambda mail: normalizar_datetime_naive(mail.date), reverse=True)

    def valor_actual_del_scroll_vertical(self):
        return self.area.verticalScrollBar().value()

    def restaurar_scroll_vertical(self, valor):
        self.area.verticalScrollBar().setValue(valor)

    def crear_texto_del_mail(self, frame, mail):
        texto_del_mail = QLabel(
            parent=frame,
            text=f"Asunto: {mail.subject}\nDe: {mail.from_}\nFecha: {mail.date.strftime('%d/%m/%y')}",
        )
        texto_del_mail.setObjectName("mailText")
        texto_del_mail.setWordWrap(True)
        texto_del_mail.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.MinimumExpanding)
        return texto_del_mail

    def cambiar_descripcion_de(self, mail):
        ventana_de_descripcion = QDialog(self.contenedor_de_mails)
        ventana_de_descripcion.setObjectName("descriptionDialog")
        ventana_de_descripcion.setWindowTitle(f"{mail.subject} description")
        ventana_de_descripcion.resize(520, 380)

        layout = QVBoxLayout(ventana_de_descripcion)
        layout.setContentsMargins(16, 16, 16, 16)
        lector_de_texto = QTextEdit(ventana_de_descripcion)
        lector_de_texto.setObjectName("descriptionEditor")
        lector_de_texto.setPlainText(self.user_interface.ver_descripcion_de(mail))
        lector_de_texto.textChanged.connect(
            lambda mail=mail, lector=lector_de_texto: self.user_interface.cambiar_descripcion_de(
                mail,
                lector.toPlainText(),
            )
        )
        layout.addWidget(lector_de_texto)

        ventana_de_descripcion.show()
        ventana_de_descripcion.raise_()
        ventana_de_descripcion.activateWindow()

    def crear_barra_de_minutos(self, frame, mail):
        barra_de_minutos = QLineEdit(frame)
        aplicar_rol_visual(barra_de_minutos, "inputRole", "minutes")
        barra_de_minutos.setMaxLength(4)
        barra_de_minutos.setFixedWidth(55)
        barra_de_minutos.setAlignment(Qt.AlignmentFlag.AlignRight)
        barra_de_minutos.setValidator(QIntValidator(0, 9999, barra_de_minutos))
        barra_de_minutos.setText(str(self.user_interface.ver_minutos_de(mail)))
        barra_de_minutos.textChanged.connect(
            lambda texto, mail=mail: self.user_interface.cambiar_minutos_de(
                mail,
                int(texto) if texto else 0,
            )
        )
        return barra_de_minutos



class Mostrador_de_mails_buscados(Mostrador_de_mails):

    def panel_role(self):
        return "found"


    def agregar_mail(self, mail):
        frame = QFrame()
        frame.setObjectName("mailCard")
        aplicar_rol_visual(frame, "panelRole", self.panel_role())
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        layout_del_frame = QVBoxLayout(frame)
        layout_del_frame.setSizeConstraint(QVBoxLayout.SizeConstraint.SetMinimumSize)
        layout_del_frame.setContentsMargins(16, 14, 16, 14)
        layout_del_frame.setSpacing(10)
        texto_del_mail = self.crear_texto_del_mail(frame, mail)
        layout_del_frame.addWidget(texto_del_mail)

        layout_de_botones = QHBoxLayout()
        layout_de_botones.setSpacing(8)

        boton_de_visualizacion = QPushButton(text="Ver", parent=frame)
        aplicar_rol_de_boton(boton_de_visualizacion, "secondary")
        boton_de_visualizacion.clicked.connect(partial(self.user_interface.ver_mail, mail))
        layout_de_botones.addWidget(boton_de_visualizacion)

        boton_de_agregar = QPushButton(text="+", parent=frame)
        aplicar_rol_de_boton(boton_de_agregar, "primary")
        boton_de_agregar.clicked.connect(partial(self.user_interface.agregar_mail, mail))
        layout_de_botones.addWidget(boton_de_agregar)
        layout_de_botones.addStretch()
        layout_del_frame.addLayout(layout_de_botones)

        self.layout.addWidget(frame)

    def agregar_mails(self, mails):
        valor_actual_del_scroll = self.valor_actual_del_scroll_vertical()

        for mail in mails:
            if mail not in self.mails:
                self.mails.append(mail)

        mails_ordenados = self.ordenar_por_mas_recientes(self.mails)
        self.limpiar_mostrador()
        self.mails = list(mails_ordenados)
        for mail in self.mails:
            self.agregar_mail(mail)
        self.restaurar_scroll_vertical(valor_actual_del_scroll)

    def mostrar(self, mails):
        mails_ordenados = self.ordenar_por_mas_recientes(mails)
        self.limpiar_mostrador()
        self.mails = list(mails_ordenados)
        for mail in self.mails:
            self.agregar_mail(mail)




class Mostrador_de_mails_del_break(Mostrador_de_mails):

    def panel_role(self):
        return "breakdown"

    def agregar_mail(self, mail):
        frame = QFrame()
        frame.setObjectName("mailCard")
        aplicar_rol_visual(frame, "panelRole", self.panel_role())
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        layout_del_frame = QVBoxLayout(frame)
        layout_del_frame.setSizeConstraint(QVBoxLayout.SizeConstraint.SetMinimumSize)
        layout_del_frame.setContentsMargins(16, 14, 16, 14)
        layout_del_frame.setSpacing(10)
        texto_del_mail = self.crear_texto_del_mail(frame, mail)
        layout_del_frame.addWidget(texto_del_mail)

        layout_de_botones = QHBoxLayout()
        layout_de_botones.setSpacing(8)

        boton_de_visualizacion = QPushButton(text="Ver", parent=frame)
        aplicar_rol_de_boton(boton_de_visualizacion, "secondary")
        boton_de_visualizacion.clicked.connect(partial(self.user_interface.ver_mail, mail))
        layout_de_botones.addWidget(boton_de_visualizacion)

        boton_de_agregar_descripcion = QPushButton(text="Description", parent=frame)
        aplicar_rol_de_boton(boton_de_agregar_descripcion, "secondary")
        boton_de_agregar_descripcion.clicked.connect(
            lambda _, mail=mail: self.cambiar_descripcion_de(mail)
        )
        layout_de_botones.addWidget(boton_de_agregar_descripcion)

        layout_de_botones.addWidget(QLabel("Minutes:", frame))
        layout_de_botones.addWidget(self.crear_barra_de_minutos(frame, mail))

        boton_de_quitar = QPushButton(text="x", parent=frame)
        aplicar_rol_de_boton(boton_de_quitar, "danger")
        boton_de_quitar.clicked.connect(partial(self.user_interface.quitar_mail, mail))
        layout_de_botones.addWidget(boton_de_quitar)
        layout_de_botones.addStretch()
        layout_del_frame.addLayout(layout_de_botones)

        self.layout.addWidget(frame)


    def mostrar(self, mails):
        mails_ordenados = self.ordenar_por_mas_recientes(mails)
        self.limpiar_mostrador()
        self.mails = list(mails_ordenados)
        for mail in self.mails:
            self.agregar_mail(mail)
