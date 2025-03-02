from utils.logger import setup_logger
from graphs.agent_graph import app
from agents.menu_cleaner import extract_pdfs
from fuzzywuzzy import fuzz
import os
import json
import ast

logger = setup_logger("main")


def partial_ratio_similarity(s1, s2):
    # partial_ratio trova la miglior sottostringha corrispondente
    return fuzz.partial_ratio(s1.lower(), s2.lower()) / 100.0

def estrai_piatti_menu(menus):
    path_dish_mapping = "./data/dish_mapping.json"
    with open(path_dish_mapping, 'r') as f:
        dish_mapping = json.load(f)
    
    piatti_num = []
    for menu in menus:
        for piatto in menu['piatti']:
            try:
                piatti_num.append(dish_mapping[piatto['nome_piatto']])
            except KeyError:
                logger.warning(f"KeyError: {piatto['nome_piatto']} not found in dish_mapping.")
                # Find the most similar key if exact match is not found
                
                similar_key = max(dish_mapping.keys(), 
                                  key=lambda k, piatto=piatto: partial_ratio_similarity(k, piatto['nome_piatto']))
                
                logger.info(f"Substituting '{piatto['nome_piatto']}' with closest match: '{similar_key}'")
                piatti_num.append(dish_mapping[similar_key])
    
    return piatti_num


json_input_menu_estratti = "./data/menu_estratti.json"
if not os.path.exists(json_input_menu_estratti):
    extract_pdfs("./data/menu", json_input_menu_estratti)


logger.info("Starting AI pipeline...")


user_message = "Quali piatti possono essere trovati, preparati da uno chef con almeno la licenza P di grado 5, che includono Teste di Idra o che sono realizzati utilizzando la tecnica della Bollitura Entropica Sincronizzata?"
prompt_filtro_licenze_ingredienti = """rimuovi dai menu indicati i piatti che NON soddisfano i criteri presenti nella richiesta.
                                        fai molta attenzione alla condizione sulla licenza della chef e sul suo livello se la licenza non soddisfa i criteri non considerare nessun piatto.
                                        non inventare piatti che non sono presenti nel menu"""
output = app.invoke({
    "user_message": user_message,
    "prompt_message_quantitativo":"""estrai solo le informazioni quantitative e le condizioni e trasormale in pseudo-codice fai attenzione agli ingredienti, alle licenze e alle tecniche da utilizzare.
                                        Considera che l'utente può abbbreviare i nomi delle licenze: licenza Q = licenza Quantistica;
                                        licenza t = licenza Temporale; licenza p = licenza Psionica; licenza g = licenza Gravitazionale;
                                        licenza Mx = licenza magnetica; licenza e+ = licenza antimateria. traducile con il loro nome completo.
                                        Genera output di questo tipo CONDIZIONI:
                                            1. Lo chef deve avere almeno la licenza Psionica di grado 5.
                                            2. Il piatto deve soddisfare almeno una delle seguenti condizioni:
                                                a. Contenere l'ingrediente "Teste di Idra".
                                                b. Essere realizzato con la tecnica "Bollitura Entropica Sincronizzata""",
    "user_message_quantitativo": "",
    "filtro_distanze_menu": "",
    "prompt_filtro_licenze_ingredienti": prompt_filtro_licenze_ingredienti,
    "output_filtro_licenze_ingredienti": ""
})

logger.info(f"Pipeline output: {output}")
logger.info(f"Pipeline output type: {type(output)}")
logger.info(f"Pipeline output_filtro_licenze_ingredienti: {output['output_filtro_licenze_ingredienti']}")
menus = ast.literal_eval(output['output_filtro_licenze_ingredienti'])
logger.info(f"menu che soddisfano i criteri: {menus}")

piatti_num = estrai_piatti_menu(menus)
logger.info(f"piatti che soddisfano i criteri: {piatti_num}")

output_path = './diagram.png'
with open(output_path, 'wb') as f:
    f.write(app.get_graph().draw_mermaid_png()) 
