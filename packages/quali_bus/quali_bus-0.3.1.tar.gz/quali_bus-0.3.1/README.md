# 📊 Quali Bus - Biblioteca para Avaliação da Qualidade do Transporte Público

Esta biblioteca tem como objetivo automatizar o cálculo do **Índice de Qualidade do Transporte (IQT)**, baseado nos critérios estabelecidos no artigo **"MESTRADO INDICADOR DE QUALIDADE PARA AVALIAR TRANSPORTE COLETIVO URBANO"**. O IQT é uma métrica essencial para a análise e otimização do transporte público, considerando fatores como pontualidade, frequência de atendimento, cumprimento de itinerários e infraestrutura.

---

## 🚀 Como Usar

🔹 1. Importação da Biblioteca

```python
import quali_bus as iqt
```

🔹 2. Exemplo de uso

```python
import os
import quali_bus as iqt

# --- 1. Configuração de Paths ---
# Define os diretórios base para facilitar o acesso aos arquivos.
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ARQUIVOS_DIR = os.path.join(BASE_DIR, "seus_dados", "arquivos")
PLANILHAS_DIR = os.path.join(BASE_DIR, "seus_dados", "planilhas")

# Paths para os arquivos de dados
SHAPEFILE_PATH = os.path.join(ARQUIVOS_DIR, "limites_bairros.shp")
LINHAS_PATH = os.path.join(PLANILHAS_DIR, "dados_linhas.csv")
FREQUENCIA_PATH = os.path.join(PLANILHAS_DIR, "frequencia.csv")
PONTUALIDADE_PATH = os.path.join(PLANILHAS_DIR, "pontualidade.csv")
RESIDENCIAS_PATH = os.path.join(PLANILHAS_DIR, "residencias.csv")
PONTOS_PATH = os.path.join(PLANILHAS_DIR, "pontos_de_onibus.csv")

# --- 2. Inicialização e Carga de Dados ---
# Inicializa o objeto de análise, fornecendo o shapefile do município.
analise = iqt.QualiBus(SHAPEFILE_PATH)

# Carrega os dados operacionais e geoespaciais a partir dos arquivos.
analise.carregar_dados_operacionais(LINHAS_PATH, FREQUENCIA_PATH, PONTUALIDADE_PATH)
analise.carregar_dados_geoespaciais(PONTOS_PATH, RESIDENCIAS_PATH)

# --- 3. Cálculo do IQT ---
# Processa todos os dados e calcula os indicadores de qualidade.
matriz_resultados = analise.calcular_indicadores_iqt()
print("Matriz de Resultados IQT:")
print(matriz_resultados)

# --- 4. Geração de Mapas e Gráficos ---
# Gera visualizações para análise espacial e estatística.
mapa_iqt = analise.gerar_mapa_rotas_por_iqt()
mapa_calor = analise.gerar_mapa_calor_acessibilidade()
analise.gerar_mapa_abrangencia_linha("101") 
analise.gerar_visualizacao_distribuicao_bairros()

# --- 5. Acesso aos Dados para Análise Customizada ---
# Obtenha os DataFrames completos para análises mais profundas.
dados_completos = analise.get_dados_completos()
associacoes_pontos_residencias = analise.get_associacoes()
```

## Classificação das Linha

| id_linha | I1  | I2  | I3  | I4  | I5  | I6  | I7  | I8  | I9  | I10 |
| -------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 101      | 3   | 2   | 1   | 0   | 0   | 3   | 2   | 3   | 0   | 1   |
| 102      | 3   | 2   | 1   | 0   | 0   | 3   | 2   | 3   | 0   | 1   |

## Dados Calculados

| id_linha | I1  | I2     | I3                                                                                                 | I4  | I5   | I6   | I7   | I8  | I9                                                   | I10                           |
| -------- | --- | ------ | -------------------------------------------------------------------------------------------------- | --- | ---- | ---- | ---- | --- | ---------------------------------------------------- | ----------------------------- |
| 101      | 1   | 148.12 | Integração tarifária temporal ocorre em determinados pontos, apenas com transferências intramodais | 0   | 49.8 | 1.45 | 0.98 | 1   | Possuir informações em site e aplicativo atualizados | Aumento equivalente ao índice |
| 102      | 2   | 111.12 | Integração tarifária temporal ocorre em determinados pontos, apenas com transferências intramodais | 0   | 21.8 | 1.75 | 0.78 | 1   | Possuir informações em site e aplicativo atualizados | Aumento equivalente ao índice |

## Alguns Resultados

![Buffer 500 da Linha de ônibus](resultados/buffer_linha.png)
![Distribuição Linhas de Ônibus](resultados/distribuicao_linhas_onibus.png)
![Distribuição Linhas de Ônibus](resultados/mapa_classificacao.png)
![Distribuição Linhas de Ônibus](resultados/dados_linha.png)


## 🤝 Contribuindo

### Contribuições são bem-vindas! Para contribuir:

- Fork o repositório.
- Crie uma branch `(feature/nova-funcionalidade)`.
- Faça suas alterações e commit `(git commit -m "Adiciona nova funcionalidade")`.
- Envie um Pull Request.

### 📜 Licença

Este projeto está sob a licença MIT. Consulte o arquivo LICENSE para mais detalhes.
👨‍💻 Autor

Desenvolvido por Yago Maia - GitHub: https://github.com/YagoMaia
