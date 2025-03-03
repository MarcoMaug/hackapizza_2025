from utils.logger import setup_logger
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from agents.menu_cleaner import DetectAction
from utils.langgraph import State
import json
import os

# Creiamo il logger per questo modulo
logger = setup_logger("detect_actions")

os.environ.get("OPENAI_API_KEY")

llm = ChatOpenAI(model="gpt-4o", temperature=0)

template = """
Istruzioni: determina se la query necessita di un filtro_distanze, filtro_licenze_ingredienti, oppure di rag. 
rag è necessario quando l'utente chiede qualcosa sui limiti di alcuni ingredienti o requisiti generici che 
non rientrano nelle casistiche precedenti. come ad esempio delle condizioni o informazioni sugli Ordini 
di Andromeda, dei Naturalisti e degli Armonisti
user_message: {user_message}
"""
structured_llm = llm.with_structured_output(DetectAction)

# Funzione per interpretare la query usando ChatOpenAI
def detect_actions(state: State) -> State:
    prompt = PromptTemplate.from_template(template)
    formatted_prompt = prompt.format(
        user_message=state['user_message'],
    )
    result = structured_llm.invoke(formatted_prompt)
    actions = result.to_dict()
    logger.info(f"Risultato di detect_actions: {actions}")

    state['routing'] = actions
    return state
