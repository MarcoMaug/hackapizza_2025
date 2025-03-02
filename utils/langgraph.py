from typing_extensions import TypedDict

# Definizione dello state
class State(TypedDict):
    user_message: str
    prompt_message_quantitativo: str
    user_message_quantitativo: str
    filtro_distanze_menu: str
    prompt_filtro_licenze_ingredienti: str
    output_filtro_licenze_ingredienti: str