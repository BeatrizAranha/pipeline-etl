#Não está sendo utilizado na pipeline, mas pode ser útil para extrair dados de arquivos antigos e criar a base inicial

import pandas as pd
import os
import time
import re
import unicodedata

mapa_estados = {
    "AC": ["ACRE", "RIO BRANCO"],
    "AL": ["ALAGOAS", "MACEIO"],
    "AP": ["AMAPA", "MACAPA"],
    "AM": ["AMAZONAS", "MANAUS"],
    "BA": ["BAHIA", "SALVADOR", "FEIRA DE SANTANA"],
    "CE": ["CEARA", "FORTALEZA", "JUAZEIRO DO NORTE"],
    "DF": ["BRASILIA", "DISTRITO FEDERAL", "BRASIL"],
    "ES": ["ESPIRITO SANTO", "VITORIA", "VILA VELHA"],
    "GO": ["GOIAS", "GOIANIA", "APARECIDA DE GOIANIA"],
    "MA": ["MARANHAO", "SAO LUIS", "IMPERATRIZ"],
    "MT": ["MATO GROSSO", "CUIABA", "VARZEA GRANDE"],
    "MS": ["MATO GROSSO DO SUL", "CAMPO GRANDE", "DOURADOS"],
    "MG": ["MINAS", "BELO HORIZONTE", "CONTAGEM", "UBERLANDIA"],
    "PA": ["PARA", "BELEM", "ANANINDEUA"],
    "PB": ["PARAIBA", "JOAO PESSOA", "CAMPINA GRANDE"],
    "PR": ["PARANA", "CURITIBA", "LONDRINA"],
    "PE": ["PERNAMBUCO", "RECIFE", "JABOATAO DOS GUARARAPES"],
    "PI": ["PIAUI", "TERESINA", "PARNAIBA"],
    "RJ": ["RIO DE JANEIRO", "NITEROI", "DUQUE DE CAXIAS"],
    "RN": ["RIO GRANDE DO NORTE", "NATAL", "MOSSORO"],
    "RS": ["RIO GRANDE DO SUL", "PORTO ALEGRE", "CANOINHAS"],
    "RO": ["RONDONIA", "PORTO VELHO", "JI-PARANA"],
    "RR": ["RORAIMA", "BOA VISTA"],
    "SC": ["SANTA CATARINA", "FLORIANOPOLIS", "JOINVILLE"],
    "SP": ["SAO PAULO", "SÃO PAULO", "CAMPINAS", "SANTOS", "SOROCABA", "RIBEIRAO PRETO"],
    "SE": ["SERGIPE", "ARACAJU", "LAGARTO"],
    "TO": ["TOCANTINS", "PALMAS", "ARAGUAINA"]
}

DATA_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
ARQUIVO_MUNICIPIOS = os.path.join(DATA_DIR, "municipios.csv")
if not os.path.exists(ARQUIVO_MUNICIPIOS):
    ARQUIVO_MUNICIPIOS = os.path.join(DATA_DIR, "municipios_uf.csv")


