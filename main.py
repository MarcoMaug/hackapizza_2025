from utils.logger import setup_logger
from graphs.planet_graph import app
from agents.menu_cleaner import extract_pdfs
import os

logger = setup_logger("main")

json_input_menu_estratti = "./data/menu_estratti.json"
if not os.path.exists(json_input_menu_estratti):
    extract_pdfs("./data/menu", json_input_menu_estratti)


logger.info("Starting AI pipeline...")

input_data = {"messages": "Quali sono i piatti che necessitano di una licenza di grado 3 o superiore per la preparazione e sono serviti in un ristorante che si trova entro un raggio di 659 anni luce dal pianeta Namecc, Namecc incluso?"}
output = app.invoke(input_data)

output_path = './diagram.png'
with open(output_path, 'wb') as f:
    f.write(app.get_graph().draw_mermaid_png()) 


logger.info(f"Pipeline output: {output}")
