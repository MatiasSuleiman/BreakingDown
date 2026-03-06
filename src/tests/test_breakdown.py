from pathlib import Path
from tempfile import NamedTemporaryFile
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from Breakdown import Breakdown


class FakeMail:
    def __init__(self, date=None):
        self.date = date or datetime(2026, 3, 6, 12, 0, 0)
        self.from_ = "lawyer@example.com"
        self.to = ("client@example.com",)


class FakeSistema:
    def __init__(self, descripcion_por_mail):
        self.descripcion_por_mail = descripcion_por_mail

    def ver_descripcion_de(self, mail):
        return self.descripcion_por_mail.get(mail, "")


def make_mail(date=None):
    return FakeMail(date=date)


def test_breakdown_usa_description_y_no_crea_columna_summary():
    mail = make_mail()
    sistema = FakeSistema({mail: "Call with client"})

    with NamedTemporaryFile(suffix=".xlsx") as archivo:
        breakdown = Breakdown.con_mails_manejado_por(
            [mail],
            "lawyer@example.com",
            path=archivo.name,
            sistema=sistema,
        )

    assert breakdown.tiene_en("A1", "Date")
    assert breakdown.tiene_en("B1", "Description")
    assert breakdown.tiene_en("C1", "Minutes")
    assert breakdown.tiene_en("D1", "Hours")
    assert breakdown.tiene_en("B2", "Call with client")
    assert breakdown.excel["E1"].value is None


def test_breakdown_ordena_los_mails_por_fecha():
    mail_reciente = make_mail(datetime(2026, 3, 6, 12, 0, 0))
    mail_viejo = make_mail(datetime(2026, 3, 4, 12, 0, 0))
    sistema = FakeSistema(
        {
            mail_reciente: "Recent description",
            mail_viejo: "Older description",
        }
    )

    with NamedTemporaryFile(suffix=".xlsx") as archivo:
        breakdown = Breakdown.con_mails_manejado_por(
            [mail_reciente, mail_viejo],
            "lawyer@example.com",
            path=archivo.name,
            sistema=sistema,
        )

    assert breakdown.tiene_en("A2", "04/03/2026")
    assert breakdown.tiene_en("B2", "Older description")
    assert breakdown.tiene_en("A3", "06/03/2026")
    assert breakdown.tiene_en("B3", "Recent description")


def test_breakdown_autoajusta_el_ancho_de_description():
    mail = make_mail()
    descripcion = "Description wider than the header"
    sistema = FakeSistema({mail: descripcion})

    with NamedTemporaryFile(suffix=".xlsx") as archivo:
        breakdown = Breakdown.con_mails_manejado_por(
            [mail],
            "lawyer@example.com",
            path=archivo.name,
            sistema=sistema,
        )

    assert breakdown.excel.column_dimensions["B"].width == len(descripcion) + 2