def normalizar_texto(texto: str) -> str:
    texto = str(texto).upper().strip()
    texto = unicodedata.normalize("NFKD", texto)
    texto = texto.encode("ASCII", "ignore").decode("ASCII")
    texto = re.sub(r"[^A-Z0-9 ]+", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def _get_coluna(df: pd.DataFrame, candidatos: list[str]) -> str | None:
    coluna_map = {normalizar_texto(col): col for col in df.columns}
    for candidato in candidatos:
        if candidato in coluna_map:
            return coluna_map[candidato]
    return None


def carregar_municipios_uf(caminho: str) -> dict:
    if not os.path.exists(caminho):
        return {}

    try:
        df = pd.read_csv(caminho, dtype=str, sep=";", encoding="latin-1")
    except Exception:
        return {}

    cidade_col = _get_coluna(df, ["MUNICIPIO IBGE", "MUNICIPIO TOM", "MUNICIPIO", "CIDADE"])
    uf_col = _get_coluna(df, ["UF", "ESTADO"])

    if cidade_col is None or uf_col is None:
        return {}

    df = df.dropna(subset=[cidade_col, uf_col])
    return {
        normalizar_texto(row[cidade_col]): str(row[uf_col]).strip().upper()
        for _, row in df.iterrows()
    }


cidade_para_uf = carregar_municipios_uf(ARQUIVO_MUNICIPIOS)


def buscar_estado_por_cidade(texto: str) -> str | None:
    if not cidade_para_uf:
        return None

    tokens = texto.split()
    max_tamanho = min(5, max((len(cidade.split()) for cidade in cidade_para_uf), default=1))

    for tamanho in range(max_tamanho, 0, -1):
        for i in range(len(tokens) - tamanho + 1):
            trecho = " ".join(tokens[i : i + tamanho])
            if trecho in cidade_para_uf:
                return cidade_para_uf[trecho]

    return None


def extrair_estado(valor):

    if valor is None:
        return None

    texto = str(valor).upper().strip()

    if texto in ["", "NONE", "(NONE)"]:
        return None

    # ignora datas
    if re.search(r"\d{1,2}/\d{1,2}/\d{2,4}", texto):
        return None

    # ignora números
    if re.match(r"^\d+$", texto):
        return None

    # se for sigla direta
    if texto in mapa_estados:
        return texto

    # dividir por separadores comuns e verificar cada parte
    partes = re.split(r'[/-]', texto)
    for parte in partes:
        parte = parte.strip()
        if parte in mapa_estados:
            return parte
        for uf, palavras in mapa_estados.items():
            for palavra in palavras:
                if palavra in parte:
                    return uf

    # procura cidade ou estado no texto completo
    for uf, palavras in mapa_estados.items():
        for palavra in palavras:
            if palavra in texto:
                return uf

    return None


data = "../../data/_raw/"
lista_dfs = []
epoch = int(time.time())

print("Executando em:", os.getcwd())

abas_excluir = ["envio parceiro", "base", "diferenças"]


def extrair_mes_ano(nome_arquivo):

    padrao = r"(janeiro|fevereiro|março|marco|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)\s+(\d{4})"

    match = re.search(padrao, str(nome_arquivo).lower())

    if match:
        mes = match.group(1)
        ano = match.group(2)
        return pd.Series([mes, ano])

    return pd.Series([None, None])


def extrair_projeto(nome_aba):

    nome = str(nome_aba).lower()

    nome = re.split(r"\bok\b", nome)[0]
    nome = re.split(r"[-_]", nome)[0]

    return nome.strip().title()


for arquivo in os.listdir(data):

    if arquivo.endswith(".xlsx"):

        print("Lendo arquivo:", arquivo)

        path = os.path.join(data, arquivo)
        planilhas = pd.read_excel(path, sheet_name=None)

        for nome_aba, df in planilhas.items():

            nome_limpo = nome_aba.strip().lower()

            if nome_limpo not in abas_excluir:

                print("  -> Incluindo aba:", nome_aba)

                df.columns = df.columns.astype(str).str.strip()

                if df.columns.duplicated().any():
                    print("Colunas duplicadas na aba:", nome_aba)
                    df = df.loc[:, ~df.columns.duplicated()]

                mapeamento_colunas = {

                    "Ticket": "Ticket",
                    "Chamado": "Ticket",
                    "Requisicao": "Ticket",
                    "Chave": "Ticket",
                    "FSA": "Ticket",
                    "CHAMADO": "Ticket",

                    "Criado": "abertura_chamado",
                    "Issue created date": "abertura_chamado",
                    "DATA ABERTURA": "abertura_chamado",

                    "Issue resolution date": "encerramento_chamado",
                    "Resolvido": "encerramento_chamado",

                    "Total do Tickt": "Custo",
                    "Issue Total do Tickt": "Custo",
                    "Total do Tickt resolved": "Custo",
                    "VALOR": "Custo",
                    "Total Geral": "Custo",
                    "Unnamed: 15": "Custo",
                    "TOTAL": "Custo",
                    "Total ticket": "Custo",

                    "Parceiro": "Parceiro",
                    "Nome parceiro": "Parceiro",
                    "Issue PARCEIRO-ATRIBUIDO": "Parceiro",
                    "Issue Nome parceiro": "Parceiro",
                    "Unnamed: 4": "Parceiro",
                    "PARCEIRO-ATRIBUIDO": "Parceiro",
                    "PARCEIRO": "Parceiro"
                }

                df = df.rename(columns=mapeamento_colunas)
                df = df.loc[:, ~df.columns.duplicated()]

                # -------- TRATAMENTO ESTADO --------

                colunas_estado = [
                    "Issue Estado / Cidade",
                    "Issue Estado",
                    "Issue Cidade",
                    "UF",
                    "Unnamed: 5",
                    "Estado",
                    "Cidade",
                    "Localização",
                    "Endereço",
                    "Issue Localização",
                    "Local ou Serviço realizado"
                ]

                estado = None

                for col in colunas_estado:

                    if col in df.columns:

                        serie = df[col].apply(extrair_estado)

                        if estado is None:
                            estado = serie
                        else:
                            estado = estado.combine_first(serie)

                df["Estado"] = estado

                # -------- GARANTIAS --------

                if "Ticket" not in df.columns:
                    df["Ticket"] = None

                if "Custo" not in df.columns:
                    df["Custo"] = None

                if "Parceiro" not in df.columns:
                    df["Parceiro"] = None

                if "abertura_chamado" not in df.columns:
                    df["abertura_chamado"] = None

                if "encerramento_chamado" not in df.columns:
                    df["encerramento_chamado"] = None


                # -------- METADADOS --------

                df["Nome_Aba"] = nome_aba
                df["Arquivo_Origem"] = arquivo


                # -------- FILTRAR COLUNAS IMPORTANTES --------

                colunas_interesse = [
                    "Ticket",
                    "Estado",
                    "abertura_chamado",
                    "encerramento_chamado",
                    "Custo",
                    "Parceiro",
                    "Nome_Aba",
                    "Arquivo_Origem"
                ]

                df = df[[c for c in colunas_interesse if c in df.columns]]

                lista_dfs.append(df)



if lista_dfs:

    df_final = pd.concat(lista_dfs, ignore_index=True)

    df_final[["mes", "ano"]] = df_final["Arquivo_Origem"].apply(extrair_mes_ano)

    df_final["Projeto"] = df_final["Nome_Aba"].apply(extrair_projeto)

    colunas_finais = [
        "Projeto",
        "Ticket",
        "Estado",
        "abertura_chamado",
        "encerramento_chamado",
        "Custo",
        "Parceiro",
        "Nome_Aba",
        "Arquivo_Origem",
        "mes",
        "ano"
    ]

    for coluna in colunas_finais:
        if coluna not in df_final.columns:
            df_final[coluna] = None

    df_final = df_final.reindex(columns=colunas_finais)

    print("Total de linhas:", len(df_final))
    
    # TIPOS DE DADOS

    df_final["Ticket"] = df_final["Ticket"].astype("string")

    df_final["Estado"] = df_final["Estado"].astype("string")

    df_final["Parceiro"] = df_final["Parceiro"].astype("string")

    df_final["Projeto"] = df_final["Projeto"].astype("string")

    df_final["Nome_Aba"] = df_final["Nome_Aba"].astype("string")

    df_final["Arquivo_Origem"] = df_final["Arquivo_Origem"].astype("string")

    df_final["mes"] = df_final["mes"].astype("string")

    df_final["ano"] = df_final["ano"].astype("Int64")

    df_final["Custo"] = pd.to_numeric(df_final["Custo"], errors="coerce")

    df_final["abertura_chamado"] = pd.to_datetime(df_final["abertura_chamado"], errors="coerce")

    df_final["encerramento_chamado"] = pd.to_datetime(df_final["encerramento_chamado"], errors="coerce")


    df_final.to_excel(
        rf"..\..\data\processed\base-parceiros.xlsx",
        index=False,
        engine="openpyxl"
    )

    print("Concluído.")

else:
    print("Nenhum dado encontrado.")
