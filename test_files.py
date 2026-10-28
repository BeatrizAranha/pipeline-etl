import pandas as pd
from pathlib import Path

# Teste com um arquivo do archive
arquivo = Path("Data/archive/Fechamento Fevereiro 2025.xlsx")

if arquivo.exists():
    print(f"📄 Testando: {arquivo}")
    try:
        planilhas = pd.read_excel(arquivo, sheet_name=None)
        
        for nome_aba, df in planilhas.items():
            print(f"\n  Aba: {nome_aba}")
            print(f"  Shape: {df.shape}")
            print(f"  Colunas ({len(df.columns)}): ")
            for i, col in enumerate(df.columns[:20]):  # Mostrar apenas 20 primeiras
                print(f"    {i}: '{col}'")
            
            if len(df.columns) > 20:
                print(f"    ... + {len(df.columns) - 20} mais colunas")
            
            # Verificar duplicatas
            duplicatas = df.columns[df.columns.duplicated()].unique()
            if len(duplicatas) > 0:
                print(f"\n  ⚠️  COLUNAS DUPLICADAS ENCONTRADAS:")
                for dup in duplicatas:
                    count = (df.columns == dup).sum()
                    print(f"    '{dup}' aparece {count}x")
            
    except Exception as e:
        print(f"  Erro: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"Arquivo não encontrado: {arquivo}")

