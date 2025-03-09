# AI Agent Framework Documentation

## Table of Contents
1. [Introduction](#introduction)
2. [Motivation](#motivation)
3. [Installation](#installation)
4. [Core Concepts](#core-concepts)
5. [Configuration Guide](#configuration-guide)
6. [Custom Actions](#custom-actions)
7. [Running the Agent](#running-the-agent)
8. [Advanced Usage](#advanced-usage)
9. [Best Practices](#best-practices)
10. [API Reference](#api-reference)
11. [Examples](#examples)

## Introduction

The AI Agent Framework is a lightweight, configurable state machine for building LLM-powered conversational agents. It simplifies the development of AI agents by providing a declarative configuration approach that separates the agent's behavior from its implementation.

**One sentence to get your own agent** - that's our promise. With minimal setup and configuration, you can create sophisticated AI agents without extensive coding.

### Key Features

- **TOML-based Configuration**: Define states, prompts, and transitions declaratively
- **Single-loop Architecture**: Each iteration makes one LLM call, processes the response, and transitions states
- **Action Dispatching**: Register custom functions that the LLM can invoke
- **OpenRouter API Integration**: Uses OpenAI-compatible SDK with OpenRouter's model marketplace
- **Multi-model Support**: Use different LLM models for different states
- **Flexible State Transitions**: Control conversation flow through predefined state transitions
- **JSON Communication Protocol**: Standardized format for LLM responses

## Motivation

This framework was created with simplicity and accessibility as core principles:

- **No Complex Dependencies**: Unlike frameworks such as LangChain or LlamaIndex that require significant learning curves, this framework uses minimal dependencies - primarily the OpenAI SDK (which can even be replaced with direct API calls using requests if you like).

- **Built with Python Standard Library**: Most functionality relies on Python's built-in packages, making it lightweight and easy to understand.

- **AI-Friendly Design**: The entire codebase is structured to be easily understood by AI assistants, enabling them to quickly grasp how to use and extend the framework without needing to process extensive documentation.

- **Easy Debugging**: With a straightforward architecture, errors are easier to identify and fix compared to more complex frameworks with multiple layers of abstraction.

- **Context-Efficient**: The entire framework can be included in an AI's context window, allowing AI assistants to understand the complete system without information loss.

- **Model Compatibility**: Based on extensive testing, the framework works best with models that provide stable JSON outputs:
  - **Highly Recommended**: OpenAI's GPT-4o and GPT-4o-mini
  - **Also Reliable**: QWEN 2.5 72B Instruct
  - **Note**: Some other models may produce formatting errors in their JSON outputs, causing runtime issues

## Installation

### Prerequisites

- Python 3.8 or higher
- An OpenRouter API key (or OpenAI API key)

### Dependencies

Install the required dependencies:

```bash
pip install openai python-dotenv requests
# Choose the appropriate TOML library
pip install tomli tomli-w  # For Python 3.10 and below
# For Python 3.11+, tomllib is built-in, but tomli-w is still needed for writing TOML (for using GUI)
```

### Setup

Create a `.env` file in your project directory to store your API key:

```
OPENROUTER_API_KEY=your_api_key_here
```

## Core Concepts

### State Machine Architecture

The agent operates as a finite state machine where:

- Each **state** represents a specific step in the conversation
- **Transitions** define how the agent moves between states
- The current state determines what prompt is sent to the LLM
- Each state can have its own temperature setting and model selection

### JSON Protocol

The LLM communicates with the agent framework using a standardized JSON format:

```json
{
  "action": "action_name",          // The action to take (or "none")
  "action_params": {                // Parameters for the action (if needed)
    "param1": "value1",
    "param2": "value2"
  },
  "message": "Message to the user", // Text shown to the user
  "next_state": "next_state_name",  // The state to transition to
  "require_input": "1"              // Whether to wait for user input
}
```

Note: The framework's reliability depends on the LLM's ability to consistently produce valid JSON in this exact format. This is why we recommend using GPT-4o, GPT-4o-mini, or QWEN 2.5 72B Instruct, which have demonstrated reliable JSON formatting in our testing.

### Conversation Flow

1. The agent starts in the initial state defined in the configuration
2. It sends the state's prompt to the LLM, along with conversation history
3. The LLM returns a JSON response with action, message, and next state
4. If an action is specified, the agent executes the registered function
5. The agent displays the message to the user
6. The agent transitions to the next state
7. If `require_input` is "1", the agent waits for user input before continuing
8. The cycle repeats until a terminal state is reached

## Configuration Guide

The agent's behavior is defined in a TOML configuration file. Here's a breakdown of its structure:

### Basic Configuration

```toml
# Agent configuration
initial_state = "greeting"  # The state the agent begins in
```

### General Description

```toml
[description]
role = """You are an AI assistant that helps users with specific tasks..."""
state_machine_logic = """This agent operates as a finite state machine..."""
work_principles = """IMPORTANT WORKING PRINCIPLES:..."""
```

### State Definitions

Each state is defined with its prompt, temperature, model, and allowed transitions:

```toml
[states.state_name]
prompt = """Instructions for the LLM in this state.

IMPORTANT: You MUST follow these constraints:
1. Your response MUST be a JSON object with the following structure:
{
  "action": "action_name",
  "action_params": { ... },
  "message": "Your message to the user",
  "next_state": "next_state_name",
  "require_input": "1"
}
"""
temperature = 0.7                      # Controls randomness (0.0-1.0)
model = "openai/gpt-4o-mini"           # Model to use for this state
transitions = ["state1", "state2"]     # States that can be transitioned to
```

### Example Configuration

```toml
# Agent configuration
initial_state = "greeting"

[description]
role = """You are an AI assistant that helps users with a variety of tasks."""
state_machine_logic = """This agent operates as a finite state machine..."""
work_principles = """IMPORTANT WORKING PRINCIPLES:..."""

[states.greeting]
prompt = """You are an AI assistant. Respond to the user's greeting and ask how you can help.

IMPORTANT: You MUST follow these constraints:
1. Your response MUST be a JSON object with the following structure:
{
  "action": "none",  # You can ONLY use "none" in this state
  "message": "Your message to the user",
  "next_state": "awaiting_task",  # You can ONLY transition to "awaiting_task" from here
  "require_input": "1"  # Use "1" to wait for user input, "0" to proceed automatically
}
"""
temperature = 0.7
model = "openai/gpt-4o-mini"
transitions = ["awaiting_task"]

[states.awaiting_task]
prompt = """Based on the user's request, determine what action to take...

IMPORTANT: You MUST follow these constraints:
1. You can ONLY choose from these actions:
   - "search": Use when the user is asking for information
   - "calculate": Use when the user is asking for a calculation
   - "none": Use for all other scenarios
"""
temperature = 0.7
model = "openai/gpt-4o-mini"
transitions = ["processing_task", "awaiting_task", "exit"]

# Additional states...
```

## Custom Actions

The agent can execute custom functions based on the LLM's decision. These functions are registered with the agent and called when specified in the LLM's response.

### Creating Action Functions

Action functions receive parameters from the LLM and return results that are added to the conversation:

```python
def search_function(params):
    """
    Function that searches for information.
    
    Args:
        params (dict): Dictionary containing search parameters,
                      with at least a "query" key.
    
    Returns:
        str: Formatted search results or error message.
    """
    query = params.get("query", "")
    if not query:
        return "Error: No search query provided."
    
    # Implement your search logic here
    # ...
    
    return "Formatted search results"


def calculate_function(params):
    """
    Function that performs calculations.
    
    Args:
        params (dict): Dictionary containing calculation parameters,
                      with at least an "expression" key.
    
    Returns:
        str: Calculation result or error message.
    """
    expression = params.get("expression", "")
    if not expression:
        return "Error: No expression provided."
    
    try:
        # For production, consider using a safer evaluation library
        result = eval(expression)
        return f"Result: {result}"
    except Exception as e:
        return f"Could not calculate expression: {str(e)}"
```

### Action Design Best Practices

- Each action should have a single, clear purpose
- Validate input parameters and handle missing data
- Return formatted results that are ready to present to the user
- Handle errors gracefully and return informative error messages
- Document the expected parameters and return format

## Running the Agent

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
agent.register_action("calculate", calculate_function)

# Start the agent with an initial message
agent.run("Hello, I need some help.")
```

### Development Mode

Enable development mode to get detailed logs about the agent's operation:

```python
# Create the agent with dev mode enabled
agent = AIAgent("agent_config.toml", api_key=api_key, dev_mode=True)
```

In development mode, the agent logs:
- Current state and transitions
- LLM calls with full prompt and parameters
- Raw LLM responses
- Action execution details
- State transitions

## Advanced Usage

### Using Different Models

One of the most powerful features is the ability to use different models for different states:

```toml
[states.simple_response]
prompt = """Generate a simple response..."""
temperature = 0.7
model = "anthropic/claude-3-haiku"  # Smaller, faster model for simple tasks
transitions = ["next_state"]

[states.complex_reasoning]
prompt = """Perform complex reasoning..."""
temperature = 0.3
model = "openai/gpt-4o"  # More capable but slower/costlier model
transitions = ["next_state"]
```

Note: Remember that models with unstable JSON output may cause errors. Our recommended models are:
- `openai/gpt-4o`
- `openai/gpt-4o-mini`
- `qwen/qwen2.5-vl-72b-instruct`

### Adding Memory and Context Management

Extend the agent with memory capabilities:

```python
class AIAgent:
    def __init__(self, config_path, api_key=None, dev_mode=False):
        # Existing initialization...
        
        # Add memory storage
        self.memory = {
            "user_preferences": {},
            "facts": [],
            "session_data": {}
        }
    
    def remember(self, category, key, value):
        """Store information in memory."""
        # Implementation...
    
    def recall(self, category, key=None):
        """Retrieve information from memory."""
        # Implementation...
```

Register memory-related actions:

```python
# Create memory action functions
def remember_preference(params, agent):
    key = params.get("key")
    value = params.get("value")
    agent.remember("user_preferences", key, value)
    return f"I've remembered that you prefer {value} for {key}."

# Register with the agent
agent.register_action("remember_preference", 
                     lambda params: remember_preference(params, agent))
```

### Implementing Web Search

Using the SearxNG meta-search engine:

```python
def search_function(params):
    query = params.get("query", "")
    if not query:
        return "Error: No search query provided."
    
    base_url = 'https://search.bostonlistener-career.org/search'
    post_data = {
        "q": query,
        "format": "json",
    }
    
    try:
        response = requests.post(base_url, data=post_data)
        
        if response.status_code == 200:
            search_results = response.json()
            
            # Format the results
            formatted_results = ""
            
            if 'results' in search_results and search_results['results']:
                formatted_results = "Search Results:\n\n"
                
                # Take the top 5 results
                for i, result in enumerate(search_results['results'][:5], 1):
                    title = result.get('title', 'No Title')
                    url = result.get('url', 'No URL')
                    content = result.get('content', 'No Description').strip()
                    
                    formatted_results += f"{i}. {title}\n"
                    formatted_results += f"   URL: {url}\n"
                    formatted_results += f"   Description: {content}\n\n"
                
                formatted_results += f"Total results found: {len(search_results['results'])}"
            else:
                formatted_results = f"No results found for query: {query}"
            
            return formatted_results
        else:
            return f"Error: Could not complete search. Status code: {response.status_code}"
    
    except Exception as e:
        return f"Error performing search: {str(e)}"
```

## Best Practices

### State Design

- **Single Responsibility**: Each state should have a clear, focused purpose
- **Descriptive Names**: Use state names that clearly indicate their function
- **Logical Transitions**: Create intuitive flows between states
- **Self-referential States**: States requiring user input should include themselves in their allowed transitions list, allowing them to persist when more information is needed
- **Feedback-driven Progression**: Each interactive state should wait for at least one user feedback message before deciding whether to transition in the next loop
- **Exit Mechanisms**: Include explicit instructions in prompts to respect user requests to skip or move on, preventing the agent from getting stuck in any particular state
- **Error Handling**: Include error states for handling unexpected situations

### Prompt Engineering

- **Clear Instructions**: Be explicit about what the LLM should do in each state
- **Constraints**: Clearly define the valid actions and transitions
- **Response Format**: Always specify the expected JSON structure
- **Examples**: Include examples for complex states
- **Format Emphasis**: Repeatedly emphasize the importance of correct JSON formatting

### Temperature Settings

- **Low (0.1-0.3)**: For precise, structured tasks requiring exact outputs
- **Medium (0.4-0.6)**: For most general tasks with some flexibility
- **High (0.7-0.9)**: For creative tasks or generating diverse responses

### Model Selection

- **Recommended Models**: Use models with stable JSON output
  - `openai/gpt-4o` - Excellent for complex reasoning with reliable formatting
  - `openai/gpt-4o-mini` - Good balance of performance and cost
  - `qwen/qwen2.5-vl-72b-instruct` - Reliable alternative option
- **Avoid**: Models that struggle with consistent JSON formatting

### Action Implementation

- **Input Validation**: Always validate action parameters
- **Error Handling**: Handle exceptions gracefully
- **Formatting**: Return well-formatted, user-ready results
- **Modularity**: Keep actions focused on specific tasks

## API Reference

### AIAgent Class

```python
class AIAgent:
    def __init__(self, config_path: str, api_key: str = None, dev_mode: bool = False):
        """
        Initialize the AI agent with a configuration file.
        
        Args:
            config_path: Path to the TOML configuration file
            api_key: OpenRouter API key (defaults to OPENAI_API_KEY environment variable)
            dev_mode: When True, prints detailed debugging information
        """
        
    def register_action(self, action_name: str, action_func: Callable):
        """
        Register an external function that the agent can call.
        
        Args:
            action_name: Name of the action (used in LLM responses)
            action_func: Function to call when the action is invoked
        """
        
    def run(self, user_input: str = None):
        """
        Run the agent's main loop, processing the user input and transitioning between states.
        
        Args:
            user_input: Initial user input to start the conversation
        """
```

### Configuration Structure

```
initial_state     String      The starting state of the agent
description       Section     General description of the agent
description.role  String      The role/purpose of the agent
states            Section     Container for all state definitions
states.<name>     Section     Definition of a specific state
prompt            String      Instructions for the LLM in this state
temperature       Float       Controls randomness (0.0-1.0)
model             String      Model to use for this state
transitions       String[]    Allowed state transitions
```

### JSON Response Format

```
action            String      Action to execute (or "none")
action_params     Object      Parameters for the action
message           String      Text to display to the user
next_state        String      State to transition to
require_input     String      "1" to require user input, "0" to continue automatically
```

## Examples

### Simple Q&A Agent

```toml
# agent_config.toml
initial_state = "listening"

[description]
role = """You are a helpful Q&A assistant."""

[states.listening]
prompt = """Answer the user's question directly and concisely.

IMPORTANT: You MUST follow these constraints:
1. Your response MUST be a JSON object with the following structure:
{
  "action": "none",
  "message": "Your answer to the user's question",
  "next_state": "listening",
  "require_input": "1"
}
"""
temperature = 0.7
model = "openai/gpt-4o-mini"
transitions = ["listening", "exit"]
```

### Search Agent

```toml
# agent_config.toml
initial_state = "greeting"

[description]
role = """You are a search assistant that helps users find information."""

[states.greeting]
prompt = """Greet the user and explain that you can help them search for information."""
temperature = 0.7
model = "openai/gpt-4o-mini"
transitions = ["awaiting_query"]

[states.awaiting_query]
prompt = """Determine if the user is asking for information that requires a search.

1. If they are asking a question that needs search, use the "search" action with their query.
2. If they're just chatting or asking something you can answer directly, use "none".

IMPORTANT: You MUST follow these constraints:
1. Your response MUST be a JSON object with the following structure:
{
  "action": "search" or "none",
  "action_params": {
    "query": "search query" (only for search action)
  },
  "message": "Your message to the user",
  "next_state": "showing_results" or "awaiting_query",
  "require_input": "0" or "1"
}
"""
temperature = 0.7
model = "openai/gpt-4o-mini"
transitions = ["showing_results", "awaiting_query", "exit"]

[states.showing_results]
prompt = """Present the search results to the user in an informative way.
Ask if they need more information or have other questions.

IMPORTANT: You MUST follow these constraints:
1. Your response MUST be a JSON object with the following structure:
{
  "action": "none",
  "message": "Your response summarizing the search results",
  "next_state": "awaiting_query",
  "require_input": "1"
}
"""
temperature = 0.7
model = "openai/gpt-4o-mini"
transitions = ["awaiting_query", "exit"]
```

### Creating Your First Agent in 60 Seconds

With this framework, creating your first agent is as simple as:

1. Install the framework:
```bash
pip install openai python-dotenv
```

2. Create a basic agent_config.toml:
```toml
initial_state = "chat"

[states.chat]
prompt = """You are a friendly assistant. Respond to the user query.

IMPORTANT: Your response MUST be a valid JSON object with:
{
  "action": "none",
  "message": "Your response to the user",
  "next_state": "chat",
  "require_input": "1"
}
"""
temperature = 0.7
model = "openai/gpt-4o-mini"
transitions = ["chat", "exit"]
```

3. Create a Python script to run your agent:
```python
from dotenv import load_dotenv
import os
from agent import AIAgent

load_dotenv()
api_key = os.environ.get("OPENROUTER_API_KEY")
agent = AIAgent("agent_config.toml", api_key=api_key)
agent.run("Hello, can you help me?")
```

That's it! You now have a functional AI agent that can carry on a conversation. Extend it with custom actions and states as needed.
