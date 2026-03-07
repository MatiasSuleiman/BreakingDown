from PyQt6.QtCore import QObject, QThread, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QFileDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
)

try:
    from src.mostrador_de_condiciones import Mostrador_de_condiciones
    from src.mostrador_de_mails import Mostrador_de_mails_buscados, Mostrador_de_mails_del_break
except ModuleNotFoundError:
    from mostrador_de_condiciones import Mostrador_de_condiciones
    from mostrador_de_mails import Mostrador_de_mails_buscados, Mostrador_de_mails_del_break


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

        self.ventana = QMainWindow()
        self.ventana.setWindowTitle("BreakingDown")
        self.ventana.setGeometry(100, 100, 1600, 900)

        texto_de_bienvenida = QLabel(
            "Bienvenido a BreakingDown,\n elija los mails para comenzar", self.ventana
        )
        texto_de_bienvenida.setGeometry(720, 10, 280, 30)

        self.mostrador_de_condiciones = Mostrador_de_condiciones.en(
            self.ventana, 700, 120, 20, 10, self.sistema
        )
        self.mostrador_de_mails_del_break = Mostrador_de_mails_del_break.en(
            self.ventana, 700, 610, 20, 180, self
        )
        self.mostrador_de_mails_encontrados = Mostrador_de_mails_buscados.en(
            self.ventana, 700, 610, 880, 180, self
        )

        self.boton_de_busqueda = QPushButton("Buscar", self.ventana)
        self.boton_de_busqueda.clicked.connect(self.buscar)
        self.boton_de_busqueda.setGeometry(880, 50, 50, 30)

        self.barra_de_busqueda = QLineEdit(self.ventana)
        self.barra_de_busqueda.setPlaceholderText("Buscar por asunto")
        self.barra_de_busqueda.returnPressed.connect(self.buscar)
        self.barra_de_busqueda.setGeometry(970, 50, 500, 30)

        self.grupo_de_modo_de_busqueda = QButtonGroup(self.ventana)
        self.grupo_de_modo_de_busqueda.setExclusive(True)

        self.boton_de_recibidos = QPushButton("Recibidos", self.ventana)
        self.boton_de_recibidos.setCheckable(True)
        self.boton_de_recibidos.setChecked(True)
        self.boton_de_recibidos.setGeometry(970, 90, 120, 30)
        self.grupo_de_modo_de_busqueda.addButton(self.boton_de_recibidos)
        self.boton_de_recibidos.clicked.connect(self.seleccionar_recibidos)

        self.boton_de_enviados = QPushButton("Enviados", self.ventana)
        self.boton_de_enviados.setCheckable(True)
        self.boton_de_enviados.setGeometry(1110, 90, 120, 30)
        self.grupo_de_modo_de_busqueda.addButton(self.boton_de_enviados)
        self.boton_de_enviados.clicked.connect(self.seleccionar_enviados)

        self.indicador_de_busqueda = QLabel("", self.ventana)
        self.indicador_de_busqueda.setGeometry(970, 125, 260, 20)
        self.indicador_de_busqueda.hide()

        self.boton_de_crear_break = QPushButton("Crear Breakdown", self.ventana)
        self.boton_de_crear_break.clicked.connect(self.crear_breakdown)
        self.boton_de_crear_break.setGeometry(520, 830, 200, 30)

        self.boton_de_volver_al_login = QPushButton("Volver al login", self.ventana)
        self.boton_de_volver_al_login.clicked.connect(self.volver_al_login)
        self.boton_de_volver_al_login.setGeometry(20, 830, 150, 30)

        self.seleccionar_recibidos()
        self.ventana.show()

    def buscar(self):
        if self.busqueda_en_curso:
            self.cancelar_busqueda()
            return

        self.limpiar_buscados()
        asunto = self.barra_de_busqueda.text().strip()
        self.mostrador_de_condiciones.aplicar_condiciones_a(self.sistema)
        self.sistema.limpiar_encontrados()

        self.busqueda_en_curso = True
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

    def al_error_en_busqueda(self, mensaje):
        QMessageBox.critical(self.ventana, "Error de busqueda", mensaje)

    def al_finalizar_busqueda(self):
        self.busqueda_en_curso = False
        self.indicador_de_busqueda.hide()

    def cancelar_busqueda(self):
        if not self.busqueda_en_curso:
            return
        self.batcher_de_busqueda.cancelar()

    def limpiar_estado_de_busqueda(self):
        if hasattr(self, "hilo_de_busqueda"):
            del self.hilo_de_busqueda
        if hasattr(self, "batcher_de_busqueda"):
            del self.batcher_de_busqueda

    def seleccionar_recibidos(self):
        self.cambiar_carpeta_de_busqueda("INBOX")

    def seleccionar_enviados(self):
        self.cambiar_carpeta_de_busqueda("[Gmail]/Sent Mail")

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
        botones = (self.boton_de_recibidos, self.boton_de_enviados)
        for boton in botones:
            boton.blockSignals(True)

        self.boton_de_recibidos.setChecked(carpeta == "INBOX")
        self.boton_de_enviados.setChecked(carpeta != "INBOX")

        for boton in botones:
            boton.blockSignals(False)

    def ver_mail(self, mail):
        ventana_del_mail = QDialog(self.ventana)
        ventana_del_mail.setWindowTitle(mail.subject)
        ventana_del_mail.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout()

        caja_de_texto = QTextBrowser(ventana_del_mail)
        caja_de_texto.setPlainText(f"{mail.subject}\n\t{mail.text}")
        layout.addWidget(caja_de_texto)

        ventana_del_mail.setLayout(layout)
        ventana_del_mail.show()
        ventana_del_mail.raise_()
        ventana_del_mail.activateWindow()

    def cambiar_descripcion_de(self, mail, descripcion):
        self.sistema.cambiar_descripcion_de(mail, descripcion)

    def ver_descripcion_de(self, mail):
        return self.sistema.ver_descripcion_de(mail)

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
