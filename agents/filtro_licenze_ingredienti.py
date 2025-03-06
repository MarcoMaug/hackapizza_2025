from utils.logger import setup_logger
from utils.langgraph import State
import ast
from langchain_openai.chat_models.base import OpenAIRefusalError
import json
from typing import List, Dict, Any
from difflib import SequenceMatcher
from typing import Dict, Any, List, Union
import traceback



# Creiamo il logger per questo modulo
logger = setup_logger("filtro_licenze_ingredienti")

SIMILARITY_THRESHOLD = 0.75
def calcola_similarita(stringa1: str, stringa2: str) -> float:
    """
    Calcola la similarità tra due stringhe usando SequenceMatcher.
    
    Args:
        stringa1 (str): Prima stringa da confrontare
        stringa2 (str): Seconda stringa da confrontare
    
    Returns:
        float: Percentuale di similarità (0-1)
    """
    return SequenceMatcher(None, stringa1.lower(), stringa2.lower()).ratio()

def normalizza_query(
    dati_input: Dict[str, Any], 
    liste_uniche: Dict[str, List[Any]], 
    soglia_similarita: float = 0.8
) -> Dict[str, Any]:
    """
    Normalizza le entità confrontandole con le liste uniche.
    
    Args:
        dati_input (Dict): Dati da normalizzare
        liste_uniche (Dict): Dizionario con le liste di riferimento
        soglia_similarita (float): Soglia di similarità per la normalizzazione
    
    Returns:
        Dict: Dati normalizzati
    """
    dati_normalizzati = dati_input.copy()
    
    # Mappe di normalizzazione per ogni categoria
    mappe_normalizzazione = {
        'ingredienti_inclusi': liste_uniche['ingredienti'],
        'ingredienti_esclusi': liste_uniche['ingredienti'],
        'tecniche_incluse': liste_uniche['tecniche'],
        'tecniche_escluse': liste_uniche['tecniche'],
        'licenze_chef': liste_uniche['licenze_chef']
    }
    
    # Normalizzazione per ogni categoria
    for categoria, lista_input in dati_input.items():
        if categoria in mappe_normalizzazione and isinstance(lista_input, list):
            lista_normalizzata = []
            
            for elemento in lista_input:
                miglior_match = elemento
                miglior_similarita = 0
                
                # Gestione specifica per licenze_chef
                if categoria == 'licenze_chef':
                    for rif in mappe_normalizzazione[categoria]:
                        # Controlla se rif è un dizionario o una stringa
                        if isinstance(rif, dict) and 'nome' in rif:
                            # Se è un dizionario con chiave 'nome'
                            similarita = calcola_similarita(elemento['nome'], rif['nome'])
                        elif isinstance(rif, str):
                            # Se è direttamente una stringa
                            similarita = calcola_similarita(elemento['nome'], rif)
                        else:
                            # Salta elementi non validi o registra un avviso
                            continue
                            
                        if similarita > soglia_similarita and similarita > miglior_similarita:
                            miglior_match = rif
                            miglior_similarita = similarita
                
                # Gestione per altre categorie
                else:
                    for rif in mappe_normalizzazione[categoria]:
                        similarita = calcola_similarita(elemento, rif)
                        if similarita > soglia_similarita and similarita > miglior_similarita:
                            miglior_match = rif
                            miglior_similarita = similarita
                
                lista_normalizzata.append(miglior_match)
            
            dati_normalizzati[categoria] = lista_normalizzata
    
    return dati_normalizzati



