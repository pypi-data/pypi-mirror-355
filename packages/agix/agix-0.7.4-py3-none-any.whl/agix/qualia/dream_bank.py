# dream_bank.py

from typing import List, Dict
import datetime
import json


class DreamBank:
    """
    Memoria emocional-poética del agente.
    Almacena sueños, visiones o recuerdos simbólicos con tono afectivo.
    """

    def __init__(self):
        self.suenos: List[Dict] = []

    def registrar_sueno(self, contenido: str, emocion: str, intensidad: float):
        """
        Guarda un sueño con su carga emocional.
        """
        self.suenos.append({
            "timestamp": datetime.datetime.now().isoformat(),
            "contenido": contenido,
            "emocion": emocion,
            "intensidad": round(intensidad, 3)
        })

    def resumen_reciente(self, n: int = 3) -> List[str]:
        """
        Devuelve una lista con los últimos N sueños en forma poética.
        """
        return [
            f"({s['emocion']} · {s['intensidad']}) {s['contenido']}"
            for s in self.suenos[-n:]
        ]

    def exportar(self, ruta: str = "qualia_state.json"):
        """
        Guarda los sueños en un archivo JSON.
        """
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(self.suenos, f, indent=2, ensure_ascii=False)

    def importar(self, ruta: str = "qualia_state.json"):
        """
        Carga los sueños desde un archivo existente.
        """
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                self.suenos = json.load(f)
        except FileNotFoundError:
            self.suenos = []
