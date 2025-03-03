from utils.logger import setup_logger
from langchain_community.document_loaders import PyPDFLoader, BSHTMLLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI
from agents.menu_cleaner import Menu
from langchain_openai.chat_models.base import OpenAIRefusalError
from utils.langgraph import State
from langchain.prompts import PromptTemplate
import os
import ast
import json

logger = setup_logger("rag")


html_loader1 = BSHTMLLoader("./data/documents_raw/blog_etere_del_gusto.html", bs_kwargs={"features": "html.parser"})
html_loader2 = BSHTMLLoader("./data/documents_raw/blog_sapore_del_dune.html", bs_kwargs={"features": "html.parser"})
pdf_loader = PyPDFLoader("./data/documents_raw/Codice Galattico.pdf")

html_doc1 = html_loader1.load()
html_doc2 = html_loader2.load()
pdf_doc = pdf_loader.load()


# Dividi SOLO il documento PDF in chunks
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
pdf_splits = text_splitter.split_documents(pdf_doc)

# Combina i documenti HTML interi con i chunks del PDF
all_docs = html_doc1 + html_doc2 + pdf_splits

# Crea embeddings e vectorstore
embeddings = OpenAIEmbeddings()
vectorstore = Chroma.from_documents(documents=all_docs, embedding=embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})


def retrieve(state: State) -> State:
    query = state["output_filtro_licenze_ingredienti"]
    context_docs = retriever.invoke(query)
    context_text = "\n\n".join([doc.page_content for doc in context_docs])
    state['context'] = context_text
    return state


template = """
Istruzioni: {instructions}

Contesto:
{context}

Domanda:
{query}

Menu: {menu}
"""
prompt = PromptTemplate.from_template(template)

# Creiamo il logger per questo modulo

os.environ.get("OPENAI_API_KEY")

llm = ChatOpenAI(model="gpt-4o", temperature=0)
structured_llm = llm.with_structured_output(Menu)


def generate_rag(state: State) -> State:
    logger.debug(f"Stato: {state}")
    all_menus = ast.literal_eval(state['final_response'])
    filtered_menus = []
    for menu in all_menus:

        formatted_prompt = prompt.format(
            instructions=state['prompt_rag'],
            query=state['user_message'],
            context = state["context"],
            menu=menu
        )
        
        try:
            result = structured_llm.invoke(formatted_prompt)
            menu = result.json()
            menu = json.loads(menu)
            try:
                logger.debug(f"Risultato type: {type(menu)}")
                if menu['piatti'] != []:
                    filtered_menus.append(menu)
                    logger.info(f"piatti che soddisfano i criteri: {menu}")
            except Exception as e:
                logger.error(f"Errore nell'interpretazione del risultato per il menu {menu}: {e}")
        except OpenAIRefusalError as e:
            logger.error(f"OpenAI ha rifiutato la richiesta per il menu {menu}.")
    logger.debug(f"filtered_menus: {filtered_menus}")
    state['final_response'] = str(filtered_menus)
    logger.debug(f"Stato finale: {state['final_response']}")
    state['routing']['generate_rag'] = False
    logger.debug(f"Stato: {state}")
    return state