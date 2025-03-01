from utils.logger import setup_logger
from graphs.planet_graph import app
from agents.menu_cleaner import extract_pdfs

logger = setup_logger("main")

extract_pdfs("./data/menu", "./data/menu_estratti.json")

logger.info("Starting AI pipeline...")

input_data = {"messages": "Dimmi i 5 pianeti più vicini a Marte"}
output = app.invoke(input_data)

output_path = './diagram.png'
with open(output_path, 'wb') as f:
    f.write(app.get_graph().draw_mermaid_png()) 


logger.info(f"Pipeline output: {output}")
