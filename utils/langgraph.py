from typing_extensions import TypedDict
from agents.menu_cleaner import QueryBuilderFormat

# Definizione dello state
class State(TypedDict):
    user_message: str
    prompt_message_quantitativo: str
    user_message_quantitativo: QueryBuilderFormat
    filtro_distanze_menu: str
    prompt_filtro_licenze_ingredienti: str
    output_filtro_licenze_ingredienti: str
    prompt_rag: str
    context: list
    routing: dict
    final_response: str
    menu_liste_uniche : dict
