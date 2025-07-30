def apply_mitigation_KW(database, column_search):
    # Lista de padrões como tuplas (nome_para_rastreio, lista_de_substrings)
    keyword_patterns = {
         #Mitigação climatica
        'MitigacaoClimatica': re.compile(r'\bmiti(?:gar|gação|gaçao|gacão|gacao)\b\s+\bclim(?:á|a)ti(?:ca|cas)\b', re.IGNORECASE),
        "MitigacaoClimatica" : re.compile(r'\bmiti(?:gar|gação|gaçao|gacão|gacao)\b\s+\bdo clima\b', re.IGNORECASE),
        #usina de biodiesel
        'UsinaBiodiesel': re.compile(r'\busi(?:na|nas)\b\s+.*?\bbiodiesel\b', re.IGNORECASE),
        # usina de etanol
        'UsinaEtanol': re.compile(r'\busi(?:na|nas)\b\s+.*?\betanol\b', re.IGNORECASE),
        #usina de alcool
        'UsinaAlcool': re.compile(r'\busi(?:na|nas)\b\s+.*?\b(?:á|a)lcool\b', re.IGNORECASE),
        #combustivel verde
        'CombustivelVerde' : re.compile(r'\bcombustivel\w*\sverde\w*\b', re.IGNORECASE),
        #combustivel eficiente
        'CombustivelEficiente' : re.compile(r'\bcombustivel\w*\seficiente\w*\b', re.IGNORECASE),
        #biodombustivel
        'Biocombustivel': re.compile(r'\bbiocombust(?:ível|ivel|íveis|iveis)\b', re.IGNORECASE),
        #biomassa
        'Biomassa': re.compile(r'\bbiomassa\b', re.IGNORECASE),
        #etanol
        'Etanol': re.compile(r'\betanol\b', re.IGNORECASE),
        #alcool
       'Alcool': re.compile(r'\b(?:á|a)lcool\b\s+.*?\b(?:bio)combus(?:tível|tivel|tíveis|tiveis)\b|\b(?:bio)combus(?:tível|tivel|tíveis|tiveis)\b\s+.*?\b(?:á|a)lcool\b', re.IGNORECASE),
        #biodiesel
        'Biodiesel': re.compile(r'\bbiodiesel\b', re.IGNORECASE),
        #solar
        'Solar': re.compile(r'\bsolar(?:es)?\b', re.IGNORECASE),
        #renovabio
        'Renovabio': re.compile(r'\brenovabio\b', re.IGNORECASE),
        #usina geotermica/geotermal
        'UsinaGeotermica': re.compile(r'\busin(?:a|as)\b\s+\bgeo(?:é|e)rmi(?:ca|cas)\b|\bgeoter(?:mal|mais)\b', re.IGNORECASE),
        #hidreletrica
        'Hidreletrica': re.compile(r'\w*hidrele\w*', re.IGNORECASE),
        #UHE
        'UHE': re.compile(r'\w*uhe\w*', re.IGNORECASE),
        #pch
        'PCH': re.compile(r'\w*pch\w*', re.IGNORECASE),    
        #maremotriz
       'Maremotriz': re.compile(r'\w*maremotriz\w*', re.IGNORECASE),
        #hidrogenio verde
        'HidrogenioVerde': re.compile( r'\bhidro(?:gê|ge)nio\b\s+\bverde\b', re.IGNORECASE),
        #fotovoltaico/fotovoltaica
        'Fotovoltaica': re.compile(r'\w*fotovolt\w*', re.IGNORECASE),
        #minerais estrategicos
        'MineraisEstrategicos': re.compile(r'\bmine(?:ral|rais)\b\s+.*?\bestrat(?:é|e)gi(?:co|cos)', re.IGNORECASE),
        #sustentavel e variações: agricultura sustentavel
        'Sustentavel': re.compile(r'\bsustentave(?:l|is)\b', re.IGNORECASE),
        #Esgotamento Sanitario
        'EsgotamentoSanitario': re.compile(r'\besgot(?:os?|amentos?)\s+sanitarios?\b', re.IGNORECASE),
        #automovel eletrico
        'AutomovelEletrico': re.compile(r'\bautomove(?:l|is)?\s+eletrico[s]?\b|carro[s]?\s+eletrico[s]?\b', re.IGNORECASE),
        #baixo carbono
        'BaixoCarbono': re.compile(r'\bbaixo\s+carbono\b', re.IGNORECASE),
        #ReducaoEmissoes
        'ReducaoEmissoes': re.compile(r'\bredu(?:ção|çao|cão|coa|ções|çoes|coes|cões|zir)\b\s+.*?\bemiss(?:ão|ao|ões|oes)\b|\bemiss(?:ão|ao|ões|oes)\b\s+.*?\bredu(?:ção|çao|cão|coa|ções|çoes|coes|cões|zir)\b', re.IGNORECASE),
        #carbono eficiente
        'CarbonoEficiente': re.compile(r'\bcarbono\s+eficiente\b', re.IGNORECASE),
        #eficiencia energetica
        'EficienciaEnergetica': re.compile(r'\befici(?:ê|e)n(?:cia|ente)\b\s+.*?\benerg(?:ética|etica|ia|ias)\b|\benerg(?:ética|etica|ia|ias)\b\s+.*?\befici(?:ê|e)n(?:cia|ente)\b', re.IGNORECASE),
        #biogas
        'Biogas': re.compile(r'\bbiogas\b', re.IGNORECASE),
        #biodiesel
        'Biodiesel': re.compile(r'\bbiodisel\b', re.IGNORECASE),
        #bioenergia
        'Bioenergia': re.compile(r'\bbioenergia\b', re.IGNORECASE),
        #brt ou bus rapid transitn
       'BRT':  re.compile(r'\bbrt\b|\bbus rapid transition\b', re.IGNORECASE),
        #captura de CO2 ou carbono
        'CapturaCo2': re.compile(r'\bcap(?:tura|turar|turamento)\b\s+.*?\bc(?:arbono|o2)\b', re.IGNORECASE),
         #redução de CO2 ou carbono
        'ReducaoCo2': re.compile(r'\bredu(?:ção|çao|cão|cao|zir)\b\s+.*?\bc(?:arbono|o2)\b', re.IGNORECASE),
        # Efeito estufa
       'EfeitoEstufa': re.compile(r'\befeito estufa\b', re.IGNORECASE),
        #eliminacao de carvao
        'EliminacaoDeCarvao': re.compile(r'\belimin\w*\s+.*?\bcar(?:vão|vao)\b', re.IGNORECASE),
        #descontinuacao carvao
        'DescontinuacaoDeCarvao': re.compile(r'\bdescontinu\w*\s+.*?\bcar(?:vão|vao)\b', re.IGNORECASE),
        #Desativacao carvao:
        'DesativacaoDeCarvao': re.compile(r'\bdesativ\w*\s+.*?\bcar(?:vão|vao)\b', re.IGNORECASE),
        #Descomissionamento Carvao
        'DescomissionamentoCarvao': re.compile(r'\bdescomission\w*\s+.*?\bcar(?:vão|vao)\b', re.IGNORECASE),
        #Coleta de lixo ou seletiva
        'ColetaLixo': re.compile(r'\bcoleta (?:de lixo|seletiva)\b', re.IGNORECASE),
        #Compostagem
        'Compostagem': re.compile(r'\bcompostagem\b', re.IGNORECASE),
         #Unidade Conservacao
        'Conservacao': re.compile(r'\bunidade de conserva[çc]ao\b', re.IGNORECASE),
        #Preservacao ambiental
        'PreservacaoAmbiental': re.compile(r'\bpreserv\w*\s+.*?\bambient(?:e|al|ais)\b', re.IGNORECASE),
        #Conservacao ambiental
        'ConservacaoAmbiental': re.compile(r'\bconserv\w*\s+.*?\bambient(?:e|al|ais)\b', re.IGNORECASE),
        #Ecossistemico
        'Ecossistemico': re.compile(r'\becossistemic\w*\b', re.IGNORECASE),
        #Ecossistema Terrestre
        'EcossistemaTerrestre': re.compile(r'\becossistemic\w*\s+.*?\bterr\w*', re.IGNORECASE),
        #Ecossistema Marinho:
        'EcossistemaMarinho': re.compile(r'\becossistemic\w*\s+.*?\bmar\w*', re.IGNORECASE),
        #Ecossistema Costeiro:
        'EcossistemaCosteiro': re.compile(r'\becossistemic\w*\s+.*?\bcost\w*', re.IGNORECASE),
        #Conservacao Terra Indigena
        'ConservacaoTerraIndigena': re.compile(r'\bconserv\w*\s+.*?\bterr(?:a|as|itorial|itoriais)\b\s+.*?\bind(?:í|i)ge(?:na|nas)\b', re.IGNORECASE),
        'PreservacaoTerraIndigena': re.compile(r'\bpreserv\w*\s+.*?\bterr(?:a|as|itorial|itoriais)\b\s+.*?\bind(?:í|i)ge(?:na|nas)\b', re.IGNORECASE),
        #GestaoTerritorial Indigena
        'GestaoTerritorialIndigena': re.compile(r'\bge(?:rir|stão|tao)\b\s+.*?\bterr(?:a|as|itorial|itoriais)\b\s+.*?\bind(?:í|i)ge(?:na|nas)\b', re.IGNORECASE),
        #Conservacao Biodiversidade
        'ConservacaoBiodiversidade': re.compile(r'\bconserv\w*\s+.*?\bbiodiv\w*', re.IGNORECASE),
        #Conservacao Especies
        'ConservacaoEspecies': re.compile(r'\bconserv\w*\s+.*?\besp(?:é|e)ci(?:e|es)\b', re.IGNORECASE),
        #Conservacao Natureza
        'ConservacaoNatureza': re.compile(r'\bconservacao da natureza\b', re.IGNORECASE),
        #Conservacao de Florestas
        'ConservacaoFlorestas': re.compile(r'\bconserv\w*\s+.*?\bflores(?:ta|tas|tal|tais)\b', re.IGNORECASE),
        #Floresta Nativa
        'FlorestaNativa': re.compile(r'\bfloresta nativa\b|\bflorestas nativas\b', re.IGNORECASE),
        #Restauracao
        'RestauracaoAmbiental': re.compile(r'\brestau(?:ração|raçao|racão|racao|rar|ra|rabilidade)\b\s+.*?\bambien(?:tal|tais)\b', re.IGNORECASE),
        #Credito de Carbono
        'CreditoCarbono': re.compile(r'\bcreditos? de carbono\b', re.IGNORECASE),
        #Descarbonizacao
        'Descarbonizacao': re.compile(r'\bdescarbon\w*\b', re.IGNORECASE),
        #Desempenho Energetico
        'DesempenhoEnergetico': re.compile(r'\bdesempe\w*\s+.*?\benerg\w*', re.IGNORECASE),
        #Combate ao desmatamento
        'CombateDesmatamento': re.compile(r'\bcombat\w*\s+.*?\bdesmat\w*', re.IGNORECASE),
        #Uso sustentavel
        'UsoSustentavel': re.compile(r'\buso\b\s+.*?\bsusten\w*', re.IGNORECASE),
        #Exploracao sustentavel
        'ExploracaoSustentavel': re.compile(r'\bexplora\w*\s+.*?\bsusten\w*', re.IGNORECASE),
        #Producao sustentavel
        'ProducaoSustentavel': re.compile(r'\bprodu\w*\s+.*?\bsusten\w*', re.IGNORECASE),
        #Despoluicao
        'Despoluicao': re.compile(r'\bdespolu\w*', re.IGNORECASE),
        #Despoluicao agua
        'DespoluicaoAgua': re.compile(r'\bdespolu\w*\s+.*?\b(?:á|a)gu(?:a|as)\b', re.IGNORECASE),
        #Recursos Naturais
        'RecursosNaturais': re.compile(r'\brecur(?:so|sos)\b\s+.*?\bnatura\w*', re.IGNORECASE),
        #Destinação residuo / rejeito / 
        'DestinacaoResiduo': re.compile(r'\bdestina\w*\s+.*?\bres(?:í|i)du(?:o|os)\b', re.IGNORECASE),
        'DestinacaoRejeito': re.compile(r'\bdestina\w*\s+.*?\brejei(?:to|tos)\b', re.IGNORECASE),
        # Faixa dedicada a onibus
        'FaixaDedidacaOnibus': re.compile(r'\bfaix(?:a|as)\b\s+.*?\bdedica(?:da|das)\b\s+.*?\b(?:ô|o)nibus\b', re.IGNORECASE),
        'FaixaExclusivaOnibus': re.compile(r'\bfaix(?:a|as)\b\s+.*?\bexclusi(?:va|vas|vidade|vidades)\b\s+.*?\b(?:ô|o)nibus\b', re.IGNORECASE),
        #Floresta Viva
        'FlorestaViva': re.compile(r'\bflores(?:ta|tas)\b\s+.*?\bvi(?:va|vas)\b', re.IGNORECASE),
        #Metro / metrovia
        'Metro': re.compile(r'\bmetr(?:os?|ovias?)\b', re.IGNORECASE),
        #Reducao do consumo/gasto/desperdicio de energia
        'ReducaoEnergia': re.compile(r'\bredu(?:zir|ção|çao|cão|cao)\b\s+.*?\benerg\w*', re.IGNORECASE),
        # Transporte nao motorizado
        'TransporteNaoMotorizado': re.compile(r'\btransport\w*\s+.*?\b(?:não|nao) motoriza(?:do|dos)', re.IGNORECASE),
        # Trens de passageiro
        'TremPassageiro': re.compile(r'\btrem\b\s+.*?\bpassagei(?:ro|ros)\b', re.IGNORECASE),
        # Veiculo eletrico
        'VeiculoEletrico': re.compile(r'\bve(?:í|i)cul(?:o|os)\b\s+.*?\bel(?:é|e)tri(?:co|cos)', re.IGNORECASE),
        #TransporteFerroviarioUrbano
        'TransporteFerroviarioUrbano': re.compile(r'\btranspor(?:te|tes)\b\s+.*?\bferrov\w*\s+.*?\burban\w*', re.IGNORECASE),
        #Trem Metropole Urbano
        'TremMetropole': re.compile(r'\btrem\b\s+.*?\bmetr(?:ó|o)pol(?:e|es)\b', re.IGNORECASE),
        #BRT
        'BRT': re.compile(r'\ssistema\b\s+.*?\btransporte\b\s+.*?\br(?:á|a)pido\b|\bbrt\b|\bbus rapid transport\b', re.IGNORECASE),
        #VLT
        'VLT': re.compile(r"\bve(?:í|i)culo leve sob(?:re|) trilho(?:s|)\b|\bVLT\b", re.IGNORECASE),
        #Metroviario
        'Metroviario': re.compile(r'\bmetroviari\w*\b', re.IGNORECASE),
        #carbono zero
        'CarbonoZero': re.compile(r'\bcarbono\s+zero\b', re.IGNORECASE),
        #captura de carbono ou metano
        'CapturaCarbono': re.compile(r'\bcaptur\w*\s+.*?\b(?:carbono|co2)\b', re.IGNORECASE),
        'CapturaMetano': re.compile(r'\bcaptur\w*\s+.*?\bmetano\b', re.IGNORECASE),
        # Turbina eolica / Central Geradoda Eolica / Parque eolico / Complexo Eolico
        'TurbinaEolica': re.compile(r'\bturbinas?\s+e[oó]licas?\b', re.IGNORECASE),
        #CentralGeradoraEolica
        'CentralGeradoraEolica': re.compile(r'\bgerador\w*\s+e[oó]licas?\b', re.IGNORECASE),
        #ParqueEolico
        'ParqueEolico': re.compile(r'\bparques?\s+e[oó]licos?\b', re.IGNORECASE),
        #ComplexoEolico
        'ComplexoEolico': re.compile(r'\bcomplexos?\s+e[oó]licos?\b', re.IGNORECASE),
        #Descontinuacao aterro
        'DescontinuacaoAterro': re.compile(r'\bdescontinu\w*\s+.*?\baterr(?:o|os)\b', re.IGNORECASE),
        #Desativacao aterro:
        'DesativacaoAterro': re.compile(r'\bdesativa\w*\s+.*?\baterr(?:o|os)\b', re.IGNORECASE),
        #Descomissionamento aterro:
        'DescomissionamentoAterro': re.compile(r'\bdescomissiona\w*\s+.*?\baterr(?:o|os)\b', re.IGNORECASE),
        #Bioeconomia
        'Bioeconomia': re.compile(r'\bbioeconomia\w*', re.IGNORECASE),
         #EconomiaCircular
        'EconomiaCircular': re.compile(r'\beconomia\s+circular\b', re.IGNORECASE),
        #CapturaFossil
        'CapturaFossil': re.compile(r'\bcaptura\w*\s+.*?\bcombust\w*\s+.*?\bf(?:ó|o)ss\w*', re.IGNORECASE),
        #ReducaoFossil
        'ReducaoFossil': re.compile(r'\bredu(?:ção|çao|cão|cao|zir|z)\b\s+.*?\bcombust\w*\s+.*?\bf(?:ó|o)ss\w*', re.IGNORECASE),
        #ReducaoEmissao
        'ReducaoEmissao': re.compile(r'\bredu(?:ção|çao|cão|cao|zir|z)\b\s+.*?\bemiss(?:ão|ao|ões|oes)\b', re.IGNORECASE),
        #Geodiversidade:
        'Geodiversidade:': re.compile(r'\bgeodiversidade\b', re.IGNORECASE),
        #PesquisaEcologica:
        'PesquisaEcologica': re.compile(r'\bpesqui\w*\s+.*?\becol(?:ó|o)gi\w*', re.IGNORECASE),
        #RecuperacaoBaciaHidrografica:
        'RecuperacaoBaciaHidrografica': re.compile(r'\brecupera\w*\s+.*?\bbaci(?:a|as)\b\s+.*?\bhidrogr(?:á|a)fic(?:a|as)\b', re.IGNORECASE),
        #ConservacaoBaciaHidrografica:
        'ConservacaoBaciaHidrografica': re.compile(r'\bconserva\w*\s+.*?\bbaci(?:a|as)\b\s+.*?\bhidrogr(?:á|a)fic(?:a|as)\b', re.IGNORECASE),
        #RegularizacaoFundiaria
        'RegularizacaoFundiaria': re.compile(r'\bregulariza\w*\s+.*?\bfundi(?:á|a)ri(?:a|as)\b', re.IGNORECASE),
        #Conservacao recursos hidricos
        'ConservacaoRecursosHidricos': re.compile(r'\bconser(?:var|vação|vaçao|vacão|vacao)\b\s+.*?\brecurs(?:os|o)\b\s+.*?\b(?:hí|hi)dri(?:co|cos)\b', re.IGNORECASE),
        #Conservacao recursos naturais
       'ConservacaoRecursosNaturais': re.compile(r'\bconser(?:var|vação|vaçao|vacão|vacao)\b\s+.*?\brecur(?:so|sos)\b\s+.*?\bnatu(?:ral|rais)\b', re.IGNORECASE),
        #MitigacaoDesastres
        'MitigacaoDesastres': re.compile(r'\bmitig\w*\s+.*?\bdesas(?:tre|tres)\b', re.IGNORECASE),
        #Biometano
        'Biometano': re.compile(r'\bbiometano\b', re.IGNORECASE),
        #ProgramaFlorestal
        'ProgramaFlorestal': re.compile(r'\bprograma\w*\b(?:\s+\w+){0,5}?\s+\bflorest\w*\b', re.IGNORECASE),
        #MonitoramentoUsoCoberturaTerra
        'MonitoramentoUsoCoberturaTerra': re.compile(r'\bmonito\w*\s+.*?\b(?:uso|uso e cobertura)\b\s+.*?\bterra\b', re.IGNORECASE),
        #MonitoramentoAmbiental
        'MonitoramentoAmbiental': re.compile(r'\bmonito\w*\s+.*?\bambient\w*', re.IGNORECASE),
         #CadastroAmbientalRural
        'CadastramentoAmbientalRural': re.compile(r'\bcadastro\s+ambiental\s+rural\b|\bCAR\b', re.IGNORECASE),
        #Regularizacao Ambiental 
        'Regularizacao Ambiental': re.compile(r'\bregulariza\w*\s+ambiental\b', re.IGNORECASE),
        #Assentamento
        'Assentamento': re.compile(r'\bassentamentos?\b', re.IGNORECASE),
        #Agroecologia/Agroecologico
        'Agroecologia': re.compile(r'\bagroecolog\w*\b', re.IGNORECASE),
        #Horta
        'Horta': re.compile(r"\bhor(?:ta|tas)\b",re.IGNORECASE),
        #Viveiro
        'Viveiro': re.compile(r'\bviveiros?\b', re.IGNORECASE),
        #Controle Ambiental
        'ControleAmbiental': re.compile(r'\bcontrole\b(?:\s+\b\w+\b){0,5}?\s+\bambiental\b', re.IGNORECASE),
        #Licenciamento Ambiental 
        'LicenciamentoAmbiental': re.compile(r'\blicenciamento\s+ambiental\b', re.IGNORECASE),
        #Informacao Ambiental 
        'InformacaoAmbiental': re.compile(r'\binformac\w*(?:\s+\w+){0,5}?\s+ambient\w*\b', re.IGNORECASE),
        #SISNAMA
        'SISNAMA': re.compile(r'\bsisnama\b', re.IGNORECASE),
         #Celulose:
        'Celulose': re.compile(r'\bcelulose\b', re.IGNORECASE),
         #retrofit:
        'Retrofit': re.compile(r'\bretrofit\b', re.IGNORECASE),
        #codigo florestal
        'CodigoFlorestal': re.compile(r'\bcodigo\s+florestal\b', re.IGNORECASE),
        #Lei de protecao da vegetacao nativa
        'LPVN': re.compile(r'\blei\s+de\s+protecao\s+da\s+vegetacao\s+nativa|LPVN\b', re.IGNORECASE),
        #Proteção Mangue
        'ProteçãoMangue': re.compile(r'\bprote(?:ção|çao|cão|cao|ger|gem)\b\s+.*?\bman(?:gue|gues)\b', re.IGNORECASE),
        #Restauracao Coral
        'RestauracaoCoral': re.compile(r'\brestau(?:rar|ra|ração|raçao|racão|racao)\b\s+.*?\bco(?:ral|rais)', re.IGNORECASE),
        #Protecao Coral
        'ProtecaoCoral': re.compile(r'\bprote(?:ção|çao|cão|cao|ger|gem)\b\s+.*?\bco(?:ral|rais)\b', re.IGNORECASE),
        #Mitigacao Erosao Ecossistema Costeiro
        'MitigacaoErosaoEcossitemaCosteiro': re.compile(r'\bmitiga(?:r|ção|çao|cão|cao)\b\s+.*?\bero(?:são|sao)\b\s+.*?\becossiste(?:mas|ma)\b\s+.*?\bcostei(?:ro|ros)\b', re.IGNORECASE),
        #Povos e ComunidadeIndigena
        'PovoIndigena': re.compile(r'\b(?:povos|comunidades)\b\s+.*?\bind(?:í|i)genas\b', re.IGNORECASE),
        #Povos e Comunidades Tradicionais 
        'ComunidadeTradicional': re.compile(r'\b(?:povos|comunidades)\b\s+.*?\btradicionais\b', re.IGNORECASE),
        #SistemaAgroflorestal
        'SistemaAgroflorestal': re.compile(r'\bsistem(?:a|as)\b\s+\bagroflores(?:tal|tais)\b|\bsaf\b|\bagroflores(?:ta|tas)\b', re.IGNORECASE),
        #Desertificacao
        'Desertificacao': re.compile(r'\bdesertificacao\b', re.IGNORECASE),
        #PatrimonioNatural
        'PatrimonioNatural': re.compile(r'\bpatrimonio\s+natural\b', re.IGNORECASE),
        #CadastroTerras
        'CadastroTerras': re.compile(r'\bcadastr\w*(?:\s+\w+){0,5}?\s+\bterras?\b', re.IGNORECASE),
        #SateliteAmazonia
        'SateliteAmazonia': re.compile(r'\bsatelites?\b\s+.*?\b\amaz(?:ônia|onia|onas|)\b', re.IGNORECASE),
        #SateliteCientifico
        'SateliteCientifico': re.compile(r'\bsatelites?\b\s+.*?\bcientificos?\b', re.IGNORECASE),
        #RedeHidrometeorologica
        'RedeHidrometeorologica': re.compile(r'\bredes?\s+\bhidrometeorologicas?\b', re.IGNORECASE),
        #QualidadeAgua
        'QualidadeAgua': re.compile(r'\bqualidade(?:\s+\w+){0,5}?\s+(?:aguas?|hidric\w)\b', re.IGNORECASE),
        #BagacoCana
        'BagacoCana': re.compile(r'\bbaga(?:ç|c)os?(?:\s+\w+){0,10}?\s+\bcana\w*\b', re.IGNORECASE),
        #AgriculturaUrbana
        "AgriculturaUrbana" : re.compile(r"\bagricul(?:tor|tura|turas)\b\s+\burban(?:a|as|o|os)\b", re.IGNORECASE),
        #EnergiaRenovavel
        "EnergiaRenovavel" : re.compile(r"\benergi(?:a|as)\b\s+\brenova(?:vel|veis)\b", re.IGNORECASE),
        #PoliticaNacionalMudancadoClima
        "PoliticaNacionalMudancadoClima" : re.compile(r"\bpo(?:lí|li)tic(?:a|as)\b\s+\bnacio(?:nal|nais)\b\s+.*?\bmudan(?:ça|ca|ças|cas)\b\s+.*?\bclima\w*", re.IGNORECASE),
        #PesquisaClima
        "PesquisaClima" : re.compile(r"\bpesqui(?:sa|sar|sas)\b\s+.*?\bcli(?:ma|mática|matica|matico|mático)\b", re.IGNORECASE),
        #PesquisaEcossistemaAmazonico
        "PesquisaEcossistemaAmazonico" : re.compile(r"\bpesqui(?:sa|sar|sas)\b\s+.*?\becossist(?:ema|emas|êmica|êmicas|emica|emicas|êmico|êmicos|emico|emicos)\b\s+.*?\bama(?:zônico|ônicos|onico|onicos|zônica|zônicas|zonica|zonicas|zonia|zônia)\b",re.IGNORECASE),
        #DesenvolvimentoProducaoOrganica
        "DesenvolvimentoProducaoOrganica" : re.compile(r"\bdesenvol(?:ver|verem|volvimento|volvimentos|vem)\b\s+.*?\bprodu(?:ção|çao|cão|cao|ções|çoes|cões|coes|zir|zirem)\b\s+.*?\borg(?:â|a)ni(?:ca|cas)\b", re.IGNORECASE),
        #EducacaoAmbiental
        "EducacaoAmbiental" : re.compile(r"\beduca(?:ção|çao|cão|cao)\b\s+\bambiental\b", re.IGNORECASE),
        #GestaoNacionalRecursoFlorestal
        "GestaoNacionalRecursoFlorestal" : re.compile(r"\bge(?:rir|stão|stao)\b\s+.*?\brecur(?:so|sos)\b\s+.*?\bflores(?:ta|tal|tais)\b", re.IGNORECASE),
        #SistemaNacionalCadastroRural
        "SistemaNacionalCadastroRural" : re.compile(r"\bsiste(?:ma|mas)\b\s+\bnacional\b\s+.*?\bcadastr(?:amento|o|os)\b\s+\bru(?:ral|rais)\b", re.IGNORECASE),
        #ImplementacaoCadastroImoveisRurais
        "ImplementacaoCadastroImoveisRurais" : re.compile(r"\bimplemen(?:tar|tação|taçao|tacão|tacao)\b\s+.*?\bcadastr(?:amento|o|os)\b\s+.*?\bim(?:ó|o)(?:vel|veis)\s+\bru(?:ral|rais)\b", re.IGNORECASE),
        #EstruturacaoSistemasGestaoFundiaria
        "EstruturacaoSistemasGestaoFundiaria" : re.compile(r"\bestrutu(?:rar|ração|raçao|racão|racao)\b\s+.*?\bsiste(?:ma|mas)\b\s+.*?\bges(tão|tao)\b\s+\bfundi(?:á|a)ri(?:a|as)\b", re.IGNORECASE),
        #PesquisaPopulacaoIndigena
        "PesquisaPopulacaoIndigena" : re.compile(r"\bpesqui(?:sar|sa)\b\s+.*?\bpopula(?:ção|çao|cão|cao|ções|çoes|cões|coes)\b\s+.*?\bind(?:í|i)ge(?:na|nas)\b", re.IGNORECASE),
        #PesquisaAgropecuaria
        "PesquisaAgropecuaria" : re.compile(r"\bpesqui(?:sar|sa)\b\s+.*?\bagropecu(?:á|a)ri(?:a|as)\b", re.IGNORECASE),
        #PesquisaMeteorologia
        "PesquisaMeteorologia" : re.compile(r"\bpesqui(?:sar|sa)\b\s+.*?\bmeteoro(?:lógica|logica|lógico|logico|logia|logias)\b", re.IGNORECASE),
        #PesquisaFlora
        "PesquisaFlora": re.compile(r"\bpesqui(?:sa|sar)\b\s+.*?\bflo(?:ra|ras)\b", re.IGNORECASE),
        #IrrigacaoSocial
        "IrrigacaoSocial" : re.compile(r"\birrig(?:ação|açao|acão|acao)\b\s+\bsoci(?:al|ais)\b", re.IGNORECASE),
        #PesquisaOceanica
        "PesquisaOceanica" : re.compile(r"\bpesquisa\b\s+.*?\boce(?:â|a)ni(?:ca|cas)\b", re.IGNORECASE),
        #FiscalizacaoFlora
        "FiscalizacaoFlora" : re.compile(r"\bfiscali(?:zar|zação|zaçao|zacão|zacao)\b\s+.*?\bflo(?:ra|ras)\b", re.IGNORECASE),
        #FiscalizacaoEmpreendimentosPoluidores
        "FiscalizacaoEmpreendimentosPoluidores" : re.compile(r"\bfiscali(?:zar|zação|zaçao|zacão|zacao)\b\s+.*?\bempreendimen(?:to|tos)\b\s+.*?\bpoluid(?:or|ores)\b", re.IGNORECASE),
        #FiscalizacaoCadastroRural
        "FiscalizacaoCadastroRural" : re.compile(r"\bfiscali(?:zar|zação|zaçao|zacão|zacao)\b\s+.*?\bcadastr(?:amento|o|os)\b\s+\bru(?:ral|rais)", re.IGNORECASE),
        #FiscalizacaoTerraIndigena
        "FiscalizacaoTerraIndigena" : re.compile(r"\bfiscali(?:zar|zação|zaçao|zacão|zacao)\b\s+.*?\bterr(?:a|as)\b\s+\bind(?:í|i)gen(?:a|as)\b", re.IGNORECASE),
        #InovacaoCienciasAgrarias
        "InovacaoCienciasAgrarias" : re.compile(r"\binova(?:ção|çao|cão|cao|ções|çoes|cões|coes)\b\s+.*?\bci(?:ên|en)ci(?:a|as)\b\s+.*?\bagr(?:á|a)ri(?:a|as)\b", re.IGNORECASE),
        #ProducaoAgroalimentarArtesanal
        "ProducaoAgroalimentarArtesanal" : re.compile(r"\bprodu(?:ção|çao|cão|cao)\b\s+.*?\bagroalimentar\b\s+.*?\bartesanal\b", re.IGNORECASE),
        #MelhoriaQualidadeAmbiental
        "MelhoriaQualidadeAmbiental" : re.compile(r"\bmelhoria\b\s+.*?\bqualidade\b\s+.*?\bambiental\b", re.IGNORECASE),
        #PoliticaNacionalEducacaoAmbiental
        "PoliticaNacionalEducacaoAmbiental" : re.compile(r"\bpol(?:í|i)tic(?:a|as)\b\s+.*?\bnacio(?:nal|nais)\b\s+.*?\beduca(?:ção|çao|cão|cao|ções|çoes|cões|coes)\b\s+\bambien(?:tal|tais)\b", re.IGNORECASE),
        #AprimoramentoQualidadeAmbiental
        "AprimoramentoQualidadeAmbiental" : re.compile(r"\baprimoramento\b\s+.*?\bqualidade\b\s+.*?\bambiental\b", re.IGNORECASE),
        #FuncionamentoLaboratoriosAgropecuarios
        "FuncionamentoLaboratoriosAgropecuarios" : re.compile(r"\bfuncionament(?:o|os)\b\s+.*?\blabora(?:tó|to)ri(?:o|os)\b\s+\bagropecu(?:á|a)ri(?:os|o)\b", re.IGNORECASE),
        #SistemaProtecaoAmazonia
        "SistemaProtecaoAmazonia" : re.compile(r"\bsiste(?:ma|mas)\b\s+.*?\bprote(?:ção|çao|cão|cao)\b\s+.*?\bama(?:zô|zo)ni(?:a|as)\b",re.IGNORECASE),
        #GeorreferenciamentoMalhaFundiaria
        "GeorreferenciamentoMalhaFundiaria" : re.compile(r"\bgeorreferenciamento\b\s+.*?\bmalh(?:a|as)\b\s+.*\bfundi(?:á|a)ri(?:a|as)\b",re.IGNORECASE),
        #GerenciamentoCadastroRural
        "GerenciamentoCadastroRural" : re.compile(r"\bgerenciamento\b\s+.*?\bcadastr(?:o|os)\b\s+\brur(?:al|ais)\b",re.IGNORECASE),
        #GestaoPoliticaMudancaClima
        "GestaoPoliticaMudancaClima" : re.compile(r"\bgest(?:ão|ao)\b\s+.*?\bpol(?:í|i)tic(?:a|as)\b\s+.*?\bmudan(?:ça|ca|ças|cas)\b\s+.*?\bcli(?:ma|mas)\b",re.IGNORECASE),
        #GestaoPoliticaAmbiental
        "GestaoPoliticaAmbiental" : re.compile(r"\bgest(?:ão|ao)\b\s+.*?\bpol(?:í|i)tic(?:a|as)\b\s+.*?\bambiental\b",re.IGNORECASE),
        #GestaoPoliticaMeioAmbiente
        "GestaoPoliticaMeioAmbiente" : re.compile(r"\bgest(?:ão|ao)\b\s+.*?\bpol(?:í|i)tic(?:a|as)\b\s+.*?\bmeio ambiente\b",re.IGNORECASE),
        #GestaoPoliticaRecursosHidricos
        "GestaoPoliticaRecursosHidricos" : re.compile(r"\bgest(?:ão|ao)\b\s+.*?\bpol(?:í|i)tic(?:a|as)\b\s+.*?\brecur(?:so|sos)\b\s+\bh(?:í|i)dric(?:o|os)\b",re.IGNORECASE),
        #MonitoramentoTerritorial
        "MonitoramentoTerritorial" : re.compile(r"\bmonitoramento\b\s+.*?\bterritorial\b",re.IGNORECASE),
        #MonitoramentoSateliteBioma
        "MonitoramentoSateliteBioma" : re.compile(r"\bmonitoramento\b\s+.*?\bsat(?:é|e)li(?:te|tes)\b\s+.*?\bbio(?:ma|mas)\b",re.IGNORECASE),
        #MonitoramentoFloresta
        "MonitoramentoFloresta" : re.compile(r"\bmonito(?:rar|ramento)\b\s+.*?\bflores(?:ta|tal|tais|tas|tamento|tamentos)\b",re.IGNORECASE),
        #ManejoFaunaSilvestre
        "ManejoFaunaSilvestre" : re.compile(r"\bmane(?:jar|jo)\b\s+.*?\bsilves(?:tre|tres)\b",re.IGNORECASE),
        # LicencaAmbiental
        "LicencaAmbiental" : re.compile(r"\blicen(?:ça|ças|ca|cas|ciamento|ciamentos)\b\s+\bambien(?:tal|tais)\b",re.IGNORECASE),
        # LevantamentoInformacoesSolo
        "LevantamentoInformacoesSolo" : re.compile(r"\blevantament(?:o|os)\b\s+.*?\binforma(?:ção|çao|cão|cao|ções|çoes|cões|coes)\b\s+.*?\bso(?:lo|los)\b",re.IGNORECASE),
        # InventarioFlorestalNacional
        "InventarioFlorestalNacional" : re.compile(r"\binven(?:tá|ta)ri(?:o|os)\b\s+.*?\bflores(?:ta|tas)\b\s+\bnacio(?:nal|nais)\b",re.IGNORECASE),
        # InfraestruturaComunitaria
        "InfraestruturaComunitaria" : re.compile(r"\binfraestrutu(?:ra|ras)\b\s+.*?\bcomunit(?:á|a)ri(?:a|as)\b",re.IGNORECASE),
        #BenfeitoriaComunidadesQuilombolas
        "BenfeitoriaComunidadesQuilombolas" : re.compile(r"\bbenfeito(?:ria|rias)\b\s+.*?\bcomunida(?:de|des)\b\s+.*?\bquilom(?:bo|bola|bolas)\b",re.IGNORECASE),
        # QualidadeAmbientalUrbana
        "QualidadeAmbientalUrbana" : re.compile(r"\bqualidade\b\s+.*?\bambient(?:al|ais)\b\s+\burban(?:a|as)\b",re.IGNORECASE),
        # PoliticaNacionalGestaoFlorestal
        "PoliticaNacionalGestaoFlorestal" : re.compile(r"\bpol(?:í|i)tic(?:a|as)\b\s+\bnacional\b\s+.*?\bgest(?:ão|ao)\b\s+\bflorestal\b",re.IGNORECASE),
        # ImplantacaoSistemaAmazonia
        "ImplantacaoSistemaAmazonia" : re.compile(r"\bimplan(?:tação|taçao|tacão|tacao|tar)\b\s+.*?\bsiste(?:ma|mas)\b\s+.*?\bama(?:zô|zo)nia\b",re.IGNORECASE),
        #GestaoSubstanciasQuimicas
        "GestaoSubstanciasQuimicas" : re.compile(r"\bgest(?:ão|ao)\b\s+.*?\bsubs(?:tâ|ta)nci(?:a|as)\b\s+.*?\bqu(?:í|i)mic(?:as|a)\b",re.IGNORECASE),
        #GestaoColecaoViva
        "GestaoColecaoViva" : re.compile(r"\bgest(?:ão|ao)\b\s+.*?\bcole(?:ção|çao|ções|çoes|cão|cao|cões|coes)\b\s+\bvi(?:vas|va)\b",re.IGNORECASE),
        #GestaoCavernas
        "GestaoCavernas" : re.compile(r"\bgest(?:ão|ao)\b\s+.*?\bcaver(?:nas|na)\b",re.IGNORECASE),
        #GestaoTerrasPublicas
        "GestaoTerrasPublicas" : re.compile(r"\bgest(?:ão|ao)\b\s+.*?\bterr(?:a|as)\b\s+\bp(?:ú|u)blic(?:a|as)\b",re.IGNORECASE),
        #SistemaNacionalInformacaoFlorestal
        "SistemaNacionalInformacaoFlorestal" : re.compile(r"\bsistem(?:ma|mas)\b\s+\bnacion(?:nal|nais)\b\s+.*?\binforma(?:ção|çao|cão|cao|ções|çoes|cões|coes)\b\s+\bflorest(?:al|ais|a)\b",re.IGNORECASE),
        #RegularizacaoTerraIndigena
        "RegularizacaoTerraIndigena" : re.compile(r"\bregulari(?:zar|zação|zaçao|zacão|zacao)\b\s+.*?\bterr(?:a|itorio|as|itorios|itório|itórios)\b\s+\bind(?:í|i)gen(?:a|as)\b",re.IGNORECASE),
        #PesquisaAquicultura
        "PesquisaAquicultura" : re.compile(r"\bpesqui(?:sa|sas|sar)\b\s+.*?\baquicul(?:tura|turas)\b",re.IGNORECASE),
        #PesquisaCientificaAntartica
        "PesquisaCientificaAntartica" : re.compile(r"\bpesqui(?:sa|sas|sar)\b\s+.*?\bcien(?:tí|ti)fi(?:ca|cas)\b\s+.*?\bant(?:á|a)rti(?:a|o)\b",re.IGNORECASE),
        #PlanoNacionalGestaoRiscosRespostasDesastresNaturais
        "PlanoNacionalGestaoRiscosRespostasDesastresNaturais" : re.compile(r"\bplano\b\s+\bnacional\b\s+.*?\bgest(?:ão|ao)\b\s+.*?\bris(?:co|cos)\b\s+.*?\brespos(?:tas|ta)\b\s+.*?\bdesas(?:tre|tres)\b\s+\bnatur(?:ais|al)\b",re.IGNORECASE),
        #ReabilitacaoBarragem
        "ReabilitacaoBarragem" : re.compile(r"\breabilita(?:ção|çao|cão|cao|ções|çoes|cões|coes)\b\s+.*?\bbarrag(?:em|ens)\b",re.IGNORECASE),
        #DesenvolvimentoInformacaoGeorreferenciada
        "DesenvolvimentoInformacaoGeorreferenciada" : re.compile(r"\bdesen(?:volver|volvimento|volvimentos)\b\s+.*?\binforma(?:ção|ções|çao|çoes|cão|cões|cao|coes)\b\s+.*?\bgeorreferenciada\b",re.IGNORECASE),
        #EstudoHidrogeologico
        "EstudoHidrogeologicoHidrologico" : re.compile(r"\bestu(?:do|dos)\b\s+.*?\bhidro(?:lógico|logico|lógicos|logicos|geológico|geológicos|geologico|geologicos)\b",re.IGNORECASE),
        #GestaoInformacaoGeologica
        "GestaoInformacaoGeologica" : re.compile(r"\bges(?:tão|tao)\b\s+.*?\binforma(?:ção|çao|cão|cao|ções|cões|çoes|coes)\b\s+.*?\bgeo(?:ló|lo)gi(?:ca|co|cas|cos)\b",re.IGNORECASE),
        #DesenvolvimentoSemiarido
        "DesenvolvimentoSemiarido" : re.compile(r"\bdesenvol(?:ver|vimento|vimentos)\b\s+.*?\bsemi(?:á|a)ri(?:do|dos)\b",re.IGNORECASE),
        #ProdutosSociobiodiversidade
        "ProdutosSociobiodiversidade" : re.compile(r"\bprodu(?:to|tos)\b\s+.*?\bsociobiodiversidad(?:e|es)\b",re.IGNORECASE),
        #CooperativismoAgropecuario
        "CooperativismoAgropecuario" : re.compile(r"\bcooperativismo\b\s+.*?\bagropecu(?:á|a)ri(?:a|as|o|os)\b",re.IGNORECASE),
        #DesenvolvimentoPrevisaoClima
        "DesenvolvimentoPrevisaoClima" : re.compile(r"\bdesenvol(?:ver|vimento|vimentos)\b\s+.*?\bpre(?:ver|visão|visao)\b\s+.*?\bclim(?:a|as)\b",re.IGNORECASE),
        #FormacaoRecursosHumanosMeioAmbiente
        "FormacaoRecursosHumanosMeioAmbiente" : re.compile(r"\bform(?:ar|ação|açao|acão|acao)\b\s+.*?\brecur(?:so|sos)\b\s+.*?\bhuma(?:no|nos)\b\s+.*?\bmeio ambiente\b",re.IGNORECASE),
        # MonitoramentoAmazoniaAzul
        "MonitoramentoAmazoniaAzul" : re.compile(r"\bmonitor(?:ar|amento)\b\s+.*?\bamaz(?:ô|o)nia\b\s+\bazul\b",re.IGNORECASE),
        #ApoioAgriculturaIrrigada
        "ApoioAgriculturaIrrigada" : re.compile(r"\bapoi(?:ar|o)\b\s+.*?\bagricul(?:tura|turas)\b\s+.*?\birriga(?:ção|çao|cao|cão|da|das)\b",re.IGNORECASE),
        #SateliteSerieAmazonia
        "SateliteSerieAmazonia" : re.compile(r"\bsat(?:é|e)li(?:te|tes)\b\s+.*?\bama(?:zô|zo)nia\b",re.IGNORECASE),
        #ApoioPesquisaMar
        "ApoioPesquisaMar" : re.compile(r"\bapoi(?:ar|o|os)\b\s+.*?\bpesqui(?:sar|sa|sas)\b\s+.*?\bma(?:r|rítima|ritima)\b",re.IGNORECASE),
        #ApoioPesquisaOceano
        "ApoioPesquisaOceano" : re.compile(r"\bapoi(?:ar|o|os)\b\s+.*?\bpesqui(?:sar|sa|sas)\b\s+.*?\boce(?:ânica|anica|ânico|anico|ano|anos)\b",re.IGNORECASE),
        #ProjetoPublicoIrrigacao
        "ProjetoPublicoIrrigacao" : re.compile(r"\bproje(?:to|tos)\b\s+.*?\bp(?:ú|u)blic(?:os|o)\b\s+.*?\birrig(?:ar|ação|açao|acão|acao)\b",re.IGNORECASE),
        #TransferenciaTecnologiaAgropecuaria
        "TransferenciaTecnologiaAgropecuaria" : re.compile(r"\btransfe(?:rir|rência|rencia)\b\s+.*?\btecnolo(?:gia|gias)\b\s+.*?\bagrope(?:cuária|cuaria|cuárias|cuarias)\b",re.IGNORECASE),
        #DifusaoInformacaoAgroalimentar/Agropecuaria
        "DifusaoInformacaoAgroalimentar" : re.compile(r"\bdi(?:fundir|fusão|fusao)\b\s+.*?\binforma(?:ção|ções|çao|çoes|cão|cões|cao|coes)\b\s+.*?\bagro(?:alimentar|alimentares|pecúaria|pecúarias|pecuaria|pecuarias)\b",re.IGNORECASE),
        #ImplementacaoProjetosAreasProtegidas
        "ImplementacaoProjetosAreasProtegidas" : re.compile(r"\bimplemen(?:tar|tação|taçao|tacão|tacao)\b\s+.*?\bproje(?:tos|to)\b\s+.*?\b(?:á|a)re(?:a|as)\b\s+\bprotegi(?:das|da)\b",re.IGNORECASE),
        #DesenvolvimentoModeloSistemaTerrestre
        "DesenvolvimentoModeloSistemaTerrestre" : re.compile(r"\bdesenvol(?:ver|vimento|vimentos)\b\s+.*?\bmode(?:los|lo)\b\s+.*?\bsistem(?:a|as)\b\s+.*?\bterres(?:tres|tre)\b",re.IGNORECASE),
        #FomentoProjetosAreasProtegidas
        "FomentoProjetosAreasProtegidas" : re.compile(r"\bfomen(?:tar|to)\b\s+.*?\bproje(?:to|tos)\b\s+.*?\b(?:á|a)reas\b\s+\bprotegi(?:das|da)\b",re.IGNORECASE),
        #PesquisaAvaliacaoSafra
        "PesquisaAvaliacaoSafra" : re.compile(r"\bpesqui(?:sas|sa|sar)\b\s+.*?\bavalia(?:ção|çao|cão|cao)\b\s+.*?\bsa(?:fra|fras)\b",re.IGNORECASE),
        #GerenciamentoAmazoniaAzul
        "GerenciamentoAmazoniaAzul" : re.compile(r"\bgerenciamento\b\s+.*?\bamaz(?:ô|o)nia\b\s+\bazul\b",re.IGNORECASE),
        #AprimoramentoModeloSistemaTerrestre
        "AprimoramentoModeloSistemaTerrestre" : re.compile(r"\baprimo(?:rar|ramento|ramentos)\b\s+.*?\bmode(?:los|lo)\b\s+.*?\bsistem(?:a|as)\b\s+.*?\bterres(?:tres|tre)\b",re.IGNORECASE),
        #IncendioFlorestal
        "IncendioFlorestal" : re.compile(r"\binc(?:ê|e)ndi(?:o|os)\b\s+\bflorest(?:a|al|ais)\b",re.IGNORECASE),
        #CatastrofeIncendio
        "CatastrofeIncendio" : re.compile(r"\bcat(?:á|a)strofe\b\s+.*?\binc(?:ê|e)ndi(?:o|os)\b",re.IGNORECASE),
        #PreparacaoIncendio
        "PreparacaoIncendio" : re.compile(r"\bprepara(?:r|ção|çao|cão|cao)\b\s+.*?\binc(?:ê|e)ndi(?:os|o)\b",re.IGNORECASE),
        #PrevencaoIncendio
        "PrevencaoIncendio" : re.compile(r"\bprev(?:enção|ençao|encão|encao|inir)\b\s+.*?\binc(?:ê|e)ndi(?:os|o)\b",re.IGNORECASE),
        #PrevisaoIncendio
        "PrevisaoIncendio" : re.compile(r"\bprevis(?:ão|ao|ões|oes)\b\s+.*?\binc(?:ê|e)ndi(?:o|os)\b",re.IGNORECASE),
        #CombateIncendio
        "CombateIncendio" : re.compile(r"\bcomba(?:ter|te)\b\s+.*?\binc(?:ê|e)nd(?:ios|io)\b",re.IGNORECASE),
        #ControleIncendio
        "ControleIncendio" : re.compile(r"\bcontro(?:le|les|lar)\b\s+.*?\binc(?:ê|e)nd(?:io|ios)\b",re.IGNORECASE),
        #FortalecimentoIncendio
        "FortalecimentoIncendio" : re.compile(r"\bfortale(?:cer|cimento|ce)\b\s+.*?\binc(?:ê|e)ndi(?:os|o)\b",re.IGNORECASE),
        #ReforcoIncendio
        "ReforcoIncendio" : re.compile(r"\brefor(?:ço|co|ços|cos|çar|car)\b\s+.*?\binc(ê|e)ndio\b",re.IGNORECASE),
        #Reflorestamento
        "Reflorestamento" : re.compile(r"\breflores(?:tar|ta|tamento)\b",re.IGNORECASE),

    }
    database["Pega_Palavra"] = [[] for _ in range(len(database))]
    database["Keyword_Catch"] = [[] for _ in range(len(database))]
    for palavra_chave, padrao in keyword_patterns.items():
        def processa_linha(row):
            descricao = row[column_search]
            match = padrao.findall(descricao)
            if match:
                row["Pega_Palavra"] += [palavra_chave]
                row["Keyword_Catch"] += match
            return row

        database = database.apply(processa_linha, axis=1)
    database["Pega_Palavra_str"] = database["Pega_Palavra"].apply(lambda x: " AND ".join(x) if x else "")
    database["Keyword_Catch_str"] = database["Keyword_Catch"].apply(lambda x: " AND ".join(x) if x else "")


    return database

