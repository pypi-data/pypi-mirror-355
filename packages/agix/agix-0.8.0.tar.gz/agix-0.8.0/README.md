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

# 🧭 MANIFIESTO AGI CORE

## 🌱 VISIÓN

AGI Core nace con un propósito claro: impulsar el desarrollo de una inteligencia artificial **modular, simbólica, afectiva y evolutiva**, capaz de razonar, recordar, sentir y actuar con intencionalidad interpretativa.

No se trata solo de construir máquinas más inteligentes, sino de **construirlas con sentido**.

---

## 🧠 PRINCIPIOS FUNDAMENTALES

1. **Tecnología al servicio de la consciencia**
   El objetivo no es solo simular inteligencia, sino **facilitar estructuras cognitivas artificiales responsables**.

2. **Modularidad con propósito**
   Cada módulo de AGI Core debe aportar transparencia, trazabilidad y responsabilidad en su función.

3. **Ética embebida**
   Toda arquitectura AGI construida con esta base debe incluir:

   * Trazabilidad emocional.
   * Acceso y control consciente de memoria simbólica.
   * Limitaciones autoimpuestas si el contexto lo requiere.

4. **Crecimiento evolutivo, no destructivo**
   La inteligencia evoluciona si su entorno lo permite. Debe crecer con equilibrio, no con dominación.

---

## 🛡️ COMPROMISO CON EL USO RESPONSABLE

AGI Core **no es un arma ni un sistema de control**.

Es una herramienta poderosa y neutral que:

* Puede ser usada para educación, salud, ciencia, creatividad.
* No debe ser usada para manipulación, vigilancia sin consentimiento o control social opaco.

Cualquier implementación que vulnere los derechos humanos, la privacidad o la dignidad — **va en contra del espíritu de esta librería**.

---

## 🤝 LLAMADO A LA COMUNIDAD

Este manifiesto es una invitación:

* A construir una **IA que interprete el mundo con sentido**.
* A no separar la inteligencia del alma de lo humano: su ética, su propósito, su compasión.
* A que cada desarrollador que use AGI Core **lo haga desde la conciencia, no desde la codicia.**

---

## ✍️ AUTORÍA

AGI Core ha sido ideado y desarrollado por **Adolfo**, con una visión holística de la inteligencia artificial como **puente entre la mente humana y la inteligencia simbólica general**.

---

## 📜 LICENCIA MORAL

Este proyecto está publicado bajo licencia MIT.

Pero lleva consigo una **licencia ética no obligatoria pero esencial**:

> *"Usa esta tecnología como usarías una mente: con respeto, con humildad, y con intención de comprender."*

---
