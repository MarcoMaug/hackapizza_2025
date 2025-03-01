from utils.logger import setup_logger
from utils.langgraph import State
import pandas as pd

logger = setup_logger("planet_finder")

df = pd.read_csv("data/Distanze.csv", index_col=0)


def find_closest_planets(state: State) -> State:
    # Ricerca dei pianeti più vicini e aggiunta a 'messages'
    closest_planets = ["Venere", "Marte", "Giove"]
    new_message = f"Trova i pianeti più vicini a {state['messages']}: {', '.join(closest_planets)}"
    state["messages"].append(new_message)
    return state
