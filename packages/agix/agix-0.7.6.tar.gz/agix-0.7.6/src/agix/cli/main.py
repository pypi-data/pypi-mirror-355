# src/agix/cli/main.py

import argparse
from src.agix.cli.commands import simulate, inspect, evaluate


def main():
    parser = argparse.ArgumentParser(
        description="AGI Core CLI - Interfaz de línea de comandos para simulación, inspección y evaluación de agentes."
    )

    subparsers = parser.add_subparsers(title="comandos disponibles", dest="command")

    # Subcomando: simulate
    sim_parser = simulate.build_parser()
    subparsers._name_parser_map["simulate"] = sim_parser

    # Subcomando: inspect
    insp_parser = inspect.build_parser()
    subparsers._name_parser_map["inspect"] = insp_parser

    # Subcomando: evaluate
    eval_parser = evaluate.build_parser()
    subparsers._name_parser_map["evaluate"] = eval_parser

    # Parsear argumentos
    args = parser.parse_args()

    if args.command == "simulate":
        simulate.run_simulation(args)
    elif args.command == "inspect":
        inspect.run_inspection(args)
    elif args.command == "evaluate":
        evaluate.run_evaluation(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
