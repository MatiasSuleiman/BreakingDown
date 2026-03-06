from abc import ABC, abstractmethod

def _ymd(fecha):
        if hasattr(fecha, "year") and hasattr(fecha, "month") and hasattr(fecha, "day"):
                return (fecha.year, fecha.month, fecha.day)
        return fecha

def _esta_vacio(valor):
        if valor is None:
                return True
        if isinstance(valor, str):
                return valor.strip() == ""
        return False

class Condicion(ABC):
        @abstractmethod
        def cumple(self,mail):
            raise TypeError("subclass should have overriden!!")

class No_condicion(Condicion):

        def cumple(self, mail):
            return True

class Condicion_de_cuerpo(Condicion):
        @classmethod
        def con_cuerpo(cls, cuerpo):
                if _esta_vacio(cuerpo):
                        return No_condicion()
                return cls(cuerpo)

        def __init__(self,cuerpo):
                self.body = cuerpo
        def cumple(self, mail):
            return self.body in mail.text


class Condicion_de_asunto(Condicion):
        @classmethod
        def con_asunto(cls, asunto):
                if _esta_vacio(asunto):
                        return No_condicion()
                return cls(asunto)

        def __init__(self, asunto):
                self.asunto = asunto.lower()

        def cumple(self, mail):
                return self.asunto in (mail.subject or "").lower()


class Condicion_de_emisor(Condicion):
        @classmethod
        def con_emisor(cls, emisor):
                if _esta_vacio(emisor):
                        return No_condicion()
                return cls(emisor)
        
        def __init__(self,emisor):
                self.emisor = emisor

        def cumple(self, mail):
            return self.emisor == mail.from_

class Condicion_de_receptor(Condicion):
        @classmethod
        def con_receptor(cls, receptor):
                if _esta_vacio(receptor):
                        return No_condicion()
                return cls(receptor)
        
        def __init__(self,receptor):
                self.receptor = receptor

        def cumple(self, mail):
            return self.receptor == mail.to[0]


class Condicion_de_enviado_antes_de(Condicion):
        @classmethod
        def enviado_antes_de(cls, fecha):
                if _esta_vacio(fecha):
                        return No_condicion()
                return cls(fecha)
        
        def __init__(self,fecha):
                self.fecha_proxima = fecha

        def cumple(self, mail):
            return _ymd(self.fecha_proxima) > _ymd(mail.date)


class Condicion_de_enviado_despues_de(Condicion):
        @classmethod
        def enviado_despues_de(cls, fecha):
                if _esta_vacio(fecha):
                        return No_condicion()
                return cls(fecha)
        
        def __init__(self,fecha):
                self.fecha_previa = fecha

        def cumple(self, mail):
            return _ymd(self.fecha_previa) < _ymd(mail.date)
