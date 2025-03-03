from utils.logger import setup_logger
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from agents.menu_cleaner import QueryQuantitativa
from utils.langgraph import State
import os

# Creiamo il logger per questo modulo
logger = setup_logger("query_quantitativa")

os.environ.get("OPENAI_API_KEY")

llm = ChatOpenAI(model="gpt-4o", temperature=0)

template = """
Istruzioni: {instructions}
user_message: {user_message}
"""
structured_llm = llm.with_structured_output(QueryQuantitativa)

# Funzione per interpretare la query usando ChatOpenAI
def agent_query_quantitativa(state: State) -> State:
    prompt = PromptTemplate.from_template(template)
    formatted_prompt = prompt.format(
        instructions=state['prompt_message_quantitativo'],
        user_message=state['user_message'],
    )
    result = structured_llm.invoke(formatted_prompt)
    logger.info(f"Risultato della query quantitativa: {result}")
    state['user_message_quantitativo'] = str(result)
    return state