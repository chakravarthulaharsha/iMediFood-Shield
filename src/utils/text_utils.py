import re
import pandas as pd

def clean_text(x):
    if pd.isna(x):
        return ""
    x = str(x)
    x = x.replace("\xa0", " ")
    x = re.sub(r"\s+", " ", x)
    return x.strip()

def normalize_name(x):
    x = clean_text(x).lower()
    x = re.sub(r"[^a-z0-9\s\-]", " ", x)
    x = re.sub(r"\s+", " ", x)
    return x.strip()
