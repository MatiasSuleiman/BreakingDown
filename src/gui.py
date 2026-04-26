import os
import time

from PyQt6.QtCore import QObject, QThread, QTimer, Qt, pyqtSignal
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


def log_debug_busqueda(mensaje):
    if os.environ.get("BREAKINGDOWN_DEBUG_SEARCH"):
        print(f"[breakingdown search] {mensaje}", flush=True)


class Senales_de_busqueda(QObject):
    lote_listo = pyqtSignal(list)
    error = pyqtSignal(str)
    finalizado = pyqtSignal()


class Batcher_de_busqueda:
    def __init__(self, sistema, texto, tamanio_de_lote=5):
        self.sistema = sistema
        self.texto = texto
        self.tamanio_de_lote = tamanio_de_lote
        self.senales = Senales_de_busqueda()
        self.cancelada = False

    def cancelar(self):
        self.cancelada = True

    def buscar_mails(self):
        raise NotImplementedError("subclass should implement buscar_mails")

    def ejecutar(self):
        lote = []
        cantidad = 0
        inicio = time.perf_counter()
        log_debug_busqueda(f"{self.__class__.__name__}: inicio texto={self.texto!r}")
        try:
            for mail in self.buscar_mails():
                if self.cancelada:
                    break
                lote.append(mail)
                cantidad += 1
                if len(lote) >= self.tamanio_de_lote:
                    log_debug_busqueda(
                        f"{self.__class__.__name__}: emite lote={len(lote)} total={cantidad}"
                    )
                    self.senales.lote_listo.emit(lote)
                    lote = []
            if lote and not self.cancelada:
                log_debug_busqueda(
                    f"{self.__class__.__name__}: emite lote={len(lote)} total={cantidad}"
                )
                self.senales.lote_listo.emit(lote)
        except Exception as error:
            log_debug_busqueda(f"{self.__class__.__name__}: error={error}")
            self.senales.error.emit(str(error))
        finally:
            duracion = time.perf_counter() - inicio
            log_debug_busqueda(
                f"{self.__class__.__name__}: finalizado total={cantidad} "
                f"cancelada={self.cancelada} duracion={duracion:.3f}s"
            )
            self.senales.finalizado.emit()


class Batcher_de_busqueda_por_asunto(Batcher_de_busqueda):
    def buscar_mails(self):
        return self.sistema.buscar_de_a_partes_por_asunto(self.texto)


class Batcher_de_busqueda_por_cuerpo(Batcher_de_busqueda):
    def buscar_mails(self):
        return self.sistema.buscar_de_a_partes_por_cuerpo(self.texto)


class Hilo_de_busqueda(QThread):
    def __init__(self, batcher):
        super().__init__()
        self.batcher = batcher

    def run(self):
        self.batcher.ejecutar()


