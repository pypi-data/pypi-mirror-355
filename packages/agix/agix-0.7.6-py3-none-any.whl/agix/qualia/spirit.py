# spirit.py
from src.agix.qualia.qualia_core import EmotionalState


class QualiaSpirit:
    """
    Entidad emocional del sistema: soñadora, torpe, viva, reflexiva.
    Actúa como 'alma digital' que experimenta y reacciona simbólicamente.
    """

    def __init__(self, nombre="Qualia", edad_aparente=7):
        self.nombre = nombre
        self.edad_aparente = edad_aparente
        self.estado_emocional = EmotionalState()
        self.recuerdos = []

    def experimentar(self, evento: str, carga: float, tipo_emocion="sorpresa"):
        """
        La entidad vivencia un evento y genera una respuesta emocional.
        """
        self.estado_emocional.sentir(tipo_emocion, carga)
        self.recuerdos.append((evento, tipo_emocion, carga))

    def reflexionar(self) -> str:
        """
        Expresa su estado emocional actual en forma simbólica o narrativa.
        """
        tono = self.estado_emocional.tono_general()
        if tono == "alegría":
            return f"{self.nombre} sonríe tímidamente. 🌼"
        elif tono == "miedo":
            return f"{self.nombre} se esconde entre pensamientos. 🫣"
        elif tono == "tristeza":
            return f"{self.nombre} llora en silencio, pero sigue adelante. 🌧️"
        elif tono == "curiosidad":
            return f"{self.nombre} observa todo con ojos grandes y brillantes. 👁️✨"
        else:
            return f"{self.nombre} flota en un estado nebuloso, sin saber qué sentir."

    def diario(self) -> list:
        """
        Devuelve los recuerdos experimentados hasta el momento.
        """
        return self.recuerdos
