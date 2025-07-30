# AGIX – AGI Core Framework

**AGIX** (antes `agi_lab`) es un framework modular en Python para investigar arquitecturas de **Inteligencia Artificial General (AGI)**, integrando principios evolutivos, neurobiológicos, simbólicos y formales.

---

## 🚀 Objetivo

Desarrollar una plataforma flexible para:

- Simular agentes con plasticidad, evolución y razonamiento híbrido.
- Probar teorías formales como inferencia activa, generalización universal o autoorganización.
- Evaluar agentes mediante métricas de generalidad, robustez y explicabilidad.
- Permitir autoevaluación reflexiva mediante ontologías internas.

---

## 📦 Instalación

Desde PyPI:

```bash
pip install agix
```

## 📂 Estructura del Proyecto

```bash
agix/
├── agents/         # Agentes genéticos y neuromórficos
├── learning/       # Plasticidad, evolución, meta-aprendizaje
├── memory/         # Ontologías y embeddings conceptuales
├── reasoning/      # Razonamiento simbólico y neuro-simbólico
├── evaluation/     # Métricas de generalidad y robustez
├── environments/   # Entornos simulados y ToyEnv
├── cli/            # Interfaz de línea de comandos

```

## 🧪 Ejemplo de uso básico

```python
from agix.agents.genetic import GeneticAgent

agent = GeneticAgent(action_space_size=4)
env = ToyEnvironment()

obs = env.reset()
while True:
    agent.perceive(obs)
    action = agent.decide()
    obs, reward, done, _ = env.step(action)
    agent.learn(reward)
    if done:
        break

```

## 🧠 Componentes principales

- ```GeneticAgent:``` aprendizaje evolutivo por mutación y cruce.

- ```NeuromorphicAgent:``` aprendizaje basado en plasticidad Hebb/STDP.

- ```MetaLearner:``` transformación adaptativa del agente (π → π′).

- ```Ontology```, ```LatentRepresentation```: representación de conceptos híbrida.

- ```NeuroSymbolicBridge```: conversión simbólico ↔ latente.

- ```EvaluationMetrics```: robustez, generalidad, transferencia, fagi_index.


## 🔍 CLI disponible

```bash
python -m agix.cli.main simulate --observations 10 --actions 4
python -m agix.cli.main inspect --name AGIX --version 0.7.4
python -m agix.cli.main evaluate --agent-class GeneticAgent --env-class ToyEnv

```

## 📚 Documentación oficial


- Sitio: https://alphonsus411.github.io/agi_core

- Contiene guía de instalación, arquitectura, ejemplos, API y hoja de ruta.

## 🧩 Mapa conceptual del sistema

```csharp
[Qualia] ← emociones, belleza, ética
   ↑
[Agent] ← decisión
   ↑
[Learning] ← evolución, plasticidad
   ↑
[Memory] ← símbolos + embeddings
   ↑
[Reasoning] ← lógica + inferencia

```

## ✨ Futuro

- Soporte para verificación formal (```Coq```, ```Lean```)

- Agentes autoevaluables con memoria reflexiva (```SelfModel```)

- Integración de arquitecturas ```AMeta```, ```UniversalAgent```

- Visualización de procesos cognitivos y gráficas de evolución

## 🧪 Estado del proyecto

| Estado       | Versión | Licencia | PyPI                                                                              |
| ------------ |---------| -------- | --------------------------------------------------------------------------------- |
| Experimental | `0.7.9` | MIT      | [![PyPI](https://img.shields.io/pypi/v/agix.svg)](https://pypi.org/project/agix/) |

## 🧠 Autor

Desarrollado por **Adolfo González Hernández**
Proyecto independiente de investigación y exploración de AGI experimental.