def normalizza_menu(
    dati_input: Union[Dict[str, Any], List[Dict[str, Any]]], 
    liste_uniche: Dict[str, List[str]], 
    soglia_similarita: float = 0.85
) -> Dict[str, Any]:
    """
    Normalizza le entità confrontandole con le liste uniche.
    
    Args:
        dati_input (Dict o List[Dict]): Dati da normalizzare
        liste_uniche (Dict): Dizionario con le liste di riferimento
        soglia_similarita (float): Soglia di similarità per la normalizzazione
    
    Returns:
        Dict o List[Dict]: Dati normalizzati
    """
    # Gestisce input singolo o lista
    if isinstance(dati_input, dict):
        dati_input = [dati_input]
        lista_input = True
    else:
        lista_input = False
    
    # Copia profonda per non modificare l'input originale
    dati_normalizzati = []
    
    # Definizione delle mappe di normalizzazione
    mappe_normalizzazione = {
        'ingredienti': liste_uniche.get('ingredienti', []),
        'tecniche': liste_uniche.get('tecniche', []),
        'licenze_chef': liste_uniche.get('licenze_chef', [])
    }
    
    # Normalizzazione per ogni dizionario
    for dizionario in dati_input:
        dizionario_normalizzato = dizionario.copy()
        
        # Normalizzazione piatti
        if 'piatti' in dizionario_normalizzato:
            piatti_normalizzati = []
            for piatto in dizionario_normalizzato['piatti']:
                piatto_normalizzato = piatto.copy()
                
                # Normalizzazione ingredienti
                if 'ingredienti' in piatto:
                    ingredienti_normalizzati = []
                    for ingrediente in piatto['ingredienti']:
                        miglior_match = ingrediente
                        miglior_similarita = 0
                        for rif in mappe_normalizzazione['ingredienti']:
                            similarita = calcola_similarita(ingrediente, rif)
                            if similarita > soglia_similarita and similarita > miglior_similarita:
                                miglior_match = rif
                                miglior_similarita = similarita
                        ingredienti_normalizzati.append(miglior_match)
                    piatto_normalizzato['ingredienti'] = ingredienti_normalizzati
                
                # Normalizzazione tecniche
                if 'tecniche' in piatto:
                    tecniche_normalizzate = []
                    for tecnica in piatto['tecniche']:
                        miglior_match = tecnica
                        miglior_similarita = 0
                        for rif in mappe_normalizzazione['tecniche']:
                            similarita = calcola_similarita(tecnica, rif)
                            if similarita > soglia_similarita and similarita > miglior_similarita:
                                miglior_match = rif
                                miglior_similarita = similarita
                        tecniche_normalizzate.append(miglior_match)
                    piatto_normalizzato['tecniche'] = tecniche_normalizzate
                
                piatti_normalizzati.append(piatto_normalizzato)
            dizionario_normalizzato['piatti'] = piatti_normalizzati
        
        # Normalizzazione licenze chef
        if 'licenze_chef' in dizionario_normalizzato:
            licenze_normalizzate = []
            for licenza in dizionario_normalizzato['licenze_chef']:
                licenza_normalizzata = licenza.copy()
                miglior_match = licenza['nome_licenza']
                miglior_similarita = 0
                for rif in mappe_normalizzazione['licenze_chef']:
                    similarita = calcola_similarita(licenza['nome_licenza'], rif)
                    if similarita > soglia_similarita and similarita > miglior_similarita:
                        miglior_match = rif
                        miglior_similarita = similarita
                licenza_normalizzata['nome_licenza'] = miglior_match
                licenze_normalizzate.append(licenza_normalizzata)
            dizionario_normalizzato['licenze_chef'] = licenze_normalizzate
        
        dati_normalizzati.append(dizionario_normalizzato)
    
    # Restituisce lista o singolo dizionario in base all'input
    return dati_normalizzati[0]


def lowercase_json_values(data):
    # Se l'input è un dizionario
    if isinstance(data, dict):
        return {k: lowercase_json_values(v) for k, v in data.items()}
    
    # Se l'input è una lista
    elif isinstance(data, list):
        return [lowercase_json_values(v) for v in data]
    
    # Se l'input è una stringa, converte in minuscolo
    elif isinstance(data, str):
        return data.lower()
    
    # Per altri tipi (numeri, booleani), restituisce il valore originale
    else:
        return data




def rimuovi_menu_senza_piatti(menus):
    new_menus = []
    for menu in menus:
        if menu['piatti']!=[]:
            new_menus.append(menu)
    return new_menus

