import fitz  # PyMuPDF
import os
from utils.logger import setup_logger
from langchain_openai import ChatOpenAI
import os
from pydantic import BaseModel, Field 
from typing import List, Optional
import json

class TecnicaCucina(BaseModel):
    tecnica_generale: str = Field(..., description="Categoria generale della tecnica di cucina più generale della famiglia")
    tecnica_famiglia: str = Field(..., description="la famiglia della tecnica")
    tecnica_specifica: Optional[str] = Field(None, description="tecnica specifica")

class EstrazioneTecincheCucina(BaseModel):
    tecniche: List[TecnicaCucina] = Field(
        ..., 
        description="Lista delle tecniche di cucina estratte dal testo"
    )


logger = setup_logger("estrai_manuale_cucina")

os.environ.get("OPENAI_API_KEY")

llm = ChatOpenAI(model="gpt-4o", temperature=0)
structured_llm = llm.with_structured_output(EstrazioneTecincheCucina)

prompt="""Estrai le varie tecniche specifiche di cucina, sono a tema spaziale e di fantasia, indicando la famiglia della tecnica e la tecnica generale
             """


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

def estrazione_manuale_cucina(pdf_path, output_file):
    text = extract_text_from_pdf(pdf_path)

    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": text}
    ]

    logger.info(f"Prompt and text prepared for LLM for file {pdf_path}: {messages}")

    result = structured_llm.invoke(messages)
    result_dict = result.dict() 

    with open(output_file, 'w') as f:
        json.dump(result_dict, f, ensure_ascii=False, indent=4)
    logger.info(f"All results written to {output_file}")