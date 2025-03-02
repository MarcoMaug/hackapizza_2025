from utils.logger import setup_logger
from langchain_openai import ChatOpenAI
from agents.menu_cleaner import Menu
from langchain.prompts import PromptTemplate
from utils.langgraph import State
import os
import ast
import json
from langchain_openai.chat_models.base import OpenAIRefusalError


# Creiamo il logger per questo modulo
logger = setup_logger("filtro_licenze_ingredienti")

os.environ.get("OPENAI_API_KEY")

llm = ChatOpenAI(model="gpt-4o")
structured_llm = llm.with_structured_output(Menu)

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
    all_menus = ast.literal_eval(state['filtro_distanze_menu'])
    filtered_menus = []

    for menu in all_menus:
        formatted_prompt = prompt.format(
            instructions=state['prompt_filtro_licenze_ingredienti'],
            user_message=state['user_message_quantitativo'],
            menu=menu
        )
        
        try:
            result = structured_llm.invoke(formatted_prompt)
            menu = result.json()
            menu = json.loads(menu)
            try:
                logger.debug(f"Risultato type: {type(menu)}")
                if menu['piatti'] != []:
                    logger.debug(f"Risultato type bis: {type(menu)}")
                    filtered_menus.append(menu)
                    logger.info(f"piatti che soddisfano i criteri: {menu}")
            except Exception as e:
                logger.error(f"Errore nell'interpretazione del risultato per il menu {menu}: {e}")
        except OpenAIRefusalError as e:
            logger.error(f"OpenAI ha rifiutato la richiesta per il menu {menu}.")
            

    state['output_filtro_licenze_ingredienti'] = str(filtered_menus)
    return state