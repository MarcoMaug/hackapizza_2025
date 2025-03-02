from utils.logger import setup_logger
from graphs.agent_graph import app
from agents.menu_cleaner import extract_pdfs
import os

logger = setup_logger("main")

json_input_menu_estratti = "./data/menu_estratti.json"
if not os.path.exists(json_input_menu_estratti):
    extract_pdfs("./data/menu", json_input_menu_estratti)


logger.info("Starting AI pipeline...")


user_message = "Quali piatti possono essere trovati, preparati da uno chef con almeno la licenza P di grado 5, che includono Teste di Idra o che sono realizzati utilizzando la tecnica della Bollitura Entropica Sincronizzata?"
prompt_filtro_licenze_ingredienti = """rimuovi dai menu indicati i piatti che NON soddisfano i criteri presenti nell'user message. 
                                        Considera che l'utente può abbbreviare i nomi delle licenze: licenza Q = licenza Quantistica;
                                        licenza t = licenza Temporale; licenza p = licenza Psionica; licenza g = licenza Gravitazionale;
                                        licenza Mx = licenza magnetica; licenza e+ = licenza antimateria.
                                        Fai attenzione alle condizioni di 'e' e 'o' presenti nell'user message."""
output = app.invoke({
    "user_message": user_message,
    "prompt_message_quantitativo":"Trasforma la richiesta dell'utente in un messaggio quantitativo, metti in evidenza le condizioni",
    "user_message_quantitativo": "",
    "filtro_distanze_menu": "",
    "prompt_filtro_licenze_ingredienti": prompt_filtro_licenze_ingredienti,
    "filtro_licenze_ingredienti": "Questo è il prompt aggiuntivo per il secondo agente",
    "output_filtro_licenze_ingredienti": ""
})


output_path = './diagram.png'
with open(output_path, 'wb') as f:
    f.write(app.get_graph().draw_mermaid_png()) 


logger.info(f"Pipeline output: {output}")
