import pandas as pd


def carregar_dados(file_path: str) -> pd.DataFrame:
	"""Carrega e processa um arquivo CSV contendo dados de horários e datas, realizando as conversões necessárias para os tipos datetime.

	Args:
		file_path (str): Caminho completo para o arquivo CSV a ser carregado.

	Returns:
		pd.DataFrame: DataFrame processado contendo as seguintes colunas:
			- horario_inicio_jornada: datetime - Horário de início
			- horario_fim_jornada: datetime - Horário de término
			- duracao: timedelta - Duração calculada (horario_fim_jornada - horario_inicio_jornada)
			- data: datetime - Data inicial
			- dataf: datetime - Data final
			- duracao_minutos: int - Duração em minutos
	"""
	df = pd.read_csv(file_path, delimiter=",")

	# Conversões de datetime
	df["horario_inicio_jornada"] = pd.to_datetime(df["horario_inicio_jornada"], format="%H:%M:%S")
	df["horario_fim_jornada"] = pd.to_datetime(df["horario_fim_jornada"], format="%H:%M:%S")
	df["duracao"] = df["horario_fim_jornada"] - df["horario_inicio_jornada"]
	df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y")
	df["dataf"] = pd.to_datetime(df["dataf"], format="%d/%m/%Y")
	df["duracao_minutos"] = df["duracao"].dt.total_seconds() // 60
	df["duracao_minutos"] = df["duracao_minutos"].astype(int)

	return df


def carregar_integracoes(file_path: str) -> pd.Series:
	"""Carrega um arquivo CSV de integrações e retorna uma série contendo as linhas de origem únicas.

	Args:
		file_path (str): Caminho completo para o arquivo CSV de integrações.

	Returns:
		pd.Series: Série contendo valores únicos da coluna 'LINHA ORIGEM'.
	"""
	df_integrations = pd.read_csv(file_path, delimiter=",")
	df_integrations = df_integrations.drop_duplicates(subset=["LINHA ORIGEM"])
	df_integrations = df_integrations["LINHA ORIGEM"]
	return df_integrations


def carregar_viagens_planejadas(file_path: str) -> pd.DataFrame:
	"""Carrega e processa um arquivo CSV contendo dados de viagens planejadas do sistema de transporte.

	Args:
		file_path (str): Caminho completo para o arquivo CSV contendo os dados de rastreamento de viagens.

	Returns:
		pd.DataFrame: DataFrame agrupado com informações sobre o cumprimento de horários contendo:
			- Índice multinível com linha e sentido (ida/volta)
			- sem_horario: Quantidade de viagens sem informação de horário
			- com_horario: Quantidade de viagens com informação de horário
			- proporcao_sem_horario: Proporção de viagens com horário registrado em relação ao total
	"""
	df_rastreamento = pd.read_csv(file_path, delimiter=",")

	df_rastreamento[["id_linha", "sentido"]] = df_rastreamento["descricao_trajeto"].str.extract(r"(\d+)\s*-\s*.*\((ida|volta)\)")

	df_rastreamento = df_rastreamento.drop("descricao_trajeto", axis=1)
	df_rastreamento.replace("-", pd.NA, inplace=True)
	df_rastreamento["com_horario"] = df_rastreamento[["chegada_planejada", "partida_real", "chegada_real"]].notna().any(axis=1)
	agrupado = df_rastreamento.groupby(["id_linha", "sentido"])["com_horario"].value_counts(normalize=False).unstack(fill_value=0)

	agrupado.columns = ["sem_horario", "com_horario"]

	agrupado["proporcao_sem_horario"] = agrupado["com_horario"] / (agrupado["sem_horario"] + agrupado["com_horario"])

	return agrupado
