import pandas as pd
import re
import numpy as np
from unidecode import unidecode
import dask.dataframe as dd
import multiprocessing
import os
import time
import dask.system
def clean_siop(dataset):
     
     
     siop_raw = dataset
     siop_final = siop_raw.iloc[1:]
     siop_final = siop_final[siop_final['Pago'] != 0]
     siop_final.drop(
            columns = ['Projeto de Lei','Dotação Inicial','Dotação Atual'],inplace = True
     )
     siop_final['year'] = pd.to_numeric(siop_final["Ano"],errors = 'coerce')
     siop_final['funcao_cod'] = siop_final['Função'].str.split().str[0]
     siop_final['funcao'] = siop_final['Função'].apply(lambda x: re.sub(r"^\d+\s*-\s*","",x)).str.lower().apply(lambda x: unidecode(x)).apply(lambda x: x.strip())
     siop_final['und_orc_cod'] = siop_final['Unidade Orçamentária'].str.split().str[0]
     siop_final['und_orc'] = siop_final['Unidade Orçamentária'].apply(lambda x: re.sub(r"^\d+\s*-\s*","",x)).str.lower().apply(lambda x: unidecode(x)).apply(lambda x: x.strip())
    #Criando programa e programa_cod
     siop_final['programa_cod'] =siop_final['Programa'].str.split().str[0]
     siop_final['programa'] =siop_final['Programa'].apply(lambda x: re.sub(r"^\d+\s*-\s*","",x)).str.lower().apply(lambda x: unidecode(x)).apply(lambda x: x.strip())
    #Criando acao e acao cod
     siop_final['acao_cod'] =siop_final['Ação'].str.split().str[0]
     siop_final['acao'] =siop_final['Ação'].apply(lambda x: re.sub(r'^\S+\s*-\s*',"",x)).str.lower().apply(lambda x: unidecode(x)).apply(lambda x: x.strip())
    #Criando localizador e localizador_cod
     siop_final['localizador_cod'] =siop_final['Localizador'].str.split().str[0]
     siop_final['localizador'] =siop_final['Localizador'].apply(lambda x: re.sub(r'^\S+\s*-\s*',"",x)).str.lower().apply(lambda x: unidecode(x)).apply(lambda x: x.strip())
    #Criando regiao e regiao_cod
     siop_final['regiao_cod'] =siop_final['Região'].str.split().str[0]
     siop_final['regiao'] =siop_final['Região'].apply(lambda x: re.sub(r'^\S+\s*-\s*',"",x)).str.lower().apply(lambda x: unidecode(x)).apply(lambda x: x.strip())
    #Criando uf e uf_cod
     siop_final['uf_cod'] =siop_final['UF'].str.split().str[0]
     siop_final['uf'] =siop_final['UF'].apply(lambda x: re.sub(r'^\S+\s*-\s*',"",x)).str.lower().apply(lambda x: unidecode(x)).apply(lambda x: x.strip())
    #Criando municipio e municipio_cod
     siop_final['municipio_cod'] =siop_final['Município'].str.split().str[0]
     siop_final['municipio'] =siop_final['Município'].apply(lambda x: re.sub(r'^\S+\s*-\s*',"",x)).str.lower().apply(lambda x: unidecode(x)).apply(lambda x: x.strip())
    #Criando plano_orc e plano_orc_cod
     siop_final['plano_orc_cod'] =siop_final['Plano Orçamentário'].str.split().str[0]
     siop_final['plano_orc'] =siop_final['Plano Orçamentário'].apply(lambda x: re.sub(r'^\S+\s*-\s*',"",x)).str.lower().apply(lambda x: unidecode(x)).apply(lambda x: x.strip())
    #Criando grupo_de_despesa e grupo_de_despesa_cod
     siop_final['grupo_de_despesa_cod'] =siop_final['Grupo de Despesa'].str.split().str[0]
     siop_final['grupo_de_despesa'] =siop_final['Grupo de Despesa'].apply(lambda x: re.sub(r'^\S+\s*-\s*',"",x)).str.lower().apply(lambda x: unidecode(x)).apply(lambda x: x.strip())
    #Criando modalidade e modalidade_cod
     siop_final['modalidade_cod'] =siop_final['Modalidade de Aplicação'].str.split().str[0]
     siop_final['modalidade'] =siop_final['Modalidade de Aplicação'].apply(lambda x: re.sub(r'^\S+\s*-\s*',"",x)).str.lower().apply(lambda x: unidecode(x)).apply(lambda x: x.strip())
    #Criando fonte e fonte_cod
     siop_final['fonte_cod'] =siop_final['Fonte'].str.split().str[0]
     siop_final['fonte'] =siop_final['Fonte'].apply(lambda x: re.sub(r"^\d+\s*-\s*","",x)).str.lower().apply(lambda x: unidecode(x)).apply(lambda x: x.strip()) 
    #Criando subfuncao e subfuncao_cod
     siop_final['subfuncao_cod'] =siop_final['Subfunção'].str.split().str[0]
     siop_final['subfuncao'] =siop_final['Subfunção'].apply(lambda x: re.sub(r'^\S+\s*-\s*',"",x)).str.lower().apply(lambda x: unidecode(x)).apply(lambda x: x.strip())
    #Criando origem_do_credito e origem_do_credito_cod
     siop_final['origem_do_credito_cod'] =siop_final['Origem do Crédito'].str.split().str[0]
     siop_final['origem_do_credito'] =siop_final['Origem do Crédito'].apply(lambda x: re.sub(r'^\S+\s*-\s*',"",x)).str.lower().apply(lambda x: unidecode(x)).apply(lambda x: x.strip())
    #Criando origem_do_credito e origem_do_credito_cod
     siop_final['origem_do_credito_cod'] =siop_final['Origem do Crédito'].str.split().str[0]
     siop_final['origem_do_credito'] =siop_final['Origem do Crédito'].apply(lambda x: re.sub(r'^\S+\s*-\s*',"",x)).str.lower().apply(lambda x: unidecode(x)).apply(lambda x: x.strip())
    #Criando objetivo e objetivo_cod
     siop_final['objetivo_cod'] = np.where(siop_final['Objetivo'] =='[valor não detalhado]',
                                                'SemCodigo',siop_final['Objetivo'].str.split().str[0])
     siop_final['objetivo'] = np.where(
        siop_final['Objetivo'] =='[valor não detalhado]','[valor não detalhado]',siop_final['Objetivo'].apply(lambda x: re.sub(r'^\S+\s*-\s*',"",x)).str.lower().apply(lambda x: unidecode(x)).apply(lambda x: x.strip())
    )
    #Criando empenhado
     siop_final['empenhado'] = pd.to_numeric(siop_final['Empenhado'],errors = 'coerce')
    #Criando Liquidado
     siop_final['liquidado'] = pd.to_numeric(siop_final['Liquidado'],errors = 'coerce')
     return siop_final


