from utils.logger import setup_logger
from graphs.agent_graph import app
from agents.menu_cleaner import extract_pdfs
from agents.filtro_licenze_ingredienti import normalizza_menu
from fuzzywuzzy import fuzz
import os
import json
from typing import List, Dict, Any
import ast
import pandas as pd
from difflib import SequenceMatcher


logger = setup_logger("main")

def convert_to_lowercase(input_data):
    """
    Converte in lowercase valori di dizionari o liste.
    
    Args:
        input_data (dict o list): Input da convertire
    
    Returns:
        dict o list: Oggetto con valori in lowercase
    """
    if isinstance(input_data, dict):
        # Conversione per dizionari
        return {chiave: convert_to_lowercase(valore) 
                for chiave, valore in input_data.items()}
    
    elif isinstance(input_data, list):
        # Conversione per liste
        return [convert_to_lowercase(elemento) 
                for elemento in input_data]
    
    elif isinstance(input_data, str):
        # Conversione stringa in lowercase
        return input_data.lower()
    
    # Per altri tipi (numeri, ecc.) restituisce l'input invariato
    return input_data


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

def normalizza_liste_uniche(liste_uniche: Dict[str, List[str]], soglia_similarita: float = 0.85) -> Dict[str, List[str]]:
    """
    Normalizza le liste uniche rimuovendo varianti simili.
    
    Args:
        liste_uniche (Dict): Dizionario con le liste da normalizzare
        soglia_similarita (float): Soglia di similarità per considerare le stringhe simili
    
    Returns:
        Dict: Dizionario con liste uniche normalizzate
    """
    liste_normalizzate = {}
    
    for categoria, lista in liste_uniche.items():
        # Inizia con la prima stringa come riferimento
        liste_normalizzate[categoria] = []
        
        for stringa in lista:
            # Verifica se la stringa è già troppo simile a qualcosa nella lista normalizzata
            if not any(calcola_similarita(stringa, x) >= soglia_similarita for x in liste_normalizzate[categoria]):
                liste_normalizzate[categoria].append(stringa)
    
    return liste_normalizzate

def estrai_liste_uniche(data: List[Dict[Any, Any]]) -> Dict[str, List[str]]:
    """
    Estrae le liste uniche da un JSON complesso.
    
    Args:
        data (List[Dict]): Dati JSON da elaborare
    
    Returns:
        Dict[str, List[str]]: Dizionario con liste uniche per categoria
    """
    liste_uniche = {
        "ristoranti": set(),
        "chef": set(),
        "pianeti": set(),
        "menu": set(),
        "licenze_chef": set(),
        "ingredienti": set(),
        "tecniche": set()
    }
    
    for elemento in data:
        # Estrazione liste uniche
        liste_uniche["ristoranti"].add(elemento.get("nome_ristorante", "").lower())
        liste_uniche["chef"].add(elemento.get("chef", "").lower())
        liste_uniche["pianeti"].add(elemento.get("nome_pianeta", "").lower())
        liste_uniche["menu"].add(elemento.get("nome_menu", "").lower())
        
        # Licenze Chef
        for licenza in elemento.get("licenze_chef", []):
            liste_uniche["licenze_chef"].add(licenza.get("nome_licenza", "").lower())
        
        # Piatti
        for piatto in elemento.get("piatti", []):
            # Conversione a lowercase per ogni ingrediente e tecnica
            liste_uniche["ingredienti"].update(
                ingrediente.lower() for ingrediente in piatto.get("ingredienti", [])
            )
            liste_uniche["tecniche"].update(
                tecnica.lower() for tecnica in piatto.get("tecniche", [])
            )
    
    # Conversione in liste ordinate
    return {k: sorted(list(v)) for k, v in liste_uniche.items()}

def salva_liste_uniche_su_json(risultati: Dict[str, List[str]], nome_file: str = './data/liste_uniche.json'):
    """
    Salva le liste uniche su un file JSON.
    
    Args:
        risultati (Dict[str, List[str]]): Dizionario con le liste uniche
        nome_file (str, optional): Nome del file di output. Default 'liste_uniche.json'
    """
    with open(nome_file, 'w', encoding='utf-8') as file:
        json.dump(risultati, file, ensure_ascii=False, indent=2)
    
    print(f"Liste uniche salvate nel file JSON: {nome_file}")

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

