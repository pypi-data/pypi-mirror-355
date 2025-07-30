# src/agix/cli/commands/evaluate.py

import argparse

from src.agix.cli.commands.simulate import ToyEnvironment
from src.agix.evaluation.metrics import EvaluationMetrics
from src.agix.agents.genetic import GeneticAgent

# Diccionarios normalizados a minúsculas
AGENTS = {
    "genetic": GeneticAgent,
    "geneticagent": GeneticAgent
}

ENVS = {
    "dummy": ToyEnvironment,
    "toyenv": ToyEnvironment
}


def run_evaluation(args):
    """
    Ejecuta métricas básicas de evaluación para un agente dado.
    """
    agent_key = args.agent_class.strip().lower()
    env_key = args.env_class.strip().lower()

    agent_class = AGENTS.get(agent_key)
    env_class = ENVS.get(env_key)

    if not agent_class or not env_class:
        print("❌ Agente o entorno no reconocidos. Usa uno de:")
        print(f"  Agentes disponibles: {list(AGENTS.keys())}")
        print(f"  Entornos disponibles: {list(ENVS.keys())}")
        return

    agent = agent_class(action_space_size=4)
    tasks = [env_class() for _ in range(args.num_tasks)]

    print("\n🧠 Ejecutando evaluación...\n")
    generality = EvaluationMetrics.generality_score(agent, tasks)

    print(f"🔎 Generalidad: {generality:.2f}")


def build_parser():
    parser = argparse.ArgumentParser(description="Evaluación del agente AGI")
    parser.add_argument("--agent-class", required=True, help="Nombre del agente (ej: genetic)")
    parser.add_argument("--env-class", required=True, help="Nombre del entorno (ej: dummy)")
    parser.add_argument("--num-tasks", type=int, default=3, help="Número de tareas a evaluar")
    return parser