# Funzione per interpretare la query usando ChatOpenAI
def algoritmo_filtro_licenze_ingredienti(state: State) -> State:
    logger.debug(f"algoritmo_filtro_licenze_ingredienti user_message_quantitativo:{state['user_message_quantitativo']}")
    all_menus = ast.literal_eval(state['final_response'])
    filtered_menus = []
    query_conditions = state['user_message_quantitativo'].model_dump()
    logger.debug(f"query_conditions type: {type(query_conditions)}")
    query_conditions = lowercase_json_values(query_conditions)
    logger.debug(f"query_conditions: {query_conditions}")
    query_conditions = normalizza_query(query_conditions, state['menu_liste_uniche'])
    logger.info(f"query_conditions normalizzata:{query_conditions}")
    for menu in all_menus:                       
        try:

            menu = apply_filters(menu, query_conditions)
            if menu['piatti'] != []:
                filtered_menus.append(menu)
                logger.info(f"piatti che soddisfano i criteri: {menu}")
        except Exception as e:
            logger.error(f"Errore nell'interpretazione del risultato per il menu {menu}: {e}")
            logger.error(f"Traceback completo: {traceback.format_exc()}")


            

    state['final_response'] = str(filtered_menus)
    state['routing']['filtro_licenze_ingredienti'] = False
    return state


