import pandas as pd
from pathlib import Path


def salvar_dataset(df, path):

    # Garantir que o diretório existe
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    
    df.to_excel(
        path,
        index=False,
        engine="openpyxl"
    )
