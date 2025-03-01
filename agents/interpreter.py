from utils.logger import setup_logger
from utils.langgraph import State

# Creiamo il logger per questo modulo
logger = setup_logger("interpreter")

def interpret_query(state: State) -> State:
    # Interpretazione della query e aggiunta a 'messages'
    new_message = f"Interpretando la query: {state['messages']}"
    state["messages"].append(new_message)
    return state

