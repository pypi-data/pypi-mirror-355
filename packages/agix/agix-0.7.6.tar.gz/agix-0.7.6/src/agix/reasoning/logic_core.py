# logic_core.py

from typing import List, Dict, Callable


class Fact:
    """
    Representa un hecho lógico atómico: predicado con argumentos.
    Ejemplo: amigo("ana", "juan")
    """
    def __init__(self, predicate: str, args: List[str]):
        self.predicate = predicate
        self.args = args

    def __str__(self):
        return f"{self.predicate}({', '.join(self.args)})"


class Rule:
    """
    Regla lógica tipo: si condición(es), entonces hecho.
    Ejemplo: si amigo(X, Y) y amigo(Y, Z) → amigo(X, Z)
    """
    def __init__(self, condition: Callable[[List[Fact]], bool], consequence: Fact, description: str = ""):
        self.condition = condition
        self.consequence = consequence
        self.description = description or str(consequence)


class LogicCore:
    """
    Núcleo de razonamiento lógico simbólico. Permite agregar hechos, reglas e inferir consecuencias.
    """

    def __init__(self):
        self.facts: List[Fact] = []
        self.rules: List[Rule] = []

    def add_fact(self, fact: Fact):
        self.facts.append(fact)

    def add_rule(self, rule: Rule):
        self.rules.append(rule)

    def infer(self):
        """
        Aplica reglas sobre los hechos actuales y añade nuevas inferencias.
        """
        new_facts = []
        for rule in self.rules:
            if rule.condition(self.facts):
                if not any(f.__str__() == str(rule.consequence) for f in self.facts):
                    self.facts.append(rule.consequence)
                    new_facts.append(rule.consequence)
        return new_facts

    def list_facts(self):
        return [str(f) for f in self.facts]

    def list_rules(self):
        return [r.description for r in self.rules]
