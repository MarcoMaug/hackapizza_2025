from langgraph.graph import StateGraph, START, END
from agents.filtro_distanze import agent_find_menu
from utils.langgraph import State
import uuid

from langchain_core.chat_history import InMemoryChatMessageHistory

chats_by_session_id = {}


def get_chat_history(session_id: str) -> InMemoryChatMessageHistory:
    chat_history = chats_by_session_id.get(session_id)
    if chat_history is None:
        chat_history = InMemoryChatMessageHistory()
        chats_by_session_id[session_id] = chat_history
    return chat_history

# Creazione del grafo con stato definito
graph_builder = StateGraph(State)
graph_builder.add_edge(START, "filtro_distanze")
# Aggiunta dei nodi con le funzioni che aggiornano lo stato
graph_builder.add_node("filtro_distanze", agent_find_menu)

graph_builder.add_edge("filtro_distanze", END)
# Compilazione del grafo
app = graph_builder.compile()
