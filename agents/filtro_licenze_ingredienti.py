from utils.logger import setup_logger
from langchain_openai import ChatOpenAI
from agents.menu_cleaner import Menus
from langchain.prompts import PromptTemplate
from utils.langgraph import State
import os
import json

# Creiamo il logger per questo modulo
logger = setup_logger("filtro_licenze_ingredienti")

os.environ.get("OPENAI_API_KEY")

llm = ChatOpenAI(model="gpt-4o")
structured_llm = llm.with_structured_output(Menus)

template = """
Istruzioni: {instructions}
user_message: {user_message}
Menu: {menu}
"""

def rimuovi_menu_senza_piatti(menus):
    new_menus = []
    for menu in menus:
        if menu['piatti']!=[]:
            new_menus.append(menu)
    return new_menus

# Funzione per interpretare la query usando ChatOpenAI
def agent_filtro_licenze_ingredienti(state: State) -> State:
    prompt = PromptTemplate.from_template(template)
    formatted_prompt = prompt.format(
        instructions=state['prompt_filtro_licenze_ingredienti'],
        user_message=state['user_message'],
        menu=state['filtro_distanze_menu']
    )
    result = structured_llm.invoke(formatted_prompt)
    try:
        menus = result.json()
        menus = json.loads(menus)
        menus = rimuovi_menu_senza_piatti(menus['menus'])
        logger.info(f"piatti che soddisfano i criteri: {menus}")
    except Exception as e:
        menus = {}
        logger.error(f"Errore nell'interpretazione del risultato: {e}")
        state['filtro_distanze_menu'] = str(menus)
    return state