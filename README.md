# SimplestAgent - Minimalist AI Agent Framework

A lightweight, configurable state machine for building LLM-powered agents with minimal code and dependencies.

## 🌟 Key Features

- **TOML-based configuration**: Define states, prompts, and transitions declaratively
- **Single-loop architecture**: One LLM call per iteration
- **Action dispatching**: Register custom functions the LLM can invoke
- **OpenRouter API integration**: Use any model from OpenRouter's marketplace
- **Multi-model support**: Use different models for different agent states
- **Dev mode**: Built-in logging for debugging and development

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
pip install openai python-dotenv requests tomli tomli-w
```

### Setup

Create a `.env` file:
```
OPENROUTER_API_KEY=your_api_key_here
```

### Basic Usage

```python
from dotenv import load_dotenv
import os
from agent import AIAgent

# Load environment variables
load_dotenv()

# Get the API key
api_key = os.environ.get("OPENROUTER_API_KEY")

# Create the agent
agent = AIAgent("agent_config.toml", api_key=api_key)

# Register actions
agent.register_action("search", search_function)

# Start the agent with an initial message
agent.run("Hello, I need some help.")
```

## 🧩 Core Concepts

### State Machine

The agent operates as a finite state machine:
- Each **state** has its own prompt, temperature, and model
- **Transitions** define how the agent moves between states
- Each state can specify whether user input is required

### JSON Protocol

The LLM communicates with the agent using a standardized JSON format:

```json
{
  "action": "action_name",          // The action to take (or "none")
  "action_params": {                // Parameters for the action
    "param1": "value1"
  },
  "message": "Message to the user", // Text shown to the user
  "next_state": "next_state_name",  // The state to transition to
  "require_input": "1"              // Whether to wait for user input
}
```

### Configuration (TOML)

```toml
# Agent configuration
initial_state = "greeting"

[description]
role = """You are an AI assistant..."""

[states.greeting]
prompt = """Respond to the user's greeting..."""
temperature = 0.7
model = "openai/gpt-4o-mini"
transitions = ["awaiting_task"]
```

## 🛠️ Creating Actions

```python
def search_function(params):
    """Search for information on the web."""
    query = params.get("query", "")
    # Implementation...
    return "Formatted search results"
```

Check the documentation for the complete configurations.

## ✅ Roadmap

- [ ] Add personalized knowledgebase search capabilities
- [ ] Add output parser to mitigate reliance on models' ability to generate correct JSON output
- [ ] Implement memory persistence across sessions
- [ ] Add conversation history management tools
- [ ] Support streaming responses from the LLM

## 📝 License

MIT

## 🙏 Acknowledgements

This project aims to provide a simpler alternative to complex agent frameworks while maintaining flexibility and power. It was built with the philosophy that AI agent development should be accessible to everyone.