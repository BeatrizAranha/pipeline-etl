import pandas as pd
from pathlib import Path

# Teste com o arquivo que foi processado
arquivo = Path("Data/archive/Fechamento Fevereiro 2026.xlsx")

if arquivo.exists():
    print(f"📄 Analisando: {arquivo.name}\n")
    try:
        planilhas = pd.read_excel(arquivo, sheet_name=None)
        
        for nome_aba, df in planilhas.items():
            print(f"Aba: '{nome_aba}'")
            print(f"Shape: {df.shape}")
            print(f"Colunas ({len(df.columns)}):")
            
            for i, col in enumerate(df.columns):
                print(f"  [{i}] '{col}'")
            
            # Verificar duplicatas
            duplicatas = df.columns[df.columns.duplicated()].unique()
            if len(duplicatas) > 0:
                print(f"\n⚠️  COLUNAS DUPLICADAS:")
                for dup in duplicatas:
                    count = (df.columns == dup).sum()
                    indices = [j for j, c in enumerate(df.columns) if c == dup]
                    print(f"  '{dup}' {count}x nos índices: {indices}")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"❌ Arquivo não encontrado")
