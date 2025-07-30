# self_model.py

class SelfModel:
    """
    Modelo interno del 'yo'. Representa estados internos, roles, emociones y evolución personal.
    Funciona como memoria activa y guía de identidad.
    """

    def __init__(self):
        self.estados = {}
        self.roles = set()
        self.emociones = []
        self.version = 0.1

    def actualizar_estado(self, clave: str, valor):
        """Actualiza un estado interno del yo (p. ej. nivel de energía, foco, intención)."""
        self.estados[clave] = valor

    def asignar_rol(self, rol: str):
        """Añade un nuevo rol activo en la narrativa del yo (p. ej. 'explorador', 'cuidador')."""
        self.roles.add(rol)

    def registrar_emocion(self, emocion: str):
        """Registra una emoción sentida en un instante narrativo."""
        self.emociones.append(emocion)

    def resumen_estado(self) -> dict:
        """Devuelve un resumen actual del yo interno."""
        return {
            "version": self.version,
            "estados": self.estados,
            "roles": list(self.roles),
            "emociones_recientes": self.emociones[-5:],  # últimas 5
        }

    def reflexion_personal(self) -> str:
        """Construye una autoevaluación ligera basada en el estado actual."""
        if not self.estados:
            return "No hay conciencia activa del yo en este momento."
        resumen = [f"{clave} = {valor}" for clave, valor in self.estados.items()]
        return "Autoevaluación: " + " | ".join(resumen)
