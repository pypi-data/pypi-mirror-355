# agi_lab/agents/base.py

from abc import ABC, abstractmethod

class AGIAgent(ABC):
    """
    Clase base abstracta para agentes de AGI.
    Todos los agentes deben implementar los siguientes métodos clave:
    - percebir: procesar observaciones del entorno
    - decidir: tomar acciones
    - aprender: actualizar internamente según experiencia
    """

    def __init__(self, name="AGIAgent"):
        self.name = name
        self.memory = None
        self.internal_state = {}

    @abstractmethod
    def perceive(self, observation):
        """Procesa una observación del entorno."""
        pass

    @abstractmethod
    def decide(self):
        """Devuelve la acción a tomar en el siguiente paso."""
        pass

    @abstractmethod
    def learn(self, reward, done=False):
        """Actualiza el agente tras recibir recompensa."""
        pass

    def reset(self):
        """Reinicia el estado interno del agente."""
        self.internal_state.clear()

    def __str__(self):
        return f"<AGIAgent: {self.name}>"
