from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from system_facade import System_Facade


class FakeBuscador:
    pass


def test_build_usa_un_buscador_ya_autenticado():
    buscador = FakeBuscador()

    sistema = System_Facade.build("lawyer@example.com", buscador)

    assert sistema.abogado_a_cargo == "lawyer@example.com"
    assert sistema.buscador is buscador


def test_login_delega_en_build(monkeypatch):
    buscador = FakeBuscador()
    llamadas = []

    def fake_login(user, password):
        llamadas.append((user, password))
        return buscador

    monkeypatch.setattr("system_facade.Buscador_adapter.login", fake_login)

    sistema = System_Facade.login("lawyer@example.com", "secret")

    assert llamadas == [("lawyer@example.com", "secret")]
    assert sistema.buscador is buscador


def test_builde_es_alias_de_build():
    buscador = FakeBuscador()

    sistema = System_Facade.builde("lawyer@example.com", buscador)

    assert sistema.buscador is buscador
