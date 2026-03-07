from PyQt6.QtCore import QObject, QThread, QTimer, pyqtSignal
from PyQt6.QtWidgets import QMainWindow, QLabel, QLineEdit, QPushButton, QMessageBox

try:
    from src.errores import CredencialesInvalidasError
    from src.google_oauth import cargar_sesion_guardada as cargar_sesion_google_guardada
    from src.google_oauth import iniciar_sesion as iniciar_sesion_google
    from src.system_facade import System_Facade
    from src.buscador_adapter import Buscador_adapter
except ModuleNotFoundError:
    from errores import CredencialesInvalidasError
    from google_oauth import cargar_sesion_guardada as cargar_sesion_google_guardada
    from google_oauth import iniciar_sesion as iniciar_sesion_google
    from system_facade import System_Facade
    from buscador_adapter import Buscador_adapter


class Trabajador_de_google(QObject):
    exito = pyqtSignal(object)
    error = pyqtSignal(object)
    terminado = pyqtSignal()

    def __init__(self, funcion):
        super().__init__()
        self.funcion = funcion

    def ejecutar(self):
        try:
            self.exito.emit(self.funcion())
        except Exception as error:
            self.error.emit(error)
        finally:
            self.terminado.emit()


class Ventana_de_login(QObject):
    senal_de_login_exitoso = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.ventana = QMainWindow()
        self.ventana.setWindowTitle("Login - BreakingDown")
        self.ventana.setGeometry(500, 250, 520, 260)

        etiqueta_de_bienvenida = QLabel("Iniciar sesion de Gmail", self.ventana)
        etiqueta_de_bienvenida.setGeometry(170, 20, 220, 30)

        etiqueta_de_correo = QLabel("Correo:", self.ventana)
        etiqueta_de_correo.setGeometry(70, 70, 70, 30)

        self.barra_de_correo = QLineEdit(self.ventana)
        self.barra_de_correo.setPlaceholderText("usuario@gmail.com")
        self.barra_de_correo.setGeometry(140, 70, 300, 30)

        etiqueta_de_contrasena = QLabel("Contrasena:", self.ventana)
        etiqueta_de_contrasena.setGeometry(50, 110, 90, 30)

        self.barra_de_contrasena = QLineEdit(self.ventana)
        self.barra_de_contrasena.setEchoMode(QLineEdit.EchoMode.Password)
        self.barra_de_contrasena.setGeometry(140, 110, 300, 30)

        self.boton_de_login = QPushButton("Entrar", self.ventana)
        self.boton_de_login.setGeometry(140, 170, 120, 30)
        self.boton_de_login.clicked.connect(self.iniciar_sesion)

        self.boton_de_login_google = QPushButton("Entrar con Google", self.ventana)
        self.boton_de_login_google.setGeometry(270, 170, 170, 30)
        self.boton_de_login_google.clicked.connect(self.iniciar_sesion_con_google)

        self.indicador_de_google = QLabel("", self.ventana)
        self.indicador_de_google.setGeometry(140, 215, 300, 30)
        self.indicador_de_google.hide()

        self.barra_de_correo.returnPressed.connect(self.iniciar_sesion)
        self.barra_de_contrasena.returnPressed.connect(self.iniciar_sesion)
        self.hilo_de_google = None
        self.trabajador_de_google = None

    def cambiar_estado_de_botones(self, habilitado):
        self.boton_de_login.setEnabled(habilitado)
        self.boton_de_login_google.setEnabled(habilitado)

    def mostrar_estado_de_google(self, mensaje=""):
        self.indicador_de_google.setText(mensaje)
        self.indicador_de_google.setVisible(bool(mensaje))

    def ejecutar_tarea_google_en_hilo(self, funcion, al_exito, al_error, mensaje):
        if self.hilo_de_google is not None:
            return

        self.cambiar_estado_de_botones(False)
        self.mostrar_estado_de_google(mensaje)

        hilo = QThread(self)
        trabajador = Trabajador_de_google(funcion)
        trabajador.moveToThread(hilo)

        hilo.started.connect(trabajador.ejecutar)
        trabajador.exito.connect(al_exito)
        trabajador.error.connect(al_error)
        trabajador.terminado.connect(hilo.quit)
        trabajador.terminado.connect(lambda: self.limpiar_tarea_google(hilo, trabajador))
        hilo.finished.connect(hilo.deleteLater)
        hilo.start()

        self.hilo_de_google = hilo
        self.trabajador_de_google = trabajador

    def limpiar_tarea_google(self, hilo, trabajador):
        trabajador.deleteLater()
        if self.hilo_de_google is hilo:
            self.hilo_de_google = None
            self.trabajador_de_google = None
            self.cambiar_estado_de_botones(True)
            self.mostrar_estado_de_google()

    def iniciar_sesion(self):
        correo = self.barra_de_correo.text().strip()
        contrasena = self.barra_de_contrasena.text().strip()

        if not correo or not contrasena:
            QMessageBox.warning(self.ventana, "Datos incompletos", "Complete correo y contrasena.")
            return

        self.cambiar_estado_de_botones(False)
        try:
            sistema = System_Facade.login(correo, contrasena)
        except CredencialesInvalidasError:
            QMessageBox.critical(
                self.ventana,
                "Login fallido",
                "Credenciales Invalidas. Chequee que el mail y la contraseña sean correctos",
            )
            self.cambiar_estado_de_botones(True)
            return
        except Exception as error:
            QMessageBox.critical(self.ventana, "Login fallido", f"No se pudo iniciar sesion.\n{error}")
            self.cambiar_estado_de_botones(True)
            return

        self.senal_de_login_exitoso.emit(sistema)

    def iniciar_sesion_con_google(self):
        if self.hilo_de_google is not None:
            return

        self.iniciar_carga_de_sesion_google_guardada()

    def iniciar_carga_de_sesion_google_guardada(self):
        self.ejecutar_tarea_google_en_hilo(
            cargar_sesion_google_guardada,
            self.al_cargar_sesion_google_guardada,
            self.al_error_al_cargar_sesion_google_guardada,
            "Verificando sesion guardada de Google...",
        )

    def al_cargar_sesion_google_guardada(self, sesion_google):
        QTimer.singleShot(0, lambda: self.resolver_sesion_google_guardada(sesion_google))

    def resolver_sesion_google_guardada(self, sesion_google):
        if sesion_google is None:
            self.iniciar_oauth_google()
            return

        decision = self.preguntar_como_continuar_con_google(sesion_google.user)
        if decision == "continuar":
            self.iniciar_login_imap_google(sesion_google)
            return
        if decision == "otra":
            self.iniciar_oauth_google(forzar_nueva=True, seleccionar_cuenta=True)
            return

    def al_error_al_cargar_sesion_google_guardada(self, error):
        QTimer.singleShot(0, lambda: self.resolver_error_al_cargar_sesion_google_guardada(error))

    def resolver_error_al_cargar_sesion_google_guardada(self, error):
        decision = self.preguntar_como_recuperar_oauth_de_google(
            error,
            contexto="No se pudo reutilizar la sesion guardada de Google.",
        )
        if decision == "reintentar":
            self.iniciar_carga_de_sesion_google_guardada()
            return
        if decision == "otra":
            self.iniciar_oauth_google(forzar_nueva=True, seleccionar_cuenta=True)
            return

    def iniciar_oauth_google(self, forzar_nueva=False, seleccionar_cuenta=False):
        self.ejecutar_tarea_google_en_hilo(
            lambda: iniciar_sesion_google(
                forzar_nueva=forzar_nueva,
                seleccionar_cuenta=seleccionar_cuenta,
            ),
            self.al_iniciar_oauth_google_exitoso,
            lambda error: self.al_error_al_iniciar_oauth_google(
                error,
                forzar_nueva=forzar_nueva,
                seleccionar_cuenta=seleccionar_cuenta,
            ),
            "Esperando respuesta de Google...",
        )

    def al_iniciar_oauth_google_exitoso(self, sesion_google):
        QTimer.singleShot(0, lambda: self.iniciar_login_imap_google(sesion_google))

    def al_error_al_iniciar_oauth_google(self, error, forzar_nueva, seleccionar_cuenta):
        QTimer.singleShot(
            0,
            lambda: self.resolver_error_al_iniciar_oauth_google(
                error,
                forzar_nueva=forzar_nueva,
                seleccionar_cuenta=seleccionar_cuenta,
            ),
        )

    def resolver_error_al_iniciar_oauth_google(self, error, forzar_nueva, seleccionar_cuenta):
        decision = self.preguntar_como_recuperar_oauth_de_google(error)
        if decision == "reintentar":
            self.iniciar_oauth_google(
                forzar_nueva=forzar_nueva,
                seleccionar_cuenta=seleccionar_cuenta,
            )
            return
        if decision == "otra":
            self.iniciar_oauth_google(forzar_nueva=True, seleccionar_cuenta=True)
            return

    def iniciar_login_imap_google(self, sesion_google):
        self.ejecutar_tarea_google_en_hilo(
            lambda: self.obtener_sistema_desde_sesion_google(sesion_google),
            self.al_iniciar_login_imap_google_exitoso,
            lambda error: self.al_error_al_iniciar_login_imap_google(error, sesion_google),
            "Conectando Gmail...",
        )

    def obtener_sistema_desde_sesion_google(self, sesion_google):
        buscador = Buscador_adapter.login_con_oauth2(sesion_google)
        sistema = System_Facade.build(sesion_google.user, buscador)
        return sesion_google, sistema

    def al_iniciar_login_imap_google_exitoso(self, resultado):
        QTimer.singleShot(0, lambda: self.finalizar_login_google(resultado))

    def finalizar_login_google(self, resultado):
        sesion_google, sistema = resultado
        self.barra_de_correo.setText(sesion_google.user)
        self.senal_de_login_exitoso.emit(sistema)

    def al_error_al_iniciar_login_imap_google(self, error, sesion_google):
        QTimer.singleShot(0, lambda: self.resolver_error_al_iniciar_login_imap_google(error, sesion_google))

    def resolver_error_al_iniciar_login_imap_google(self, error, sesion_google):
        decision = self.preguntar_como_recuperar_oauth_de_google(
            error,
            contexto="No se pudo conectar Gmail con la cuenta de Google.",
        )
        if decision == "reintentar":
            self.iniciar_login_imap_google(sesion_google)
            return
        if decision == "otra":
            self.iniciar_oauth_google(forzar_nueva=True, seleccionar_cuenta=True)
            return

    def obtener_sistema_con_google(self):
        sesion_google = self.obtener_sesion_google()
        if sesion_google is None:
            return None

        while True:
            try:
                buscador = Buscador_adapter.login_con_oauth2(sesion_google)
                sistema = System_Facade.build(sesion_google.user, buscador)
                return sesion_google, sistema
            except Exception as error:
                decision = self.preguntar_como_recuperar_oauth_de_google(
                    error,
                    contexto="No se pudo conectar Gmail con la cuenta de Google.",
                )
                if decision == "reintentar":
                    continue
                if decision == "otra":
                    sesion_google = self.ejecutar_oauth_de_google(
                        forzar_nueva=True,
                        seleccionar_cuenta=True,
                    )
                    if sesion_google is None:
                        return None
                    continue
                return None

    def obtener_sesion_google(self):
        try:
            sesion_guardada = cargar_sesion_google_guardada()
        except Exception as error:
            return self.recuperar_oauth_de_google(
                "No se pudo reutilizar la sesion guardada de Google.",
                error,
            )

        if sesion_guardada is None:
            return self.ejecutar_oauth_de_google()

        decision = self.preguntar_como_continuar_con_google(sesion_guardada.user)
        if decision == "continuar":
            return sesion_guardada
        if decision == "otra":
            return self.ejecutar_oauth_de_google(forzar_nueva=True, seleccionar_cuenta=True)
        return None

    def ejecutar_oauth_de_google(self, forzar_nueva=False, seleccionar_cuenta=False):
        while True:
            try:
                return iniciar_sesion_google(
                    forzar_nueva=forzar_nueva,
                    seleccionar_cuenta=seleccionar_cuenta,
                )
            except Exception as error:
                decision = self.preguntar_como_recuperar_oauth_de_google(error)
                if decision == "reintentar":
                    continue
                if decision == "otra":
                    forzar_nueva = True
                    seleccionar_cuenta = True
                    continue
                return None

    def recuperar_oauth_de_google(self, contexto, error):
        decision = self.preguntar_como_recuperar_oauth_de_google(error, contexto=contexto)
        if decision == "reintentar":
            return self.obtener_sesion_google()
        if decision == "otra":
            return self.ejecutar_oauth_de_google(forzar_nueva=True, seleccionar_cuenta=True)
        return None

    def preguntar_como_continuar_con_google(self, user):
        dialogo = QMessageBox(self.ventana)
        dialogo.setWindowTitle("Sesion de Google guardada")
        dialogo.setIcon(QMessageBox.Icon.Question)
        dialogo.setText(f"Se encontro una sesion guardada para {user}.")
        dialogo.setInformativeText("Puede continuar con esa cuenta o iniciar sesion con otra.")

        boton_continuar = dialogo.addButton("Continuar", QMessageBox.ButtonRole.AcceptRole)
        boton_otra = dialogo.addButton("Usar otra cuenta", QMessageBox.ButtonRole.ActionRole)
        dialogo.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
        dialogo.exec()

        if dialogo.clickedButton() is boton_continuar:
            return "continuar"
        if dialogo.clickedButton() is boton_otra:
            return "otra"
        return "cancelar"

    def preguntar_como_recuperar_oauth_de_google(self, error, contexto=None):
        dialogo = QMessageBox(self.ventana)
        dialogo.setWindowTitle("Error de Google")
        dialogo.setIcon(QMessageBox.Icon.Warning)
        dialogo.setText(contexto or "No se pudo completar el inicio de sesion con Google.")
        dialogo.setInformativeText(
            "Puede reintentar este paso o iniciar sesion con otra cuenta.\n\n"
            f"Detalle: {error}"
        )

        boton_reintentar = dialogo.addButton("Reintentar", QMessageBox.ButtonRole.AcceptRole)
        boton_otra = dialogo.addButton("Usar otra cuenta", QMessageBox.ButtonRole.ActionRole)
        dialogo.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
        dialogo.exec()

        if dialogo.clickedButton() is boton_reintentar:
            return "reintentar"
        if dialogo.clickedButton() is boton_otra:
            return "otra"
        return "cancelar"
