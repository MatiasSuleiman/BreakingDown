from PyQt6.QtCore import QObject, pyqtSignal
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

        self.barra_de_correo.returnPressed.connect(self.iniciar_sesion)
        self.barra_de_contrasena.returnPressed.connect(self.iniciar_sesion)

    def cambiar_estado_de_botones(self, habilitado):
        self.boton_de_login.setEnabled(habilitado)
        self.boton_de_login_google.setEnabled(habilitado)

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
        self.cambiar_estado_de_botones(False)

        try:
            sesion_google = self.obtener_sesion_google()
            if sesion_google is None:
                self.cambiar_estado_de_botones(True)
                return
            buscador = Buscador_adapter.login_con_oauth2(sesion_google)
            sistema = System_Facade.build(sesion_google.user, buscador)
        except Exception as error:
            QMessageBox.critical(
                self.ventana,
                "Login con Google fallido",
                f"No se pudo iniciar sesion con Google.\n{error}",
            )
            self.cambiar_estado_de_botones(True)
            return

        self.barra_de_correo.setText(sesion_google.user)
        self.senal_de_login_exitoso.emit(sistema)

    def obtener_sesion_google(self):
        sesion_guardada = cargar_sesion_google_guardada()

        if sesion_guardada is None:
            return iniciar_sesion_google()

        decision = self.preguntar_como_continuar_con_google(sesion_guardada.user)
        if decision == "continuar":
            return sesion_guardada
        if decision == "otra":
            return iniciar_sesion_google(forzar_nueva=True)
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
