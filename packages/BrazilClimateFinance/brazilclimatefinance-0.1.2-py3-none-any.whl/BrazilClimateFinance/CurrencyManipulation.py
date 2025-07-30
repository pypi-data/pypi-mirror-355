# BRL Deflation
def deflation_brl(initial_date, final_date, ano_data_column ,data_set):
    
    
    import subprocess
    import sys
    try:
        import sidrapy
        import pandas as pd
        import importlib
        
    except ImportError:
        print("Packages not installed... Installing now")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "sidrapy","pandas","importlib"])
        sidrapy = importlib.import_module("sidrapy")
        pandas = importlib.import_module("pandas")
        importlib = importlib.import_module("importlib")
        print("Packages successfully installed")
    
    df_ = data_set
    
    data = sidrapy.get_table(
        table_code="1737",
        territorial_level="1",
        ibge_territorial_code="all",
        period="all",
        variable="all"
    )
    ipca = data[data['D3C'] == '69'].copy()
    ipca['ano'] = ipca['D2C'].str[:4].astype(int)
    ipca['mes'] = ipca['D2C'].str[-2:]
    ipca['ano'] = pd.to_numeric(ipca['ano'])
    ipca_filtrado = ipca[(ipca['mes'] == '12') & (ipca['ano'] >= initial_date) & (ipca['ano'] <= final_date)]
    ipca_filtrado = ipca_filtrado.sort_values('ano', ascending=False)
    ipca_filtrado['V'] = pd.to_numeric(ipca_filtrado['V'])
    #Realizando deflacao
    deflatores = []
    prod = 1.0
    for _, row in ipca_filtrado.iterrows():
        ano = row['ano']
        var = row['V'] / 100.0
        deflatores.append({'ano': ano, 'deflator': prod})
        prod *= (1 + var)

    df_deflatores = pd.DataFrame(deflatores).sort_values('ano')
    df = df_.merge(df_deflatores, how='left', left_on=ano_data_column, right_on='ano')
    

    return df