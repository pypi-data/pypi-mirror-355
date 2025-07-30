def deflation_brl(initial_date,final_date,date_column, data_set):
    import subprocess
    import sys
    

    try:
        import sidrapy
        import pandas as pd
        import importlib
    except ImportError:
        print("Packages not installed. \nInstalling now")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "sidrapy","pandas","importlib"])
        sidrapy = importlib.import_module("sidrapy")
        pandas = importlib.import_module("pandas")
        importlib = importlib.import_module("importlib")
        print("packages successfully installed!")
    

    df = data_set
    brl_inflation_dataset = sidrapy.get_table(
        table_code= "1737",
        territorial_level="1",
        ibge_territorial_code="all",
        period="all",
        variable="all"
    )
    ipca = brl_inflation_dataset[brl_inflation_dataset['D3C']=='69'].copy()
    ipca['year'] = ipca['D2C'].str[:4].astype(int)
    ipca['month'] = ipca['D2C'].str[-2:]
    ipca['year'] = pd.to_numeric(ipca['year'])
    ipca_filtered = ipca[
        (ipca['month']=='12') & 
        (ipca['year']>= initial_date) &
        (ipca['year']<= final_date)]
    ipca_filtered['V'] = pd.to_numeric(ipca_filtered['V'])
    deflation =[]
    prod = 1.0
    for _,row in ipca_filtered.iterrows():
        year_ = row['year']
        var = row['V'] / 100.0
        deflation.append({'year':year_,
                          'deflation':prod})
        prod *= (1+var)
    df_deflation = pd.DataFrame(deflation).sort_values('year')
    df_ = df.merge(df_deflation,how='left',left_on =date_column,right_on = 'year')
    return df_




