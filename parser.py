
import pandas as pd

def parse_csv(path):
    raw = pd.read_csv(path, header=None)
    return raw
