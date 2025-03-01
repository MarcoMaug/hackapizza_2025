from langgraph.graph import StateGraph, START, END
from agents.interpreter import interpret_query
from agents.planet_finder import find_closest_planets
from utils.langgraph import State


# Creazione del grafo con stato definito
graph_builder = StateGraph(State)
graph_builder.add_edge(START, "interpret")
# Aggiunta dei nodi con le funzioni che aggiornano lo stato
graph_builder.add_node("interpret", interpret_query)
graph_builder.add_node("find_closest", find_closest_planets)

# Definizione delle transizioni
graph_builder.add_edge("interpret", "find_closest")


graph_builder.add_edge("find_closest", END)
# Compilazione del grafo
app = graph_builder.compile()

# Esecuzione del grafo
input_data = {"messages": "Dimmi i 5 pianeti più vicini alla Terra"}
output = app.invoke(input_data)