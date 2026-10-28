import os
import re
import shutil
import time
import unicodedata

import pandas as pd


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


abas_excluir = ["envio parceiro", "base", "diferenças"]


def extrair_estado(valor):
    if valor is None:
        return None

    texto = normalizar_texto(valor)

    if texto in ["", "NONE", "(NONE)"]:
        return None

    if re.search(r"\d{1,2}/\d{1,2}/\d{2,4}", texto):
        return None

    if re.match(r"^\d+$", texto):
        return None

    if texto in mapa_estados:
        return texto

    partes = re.split(r"[/-]", texto)
    for parte in partes:
        parte = parte.strip()
        if parte in mapa_estados:
            return parte
        for uf, palavras in mapa_estados.items():
            for palavra in palavras:
                if normalizar_texto(palavra) in parte:
                    return uf

    for uf, palavras in mapa_estados.items():
        for palavra in palavras:
            if normalizar_texto(palavra) in texto:
                return uf

    cidade_uf = buscar_estado_por_cidade(texto)
    if cidade_uf:
        return cidade_uf

    return None


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


def deve_processar_aba(nome_aba, df=None):
    return str(nome_aba).strip().lower() not in abas_excluir


def transformar_planilha(df: pd.DataFrame, nome_aba: str, arquivo: str) -> pd.DataFrame:
    df = df.copy()

    # limpeza de colunas
    df.columns = (
        df.columns
        .astype(str)
        .str.replace("\n", " ")
        .str.replace("\r", " ")
        .str.strip()
    )

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
        "PARCEIRO": "Parceiro",
    }

    df = df.rename(columns=mapeamento_colunas)
    df = df.loc[:, ~df.columns.duplicated()]

    # -------- ESTADO --------
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
        "Issue Localização"
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
    for required in ["Ticket", "Custo", "Parceiro", "abertura_chamado", "encerramento_chamado"]:
        if required not in df.columns:
            df[required] = None

    # -------- METADADOS --------
    df["Nome_Aba"] = nome_aba
    df["Arquivo_Origem"] = arquivo

    # -------- SCHEMA FIXO --------
    colunas_schema = [
        "Ticket",
        "Estado",
        "abertura_chamado",
        "encerramento_chamado",
        "Custo",
        "Parceiro",
        "Nome_Aba",
        "Arquivo_Origem",
    ]

    return df.reindex(columns=colunas_schema)


def _salvar_resultado(df_final: pd.DataFrame, output_path: str):
    """Salva o DataFrame em Excel com tratamento de erros de permissão."""
    import os
    import time
    
    max_tentativas = 3
    for tentativa in range(max_tentativas):
        try:
            df_final.to_excel(
                output_path,
                index=False,
                engine="openpyxl",
            )
            return  # Sucesso, sai da função
            
        except PermissionError as e:
            if tentativa < max_tentativas - 1:
                print(f"[WARN] Arquivo em uso (tentativa {tentativa + 1}/{max_tentativas}). Aguardando 2 segundos...")
                time.sleep(2)
            else:
                # Última tentativa falhou, tenta salvar com nome temporário
                print(f"[WARN] Não foi possível salvar {output_path} (arquivo em uso). Tentando nome temporário...")
                try:
                    temp_path = output_path.replace('.xlsx', f'_temp_{int(time.time())}.xlsx')
                    df_final.to_excel(temp_path, index=False, engine="openpyxl")
                    print(f"[INFO] Arquivo salvo temporariamente como: {temp_path}")
                    print("[INFO] Renomeie manualmente ou feche o arquivo original no Excel/Power BI")
                    return
                except Exception as temp_e:
                    print(f"[ERROR] Falha crítica ao salvar arquivo: {temp_e}")
                    raise temp_e
        
        except Exception as e:
            print(f"[ERROR] Erro ao salvar arquivo: {e}")
            raise e


def run(
    pasta_raw="../../data/_raw",
    pasta_processed="../../data/processed",
    pasta_archive="../../data/archive",
    output_file: str | None = None,
):
    """Run the extraction/transformation and write to a single output file.

    - If the output file does not exist, it is created with data from all _raw files.
    - If the output file exists, new rows are appended and the file is rewritten.

    This allows incremental behavior (adding new uploads to a single accumulated file).
    """

    print("Executando em:", os.getcwd())

    output_file = output_file or os.path.join(pasta_processed, "base_parceiros.xlsx")
    output_dir = os.path.dirname(output_file) or "."
    os.makedirs(output_dir, exist_ok=True)

    lista_dfs = []

    for arquivo in os.listdir(pasta_raw):
        if not arquivo.endswith(".xlsx"):
            continue

        print("Lendo arquivo:", arquivo)
        path = os.path.join(pasta_raw, arquivo)

        planilhas = pd.read_excel(path, sheet_name=None)

        for nome_aba, df in planilhas.items():
            if not deve_processar_aba(nome_aba, df):
                continue

            print("  -> Incluindo aba:", nome_aba)
            lista_dfs.append(transformar_planilha(df, nome_aba, arquivo))

        os.makedirs(pasta_archive, exist_ok=True)
        shutil.copy2(path, os.path.join(pasta_archive, arquivo))
        print("  [ARCHIVED (copied)]", arquivo)

    if not lista_dfs:
        print("Nenhum dado encontrado.")
        return

    # Filtrar DataFrames vazios antes da concatenação para evitar FutureWarning
    lista_dfs = [df for df in lista_dfs if not df.empty and len(df) > 0]
    
    if not lista_dfs:
        print("Nenhum dado válido encontrado após filtragem.")
        return

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
        "ano",
    ]

    for coluna in colunas_finais:
        if coluna not in df_final.columns:
            df_final[coluna] = None

    df_final = df_final.reindex(columns=colunas_finais)

    # -------- TIPOS --------
    df_final = df_final.astype(
        {
            "Ticket": "string",
            "Estado": "string",
            "Parceiro": "string",
            "Projeto": "string",
            "Nome_Aba": "string",
            "Arquivo_Origem": "string",
            "mes": "string",
            "ano": "Int64",
        }
    )

    df_final["Custo"] = pd.to_numeric(df_final["Custo"], errors="coerce")
    df_final["abertura_chamado"] = pd.to_datetime(df_final["abertura_chamado"], errors="coerce")
    df_final["encerramento_chamado"] = pd.to_datetime(
        df_final["encerramento_chamado"], errors="coerce"
    )

    # Se já existir arquivo base, concatena e remove duplicatas
    if os.path.exists(output_file):
        try:
            df_existente = pd.read_excel(output_file)
            df_final = pd.concat([df_existente, df_final], ignore_index=True, sort=False)
            df_final = df_final.drop_duplicates(ignore_index=True)
        except Exception as e:
            print(f"[WARN] Não foi possível ler/concatenar o arquivo existente: {e}")

    _salvar_resultado(df_final, output_file)

    print("Total de linhas:", len(df_final))
    print(f"Arquivo gerado: {output_file}")
    print("Concluído.")


if __name__ == "__main__":
    run()
