try:
    from src.buscador_adapter import Buscador_adapter
    from src.Breakdown import Breakdown
    from src.condicion import (
        Condicion_de_cuerpo,
        Condicion_de_emisor,
        Condicion_de_receptor,
        Condicion_de_enviado_antes_de,
        Condicion_de_enviado_despues_de,
    )
except ModuleNotFoundError:
    from buscador_adapter import Buscador_adapter
    from Breakdown import Breakdown
    from condicion import (
        Condicion_de_cuerpo,
        Condicion_de_emisor,
        Condicion_de_receptor,
        Condicion_de_enviado_antes_de,
        Condicion_de_enviado_despues_de,
    )

class System_Facade:

    @classmethod
    def login(cls, user, password):
        buscador = Buscador_adapter.login(user, password)
        return cls.build(user, buscador)

    @classmethod
    def build(cls, user, buscador):
        return cls(user, buscador)

    builde = build

    def __init__(self, user, buscador):
        self.abogado_a_cargo = user
        self.mails_encontrados = []
        self.mails_del_breakdown = []
        self.descripcion_por_mail = {}
        self.buscador = buscador
        self.condiciones = []

    def buscar_de_a_partes(self, asunto):
        return self.buscador.encontrar_de_a_partes(asunto, self.condiciones)

    def agregar_mail_encontrado(self, mail):
        self.mails_del_breakdown.append(mail)
        self.mails_encontrados.remove(mail)
        self.descripcion_por_mail[mail] = ""

    def agregar_mails_encontrados(self, mails):
        self.mails_encontrados.extend(mails)
    

    def limpiar_encontrados(self):
        self.mails_encontrados = []


    def agregar_todos_los_mails_encontrados(self):
        for mail in list(self.mails_encontrados):
            self.agregar_mail_encontrado(mail)
    

    def ver_mail_encontrado(self, numero):
        return self.mails_encontrados[numero]
     

    def ver_todos_los_mails_encontrados(self):
        return self.mails_encontrados
     

    def quitar_mail_del_breakdown(self, mail):
        self.mails_del_breakdown.remove(mail)
        self.mails_encontrados.append(mail)
        self.descripcion_por_mail.pop(mail, None)


    def ver_mail_en_breakdown(self, numero):
        return self.mails_del_breakdown[numero]

    def agregar_condicion_de_cuerpo(self, cuerpo):
        condicion = Condicion_de_cuerpo.con_cuerpo(cuerpo)
        self.condiciones += [condicion]


    def agregar_condicion_de_emisor(self, emisor):
        condicion = Condicion_de_emisor.con_emisor(emisor)
        self.condiciones += [condicion]

    def agregar_condicion_de_receptor(self, receptor):
        condicion = Condicion_de_receptor.con_receptor(receptor)
        self.condiciones += [condicion]

    def agregar_condicion_de_enviado_antes_de(self, fecha):
        condicion = Condicion_de_enviado_antes_de.enviado_antes_de(fecha)
        self.condiciones += [condicion]

    def agregar_condicion_de_enviado_despues_de(self, fecha):
        condicion = Condicion_de_enviado_despues_de.enviado_despues_de(fecha)
        self.condiciones += [condicion]


    def ver_condicion(self, numero):
        return self.condiciones[numero]


    def limpiar_condiciones(self):
        self.condiciones = []

    def cambiar_descripcion_de(self, mail, descripcion):
        self.descripcion_por_mail[mail] = descripcion

    def ver_descripcion_de(self, mail):
        return self.descripcion_por_mail.get(mail, "")

    def crear_breakdown(self, path):
        return Breakdown.con_mails_manejado_por(
            self.mails_del_breakdown, self.abogado_a_cargo, path=path, sistema=self
        )
