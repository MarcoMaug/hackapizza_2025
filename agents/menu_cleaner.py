import fitz  # PyMuPDF
import os
from utils.logger import setup_logger
from langchain_openai import ChatOpenAI
import os
from pydantic import BaseModel, Field
from typing import List
import json

class DetectAction(BaseModel):
    filtro_distanze: bool = Field(..., description="l'utente fa una richiesta con delle distanze da considerare")
    filtro_licenze_ingredienti: bool = Field(..., description="l'utente fa una richiesta con delle licenze e/o ingredienti e/o delle tecniche modalità, di cottura da considerare")
    generate_rag: bool = Field(..., description="rag è necessario quando l'utente chiede qualcosa sui limiti di alcuni ingredienti o requisiti generici che non rientrano nelle casistiche precedenti o informazioni sugli Ordini di Andromeda, dei Naturalisti e degli Armonisti")

    def set_field(self, field_name: str, value: bool):
        if hasattr(self, field_name):
            setattr(self, field_name, value)
        else:
            raise ValueError(f"Field {field_name} does not exist in DetectAction")

    def to_dict(self):
        return self.model_dump()


class QueryQuantitativa(BaseModel):
    query: str = Field(..., description="La query dell'utente in forma pseudo-codice")

class Piatto(BaseModel):
    nome_piatto: str = Field(..., description="Il nome del piatto")
    ingredienti: List[str] = Field(default_factory=list, description="Lista degli ingredienti")
    tecniche: List[str] = Field(default_factory=list, description="Lista delle tecniche di preparazione")

class Licenza(BaseModel):
    nome_licenza: str = Field(..., description="Il nome della licenza")
    livello: int = Field(default_factory=int, description="Livello della licenza, potrebbe essere scritta con i numeri romani, converti in intero")

class Menu(BaseModel):
    nome_ristorante: str = Field(..., description="Il nome del ristorante")
    chef: str = Field(..., description="Nome dello chef")
    nome_pianeta: str = Field(..., description="Nome del pianeta")
    nome_menu: str = Field(..., alias="nome menu", description="Nome del menu")
    licenze_chef: List[Licenza] = Field(..., default_factory=list, description="Licenze possedute dallo chef del ristorante")
    piatti: List[Piatto] = Field(..., default_factory=list, description="Lista dei piatti nel menu")

class Menus(BaseModel):
    menus: List[Menu] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "required": ["nome_ristorante", "chef", "nome_pianeta", "nome_menu", "licenze_chef", "piatti"]
        }


logger = setup_logger("menu_cleaner")

os.environ.get("OPENAI_API_KEY")

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
structured_llm = llm.with_structured_output(Menu)

prompt="Estrai dal testo le seguenti inforazioni utili"


# Funzione per estrarre il testo dal PDF
def extract_text_from_pdf(pdf_path):
    logger.info(f"Starting to extract text from {pdf_path}")
    text = ""
    try:
        with fitz.open(pdf_path) as doc:
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text += page.get_text()
        logger.info(f"Text extraction from {pdf_path} completed successfully.")
    except Exception as e:
        logger.error(f"Error extracting text from {pdf_path}: {e}")
    return text


def extract_pdfs(pdf_directory, output_file):
    all_results = []
    
    for filename in os.listdir(pdf_directory):
        logger.info(f"file {filename}.")
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(pdf_directory, filename)
            text = extract_text_from_pdf(pdf_path)
            
            if not text:
                logger.warning(f"No text extracted from {pdf_path}.")
                continue

            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": text}
            ]
            
            logger.info(f"Prompt and text prepared for LLM for file {filename}: {messages}")

            result = structured_llm.invoke(messages)
            result_dict = result.dict() 
            all_results.append(result_dict)
    
    with open(output_file, 'w') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=4)
    logger.info(f"All results written to {output_file}")