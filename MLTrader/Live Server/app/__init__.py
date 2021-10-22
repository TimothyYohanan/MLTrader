from numpy import load
from app.general_purpose.utils import tickers_fromCSV, load_object
from app.structures.QuotesHandler import QuotesHandler
from pathlib import Path
from flask import Flask
from config import Config

tickers = tickers_fromCSV('TopTech_Companies.csv')

resources_folder = Path.cwd()/'app'/'resources'
tdaAPI_filepath = resources_folder/'api_state'/'tdaAPI.save'
quotesHandler_filepath = resources_folder/'api_state'/'quotes.save'

STATIC_DIR = "static_resources"
CLIENT_DIR = "html_docs"

Path(resources_folder).mkdir(parents=True, exist_ok=True)
quotesHandler = load_object(quotesHandler_filepath)
if not quotesHandler:
    quotesHandler = QuotesHandler(resources_folder, tickers)

def create_app(config_class=Config):
    app = Flask(__name__, template_folder=CLIENT_DIR, static_folder=STATIC_DIR)
    app.config.from_object(config_class)
    from app.routes.streaming_interfaces import datastream
    app.register_blueprint(datastream)  
    return app
