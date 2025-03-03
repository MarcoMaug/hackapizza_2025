
from utils.logger import setup_logger
from pydantic import BaseModel, Field
from typing import Optional
import pandas as pd
import json
from langchain_openai import ChatOpenAI
from utils.langgraph import State
import os



class Riferimento(BaseModel):
    pianeta_riferimento: Optional[str] = Field(None, description="Il pianeta di riferimento")
    max_distance: Optional[float] = Field(None, description="La distanza massima")

# Creiamo il logger per questo modulo
logger = setup_logger("filtro_distanze")

os.environ.get("OPENAI_API_KEY")

llm = ChatOpenAI(model="gpt-4o-mini" , temperature=0)
structured_llm = llm.with_structured_output(Riferimento)

# Funzione per caricare i dati dai file
def load_data():
    # Carica il CSV come matrice delle distanze tra pianeti.
    # Il CSV ha una struttura dove la prima riga contiene i nomi dei pianeti
    # e la prima colonna (index) contiene lo stesso insieme di nomi.
    distanze = pd.read_csv("./data/Distanze.csv", index_col=0)
    return distanze

# Funzione per interpretare la query usando ChatOpenAI
def filtro_distanze(messages):
    prompt = "Individua il pianeta di riferimento e la distanza massima indicata dall'utente. Se non sono presenti valorizza i campi di output come None"
    result = structured_llm.invoke(f"Istruzioni:{prompt}. user_message: {messages}")
    try:
        criteria = result.dict() 
        logger.info(f"Risultato pianeta e distanza max: {criteria}")
    except Exception as e:
        # Se l'LLM non restituisce un JSON valido, si usano dei valori di default (nessun filtro)
        criteria = {"reference_planet": None, "max_distance": None}
        logger.error(f"Errore nell'interpretazione del risultato: {e}")
    return criteria

# Funzione per filtrare i ristoranti in base alla query e alla matrice delle distanze
def find_matching_menu(messages, distanze):
    criteria = filtro_distanze(messages)
    reference_planet = criteria.get("pianeta_riferimento")
    max_distance = criteria.get("max_distance")
    if reference_planet is None:
        reference_planet = "Tatooine"
        max_distance = 9999999
    
    try:
        # Ottieni le distanze dal pianeta di riferimento dalla matrice CSV
        distances_from_ref = distanze.loc[reference_planet]
        # Seleziona i pianeti che sono entro la distanza massima specificata
        valid_planets = distances_from_ref[distances_from_ref <= max_distance].index.tolist()
    except Exception as e:
        logger.error(f"Errore nel filtrare i pianeti: {e}")
        valid_planets = []
    logger.info(f"Pianeti validi: {valid_planets}")
    # Carica il JSON dei menu estratti
    with open("./data/menu_estratti.json", "r") as f:
        menu_estratti = json.load(f)
    
    # Filtra i menu che si trovano nei pianeti validi
    matching_menus = [menu for menu in menu_estratti if menu["nome_pianeta"] in valid_planets]
    
    return matching_menus

# Funzione agente per LangGraph
def agent_find_menu_distanze(state: State) -> State:
    messages = state["user_message"]
    logger.info(f"Query: {messages}")
    distanze = load_data()
    menu = find_matching_menu(messages, distanze)
    logger.info(f"menu filtrati: {menu}")
    state["final_response"] = str(menu)
    state['routing']['filtro_distanze'] = False
    return state

