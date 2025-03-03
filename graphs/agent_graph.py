from langgraph.graph import StateGraph, START, END
from agents.filtro_distanze import agent_find_menu_distanze
from agents.filtro_licenze_ingredienti import agent_filtro_licenze_ingredienti
from agents.query_quantitativa import agent_query_quantitativa
from agents.rag import retrieve, generate_rag
from agents.detect_actions import detect_actions
from utils.langgraph import State
from utils.logger import setup_logger
import time

logger = setup_logger("agent_graph")


def is_filtro_distanze(state):
    logger.info(f"routing_filtro_distanze: {state['routing']['filtro_distanze']}")
    if state['routing']['filtro_distanze'] is True:
        return "filtro_distanze"
    else:
        return "is_filtro_licenze_ingredienti_condition"


def is_filtro_licenze_ingredienti(state):
    logger.info(f"routing_filtro_licenze_ingredienti: {state['routing']['filtro_licenze_ingredienti']}")
    if state['routing']['filtro_licenze_ingredienti'] is True:
        return "query_quantitativa"
    else:
        return "is_generate_rag_condition"


def is_generate_rag(state):
    logger.info(f"routing_generate_rag: {state['routing']['generate_rag']}")
    if state['routing']['generate_rag'] is True:
        return "retrieve"
    else:
        return "END"

def nothing1(state):
    return state

def nothing2(state):
    return state


# Creazione del grafo con stato definito
graph_builder = StateGraph(State)

# Aggiunta dei nodi con le funzioni che aggiornano lo stato
graph_builder.add_node("detect_actions", detect_actions)
#graph_builder.add_node("is_filtro_distanze_condition", is_filtro_distanze)
graph_builder.add_node("filtro_distanze", agent_find_menu_distanze)
graph_builder.add_node("nothing1", nothing1)
graph_builder.add_node("nothing2", nothing2)
#graph_builder.add_node("is_filtro_licenze_ingredienti_condition", is_filtro_licenze_ingredienti)
graph_builder.add_node("query_quantitativa", agent_query_quantitativa)
graph_builder.add_node("filtro_licenze_ingredienti", agent_filtro_licenze_ingredienti)
#graph_builder.add_node("is_generate_rag_condition", is_generate_rag)
graph_builder.add_node("retrieve", retrieve)
graph_builder.add_node("generate_rag", generate_rag)

# Connessione iniziale
graph_builder.add_edge(START, "detect_actions")
#graph_builder.add_edge("detect_actions", "is_filtro_distanze_condition")

# Prima condizione
graph_builder.add_conditional_edges(
    "detect_actions",
    is_filtro_distanze,
    {
        "filtro_distanze": "filtro_distanze",
        "is_filtro_licenze_ingredienti_condition": "nothing1"
    }
)

# Dopo aver eseguito filtro_distanze, vai comunque alla seconda condizione
graph_builder.add_edge("filtro_distanze", "nothing1")

# Seconda condizione
graph_builder.add_conditional_edges(
    "nothing1",
    is_filtro_licenze_ingredienti,
    {
        "query_quantitativa": "query_quantitativa",
        "is_generate_rag_condition": "nothing2"
    }
)

# Dopo query_quantitativa, esegui filtro_licenze_ingredienti
graph_builder.add_edge("query_quantitativa", "filtro_licenze_ingredienti")

# Dopo aver eseguito filtro_licenze_ingredienti, vai alla terza condizione
graph_builder.add_edge("filtro_licenze_ingredienti", "nothing2")

# Terza condizione
graph_builder.add_conditional_edges(
    "nothing2",
    is_generate_rag,
    {
        "retrieve": "retrieve",
        "END": END
    }
)

# Processo RAG
graph_builder.add_edge("retrieve", "generate_rag")
graph_builder.add_edge("generate_rag", END)

# Compilazione del grafo
app = graph_builder.compile()


output_path = './diagram.png'
attempts = 3
for attempt in range(attempts):
    try:
        with open(output_path, 'wb') as f:
            f.write(app.get_graph().draw_mermaid_png())
        logger.info(f"Graph successfully saved to {output_path}")
        break
    except Exception as e:
        logger.error(f"Attempt {attempt + 1} failed: {e}")
        if attempt < attempts - 1:
            time.sleep(1)
        else:
            logger.error("All attempts to save the graph failed.")