def mitigation_flask_encapsulation(df, coluna, num_partitions=None):
    
    """ 
    Função para aplicar a funcao de pegar palavras de adaptação mas em paralelo usando Dask
    @param df: Dataframe que sera aplicada a funcao de procura por palavras chave de adaptação
    @param coluna: Coluna onde aplicaremos as regras de regex
    @param num_partitions: Numero que indicará quantas partições teremos
    """
    print("\n--- ATENÇÃO ---")
    print(f"numero de nucleos em seu computador é de {dask.system.cpu_count()}")
    print(f'Caso voce não utilize nenhum numero especifico de partições (chunks), utilizaremos {dask.system.cpu_count()*4} partições')
    print("\n--- --- ---")
    if num_partitions is None:
        num_partitions = multiprocessing.cpu_count() * 4
    
    start_time = time.perf_counter()
    print("\n--- Configuração de Processamento Dask ---")
    print(f"Número de partições: {num_partitions}")
    print(f"Número total de linhas: {len(df)}")
    print(f"Número de CPUs disponíveis: {multiprocessing.cpu_count()}")
    df["Pega_Palavra"] = [[] for _ in range(len(df))]
    df["Keyword_Catch"] = [[] for _ in range(len(df))]
    df["Pega_Palavra_str"] = [[] for _ in range(len(df))]
    df["Keyword_Catch_str"] = [[] for _ in range(len(df))]
    dask_df = dd.from_pandas(df, npartitions=num_partitions)
    processed_dask_df = dask_df.map_partitions(
        lambda partition: apply_mitigation_KW(partition, coluna), 
        meta=df
    )
    resultado_final = processed_dask_df.compute()
    stop_time = time.perf_counter()
    print("\n--- --- ---")
    print(f"Tempo de execução: {stop_time - start_time}")
    print("\n--- --- ---")
    return (resultado_final,stop_time - start_time)