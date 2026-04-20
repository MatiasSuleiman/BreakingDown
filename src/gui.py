from PyQt6.QtCore import QObject, QThread, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

try:
    from src.mostrador_de_condiciones import Mostrador_de_condiciones
    from src.mostrador_de_mails import Mostrador_de_mails_buscados, Mostrador_de_mails_del_break
    from src.ui_theme import aplicar_rol_de_boton, aplicar_tema_compartido
except ModuleNotFoundError:
    from mostrador_de_condiciones import Mostrador_de_condiciones
    from mostrador_de_mails import Mostrador_de_mails_buscados, Mostrador_de_mails_del_break
    from ui_theme import aplicar_rol_de_boton, aplicar_tema_compartido


class Senales_de_busqueda(QObject):
    lote_listo = pyqtSignal(list)
    error = pyqtSignal(str)
    finalizado = pyqtSignal()


class Batcher_de_busqueda:
    def __init__(self, sistema, asunto, tamanio_de_lote=5):
        self.sistema = sistema
        self.asunto = asunto
        self.tamanio_de_lote = tamanio_de_lote
        self.senales = Senales_de_busqueda()
        self.cancelada = False

    def cancelar(self):
        self.cancelada = True

    def ejecutar(self):
        lote = []
        try:
            for mail in self.sistema.buscar_de_a_partes(self.asunto):
                if self.cancelada:
                    break
                lote.append(mail)
                if len(lote) >= self.tamanio_de_lote:
                    self.senales.lote_listo.emit(lote)
                    lote = []
            if lote and not self.cancelada:
                self.senales.lote_listo.emit(lote)
        except Exception as error:
            self.senales.error.emit(str(error))
        finally:
            self.senales.finalizado.emit()


class Hilo_de_busqueda(QThread):
    def __init__(self, batcher):
        super().__init__()
        self.batcher = batcher

    def run(self):
        self.batcher.ejecutar()


