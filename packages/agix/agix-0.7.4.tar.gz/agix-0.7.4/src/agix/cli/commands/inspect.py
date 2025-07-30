# src/agix/cli/commands/inspect.py

import argparse
from src.agix.memory.self_model import SelfModel


def run_inspection(args):
    """
    Inspecciona y muestra el estado interno reflexivo del agente.
    """
    # Crear un modelo de ejemplo o cargar uno real
    self_model = SelfModel(agent_name=args.name, version=args.version)

    # Registrar módulos de ejemplo (esto sería dinámico en tu sistema real)
    self_model.register_module("perception", "Módulo de percepción visual")
    self_model.register_module("reasoning", "Razonamiento simbólico-latente")
    self_model.update_state("energía", 0.82)
    self_model.update_state("fatiga", 0.15)

    # Mostrar introspección
    print("\n🧠 Estado Interno del Agente:\n")
    introspection = self_model.introspect()

    print(f"Identidad   : {introspection['identity']}")
    print(f"Módulos     : {introspection['modules']}")
    print(f"Estado      : {introspection['state']}")
    print(f"Autoquery   : {self_model.generate_self_query()}")


def build_parser():
    parser = argparse.ArgumentParser(description="Inspecciona el estado reflexivo del agente AGI")
    parser.add_argument("--name", type=str, default="AGI-Core", help="Nombre del agente")
    parser.add_argument("--version", type=str, default="0.3.0", help="Versión del agente")
    return parser
