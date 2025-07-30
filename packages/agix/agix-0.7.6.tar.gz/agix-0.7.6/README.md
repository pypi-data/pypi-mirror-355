# AGI Lab: Framework Experimental para Inteligencia Artificial General

`agi_lab` es una librería modular en Python para investigar y desarrollar arquitecturas de AGI (Inteligencia Artificial General) inspiradas en principios evolutivos, neuromórficos, simbólicos y matemáticos formales.

---

## 🚀 Objetivo
Desarrollar una plataforma flexible para:
- Probar teorías formales de AGI (como inferencia activa, autoorganización, generalización universal).
- Experimentar con agentes adaptativos que combinan aprendizaje, razonamiento y plasticidad.
- Evaluar sistemas en términos de generalidad, transferencia, robustez y explicabilidad.

---

## 📦 Estructura del Proyecto

```bash
agi_lab/
├── agents/             # Definición de agentes (genéticos, neuromórficos...)
├── environments/       # Entornos cognitivos o simulaciones
├── evaluation/         # Métricas de desempeño y generalidad
├── learning/           # Módulos de aprendizaje (plasticidad, evolución, meta)
├── memory/             # Representación simbólica y subsimbólica
├── reasoning/          # Razonamiento neuro-simbólico y composicional
├── utils/              # Herramientas matemáticas y gráficas
└── README.md           # Este archivo
```

---

## 🧠 Componentes Clave

### `agents/`
- `GeneticAgent`: política evolutiva simple.
- `NeuromorphicAgent`: sinapsis plástica basada en Hebb o STDP.

### `learning/`
- `HebbianPlasticity`, `STDP`, `BCM`: reglas biológicas de aprendizaje.
- `EvolutionaryEngine`: motor de evolución de poblaciones.
- `MetaLearner`: auto-mejora computacional.

### `memory/`
- `Ontology`, `SymbolicConcept`: conocimiento estructurado.
- `LatentRepresentation`: embeddings conceptuales.

### `reasoning/`
- `NeuroSymbolicBridge`: puente entre lógica simbólica y latente.

### `evaluation/`
- Métricas de generalidad, transferencia, robustez y explicabilidad.

### `utils/`
- `ConceptualTopology`: grafos semánticos y relaciones de proximidad.

---

## 🧪 Ejemplo de Uso
```python
from agents.genetic import GeneticAgent
from environments.env_base import AGIEnvironment

# Crear un agente y simular en un entorno personalizado
agent = GeneticAgent(action_space_size=4)
env = SomeToyEnvironment()

obs = env.reset()
while True:
    agent.perceive(obs)
    action = agent.decide()
    obs, reward, done, _ = env.step(action)
    agent.learn(reward)
    if done:
        break
```

---

## 📚 Referencias Teóricas
Este framework está inspirado en una teoría formal desarrollada para AGI, que incluye fundamentos axiomáticos, representaciones topológicas y categóricas del conocimiento, inferencia activa, generalización universal, y simulación epistémica.

---

## ✨ Futuro
- Integración con `Coq`, `Lean` o `Agda` para verificación formal.
- Simuladores cognitivos multiagente.
- Arquitectura modular `𝒜_meta` con autoevaluación.

---

## 🧩 Autor
Desarrollado por Adolfo González Hernández, como proyecto experimental para una librería avanzada de AGI con fundamentos formales y computacionales.

---

## 📂 Ejemplos incluidos

Consulta [examples/README.md](examples/README.md) para una lista completa de scripts demostrativos:
- AGI simbólica
- Plasticidad
- Agentes evolutivos
- Razonamiento latente
- Evaluación de robustez y transferencia

## 🧭 Mapa Conceptual del Sistema

[Qualia] ← emociones, belleza, ética
   ↑
[Agent] ← decisión
   ↑
[Learning] ← evolución, plasticidad
   ↑
[Memory] ← símbolos + embeddings
   ↑
[Reasoning] ← lógica + inferencia

