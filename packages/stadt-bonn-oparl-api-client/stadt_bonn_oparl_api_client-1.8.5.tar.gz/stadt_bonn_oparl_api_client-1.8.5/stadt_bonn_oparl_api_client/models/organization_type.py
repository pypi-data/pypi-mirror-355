from enum import Enum


class OrganizationType(str, Enum):
    AMT = "Amt"
    EXTERNES_GREMIUM = "Externes Gremium"
    FRAKTION = "Fraktion"
    GREMIUM = "Gremium"
    HAUPTORGAN = "Hauptorgan"
    HILFSORGAN = "Hilfsorgan"
    INSTITUTION = "Institution"
    PARTEI = "Partei"
    SONSTIGES = "Sonstiges"
    VERWALTUNGSBEREICH = "Verwaltungsbereich"

    def __str__(self) -> str:
        return str(self.value)
