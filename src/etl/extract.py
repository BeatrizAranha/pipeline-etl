import pandas as pd


def ler_excel(path):

    planilhas = pd.read_excel(path, sheet_name=None)

    return planilhas