class Gui:
    def __init__(self, sistema, al_volver_al_login=None):
        self.sistema = sistema
        self.al_volver_al_login = al_volver_al_login
        self.busqueda_en_curso = False

        aplicar_tema_compartido()

        self.ventana = QMainWindow()
        self.ventana.setObjectName("mainWindow")
        self.ventana.setWindowTitle("BreakingDown")
        self.ventana.resize(1400, 860)
        self.ventana.setMinimumSize(1100, 700)

        self.area_de_contenido = QWidget()
        self.area_de_contenido.setObjectName("mainContent")
        self.ventana.setCentralWidget(self.area_de_contenido)

        layout_principal = QVBoxLayout(self.area_de_contenido)
        layout_principal.setContentsMargins(20, 20, 20, 20)
        layout_principal.setSpacing(18)

        fila_superior = QHBoxLayout()
        fila_superior.setSpacing(18)
        layout_principal.addLayout(fila_superior)

        self.mostrador_de_condiciones = Mostrador_de_condiciones.en(
            self.area_de_contenido, 700, 120, 20, 10, self.sistema
        )
        fila_superior.addWidget(self.mostrador_de_condiciones.caja_filtros, 1)

        panel_de_controles = QFrame(self.area_de_contenido)
        panel_de_controles.setObjectName("controlPanel")
        panel_de_controles.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout_panel_de_controles = QVBoxLayout(panel_de_controles)
        layout_panel_de_controles.setContentsMargins(18, 18, 18, 18)
        layout_panel_de_controles.setSpacing(12)
        fila_superior.addWidget(panel_de_controles, 1)

        fila_de_busqueda = QHBoxLayout()
        fila_de_busqueda.setSpacing(10)
        layout_panel_de_controles.addLayout(fila_de_busqueda)

        fila_de_modos_de_busqueda = QHBoxLayout()
        fila_de_modos_de_busqueda.setSpacing(10)
        layout_panel_de_controles.addLayout(fila_de_modos_de_busqueda)

        fila_de_estado = QVBoxLayout()
        fila_de_estado.setSpacing(4)
        layout_panel_de_controles.addLayout(fila_de_estado)
        layout_panel_de_controles.addStretch()

        self.mostrador_de_mails_del_break = Mostrador_de_mails_del_break.en(
            self.area_de_contenido, 700, 610, 20, 180, self
        )
        self.mostrador_de_mails_encontrados = Mostrador_de_mails_buscados.en(
            self.area_de_contenido, 700, 610, 880, 180, self
        )

        self.boton_de_busqueda = QPushButton("Buscar", panel_de_controles)
        aplicar_rol_de_boton(self.boton_de_busqueda, "primary")
        self.boton_de_busqueda.clicked.connect(self.buscar)
        self.boton_de_busqueda.setMinimumWidth(96)
        fila_de_busqueda.addWidget(self.boton_de_busqueda)

        self.barra_de_busqueda = QLineEdit(panel_de_controles)
        self.barra_de_busqueda.setPlaceholderText("Buscar por asunto")
        self.barra_de_busqueda.returnPressed.connect(self.buscar)
        fila_de_busqueda.addWidget(self.barra_de_busqueda, 1)

        self.grupo_de_modo_de_busqueda = QButtonGroup(panel_de_controles)
        self.grupo_de_modo_de_busqueda.setExclusive(True)

        self.boton_de_recibidos = QPushButton("Recibidos", panel_de_controles)
        aplicar_rol_de_boton(self.boton_de_recibidos, "toggle")
        self.boton_de_recibidos.setCheckable(True)
        self.boton_de_recibidos.setChecked(True)
        self.grupo_de_modo_de_busqueda.addButton(self.boton_de_recibidos)
        self.boton_de_recibidos.clicked.connect(self.seleccionar_recibidos)
        fila_de_modos_de_busqueda.addWidget(self.boton_de_recibidos)

        self.boton_de_enviados = QPushButton("Enviados", panel_de_controles)
        aplicar_rol_de_boton(self.boton_de_enviados, "toggle")
        self.boton_de_enviados.setCheckable(True)
        self.grupo_de_modo_de_busqueda.addButton(self.boton_de_enviados)
        self.boton_de_enviados.clicked.connect(self.seleccionar_enviados)
        fila_de_modos_de_busqueda.addWidget(self.boton_de_enviados)

        self.boton_de_todos = QPushButton("Todos", panel_de_controles)
        aplicar_rol_de_boton(self.boton_de_todos, "toggle")
        self.boton_de_todos.setCheckable(True)
        self.grupo_de_modo_de_busqueda.addButton(self.boton_de_todos)
        self.boton_de_todos.clicked.connect(self.seleccionar_todos)
        fila_de_modos_de_busqueda.addWidget(self.boton_de_todos)
        fila_de_modos_de_busqueda.addStretch()

        self.indicador_de_busqueda = QLabel("", panel_de_controles)
        self.indicador_de_busqueda.setObjectName("statusLabel")
        self.indicador_de_busqueda.hide()
        fila_de_estado.addWidget(self.indicador_de_busqueda)
        
        self.cantidad_de_encontrados = QLabel("", panel_de_controles)
        self.cantidad_de_encontrados.setObjectName("resultCountLabel")
        self.cantidad_de_encontrados.hide()
        fila_de_estado.addWidget(self.cantidad_de_encontrados)

        fila_mostradores = QHBoxLayout()
        fila_mostradores.setSpacing(18)
        layout_principal.addLayout(fila_mostradores, 1)
        fila_mostradores.addWidget(self.mostrador_de_mails_del_break.area, 1)
        fila_mostradores.addWidget(self.mostrador_de_mails_encontrados.area, 1)

        fila_inferior = QHBoxLayout()
        fila_inferior.setSpacing(12)
        layout_principal.addLayout(fila_inferior)

        self.boton_de_volver_al_login = QPushButton("Volver al login", self.area_de_contenido)
        aplicar_rol_de_boton(self.boton_de_volver_al_login, "secondary")
        self.boton_de_volver_al_login.clicked.connect(self.volver_al_login)
        fila_inferior.addWidget(self.boton_de_volver_al_login)
        fila_inferior.addStretch()

        self.boton_de_crear_break = QPushButton("Crear Breakdown", self.area_de_contenido)
        aplicar_rol_de_boton(self.boton_de_crear_break, "primary")
        self.boton_de_crear_break.clicked.connect(self.crear_breakdown)
        fila_inferior.addWidget(self.boton_de_crear_break)

        self.seleccionar_recibidos()
        self.ventana.show()

    def buscar(self):
        self.cantidad_de_encontrados.hide()

        if self.busqueda_en_curso:
            self.cancelar_busqueda()
            return

        self.limpiar_buscados()
        asunto = self.barra_de_busqueda.text().strip()
        self.mostrador_de_condiciones.aplicar_condiciones_a(self.sistema)
        self.sistema.limpiar_encontrados()

        self.busqueda_en_curso = True
        self.boton_de_busqueda.setText("Cancelar")
        self.indicador_de_busqueda.setText("Buscando...")
        self.indicador_de_busqueda.show()

        self.batcher_de_busqueda = Batcher_de_busqueda(self.sistema, asunto, tamanio_de_lote=5)
        self.hilo_de_busqueda = Hilo_de_busqueda(self.batcher_de_busqueda)

        self.batcher_de_busqueda.senales.lote_listo.connect(
            self.al_recibir_lote, Qt.ConnectionType.QueuedConnection
        )
        self.batcher_de_busqueda.senales.error.connect(
            self.al_error_en_busqueda, Qt.ConnectionType.QueuedConnection
        )
        self.batcher_de_busqueda.senales.finalizado.connect(
            self.al_finalizar_busqueda, Qt.ConnectionType.QueuedConnection
        )
        self.hilo_de_busqueda.finished.connect(self.limpiar_estado_de_busqueda)
        self.hilo_de_busqueda.start()

    def al_recibir_lote(self, mails):
        self.sistema.agregar_mails_encontrados(mails)
        self.mostrador_de_mails_encontrados.agregar_mails(mails)
        self.actualizar_cantidad_de_entcontrados()

    def al_error_en_busqueda(self, mensaje):
        QMessageBox.critical(self.ventana, "Error de busqueda", mensaje)

    def al_finalizar_busqueda(self):
        self.busqueda_en_curso = False
        self.restaurar_estado_visual_de_busqueda()

    def restaurar_estado_visual_de_busqueda(self):
        self.boton_de_busqueda.setText("Buscar")
        self.indicador_de_busqueda.setText("")
        self.indicador_de_busqueda.hide()

    def cancelar_busqueda(self):
        if not self.busqueda_en_curso:
            return
        self.batcher_de_busqueda.cancelar()
        self.restaurar_estado_visual_de_busqueda()

    def limpiar_estado_de_busqueda(self):
        if hasattr(self, "hilo_de_busqueda"):
            del self.hilo_de_busqueda
        if hasattr(self, "batcher_de_busqueda"):
            del self.batcher_de_busqueda

    def seleccionar_recibidos(self):
        self.cambiar_carpeta_de_busqueda("INBOX")

    def seleccionar_enviados(self):
        self.cambiar_carpeta_de_busqueda("[Gmail]/Sent Mail")

    def seleccionar_todos(self):
        self.cambiar_carpeta_de_busqueda("[Gmail]/All Mail")


    def cambiar_carpeta_de_busqueda(self, carpeta):
        carpeta_previa = self.sistema.buscador.carpeta_actual

        if self.busqueda_en_curso:
            self.restaurar_selector_de_carpeta(carpeta_previa)
            QMessageBox.warning(
                self.ventana,
                "Busqueda en curso",
                "No se puede cambiar la carpeta mientras se esta buscando.",
            )
            return

        try:
            self.sistema.buscador.cambiar_carpeta(carpeta)
        except Exception as error:
            self.restaurar_selector_de_carpeta(carpeta_previa)
            QMessageBox.critical(
                self.ventana,
                "Error de carpeta",
                f"No se pudo seleccionar la carpeta.\n{error}",
            )

    def restaurar_selector_de_carpeta(self, carpeta):
        botones = (self.boton_de_recibidos, self.boton_de_enviados, self.boton_de_todos)
        for boton in botones:
            boton.blockSignals(True)

        self.boton_de_recibidos.setChecked(carpeta == "INBOX")
        self.boton_de_enviados.setChecked(carpeta in ("[Gmail]/Sent Mail", "[Gmail]/Enviados"))
        self.boton_de_todos.setChecked(carpeta in ("[Gmail]/All Mail", "[Gmail]/Todos"))

        for boton in botones:
            boton.blockSignals(False)

    def ver_mail(self, mail):
        ventana_del_mail = QDialog(self.ventana)
        ventana_del_mail.setObjectName("mailDialog")
        ventana_del_mail.setWindowTitle(mail.subject)
        ventana_del_mail.resize(700, 500)

        layout = QVBoxLayout(ventana_del_mail)
        layout.setContentsMargins(16, 16, 16, 16)

        caja_de_texto = QTextBrowser(ventana_del_mail)
        caja_de_texto.setObjectName("mailViewer")
        caja_de_texto.setPlainText(f"{mail.subject}\n\t{mail.text}")
        layout.addWidget(caja_de_texto)

        ventana_del_mail.show()
        ventana_del_mail.raise_()
        ventana_del_mail.activateWindow()

    def cambiar_descripcion_de(self, mail, descripcion):
        self.sistema.cambiar_descripcion_de(mail, descripcion)

    def ver_descripcion_de(self, mail):
        return self.sistema.ver_descripcion_de(mail)

    def cambiar_minutos_de(self, mail, minutos):
        self.sistema.cambiar_minutos_de(mail, minutos)

    def ver_minutos_de(self, mail):
        return self.sistema.ver_minutos_de(mail)

    def agregar_mail(self, mail):
        self.sistema.agregar_mail_encontrado(mail)
        self.mostrador_de_mails_del_break.mostrar(self.sistema.mails_del_breakdown)
        self.mostrador_de_mails_encontrados.mostrar(self.sistema.ver_todos_los_mails_encontrados())

    def quitar_mail(self, mail):
        self.sistema.quitar_mail_del_breakdown(mail)
        self.mostrador_de_mails_del_break.mostrar(self.sistema.mails_del_breakdown)
        self.mostrador_de_mails_encontrados.mostrar(self.sistema.ver_todos_los_mails_encontrados())

    def limpiar_buscados(self):
        self.mostrador_de_mails_encontrados.limpiar_mostrador()


    def actualizar_cantidad_de_entcontrados(self):
        self.cantidad_de_encontrados.setText(f"{self.sistema.cantidad_de_encontrados()} resultados")
        self.cantidad_de_encontrados.show()

    def crear_breakdown(self):
        path, _ = QFileDialog.getSaveFileName(
            self.ventana, "Guardar Breakdown", "", "Excel files (*.xlsx)"
        )
        if not path:
            return
        if not path.lower().endswith(".xlsx"):
            path = f"{path}.xlsx"
        self.sistema.crear_breakdown(path=path)

    def volver_al_login(self):
        if self.busqueda_en_curso:
            QMessageBox.warning(
                self.ventana,
                "Busqueda en curso",
                "Cancele la busqueda actual antes de volver al login.",
            )
            return

        if self.al_volver_al_login is not None:
            self.al_volver_al_login()