with open("./data/menu_estratti.json", "r") as f:
    menu_estratti = json.load(f)



menu_estratti_lower = convert_to_lowercase(menu_estratti)

risultati = estrai_liste_uniche(menu_estratti_lower)
risultati = normalizza_liste_uniche(risultati)
salva_liste_uniche_su_json(risultati)


with open("./data/liste_uniche.json", "r") as f:
    json_liste_uniche = json.load(f)

menu_normalizzati = []
# normalizzo il menuu
for menu in menu_estratti:
    singolo_menu_normalizato = normalizza_menu(menu, json_liste_uniche)
    menu_normalizzati.append(singolo_menu_normalizato)


def loop_get_piatti(user_message):
    prompt_filtro_licenze_ingredienti = """rimuovi dai menu indicati i piatti che NON soddisfano i criteri presenti nella richiesta.
                                            fai molta attenzione alla condizione sulla licenza della chef e sul suo livello se la licenza non soddisfa i criteri non considerare nessun piatto.
                                            non inventare piatti che non sono presenti nel menu"""
    output = app.invoke({
        "user_message": user_message,
        "prompt_message_quantitativo":"""estrai solo le informazioni quantitative e le condizioni, fatta eccezione per quelle sulla distanza, nella struttura JSON indicata fai attenzione agli ingredienti, alle licenze e alle tecniche da utilizzare.
                                            Non inventare ingredienti, tecniche o licenze che non sono presenti nella richiesta dell'utente
                                            Considera che l'utente può abbreviare i nomi delle licenze:

                                            Quantistica (potrebbe essere abbreviata con Q)
                                            Temporale (potrebbe essere abbreviata con t)
                                            Psionica (potrebbe essere abbreviata con P)
                                            Gravitazionale (potrebbe essere abbreviata con g)
                                            magnetica (potrebbe essere abbreviata con Mx)
                                            antimateria (potrebbe essere abbreviata con e+)
                                            luce (potrebbe essere abbreviata con c)
                                            LTK (semplicemente LTK si chiama così la licenza)

                                            elenco dei pianeti possibili: Tatooine,Asgard,Namecc,Arrakis,Krypton,Pandora,Cybertron,Ego,Montressosr,Klyntar
                                            traducile con il loro nome completo.
                                            Ricorda che l'utente può chiedere di escludere ingredienti, tecniche o licenze, fai attenzione a non includerli nei piatti estratti.
                                            NON inventare condizioni che non sono presenti nella richiesta dell'utente.
                                            NON inventare condizioni su Licenze dello chef, l'utente deve specificare se vuole includere una condizione sulla licenza, ad esempio dicendo 
                                            che vuole un piatto con licenza gravitazionale almeno 2. Non è sufficiente il nome della licenza nella richiesta.   
                                            alcuni ingredienti hanno porzioni di nomi di licenze. 
 {
   "licenze_chef": [
    "antimateria",
    "gravitazionale",
    "luce",
    "magnetica",
    "psionica",
    "quantistica",
    "tecnologica",
    "temporale"
  ],
  "ingredienti": [
    "alghe bioluminescenti",
    "amido di stellarion",
    "baccacedro",
    "baccacedro caramellato",
    "bacche di baccacedro",
    "balena spaziale",
    "biscotti della galassia",
    "brodo di liane di plasmodio",
    "brodo di teste di idra",
    "brodo di vero ghiaccio",
    "buccia del baccacedro",
    "burrobirra",
    "carne delle teste di idra",
    "carne di balena spaziale",
    "carne di drago",
    "carne di kraken",
    "carne di mucca",
    "carne di xenodonte",
    "carpaccio di carne di kraken",
    "carpaccio di funghi orbitali",
    "chocobo wings",
    "cioccorane",
    "colonia di mycoflora",
    "cristalli di memoria",
    "cristalli di nebulite",
    "cristalli di sale temporale",
    "croissant celestiale",
    "crononite",
    "erba pipa",
    "essenza di speziaria",
    "essenza di tachioni",
    "essenza di vuoto",
    "farina di nettuno",
    "fibra di sintetex",
    "foglie di mandragora",
    "foglie di nebulosa",
    "frammenti di supernova",
    "frutti del diavolo",
    "funghi dell’etere",
    "funghi orbitali",
    "fusilli del vento",
    "gnoccchi del crepuscolo",
    "granuli di nebbia arcobaleno",
    "impasto gravitazionale",
    "lacrime di andromeda",
    "lacrime di unicorno",
    "latte+",
    "lattuga namecciana",
    "liane di plasmodio",
    "materia oscura",
    "muffa lunare",
    "mycoflora fresca",
    "nduja fritta tanto",
    "nebbia arcobaleno",
    "nettare di sirena",
    "pane degli abissi",
    "pane di farina di nettuno",
    "pane di luce",
    "petali di eco",
    "pickle rick croccante",
    "plasma vitale",
    "polvere di crononite",
    "polvere di pulsar",
    "polvere di stelle",
    "proteine di mare e terra",
    "proteine rigenerative delle teste di idra",
    "radici di gravità",
    "radici di gravità e singolarità",
    "radici di singolarità",
    "ravioli al vaporeon",
    "riso di cassandra",
    "risotto dei multiversi",
    "risotto galattico",
    "sale temporale",
    "salsa szechuan",
    "salsa szechuan interdimensionale",
    "sashimi di magicarp",
    "scorza artica",
    "shard di materia oscura",
    "shard di prisma stellare",
    "slurm",
    "soufflé al vero ghiaccio",
    "spaghi del sole",
    "spezie melange",
    "spore quantiche",
    "succo di baccacedro",
    "teste di idra",
    "uova di fenice",
    "vegetali sublimati",
    "vero ghiaccio",
    "xenodonte"
  ],
  "tecniche": [
    "affettamento a pulsazioni quantistiche",
    "affumicatura a stratificazione quantica",
    "affumicatura polarizzata a freddo iperbarico",
    "affumicatura psionica sensoriale",
    "affumicatura temporal risonante",
    "affumicatura tramite big bang microcosmico",
    "amalgamazione sintetica molecolare",
    "big bang microcosmico",
    "bollitura entropica sincronizzata",
    "bollitura infrasonica armonizzata",
    "bollitura termografica a rotazione veloce",
    "campi magnetici entropici",
    "congelamento bio-luminiscente sincronico",
    "congelazione iperdimensionalmente stratificata",
    "cottura a forno dinamico inversionale",
    "cottura a vapore con flusso di particelle isoarmoniche",
    "cottura a vapore ecodinamico bilanciato",
    "cottura a vapore risonante simbiotico",
    "cottura a vapore termocinetica multipla",
    "cottura al forno con paradosso temporale cronospeculare",
    "cottura con microonde entropiche sincronizzate",
    "cottura idrodinamica autoregolante",
    "cottura olografica quantum fluttuante",
    "cottura sottovuoto",
    "cottura sottovuoto antimateria",
    "cottura sottovuoto bioma sintetico",
    "cottura sottovuoto frugale energeticamente negativa",
    "cottura sottovuoto multirealità collassante",
    "cottura sottovuoto pulsar magnetica",
    "cristallizzazione temporale reversiva",
    "cryo-tessitura energetica polarizzata",
    "decostruzione ancestrale",
    "decostruzione atomica a strati energetici",
    "decostruzione bio-fotonica emotiva",
    "decostruzione interdimensionale lovecraftiana",
    "decostruzione magnetica risonante",
    "ebollizione magneto-cinetica pulsante",
    "fermentazione psionica energetica",
    "fermentazione quantica a strati multiversali",
    "fermentazione quantico biometrica",
    "fermentazione temporale sincronizzata",
    "flusso di particelle isoarmoniche",
    "forno dinamico inversionale",
    "gravitazionale",
    "grigliatura a energia stellare div",
    "grigliatura eletro-molecolare a spaziatura variabile",
    "grigliatura plasma sintetico risonante",
    "grigliatura psionica dinamica ritmica",
    "idro-cristallizzazione sonora quantistica",
    "impasto a campi magnetici dualistici",
    "impasto gravitazionale vorticoso",
    "incisione elettromagnetica plasmica",
    "luminante",
    "manipolazione gravitazionale",
    "manipolazioni della luce",
    "marinatura a infusione gravitazionale",
    "marinatura psionica",
    "marinatura sotto zero a polarità inversa",
    "marinatura temporale sincronizzata",
    "marinatura tramite reazioni d'antimateria diluite",
    "modellatura onirica tetrazionale",
    "padella classica",
    "padella via realtà energetiche parallele",
    "proiezioni olografiche quantum fluttuanti",
    "pulsante magneto-cinetica",
    "pulsazioni quantistiche",
    "quantico biometrica",
    "reazioni d'antimateria diluite",
    "risonanza sonica rigenerativa",
    "saltare in padella classica",
    "saltare in padella realtà energetiche parallele",
    "saltare in padella sinergia psionica",
    "saltare in padella singolarità inversa",
    "saltato in padella",
    "sferificazione a gravità psionica variabile",
    "sferificazione con campi magnetici entropici",
    "sferificazione cromatica interdimensionale",
    "sferificazione filamentare a molecole vibrazionali",
    "sferificazione tramite matrici biofotiche",
    "sinergia elettro-osmotica programmabile",
    "sinergia psionica",
    "sottovuoto antimateria",
    "spore quantiche",
    "stratificazione quantica",
    "surgelamento antimaterico a risonanza inversa",
    "taglio dimensionale a lame fotofiliche",
    "taglio sinaptico biomimetico",
    "vapore termocinetico multiplo"]
    }


                                            """,
        "user_message_quantitativo": None,
        "filtro_distanze_menu": "",
        "prompt_filtro_licenze_ingredienti": prompt_filtro_licenze_ingredienti,
        "output_filtro_licenze_ingredienti": "",
        "prompt_rag": """rimuovi dai menu indicati i piatti che NON soddisfano i criteri presenti nella richiesta
                        Ricorda le seguenti regole:
                        Chi fa parte dell'Ordine della Galassia di Andromeda deve rispettare la seguuente regola: Ogni piatto dev’essere rigorosamente privo di lattosio. 
                        Chi fa parte dell'Ordine dei Naturalisti mangia ingredienti con nessuna trasformazione drastica, niente manipolazioni invasive, fare attenzione alle tecnica utilizzate.
                        Chi fa parte dell'Ordine degli Armonisti mangiano piatti che parlano al cuore, adattandosi alle frequenze emotive del momento 
                        considera il contesto dato.""",
        "contex": [],
        "routing": {"filtro_distanze":False,
        "filtro_licenze_ingredienti":False,
        "generate_rag":True},
        "final_response": str(menu_normalizzati),
        "menu_liste_uniche" : json_liste_uniche
    })

    logger.info(f"Pipeline output: {output}")
    logger.info(f"Pipeline output type: {type(output)}")
    logger.info(f"Pipeline final_response: {output['final_response']}")
    menus = ast.literal_eval(output['final_response'])
    logger.info(f"menu che soddisfano i criteri: {menus}")

    piatti_num = estrai_piatti_menu(menus)

    logger.info(f"piatti che soddisfano i criteri: {piatti_num}")

    return piatti_num

domande_df = pd.read_csv("./data/domande.csv")
results = []

for i, domanda in domande_df.iterrows():
    user_message = domanda['domanda']
    piatti_num = loop_get_piatti(user_message)
    
    piatti_str = ",".join(map(str, piatti_num)) if isinstance(piatti_num, list) else str(piatti_num)
    results.append({"row_id": i + 1, "result": piatti_str})
    
    if i == 0:
        results_df = pd.DataFrame([results[-1]])
        results_df.to_csv("./data/results.csv", index=False, mode='w', header=True)
    else:
        results_df = pd.DataFrame([results[-1]])
        results_df.to_csv("./data/results.csv", index=False, mode='a', header=False)
    break

