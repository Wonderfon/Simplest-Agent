import os
from dotenv import load_dotenv
from agent import AIAgent
import requests

# Load environment variables from .env file
load_dotenv()

def search_function(params):
    """
    Function that uses SearxNG to search the web for information.
    
    Args:
        params (dict): Dictionary containing the search parameters,
                      with at least a "query" key.
    
    Returns:
        str: Formatted search results or error message.
    """
    
    
    query = params.get("query", "")
    if not query:
        return "Error: No search query provided."
    
    # Define the SearxNG API endpoint
    base_url = 'https://search.bostonlistener-career.org/search'
    
    # Define the search query parameters
    post_data = {
        "q": query,
        "format": "json",
    }
    
    try:
        # Make the POST request
        response = requests.post(base_url, data=post_data)
        
        # Check response status and format results
        if response.status_code == 200:
            search_results = response.json()
            
            # Format the results
            formatted_results = ""
            
            if 'results' in search_results and search_results['results']:
                formatted_results = "Search Results:\n\n"
                
                # Take the top 5 results or fewer if less are available
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

def calculate_function(params):
    """
    Mock calculation function that would be called when the action is "calculate".
    In a real implementation, this could perform more complex calculations.
    """
    expression = params.get("expression", "")
    print(f"Calculating: {expression}")
    try:
        result = eval(expression)
        return f"Result: {result}"
    except Exception as e:
        return f"Could not calculate expression: {str(e)}"

# Usage example
if __name__ == "__main__":
    # Get openrouter API key from environment variable or prompt the user
    openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
    
    if not openrouter_api_key:
        openrouter_api_key = input("Please enter your openrouter API key: ")
        if not openrouter_api_key:
            print("Error: openrouter API key is required.")
            exit(1)
    
    # Prompt user for dev mode
    dev_mode_input = input("Enable development mode with detailed logging? (y/n): ").strip().lower()
    dev_mode = dev_mode_input in ['y', 'yes']
    
    if dev_mode:
        print("Starting agent in DEVELOPMENT mode - detailed logs will be shown")
    
    # Create the agent with the API key and dev mode flag
    agent = AIAgent("agent_config.toml", api_key=openrouter_api_key, dev_mode=dev_mode)
    
    # Register available actions
    agent.register_action("search", search_function)
    agent.register_action("calculate", calculate_function)
    
    # Start the agent with an initial user input
    agent.run("Hello, I need some help.")