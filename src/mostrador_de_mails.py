from functools import partial
from PyQt6.QtCore import QTimer, Qt
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


class Mostrador_de_mails:

    @classmethod
    def en(self, master, altura, anchura, x, y, user_interface):
        return self(master, altura, anchura, x, y, user_interface)

    def __init__(self, master, altura, anchura, x, y, user_interface):
        self.user_interface = user_interface
        self.mails = []
        self.mails_por_clave = {}
        self.es_mail_por_asunto = {}
        self.generacion_de_scroll = 0

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

    def clave_de_mail(self, mail):
        return getattr(mail, "uid", id(mail))

    def limpiar_mostrador(self):
        self._limpiar_widgets()
        self.mails = []
        self.mails_por_clave = {}
        self.es_mail_por_asunto = {}

    def _limpiar_widgets(self):
        while self.layout.count() > 0:
            item = self.layout.takeAt(0)
            widget = item.widget()

            if widget:
                widget.setParent(None)
                widget.deleteLater()

    def ordenar_por_mas_recientes(self, mails):
        return sorted(mails, key=lambda mail: normalizar_datetime_naive(mail.date), reverse=True)

    def valor_actual_del_scroll_vertical(self):
        return self.area.verticalScrollBar().value()

    def restaurar_scroll_vertical(self, valor):
        scroll = self.area.verticalScrollBar()
        maximo = scroll.maximum()
        if maximo <= 0:
            return
        valor_clampeado = max(scroll.minimum(), min(valor, maximo))
        scroll.setValue(valor_clampeado)

    def ancla_actual_del_scroll_vertical(self):
        scroll = self.area.verticalScrollBar()
        valor = scroll.value()
        limite_inferior = valor + self.area.viewport().height()
        ancla = {"clave": None, "desplazamiento": 0, "valor": valor}

        for indice in range(self.layout.count()):
            widget = self.layout.itemAt(indice).widget()
            if widget is None:
                continue

            geometria = widget.geometry()
            if geometria.bottom() >= valor and geometria.top() <= limite_inferior:
                ancla["clave"] = widget.property("mailKey")
                ancla["desplazamiento"] = geometria.top() - valor
                break

        return ancla

    def restaurar_scroll_vertical_despues_de_layout(self, ancla, generacion, intentos=8):
        if generacion != self.generacion_de_scroll:
            return

        self.layout.activate()
        self.contenedor_de_mails.adjustSize()
        scroll = self.area.verticalScrollBar()
        maximo = scroll.maximum()
        if maximo <= 0 and intentos > 0:
            QTimer.singleShot(
                0,
                lambda ancla=ancla, generacion=generacion, intentos=intentos - 1:
                    self.restaurar_scroll_vertical_despues_de_layout(ancla, generacion, intentos),
            )
            return
        if maximo <= 0:
            return

        valor_a_restaurar = ancla["valor"]
        clave = ancla["clave"]
        if clave is not None:
            for indice in range(self.layout.count()):
                widget = self.layout.itemAt(indice).widget()
                if widget is not None and widget.property("mailKey") == clave:
                    valor_a_restaurar = widget.geometry().top() - ancla["desplazamiento"]
                    break

        valor_clampeado = max(scroll.minimum(), min(valor_a_restaurar, maximo))
        scroll.setValue(valor_clampeado)

    def crear_texto_del_mail(self, frame, mail):
        texto_del_mail = QLabel(
            parent=frame,
            text=f"Asunto: {mail.subject}\nDe: {mail.from_}\nFecha: {mail.date.strftime('%d/%m/%y')}",
        )
        texto_del_mail.setObjectName("mailText")
        texto_del_mail.setWordWrap(True)
        texto_del_mail.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.MinimumExpanding)
        return texto_del_mail

    def crear_tarjeta_base(self, mail, es_por_asunto):
        rol_de_match = "subject" if es_por_asunto else "body"

        frame = QFrame()
        frame.setObjectName("mailCard")
        frame.setProperty("mailKey", self.clave_de_mail(mail))
        aplicar_rol_visual(frame, "panelRole", self.panel_role())
        aplicar_rol_visual(frame, "matchRole", rol_de_match)
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        layout_externo = QHBoxLayout(frame)
        layout_externo.setContentsMargins(0, 0, 0, 0)
        layout_externo.setSpacing(0)

        layout_del_frame = QVBoxLayout()
        layout_del_frame.setSizeConstraint(QVBoxLayout.SizeConstraint.SetMinimumSize)
        layout_del_frame.setContentsMargins(16, 14, 16, 14)
        layout_del_frame.setSpacing(10)
        layout_externo.addLayout(layout_del_frame, 1)

        texto_del_mail = self.crear_texto_del_mail(frame, mail)
        layout_del_frame.addWidget(texto_del_mail)
        return frame, layout_del_frame

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

    def agregar_mail_por_asunto(self, mail):
        self._registrar_mail(mail, True)

    def agregar_mail_por_cuerpo(self, mail):
        self._registrar_mail(mail, False)

    def actualizar_mail_a_asunto(self, mail):
        self._registrar_mail(mail, True)

    def _registrar_mail(self, mail, es_por_asunto):
        cambio = self._registrar_mail_en_estado(mail, es_por_asunto)
        if cambio:
            self._renderizar_desde_estado()

    def registrar_lotes_de_busqueda(
        self,
        mails_por_cuerpo=None,
        mails_por_asunto=None,
        mails_actualizados_a_asunto=None,
    ):
        cambio = False
        for mail in mails_por_cuerpo or []:
            cambio = self._registrar_mail_en_estado(mail, False) or cambio
        for mail in mails_por_asunto or []:
            cambio = self._registrar_mail_en_estado(mail, True) or cambio
        for mail in mails_actualizados_a_asunto or []:
            cambio = self._registrar_mail_en_estado(mail, True) or cambio

        if cambio:
            self._renderizar_desde_estado()

    def _registrar_mail_en_estado(self, mail, es_por_asunto):
        clave = self.clave_de_mail(mail)
        cambio = False
        if clave not in self.mails_por_clave:
            self.mails_por_clave[clave] = mail
            cambio = True
        if es_por_asunto or clave not in self.es_mail_por_asunto:
            if self.es_mail_por_asunto.get(clave) != es_por_asunto:
                cambio = True
            self.es_mail_por_asunto[clave] = es_por_asunto
        return cambio

    def _renderizar_desde_estado(self):
        ancla_del_scroll = self.ancla_actual_del_scroll_vertical()
        self.generacion_de_scroll += 1
        generacion_de_este_render = self.generacion_de_scroll

        self.area.setUpdatesEnabled(False)
        self.contenedor_de_mails.setUpdatesEnabled(False)
        try:
            self._limpiar_widgets()

            self.mails = self.ordenar_por_mas_recientes(self.mails_por_clave.values())
            for mail in self.mails:
                self.agregar_mail_renderizado(
                    mail,
                    self.es_mail_por_asunto.get(self.clave_de_mail(mail), False),
                )
        finally:
            self.contenedor_de_mails.setUpdatesEnabled(True)
            self.area.setUpdatesEnabled(True)

        QTimer.singleShot(
            0,
            lambda ancla=ancla_del_scroll, generacion=generacion_de_este_render:
                self.restaurar_scroll_vertical_despues_de_layout(ancla, generacion),
        )

    def mostrar(self, mails, es_mail_por_asunto=None):

        ancla_del_scroll = self.ancla_actual_del_scroll_vertical()
        self.generacion_de_scroll += 1
        generacion_de_este_render = self.generacion_de_scroll
        self.area.setUpdatesEnabled(False)
        self.contenedor_de_mails.setUpdatesEnabled(False)

        try:
            self._limpiar_widgets()
            self.mails_por_clave = {}
            self.es_mail_por_asunto = {}

            for mail in mails:
                clave = self.clave_de_mail(mail)
                self.mails_por_clave[clave] = mail
                self.es_mail_por_asunto[clave] = (
                    es_mail_por_asunto(mail) if es_mail_por_asunto is not None else False
                )

            self.mails = self.ordenar_por_mas_recientes(self.mails_por_clave.values())
            for mail in self.mails:
                self.agregar_mail_renderizado(
                    mail,
                    self.es_mail_por_asunto.get(self.clave_de_mail(mail), False),
                )
        finally:
            self.contenedor_de_mails.setUpdatesEnabled(True)
            self.area.setUpdatesEnabled(True)
            QTimer.singleShot(
                0,
                lambda ancla=ancla_del_scroll, generacion=generacion_de_este_render:
                    self.restaurar_scroll_vertical_despues_de_layout(ancla, generacion),
            )

    def agregar_mail_renderizado(self, mail, es_por_asunto):
        raise NotImplementedError("subclass should implement agregar_mail_renderizado")


class Mostrador_de_mails_buscados(Mostrador_de_mails):

    def panel_role(self):
        return "found"

    def agregar_mail_renderizado(self, mail, es_por_asunto):
        frame, layout_del_frame = self.crear_tarjeta_base(mail, es_por_asunto)

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


class Mostrador_de_mails_del_break(Mostrador_de_mails):

    def panel_role(self):
        return "breakdown"

    def agregar_mail_renderizado(self, mail, es_por_asunto):
        frame, layout_del_frame = self.crear_tarjeta_base(mail, es_por_asunto)

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
