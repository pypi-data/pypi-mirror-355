# controller_core.py

from typing import Any, Optional
from .policy_optimization import PolicyOptimizer


class ControllerCore:
    """
    Núcleo del sistema de control jerárquico.
    Se encarga de seleccionar políticas activas, gestionar su ciclo y evaluar rendimiento.
    """

    def __init__(self, policy_optimizer: PolicyOptimizer):
        self.policy_optimizer = policy_optimizer
        self.estado_interno = {}
        self.historial_politicas = []
        self.politica_actual = None

    def seleccionar_politica(self, contexto: Any) -> Any:
        """
        Selecciona una política en base al contexto (percepción, metas, estado emocional).
        Por ahora retorna una política dummy, puede integrarse con módulos externos.
        """
        self.politica_actual = "default_policy"
        self.historial_politicas.append(self.politica_actual)
        return self.politica_actual

    def evaluar_desempeno(self, resultados: Any) -> float:
        """
        Evalúa el rendimiento reciente para decidir si adaptar la política.
        """
        # Dummy: puedes usar recompensas promedio, feedback emocional o métricas éticas
        return resultados.get("reward", 0.0)

    def ciclo_control(self, percepcion: Any, metas: Any, retroalimentacion: Any):
        """
        Bucle principal del controlador:
        1. Selecciona política según contexto.
        2. Evalúa desempeño.
        3. Decide si invocar optimización de política.
        """
        self.seleccionar_politica(percepcion)
        score = self.evaluar_desempeno(retroalimentacion)

        if score < 0.5:  # umbral adaptable
            print("🔄 Ajustando política...")
            try:
                self.policy_optimizer.update_policy(
                    states=retroalimentacion["states"],
                    actions=retroalimentacion["actions"],
                    advantages=retroalimentacion["advantages"]
                )
            except NotImplementedError:
                print("⚠️ Método update_policy aún no implementado.")

    def resumen_estado(self) -> str:
        return f"Política actual: {self.politica_actual} | Historial: {self.historial_politicas[-3:]}"