def apply_filters(menu: dict, query_conditions: dict) -> dict:
    """
    Applica i filtri definiti in query_conditions sul menu, con tutti i confronti case-insensitive.
    Utilizza similarità per i nomi dei ristoranti.

    Parametri:
      - menu: dizionario contenente le informazioni sul menu, inclusi i piatti e le licenze della chef.
      - query_conditions: dizionario con le condizioni da applicare.

    Ritorna:
      Il menu con i piatti filtrati. Se uno dei filtri a livello di menu (es. chef, nome ristorante, pianeta)
      o le condizioni sulle licenze non viene soddisfatto, la lista dei piatti verrà svuotata.
    """

    # Verifica se il menu soddisfa i criteri di base prima di procedere con il filtraggio dei piatti

    # 1. Filtro sul nome del chef
    chef_name = menu.get("chef", "").lower()
    if "chef_inclusi" in query_conditions and query_conditions["chef_inclusi"]:
        chef_inclusi_lower = [chef.lower() for chef in query_conditions["chef_inclusi"]]
        if chef_name not in chef_inclusi_lower:
            menu["piatti"] = []
            return menu
    
    if "chef_esclusi" in query_conditions:
        chef_esclusi_lower = [chef.lower() for chef in query_conditions["chef_esclusi"]]
        if chef_name in chef_esclusi_lower:
            menu["piatti"] = []
            return menu

    # 2. Filtro sul nome ristorante (con similarità)
    restaurant_name = menu.get("nome_ristorante", "").lower()
    if "ristoranti_inclusi" in query_conditions and query_conditions["ristoranti_inclusi"]:
        ristoranti_inclusi_lower = [rist.lower() for rist in query_conditions["ristoranti_inclusi"]]
        # Verifica se il nome del ristorante è simile ad almeno uno dei ristoranti inclusi
        if not any(calcola_similarita(restaurant_name, rist) >= SIMILARITY_THRESHOLD for rist in ristoranti_inclusi_lower):
            menu["piatti"] = []
            return menu
    
    if "ristoranti_esclusi" in query_conditions:
        ristoranti_esclusi_lower = [rist.lower() for rist in query_conditions["ristoranti_esclusi"]]
        # Verifica se il nome del ristorante è simile ad almeno uno dei ristoranti esclusi
        if any(calcola_similarita(restaurant_name, rist) >= SIMILARITY_THRESHOLD for rist in ristoranti_esclusi_lower):
            menu["piatti"] = []
            return menu

    # 3. Filtro sul pianeta
    planet_name = menu.get("nome_pianeta", "").lower()
    if "pianeti_inclusi" in query_conditions and query_conditions["pianeti_inclusi"]:
        pianeti_inclusi_lower = [pianeta.lower() for pianeta in query_conditions["pianeti_inclusi"]]
        if planet_name not in pianeti_inclusi_lower:
            menu["piatti"] = []
            return menu
    
    if "pianeti_esclusi" in query_conditions:
        pianeti_esclusi_lower = [pianeta.lower() for pianeta in query_conditions["pianeti_esclusi"]]
        if planet_name in pianeti_esclusi_lower:
            menu["piatti"] = []
            return menu

    # 4. Verifica delle licenze della chef
    licenze_richieste = query_conditions.get("licenze_chef", [])
    if licenze_richieste:
        licenze_chef = menu.get("licenze_chef", [])
        for richiesta in licenze_richieste:
            # Verifica se richiesta è un dizionario o una stringa
            if isinstance(richiesta, dict):
                nome_richiesto = richiesta.get("nome", "").lower()
                livello_minimo = richiesta.get("livello_minimo", 0)
            elif isinstance(richiesta, str):
                # Se è una stringa, assumiamo che sia il nome della licenza 
                # e impostiamo un livello minimo predefinito
                nome_richiesto = richiesta.lower()
                livello_minimo = 0
            else:
                # Se non è né un dizionario né una stringa, 
                # saltiamo questo elemento o impostiamo valori predefiniti
                continue
                
            if not any(
                licenza.get("nome_licenza", "").lower() == nome_richiesto and licenza.get("livello", 0) >= livello_minimo
                for licenza in licenze_chef
            ):
                menu["piatti"] = []
                return menu

    # 5. Filtri AND per i piatti
    ingredienti_inclusi = [ing.lower() for ing in query_conditions.get("ingredienti_inclusi", [])]
    ingredienti_esclusi = [ing.lower() for ing in query_conditions.get("ingredienti_esclusi", [])]
    tecniche_incluse = [tec.lower() for tec in query_conditions.get("tecniche_incluse", [])]
    tecniche_escluse = [tec.lower() for tec in query_conditions.get("tecniche_escluse", [])]

    # 6. Condizioni OR (se presenti)
    or_conditions = query_conditions.get("or_conditions", [])
    # Convertiamo i valori delle condizioni OR in lowercase
    for cond in or_conditions:
        if "values" in cond:
            cond["values"] = [val.lower() for val in cond["values"]]

    piatti_filtrati = []
    for piatto in menu.get("piatti", []):
        # Convertiamo gli ingredienti e le tecniche del piatto in lowercase
        dish_ingredienti = [ing.lower() for ing in piatto.get("ingredienti", [])]
        dish_tecniche = [tec.lower() for tec in piatto.get("tecniche", [])]

        # Verifica condizioni AND sugli ingredienti
        if ingredienti_inclusi and not all(item in dish_ingredienti for item in ingredienti_inclusi):
            continue
        if ingredienti_esclusi and any(item in dish_ingredienti for item in ingredienti_esclusi):
            continue

        # Verifica condizioni AND sulle tecniche
        if tecniche_incluse and not all(item in dish_tecniche for item in tecniche_incluse):
            continue
        if tecniche_escluse and any(item in dish_tecniche for item in tecniche_escluse):
            continue

        # Se sono presenti condizioni OR, il piatto deve soddisfare almeno una di esse.
        if or_conditions:
            satisfies_or = False
            for cond in or_conditions:
                field = cond.get("field")
                values = cond.get("values", [])
                if field == "ingredienti":
                    if any(val in dish_ingredienti for val in values):
                        satisfies_or = True
                        break
                elif field == "tecniche":
                    if any(val in dish_tecniche for val in values):
                        satisfies_or = True
                        break
                # Altre condizioni OR su altri campi possono essere aggiunte qui
            if not satisfies_or:
                continue

        piatti_filtrati.append(piatto)

    menu["piatti"] = piatti_filtrati
    return menu