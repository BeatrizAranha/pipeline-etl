#!/usr/bin/env python
"""Script para processar todos os arquivos da pasta _raw"""

import sys
from pathlib import Path

# Adicionar path para importar módulos
sys.path.insert(0, str(Path(__file__).parent))

from src.etl.pipeline import run_pipeline

BASE_DIR = Path(__file__).parent / "Data"
PASTA_RAW = str(BASE_DIR / "_raw")
PASTA_PROCESSED = str(BASE_DIR / "processed")
PASTA_ARCHIVE = str(BASE_DIR / "archive")

print("=" * 60)
print("PROCESSANDO TODOS OS ARQUIVOS DA PASTA _RAW")
print("=" * 60)

# Contar arquivos
arquivos = list(Path(PASTA_RAW).glob("*.xlsx"))
print(f"\nPasta: {PASTA_RAW}")
print(f"Arquivos encontrados: {len(arquivos)}\n")

for arquivo in arquivos:
    print(f"  - {arquivo.name}")

print("\n" + "=" * 60)

# Rodar pipeline
run_pipeline(PASTA_RAW, PASTA_PROCESSED, PASTA_ARCHIVE)

print("\n" + "=" * 60)
print("PROCESSAMENTO CONCLUÍDO!")
print("=" * 60)
