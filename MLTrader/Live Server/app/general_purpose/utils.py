import csv
import joblib
from pathlib import Path

def tickers_fromCSV(filename) -> list:
    source = Path.cwd()/'app'/'resources'/filename
    with open(source, 'r', newline='') as _t:
        reader = csv.reader(_t, delimiter=',')
        tickers = [row[0] for row in reader]
    return tickers

def load_object(filepath: Path) -> object:
    if filepath.is_file():
        return joblib.load(filepath)
    else:
        return None

            
            
            


    