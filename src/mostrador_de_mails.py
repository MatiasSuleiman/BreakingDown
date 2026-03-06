from functools import partial
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class Mostrador_de_mails():

    @classmethod
    def en(self, master ,altura, anchura, x, y, user_interface):
        return self(master ,altura, anchura, x, y, user_interface)


    def __init__(self, master ,altura, anchura, x, y, user_interface):

        self.user_interface = user_interface
        self.mails = []

        area = QScrollArea(master)
        area.setGeometry(x, y, altura, anchura)
        area.setWidgetResizable(True)

        self.contenedor_de_mails = QWidget()

        self.layout = QVBoxLayout(self.contenedor_de_mails)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.contenedor_de_mails.setLayout(self.layout)

        area.setWidget(self.contenedor_de_mails)


    def limpiar_mostrador(self):

        while self.layout.count() > 0: 
            item = self.layout.takeAt(0)  
            widget = item.widget()  
            
            if widget:  
                widget.deleteLater()
        self.mails = []

    def ordenar_por_mas_recientes(self, mails):
        return sorted(mails, key=lambda mail: mail.date, reverse=True)

    def crear_texto_del_mail(self, frame, mail):
        texto_del_mail = QLabel(
            parent=frame,
            text=f"Asunto: {mail.subject}\nDe: {mail.from_}\nFecha: {mail.date.strftime('%d/%m/%y')}",
        )
        texto_del_mail.setWordWrap(True)
        texto_del_mail.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.MinimumExpanding)
        return texto_del_mail

    def cambiar_descripcion_de(self, mail):
        ventana_de_descripcion = QDialog(self.contenedor_de_mails)
        ventana_de_descripcion.setWindowTitle(f"{mail.subject} description")
        ventana_de_descripcion.setGeometry(100, 100, 300, 400)

        layout = QVBoxLayout()
        lector_de_texto = QTextEdit(ventana_de_descripcion)
        lector_de_texto.setPlainText(self.user_interface.ver_descripcion_de(mail))
        layout.addWidget(lector_de_texto)

        boton_aplicar_cambios = QPushButton("Apply changes", ventana_de_descripcion)
        boton_aplicar_cambios.clicked.connect(
            lambda _, mail=mail, lector=lector_de_texto: self.aplicar_cambios_de_descripcion(
                mail, lector.toPlainText(), ventana_de_descripcion
            )
        )
        layout.addWidget(boton_aplicar_cambios)

        ventana_de_descripcion.setLayout(layout)
        ventana_de_descripcion.show()
        ventana_de_descripcion.raise_()
        ventana_de_descripcion.activateWindow()

    def aplicar_cambios_de_descripcion(self, mail, descripcion, parent):
        self.user_interface.cambiar_descripcion_de(mail, descripcion)
        QMessageBox.information(parent, "Description", "Description changed successfully")



class Mostrador_de_mails_buscados(Mostrador_de_mails):


    def agregar_mail(self, mail):
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.Box)
        frame.setLineWidth(3)
        frame.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        layout_del_frame = QVBoxLayout(frame)
        layout_del_frame.setSizeConstraint(QVBoxLayout.SizeConstraint.SetMinimumSize)
        texto_del_mail = self.crear_texto_del_mail(frame, mail)
        layout_del_frame.addWidget(texto_del_mail)

        layout_de_botones = QHBoxLayout()

        boton_de_visualizacion = QPushButton(text="Ver", parent=frame)
        boton_de_visualizacion.clicked.connect(partial(self.user_interface.ver_mail, mail))
        layout_de_botones.addWidget(boton_de_visualizacion)

        boton_de_agregar = QPushButton(text="+", parent=frame)
        boton_de_agregar.clicked.connect(partial(self.user_interface.agregar_mail, mail))
        layout_de_botones.addWidget(boton_de_agregar)
        layout_de_botones.addStretch()
        layout_del_frame.addLayout(layout_de_botones)

        self.layout.addWidget(frame)

    def agregar_mails(self, mails):
        for mail in mails:
            if mail not in self.mails:
                self.mails.append(mail)

        mails_ordenados = self.ordenar_por_mas_recientes(self.mails)
        self.limpiar_mostrador()
        self.mails = list(mails_ordenados)
        for mail in self.mails:
            self.agregar_mail(mail)

    def mostrar(self, mails):
        mails_ordenados = self.ordenar_por_mas_recientes(mails)
        self.limpiar_mostrador()
        self.mails = list(mails_ordenados)
        for mail in self.mails:
            self.agregar_mail(mail)




class Mostrador_de_mails_del_break(Mostrador_de_mails):


    def mostrar(self, mails):
        mails_ordenados = self.ordenar_por_mas_recientes(mails)
        self.limpiar_mostrador()
        self.mails = list(mails_ordenados)
        for mail in self.mails:
            frame = QFrame()
            frame.setFrameShape(QFrame.Shape.Box)
            frame.setLineWidth(3)
            frame.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

            layout_del_frame = QVBoxLayout(frame)
            layout_del_frame.setSizeConstraint(QVBoxLayout.SizeConstraint.SetMinimumSize)
            texto_del_mail = self.crear_texto_del_mail(frame, mail)
            layout_del_frame.addWidget(texto_del_mail)

            layout_de_botones = QHBoxLayout()

            boton_de_visualizacion = QPushButton(text="Ver", parent=frame)
            boton_de_visualizacion.clicked.connect(partial(self.user_interface.ver_mail, mail))
            layout_de_botones.addWidget(boton_de_visualizacion)

            boton_de_agregar_descripcion = QPushButton(text="Description", parent=frame)
            boton_de_agregar_descripcion.clicked.connect(
                lambda _, mail=mail: self.cambiar_descripcion_de(mail)
            )
            layout_de_botones.addWidget(boton_de_agregar_descripcion)

            boton_de_quitar = QPushButton(text="x", parent=frame)
            boton_de_quitar.clicked.connect(partial(self.user_interface.quitar_mail, mail))
            layout_de_botones.addWidget(boton_de_quitar)
            layout_de_botones.addStretch()
            layout_del_frame.addLayout(layout_de_botones)

            self.layout.addWidget(frame)