def clean_bndes_naut(dataset):
      
      
      
      bndes_naut_ = dataset
       # Ajustando as colunas
      bndes_naut_.columns = (bndes_naut_.columns.str.lower().str.strip().str.replace(" ", "_", regex=False).str.replace("[^0-9a-z_]", "", regex=True))
       # Mudando para formato data e criando coluna de ano
      bndes_naut_['data_da_contratacao'] = pd.to_datetime(bndes_naut_['data_da_contratacao'],format='%Y-%m-%d')
      bndes_naut_['ano'] = bndes_naut_['data_da_contratacao'].dt.year
       # Convertendo todas as strings para minúsculo
      bndes_naut_ = bndes_naut_.applymap(lambda x: x.lower() if isinstance(x, str) else x)
       # Função interna para remover acentos usando regex
      def remove_accentos(texto):

       if isinstance(texto, str):
              texto = re.sub(r'[áàãâä]', 'a', texto)
              texto = re.sub(r'[éèêë]', 'e', texto)
              texto = re.sub(r'[íìîï]', 'i', texto)
              texto = re.sub(r'[óòõôö]', 'o', texto)
              texto = re.sub(r'[úùûü]', 'u', texto)
              texto = re.sub(r'[ç]', 'c', texto)
       return texto
       # Aplicando a remoção de acentos
      bndes_naut_ = bndes_naut_.applymap(lambda x: remove_accentos(x) if isinstance(x, str) else x)
       # Removendo espaços em branco
      bndes_naut_ = bndes_naut_.applymap(  lambda x: x.strip() if isinstance(x, str) else x)
       # Removendo pontos
      bndes_naut_ = bndes_naut_.applymap(lambda x: x.replace('.', '') if isinstance(x, str) else x)
       # Ajustando o tipo numérico (trocando vírgula por ponto)
      bndes_naut_['valor_desembolsado_reais'] = (bndes_naut_['valor_desembolsado_reais'].str.replace(",", "."))
      bndes_naut_['valor_desembolsado_reais'] = pd.to_numeric(bndes_naut_['valor_desembolsado_reais'])
      bndes_naut_['valor_contratado_reais'] = (bndes_naut_['valor_contratado_reais'].str.replace(",", "."))
      bndes_naut_['valor_contratado_reais'] = pd.to_numeric(bndes_naut_['valor_contratado_reais'])
      return bndes_naut_

def create_uniqueID(dataset,year_column,ID_column_name):
     list_dfs = []
     for i in dataset.year_column.unique():
          w = dataset[dataset[year_column]==i]
          w.reset_index(drop = True,inplace = True)
          w[ID_column_name] = w.index.to_series().astype(str) + "_" + w.year_column.astype(str)
          list_dfs.append(w)
     df_ = pd.concat(list_dfs)
     return df_
     