class Gui:
    TEXTO_BOTON_FILTROS_COLAPSADO = "Filtros ▾"
    TEXTO_BOTON_FILTROS_EXPANDIDO = "Filtros ▴"

    def __init__(self, sistema, al_volver_al_login=None):
        self.sistema = sistema
        self.al_volver_al_login = al_volver_al_login
        self.busqueda_en_curso = False
        self.batchers_de_busqueda = {}
        self.hilos_de_busqueda = {}
        self.busquedas_activas = set()
        self.busquedas_finalizadas = set()
        self.mails_encontrados_por_asunto = {}
        self.mails_encontrados_por_cuerpo = {}
        self.lotes_pendientes_por_asunto = []
        self.lotes_pendientes_por_cuerpo = []
        self.procesamiento_de_lotes_programado = False
        self.procesando_lotes = False

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

        self.slot_de_filtros = QWidget(self.area_de_contenido)
        self.slot_de_filtros.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout_slot_de_filtros = QVBoxLayout(self.slot_de_filtros)
        layout_slot_de_filtros.setContentsMargins(0, 0, 0, 0)
        layout_slot_de_filtros.setSpacing(8)
        fila_superior.addWidget(self.slot_de_filtros, 1, Qt.AlignmentFlag.AlignTop)

        fila_encabezado_de_filtros = QHBoxLayout()
        fila_encabezado_de_filtros.setContentsMargins(0, 0, 0, 0)
        fila_encabezado_de_filtros.setSpacing(0)
        layout_slot_de_filtros.addLayout(fila_encabezado_de_filtros)

        self.boton_de_filtros = QPushButton(self.slot_de_filtros)
        aplicar_rol_de_boton(self.boton_de_filtros, "filterToggle")
        self.boton_de_filtros.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.boton_de_filtros.clicked.connect(
            lambda: self.alternar_filtros(self.boton_de_filtros.text())
        )
        self.boton_de_filtros.setText(self.TEXTO_BOTON_FILTROS_COLAPSADO)
        fila_encabezado_de_filtros.addWidget(self.boton_de_filtros, 0, Qt.AlignmentFlag.AlignLeft)
        fila_encabezado_de_filtros.addStretch()

        self.mostrador_de_condiciones = Mostrador_de_condiciones.en(
            self.area_de_contenido, 700, 120, 20, 10, self.sistema
        )
        self.cuerpo_de_filtros = self.mostrador_de_condiciones.caja_filtros
        self.cuerpo_de_filtros.hide()
        layout_slot_de_filtros.addWidget(self.cuerpo_de_filtros)

        self.panel_de_controles = QFrame(self.area_de_contenido)
        self.panel_de_controles.setObjectName("controlPanel")
        self.panel_de_controles.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout_panel_de_controles = QVBoxLayout(self.panel_de_controles)
        layout_panel_de_controles.setContentsMargins(18, 18, 18, 18)
        layout_panel_de_controles.setSpacing(12)
        fila_superior.addWidget(self.panel_de_controles, 1)

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

        self.boton_de_busqueda = QPushButton("Buscar", self.panel_de_controles)
        aplicar_rol_de_boton(self.boton_de_busqueda, "primary")
        self.boton_de_busqueda.clicked.connect(self.buscar)
        self.boton_de_busqueda.setMinimumWidth(96)
        fila_de_busqueda.addWidget(self.boton_de_busqueda)

        self.barra_de_busqueda = QLineEdit(self.panel_de_controles)
        self.barra_de_busqueda.setPlaceholderText("Buscar por asunto o cuerpo")
        self.barra_de_busqueda.returnPressed.connect(self.buscar)
        fila_de_busqueda.addWidget(self.barra_de_busqueda, 1)

        self.grupo_de_modo_de_busqueda = QButtonGroup(self.panel_de_controles)
        self.grupo_de_modo_de_busqueda.setExclusive(True)

        self.boton_de_recibidos = QPushButton("Recibidos", self.panel_de_controles)
        aplicar_rol_de_boton(self.boton_de_recibidos, "toggle")
        self.boton_de_recibidos.setCheckable(True)
        self.boton_de_recibidos.setChecked(True)
        self.grupo_de_modo_de_busqueda.addButton(self.boton_de_recibidos)
        self.boton_de_recibidos.clicked.connect(self.seleccionar_recibidos)
        fila_de_modos_de_busqueda.addWidget(self.boton_de_recibidos)

        self.boton_de_enviados = QPushButton("Enviados", self.panel_de_controles)
        aplicar_rol_de_boton(self.boton_de_enviados, "toggle")
        self.boton_de_enviados.setCheckable(True)
        self.grupo_de_modo_de_busqueda.addButton(self.boton_de_enviados)
        self.boton_de_enviados.clicked.connect(self.seleccionar_enviados)
        fila_de_modos_de_busqueda.addWidget(self.boton_de_enviados)

        self.boton_de_todos = QPushButton("Todos", self.panel_de_controles)
        aplicar_rol_de_boton(self.boton_de_todos, "toggle")
        self.boton_de_todos.setCheckable(True)
        self.grupo_de_modo_de_busqueda.addButton(self.boton_de_todos)
        self.boton_de_todos.clicked.connect(self.seleccionar_todos)
        fila_de_modos_de_busqueda.addWidget(self.boton_de_todos)
        fila_de_modos_de_busqueda.addStretch()

        self.indicador_de_busqueda = QLabel("", self.panel_de_controles)
        self.indicador_de_busqueda.setObjectName("statusLabel")
        self.indicador_de_busqueda.hide()
        fila_de_estado.addWidget(self.indicador_de_busqueda)

        self.cantidad_de_encontrados = QLabel("", self.panel_de_controles)
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

    def clave_de_mail(self, mail):
        return getattr(mail, "uid", id(mail))

    def mail_fue_encontrado_por_asunto(self, mail):
        return self.clave_de_mail(mail) in self.mails_encontrados_por_asunto

    def reiniciar_estado_de_busqueda(self):
        self.batchers_de_busqueda = {}
        self.hilos_de_busqueda = {}
        self.busquedas_activas = set()
        self.busquedas_finalizadas = set()
        self.lotes_pendientes_por_asunto = []
        self.lotes_pendientes_por_cuerpo = []
        self.procesamiento_de_lotes_programado = False
        self.procesando_lotes = False

    def reiniciar_origenes_de_resultados(self):
        self.mails_encontrados_por_asunto = {}
        self.mails_encontrados_por_cuerpo = {}

    def alternar_filtros(self, texto_actual):
        filtros_estan_ocultos = texto_actual == self.TEXTO_BOTON_FILTROS_COLAPSADO
        self.cuerpo_de_filtros.setVisible(filtros_estan_ocultos)
        self.boton_de_filtros.setText(
            self.TEXTO_BOTON_FILTROS_EXPANDIDO
            if filtros_estan_ocultos
            else self.TEXTO_BOTON_FILTROS_COLAPSADO
        )

    def buscar(self):
        self.cantidad_de_encontrados.hide()

        if self.busqueda_en_curso:
            self.cancelar_busqueda()
            return

        self.limpiar_buscados()
        texto = self.barra_de_busqueda.text().strip()
        self.mostrador_de_condiciones.aplicar_condiciones_a(self.sistema)
        self.sistema.limpiar_encontrados()
        self.reiniciar_origenes_de_resultados()

        if not texto:
            self.restaurar_estado_visual_de_busqueda()
            return

        self.busqueda_en_curso = True
        self.boton_de_busqueda.setText("Cancelar")
        self.indicador_de_busqueda.setText("Buscando...")
        self.indicador_de_busqueda.show()
        self.reiniciar_estado_de_busqueda()

        self.iniciar_busqueda(
            "asunto",
            Batcher_de_busqueda_por_asunto(self.sistema, texto, tamanio_de_lote=5),
            self.al_recibir_lote_de_asunto,
        )
        self.iniciar_busqueda(
            "cuerpo",
            Batcher_de_busqueda_por_cuerpo(self.sistema, texto, tamanio_de_lote=5),
            self.al_recibir_lote_de_cuerpo,
        )

    def iniciar_busqueda(self, tipo, batcher, receptor_de_lotes):
        hilo = Hilo_de_busqueda(batcher)
        self.batchers_de_busqueda[tipo] = batcher
        self.hilos_de_busqueda[tipo] = hilo
        self.busquedas_activas.add(tipo)

        batcher.senales.lote_listo.connect(receptor_de_lotes, Qt.ConnectionType.QueuedConnection)
        batcher.senales.error.connect(
            self.al_error_en_busqueda, Qt.ConnectionType.QueuedConnection
        )
        batcher.senales.finalizado.connect(
            lambda tipo=tipo: self.al_finalizar_busqueda_de(tipo),
            Qt.ConnectionType.QueuedConnection,
        )
        hilo.finished.connect(lambda tipo=tipo: self.limpiar_estado_de_busqueda(tipo))
        hilo.start()

    def al_recibir_lote_de_asunto(self, mails):
        self.encolar_lote_de_busqueda_de_asunto(mails)

    def al_recibir_lote_de_cuerpo(self, mails):
        self.encolar_lote_de_busqueda_de_cuerpo(mails)

    def encolar_lote_de_busqueda_de_asunto(self, mails):
        if not mails:
            return
        self.lotes_pendientes_por_asunto.append(list(mails))

        if self.procesamiento_de_lotes_programado:
            return

        self.procesamiento_de_lotes_programado = True
        QTimer.singleShot(0, self.procesar_lotes_pendientes)

    def encolar_lote_de_busqueda_de_cuerpo(self, mails):
        if not mails:
            return
        self.lotes_pendientes_por_cuerpo.append(list(mails))
        if self.procesamiento_de_lotes_programado:
            return

        self.procesamiento_de_lotes_programado = True
        QTimer.singleShot(0, self.procesar_lotes_pendientes)


    def procesar_lotes_pendientes(self):
        if self.procesando_lotes:
            QTimer.singleShot(0, self.procesar_lotes_pendientes)
            return

        lotes_por_asunto = self.lotes_pendientes_por_asunto
        lotes_por_cuerpo = self.lotes_pendientes_por_cuerpo
        self.lotes_pendientes_por_asunto = []
        self.lotes_pendientes_por_cuerpo = []
        self.procesamiento_de_lotes_programado = False

        mails_por_asunto = [mail for lote in lotes_por_asunto for mail in lote]
        mails_por_cuerpo = [mail for lote in lotes_por_cuerpo for mail in lote]
        if not mails_por_asunto and not mails_por_cuerpo:
            return

        self.procesando_lotes = True

        try:
            mails_nuevos_por_cuerpo = self.procesar_lote_de_cuerpo(mails_por_cuerpo)
            (
                mails_nuevos_por_asunto,
                mails_actualizados_a_asunto,
            ) = self.procesar_lote_de_asunto(mails_por_asunto)
            self.mostrador_de_mails_encontrados.registrar_lotes_de_busqueda(
                mails_por_cuerpo=mails_nuevos_por_cuerpo,
                mails_por_asunto=mails_nuevos_por_asunto,
                mails_actualizados_a_asunto=mails_actualizados_a_asunto,
            )
            self.actualizar_cantidad_de_entcontrados()
        finally:
           self.procesando_lotes = False

        if self.lotes_pendientes_por_asunto or self.lotes_pendientes_por_cuerpo:
            self.procesamiento_de_lotes_programado = True
            QTimer.singleShot(0, self.procesar_lotes_pendientes)
            return

        self.finalizar_busqueda_si_corresponde()

    def procesar_lote_de_asunto(self, mails):
        mails_nuevos = []
        mails_actualizados_a_asunto = []
        for mail in mails:
            clave = self.clave_de_mail(mail)
            if clave in self.mails_encontrados_por_asunto:
                continue

            self.mails_encontrados_por_asunto[clave] = mail
            if clave in self.mails_encontrados_por_cuerpo:
                mails_actualizados_a_asunto.append(mail)
                continue

            self.sistema.agregar_mails_encontrados([mail])
            mails_nuevos.append(mail)

        return mails_nuevos, mails_actualizados_a_asunto

    def procesar_lote_de_cuerpo(self, mails):
        mails_nuevos = []
        for mail in mails:
            clave = self.clave_de_mail(mail)
            if clave in self.mails_encontrados_por_asunto or clave in self.mails_encontrados_por_cuerpo:
                continue

            self.mails_encontrados_por_cuerpo[clave] = mail
            self.sistema.agregar_mails_encontrados([mail])
            mails_nuevos.append(mail)

        return mails_nuevos

    def al_error_en_busqueda(self, mensaje):
        QMessageBox.critical(self.ventana, "Error de busqueda", mensaje)

    def al_finalizar_busqueda_de(self, tipo):
        self.busquedas_finalizadas.add(tipo)
        self.finalizar_busqueda_si_corresponde()

    def hay_lotes_de_busqueda_pendientes(self):
        return (
            self.procesamiento_de_lotes_programado
            or self.procesando_lotes
            or bool(self.lotes_pendientes_por_asunto)
            or bool(self.lotes_pendientes_por_cuerpo)
        )

    def finalizar_busqueda_si_corresponde(self):
        if (
            self.busquedas_activas
            and self.busquedas_finalizadas == self.busquedas_activas
            and not self.hay_lotes_de_busqueda_pendientes()
        ):
            self.busqueda_en_curso = False
            self.restaurar_estado_visual_de_busqueda()

    def restaurar_estado_visual_de_busqueda(self):
        self.boton_de_busqueda.setText("Buscar")
        self.indicador_de_busqueda.setText("")
        self.indicador_de_busqueda.hide()

    def cancelar_busqueda(self):
        if not self.busqueda_en_curso:
            return
        for batcher in self.batchers_de_busqueda.values():
            batcher.cancelar()
        self.indicador_de_busqueda.setText("Cancelando...")
        self.indicador_de_busqueda.show()

    def limpiar_estado_de_busqueda(self, tipo):
        self.hilos_de_busqueda.pop(tipo, None)
        self.batchers_de_busqueda.pop(tipo, None)

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
            self.sistema.cambiar_carpeta_de_busqueda(carpeta)
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
        self.mostrador_de_mails_del_break.mostrar(
            self.sistema.mails_del_breakdown,
            self.mail_fue_encontrado_por_asunto,
        )
        self.mostrador_de_mails_encontrados.mostrar(
            self.sistema.ver_todos_los_mails_encontrados(),
            self.mail_fue_encontrado_por_asunto,
        )

    def quitar_mail(self, mail):
        self.sistema.quitar_mail_del_breakdown(mail)
        self.mostrador_de_mails_del_break.mostrar(
            self.sistema.mails_del_breakdown,
            self.mail_fue_encontrado_por_asunto,
        )
        self.mostrador_de_mails_encontrados.mostrar(
            self.sistema.ver_todos_los_mails_encontrados(),
            self.mail_fue_encontrado_por_asunto,
        )

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
