import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Creiamo la cartella logs se non esiste
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

def setup_logger(module_name):
    """Crea e configura un logger con file rotanti."""
    log_date = datetime.now().strftime("%Y-%m-%d")  # Formato YYYY-MM-DD
    log_filename = os.path.join(LOG_DIR, f"{log_date}_{module_name}.log")

    logger = logging.getLogger(module_name)
    logger.setLevel(logging.DEBUG)  # Imposta il livello minimo del log

    # Evita di aggiungere più handler se il logger è già stato configurato
    if not logger.hasHandlers():
        # Rotazione fino a 10 file, max 1MB ciascuno
        file_handler = RotatingFileHandler(log_filename, maxBytes=1_000_000, backupCount=10)
        file_handler.setLevel(logging.DEBUG)

        # Formato del log
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)

        # Aggiungiamo gli handler al logger
        logger.addHandler(file_handler)

        # Opzionale: Stampa anche su console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        logger.addHandler(console_handler)

    return logger
