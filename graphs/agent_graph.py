from langgraph.graph import StateGraph, START, END
from agents.filtro_distanze import agent_find_menu 
from agents.filtro_licenze_ingredienti import agent_filtro_licenze_ingredienti
from utils.langgraph import State

# Creazione del grafo con stato definito
graph_builder = StateGraph(State)

# Aggiunta dei nodi con le funzioni che aggiornano lo stato
graph_builder.add_node("filtro_distanze", agent_find_menu)
graph_builder.add_node("filtro_licenze_ingredienti", agent_filtro_licenze_ingredienti)


graph_builder.add_edge(START, "filtro_distanze")
graph_builder.add_edge("filtro_distanze", "filtro_licenze_ingredienti")
graph_builder.add_edge("filtro_licenze_ingredienti", END)

# Compilazione del grafo
app = graph_builder.compile()
