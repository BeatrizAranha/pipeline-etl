import streamlit as st
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Adicionar caminho para usar módulos do etl
sys.path.insert(0, str(Path(__file__).parent.parent))

from etl.pipeline import run_pipeline

BASE_DIR = Path(__file__).parent.parent.parent / "Data"
PASTA_RAW = str(BASE_DIR / "_raw")
PASTA_PROCESSED = str(BASE_DIR / "processed")
PASTA_ARCHIVE = str(BASE_DIR / "archive")

st.title("Upload de Arquivos - Performance Parceiros")

st.write("Envie o arquivo Excel para atualizar a base do BI.")

arquivo = st.file_uploader(
    "Selecione o arquivo",
    type=["xlsx"]
)

if arquivo:

    caminho = os.path.join(PASTA_RAW, arquivo.name)

    with open(caminho, "wb") as f:
        f.write(arquivo.getbuffer())

    st.success("Arquivo enviado com sucesso!")

    if st.button("Processar Arquivo"):

        with st.spinner("Executando pipeline..."):

            run_pipeline(
                PASTA_RAW,
                PASTA_PROCESSED,
                PASTA_ARCHIVE
            )

        st.success("Pipeline finalizado! Base atualizada.")
