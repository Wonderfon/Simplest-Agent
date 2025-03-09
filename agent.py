import os
import json
import datetime
from typing import Dict, Any, Callable

# Choose the appropriate TOML library based on Python version
try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # Python 3.10 and below, requires 'pip install tomli'

from openai import OpenAI

class AIAgent:
    def __init__(self, config_path: str, api_key: str = None, dev_mode: bool = False):
        """
        Initialize the AI agent with a configuration file.
        
        Args:
            config_path: Path to the TOML configuration file
            api_key: OpenRouter API key (defaults to OPENAI_API_KEY environment variable)
            dev_mode: When True, prints detailed debugging information
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenRouter API key is required. Provide it as a parameter or set OPENAI_API_KEY environment variable.")
        
        # Initialize dev mode flag
        self.dev_mode = dev_mode
        
        # Initialize OpenAI client with OpenRouter configuration
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key
        )
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Current state and conversation history
        self.current_state = self.config.get("initial_state", "start")
        self.conversation_history = []
        
        # Separate search history
        self.search_history = []
        
        # Register available actions
        self.available_actions = {}
        
        # 初始化日志文件
        self.log_timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
        self.log_file = f"agent_log_{self.log_timestamp}.txt"
        
        # 记录初始化信息
        self._log_info(f"Agent initialized with config from {config_path}")
        self._log_info(f"Initial state: {self.current_state}")
        self._log_info(f"Dev mode: {self.dev_mode}")
        
        if self.dev_mode:
            print(f"[DEV] Agent initialized in dev mode with config from {config_path}")
            print(f"[DEV] Initial state: {self.current_state}")
            print(f"[DEV] Logging to file: {self.log_file}")
    
    def _log_info(self, message: str):
        """写入信息到日志文件"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    
    def _log_json(self, title: str, data: Any):
        """将JSON数据格式化并写入日志文件"""
        self._log_info(f"===== {title} =====")
        if isinstance(data, (dict, list)):
            try:
                formatted_json = json.dumps(data, ensure_ascii=False, indent=2)
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(f"{formatted_json}\n")
            except:
                self._log_info(f"无法序列化为JSON: {str(data)}")
        else:
            self._log_info(str(data))
        self._log_info("=" * (len(title) + 12))  # 12 是 "===== " 和 " =====" 的长度
    
    def _load_config(self, config_path: str) -> Dict:
        """Load and parse the TOML configuration file."""
        with open(config_path, "rb") as f:
            return tomllib.load(f)
    
    def register_action(self, action_name: str, action_func: Callable):
        """Register an external function that the agent can call."""
        self.available_actions[action_name] = action_func
        self._log_info(f"Registered action: {action_name}")
        if self.dev_mode:
            print(f"[DEV] Registered action: {action_name}")
    
    def _call_llm(self, prompt: str, temperature: float, model: str) -> Dict:
        """Call the LLM API and return the response as a parsed JSON."""
        try:
            # Get the general description from the config
            description = self.config.get("description", {})
            role = description.get("role", "")
            state_machine_logic = description.get("state_machine_logic", "")
            work_principles = description.get("work_principles", "")
            
            # Format search history as a separate block if it exists
            search_history_block = ""
            if self.search_history:
                search_history_block = "\n\nSEARCH HISTORY:\n"
                for idx, search_result in enumerate(self.search_history):
                    search_history_block += f"Search #{idx+1}: {search_result}\n\n"
                print("[DEV] SEARCH HISTORY:")
                for i, search_result in enumerate(self.search_history):
                    print(f"[DEV] Search Result #{i+1}:")
                    print(search_result)
                    print("-"*40) 
            
            # Construct a complete system prompt that includes the general description and search history
            complete_system_prompt = f"""
{role}

{state_machine_logic}

{work_principles}

CURRENT STATE: {self.current_state}
{search_history_block}
{prompt}
"""
            
            # Format the system prompt and user conversation history
            messages = [{"role": "system", "content": complete_system_prompt}]
            
            # Add conversation history
            for msg in self.conversation_history:
                messages.append(msg)
            
            # 记录LLM调用的详细信息
            self._log_info(f"CALLING LLM - Model: {model}, Temperature: {temperature}")
            self._log_info(f"Current state: {self.current_state}")
            self._log_json("System prompt", {"role": "system", "content": complete_system_prompt})
            
            for i, msg in enumerate(messages):
                if i > 0:  # 跳过系统提示，因为已经单独记录了
                    self._log_json(f"Message {i} ({msg['role']})", msg)
            
            if self.search_history:
                for i, search_result in enumerate(self.search_history):
                    self._log_info(f"Search Result #{i+1}:")
                    self._log_info(search_result)

          

            if self.dev_mode:
                print("\n" + "="*80)
                if self.search_history:
                    print("[DEV] SEARCH HISTORY:")
                    for i, search_result in enumerate(self.search_history):
                        print(f"[DEV] Search Result #{i+1}:")
                        print(search_result)
                        print("-"*40)  

                print("[DEV] CALLING LLM")
                print(f"[DEV] Model: {model}")
                print(f"[DEV] Temperature: {temperature}")
                print("[DEV] Prompt and Messages:")
                for i, msg in enumerate(messages):
                    print(f"[DEV] Message {i} ({msg['role']}):")
                    print(f"{msg['content']}")
                    print("-"*40)  # 添加消息间的分隔符以提高可读性
                

                
                print("="*80 + "\n")
            
            completion = self.client.chat.completions.create(
                model=model,
                temperature=temperature,
                messages=messages,
                max_tokens=5000,
                response_format={"type": "json_object"}
            )
            
            response_text = completion.choices[0].message.content
            
            # 记录LLM返回的原始响应
            self._log_json("LLM RAW RESPONSE", response_text)
            
            if self.dev_mode:
                print("\n" + "="*80)
                print("[DEV] LLM RAW RESPONSE:")
                print(response_text)
                print("="*80 + "\n")
            
            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                error_msg = f"Error: LLM response is not valid JSON: {response_text}"
                self._log_info(error_msg)
                if self.dev_mode:
                    print(f"[DEV] {error_msg}")
                return {
                    "action": "error",
                    "message": "I apologize, but I encountered an error processing your request.",
                    "next_state": "error",
                    "require_input": "1"  # Default to requiring input after an error
                }
        except Exception as e:
            error_msg = f"Error calling LLM API: {e}"
            self._log_info(error_msg)
            if self.dev_mode:
                print(f"[DEV] {error_msg}")
            return {
                "action": "error",
                "message": f"Error occurred: {str(e)}",
                "next_state": "error",
                "require_input": "1"  # Default to requiring input after an error
            }
    
    def run(self, user_input: str = None):
        """
        Run the agent's main loop, processing the user input and transitioning between states.
        
        Args:
            user_input: Initial user input to start the conversation
        """
        if user_input:
            self.conversation_history.append({"role": "user", "content": user_input})
            self._log_json("Initial user input", {"role": "user", "content": user_input})
            if self.dev_mode:
                print(f"[DEV] Initial user input: {user_input}")
        
        loop_count = 0
        
        while True:
            loop_count += 1
            self._log_info(f"===== LOOP #{loop_count} =====")
            
            # Get current state configuration
            state_config = self.config["states"].get(self.current_state)
            if not state_config:
                error_msg = f"Error: State '{self.current_state}' not found in configuration"
                self._log_info(error_msg)
                if self.dev_mode:
                    print(f"[DEV] {error_msg}")
                print(error_msg)
                break
            
            self._log_info(f"Current state: {self.current_state}")
            self._log_info(f"Allowed transitions: {state_config.get('transitions', [])}")
            
            if self.dev_mode:
                print(f"[DEV] Current state: {self.current_state}")
                print(f"[DEV] Allowed transitions: {state_config.get('transitions', [])}")
            
            # Call LLM with the state's prompt
            prompt = state_config["prompt"]
            temperature = state_config.get("temperature", 0.7)
            model = state_config.get("model", "llama3-70b-8192")
            
            response = self._call_llm(prompt, temperature, model)
            
            # Extract response components
            action = response.get("action", "")
            message = response.get("message", "")
            next_state = response.get("next_state", "")
            require_input = response.get("require_input", "1")  # Default to requiring input if not specified
            
            self._log_info(f"LLM decided action: {action}")
            self._log_info(f"LLM next state: {next_state}")
            self._log_info(f"LLM require_input: {require_input}")
            
            if self.dev_mode:
                print(f"[DEV] LLM decided action: {action}")
                print(f"[DEV] LLM next state: {next_state}")
                print(f"[DEV] LLM require_input: {require_input}")
            
            # Add assistant's message to conversation history
            self.conversation_history.append({"role": "assistant", "content": message})
            
            # 记录助手的回复
            self._log_json("Assistant reply", {"role": "assistant", "content": message})
            
            # Display the message to the user
            print(f"Agent: {message}")            
                
            # Execute the action if it exists
            if action and action in self.available_actions:
                # Extract any action parameters from the response
                action_params = response.get("action_params", {})
                self._log_json(f"Executing action: {action}", action_params)
                if self.dev_mode:
                    print(f"[DEV] Executing action: {action}")
                    print(f"[DEV] Action parameters: {action_params}")
                
                action_result = self.available_actions[action](action_params)
                self._log_info(f"Action result: {action_result}")
                
                # Handle action results differently based on action type
                if action_result:
                    if action == "search":
                        # Add search results to search history
                        self.search_history.append(action_result)
                        self._log_info(f"Search result added to search history")
                        if self.dev_mode:
                            print(f"[DEV] Search result added to search history")
                    else:
                        # For other actions, add to conversation history
                        self.conversation_history.append({
                            "role": "system", 
                            "content": f"Action result: {action_result}"
                        })
                        self._log_json("Action result added to conversation", {
                            "role": "system", 
                            "content": f"Action result: {action_result}"
                        })
                    
                    if self.dev_mode:
                        print(f"[DEV] Action result: {action_result}")
            
            # Check if the next state is valid
            allowed_transitions = state_config.get("transitions", [])
            if next_state in self.config["states"] and (not allowed_transitions or next_state in allowed_transitions):
                self._log_info(f"Transitioning from '{self.current_state}' to '{next_state}'")
                if self.dev_mode:
                    print(f"[DEV] Transitioning from '{self.current_state}' to '{next_state}'")
                self.current_state = next_state
            else:
                error_msg = f"Error: Invalid transition from '{self.current_state}' to '{next_state}'"
                self._log_info(error_msg)
                if self.dev_mode:
                    print(f"[DEV] {error_msg}")
                print(error_msg)
                self.current_state = "error"
            
            # Check if this is a terminal state
            if next_state == "exit" or next_state == "":
                self._log_info("Reached terminal state, exiting.")
                if self.dev_mode:
                    print("[DEV] Reached terminal state, exiting.")
                break            

            # Check if user input is required before next iteration
            if require_input == "1":
                # Get user input for the next iteration
                user_input = input("You: ")
                self.conversation_history.append({"role": "user", "content": user_input})
                self._log_json("User input", {"role": "user", "content": user_input})
                if self.dev_mode:
                    print(f"[DEV] User input: {user_input}")
            else:
                self._log_info("No user input required, proceeding to next state automatically")
                if self.dev_mode:
                    print("[DEV] No user input required, proceeding to next state automatically")
            