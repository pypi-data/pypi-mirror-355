# Evi - Multi-Agent Framework Generator

Evi is a flexible, modular code generator for multi-agent systems that supports multiple agent frameworks (CrewAI, LangGraph, ReAct) and LLM providers (OpenAI, Gemini).

## Features

- **Multiple Agent Frameworks**
  - [CrewAI](https://github.com/joaomdmoura/crewAI) - Create agent crews with specialized roles and tasks
  - [LangGraph](https://github.com/langchain-ai/langgraph) - Create agent workflows using directed graphs
  - [ReAct](https://arxiv.org/abs/2210.03629) - Build agents using the Reasoning+Acting pattern

- **Multiple LLM Providers**
  - OpenAI (GPT-3.5, GPT-4)
  - Google Gemini (Pro, Pro Vision)

- **Dual Interfaces**
  - Command-line interface (CLI) for scripting and automation
  - Streamlit web interface with visualization and interactive controls

- **Modular, Pluggable Architecture**
  - Easily extend with new providers or frameworks
  - Customizable templates using Jinja2

- **Advanced Features**
  - Multiple output formats (Python code or JSON configuration)
  - Agent workflow visualization
  - Configurable model parameters

## Installation

### Basic Installation

```bash
pip install evi
```

### With GUI Support

```bash
pip install evi[streamlit]
```

### With Framework-Specific Dependencies

```bash
pip install evi[crewai]  # For CrewAI support
pip install evi[langgraph]  # For LangGraph support
pip install evi[react]  # For ReAct support
```

### Full Installation

```bash
pip install evi[all]
```

### For Development

```bash
pip install evi[dev]
```

## Usage

### Command-Line Interface

```bash
# Generate CrewAI code using OpenAI
evi --prompt "Create a team of researchers to analyze climate data" --framework crewai --provider openai

# Generate LangGraph configuration using Gemini
evi --prompt "Create a customer service workflow" --framework langgraph --provider gemini --output json

# Save output to a file
evi --prompt "Create a team of researchers to analyze climate data" --output-file my_agents.py
```

### Streamlit Interface

```bash
# Launch the Streamlit web interface
evi-gui
```

### Python API

```python
from evi.core import EviGenerator

# Create a generator instance
generator = EviGenerator(provider="openai", framework="crewai")

# Generate code from a prompt
code = generator.generate(
    "Create a research team with three agents that analyze financial data",
    output_format="code"
)

# Generate JSON configuration
config = generator.generate(
    "Create a research team with three agents that analyze financial data",
    output_format="json"
)

# Print or save the generated code
print(code)
with open("my_agents.py", "w") as f:
    f.write(code)
```

## API Key Configuration

Evi requires API keys for accessing LLM providers:

### Environment Variables

```bash
# For OpenAI
export OPENAI_API_KEY=your_api_key_here

# For Gemini
export GEMINI_API_KEY=your_api_key_here
```

### Using .env File

Create a `.env` file in your project directory:

```
OPENAI_API_KEY=your_api_key_here
GEMINI_API_KEY=your_api_key_here
```

Then in your Python code:

```python
from dotenv import load_dotenv

load_dotenv()  # This loads the .env file
```

## Framework-Specific Examples

### CrewAI Example

```python
from evi.core import EviGenerator

prompt = """
Create a research crew with two agents:
1. A data collector that finds information online
2. An analyst that summarizes and provides insights
The crew should analyze recent developments in quantum computing.
"""

generator = EviGenerator(provider="openai", framework="crewai")
code = generator.generate(prompt, output_format="code")

# Save the generated code
with open("quantum_research_crew.py", "w") as f:
    f.write(code)
```

### LangGraph Example

```python
from evi.core import EviGenerator

prompt = """
Create a customer support workflow that:
1. Classifies the initial customer query
2. Routes to either technical support or billing department
3. Generates a response based on the department's knowledge base
"""

generator = EviGenerator(provider="openai", framework="langgraph")
code = generator.generate(prompt, output_format="code")

# Save the generated code
with open("customer_support_workflow.py", "w") as f:
    f.write(code)
```

### ReAct Example

```python
from evi.core import EviGenerator

prompt = """
Create a reasoning agent that can:
1. Answer questions about physics
2. Break down complex problems into steps
3. Generate analogies to explain difficult concepts
"""

generator = EviGenerator(provider="gemini", framework="react")
code = generator.generate(prompt, output_format="code")

# Save the generated code
with open("physics_tutor_agent.py", "w") as f:
    f.write(code)
```

## Architecture

Evi is built with a modular, pluggable architecture:

- **Core**: Central controller that orchestrates the generation process
- **Providers**: Interfaces to LLM providers (OpenAI, Gemini)
- **Frameworks**: Handlers for different agent frameworks (CrewAI, LangGraph, ReAct)
- **Templates**: Jinja2 templates for code generation

This architecture makes it easy to extend Evi with new providers or frameworks by implementing the appropriate interfaces.

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to contribute to Evi.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
