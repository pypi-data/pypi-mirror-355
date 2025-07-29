import geopandas as gpd
import pandas as pd


def validar_gdf_city(df: pd.DataFrame) -> bool:
	"""Valida um DataFrame contendo informações sobre áreas urbanas.

	Args:
		df (pd.DataFrame): DataFrame contendo os dados a serem validados.

	Returns:
		bool: True se o DataFrame contiver todas as colunas esperadas.

	Raises:
		ValueError: Se alguma coluna estiver faltando no DataFrame.
	"""
	required_columns = ["geometry"]
	missing_columns = [col for col in required_columns if col not in df.columns]
	if missing_columns:
		raise ValueError(f"gdf_city está faltando colunas: {missing_columns}")
	return True


def validar_df_dados_linhas(df: pd.DataFrame) -> bool:
	"""Valida um DataFrame contendo informações sobre linhas de transporte.

	Args:
		df (pd.DataFrame): DataFrame contendo os dados das linhas.

	Returns:
		bool: True se o DataFrame contiver todas as colunas esperadas.

	Raises:
		ValueError: Se alguma coluna estiver faltando no DataFrame.
	"""
	required_columns = [
		"id_linha",
		"geometria_linha",
		"indicador_via_pavimentada",
		"tipo_integracao",
		"indicador_treinamento_motorista",
		"disponibilidade_informacao",
		"valor_tarifa",
	]
	missing_columns = [col for col in required_columns if col not in df.columns]
	if missing_columns:
		raise ValueError(f"df_dados_linhas está faltando colunas: {missing_columns}")
	return True


def validar_df_frequencia(df: pd.DataFrame) -> bool:
	"""Valida um DataFrame contendo informações sobre frequência de viagens.

	Args:
		df (pd.DataFrame): DataFrame contendo os dados de frequência.

	Returns:
		bool: True se o DataFrame contiver todas as colunas esperadas.

	Raises:
		ValueError: Se alguma coluna estiver faltando no DataFrame.
	"""
	required_columns = ["horario_inicio_jornada", "horario_fim_jornada", "data_jornada", "sentido_viagem", "id_linha", "quantidade_passageiros"]
	missing_columns = [col for col in required_columns if col not in df.columns]
	if missing_columns:
		raise ValueError(f"df_frequencia está faltando colunas: {missing_columns}")
	return True


def validar_df_pontualidade(df: pd.DataFrame) -> bool:
	"""Valida um DataFrame contendo informações sobre pontualidade de transporte.

	Args:
		df (pd.DataFrame): DataFrame contendo os dados de pontualidade.

	Returns:
		bool: True se o DataFrame contiver todas as colunas esperadas.

	Raises:
		ValueError: Se alguma coluna estiver faltando no DataFrame.
	"""
	required_columns = [
		"data_viagem",
		"id_linha",
		"sentido",
		"descricao_trajeto",
		"partida_planejada",
		"partida_real",
		"chegada_planejada",
		"chegada_real",
		"km_executado",
	]
	missing_columns = [col for col in required_columns if col not in df.columns]
	if missing_columns:
		raise ValueError(f"df_pontualidade está faltando colunas: {missing_columns}")
	return True


def validar_df_cumprimento(df: pd.DataFrame) -> bool:
	"""Valida um DataFrame contendo informações sobre cumprimento de rotas.

	Args:
		df (pd.DataFrame): DataFrame contendo os dados de cumprimento de rotas.

	Returns:
		bool: True se o DataFrame contiver todas as colunas esperadas.

	Raises:
		ValueError: Se alguma coluna estiver faltando no DataFrame.
	"""
	required_columns = ["data_viagem", "id_linha", "sentido", "descricao_trajeto", "km_executado"]
	missing_columns = [col for col in required_columns if col not in df.columns]
	if missing_columns:
		raise ValueError(f"df_cumprimento está faltando colunas: {missing_columns}")
	return True


def validar_residencias(gdf: gpd.GeoDataFrame) -> bool:
	"""Valida um GeoDataFrame contendo informações sobre residências.

	Args:
		gdf (gpd.GeoDataFrame): GeoDataFrame contendo os dados das residências.

	Returns:
		bool: True se o GeoDataFrame contiver todas as colunas esperadas.

	Raises:
		ValueError: Se alguma coluna estiver faltando no GeoDataFrame.
	"""
	required_columns = ["id", "longitude", "latitude"]
	missing_columns = [col for col in required_columns if col not in gdf.columns]
	if missing_columns:
		raise ValueError(f"gdf_residências está faltando colunas: {missing_columns}")
	return True


def validar_pontos_onibus(gdf: gpd.GeoDataFrame) -> bool:
	"""Valida um GeoDataFrame contendo informações sobre pontos de ônibus.

	Args:
		gdf (gpd.GeoDataFrame): GeoDataFrame contendo os dados dos pontos de ônibus.

	Returns:
		bool: True se o GeoDataFrame contiver todas as colunas esperadas.

	Raises:
		ValueError: Se alguma coluna estiver faltando no GeoDataFrame.
	"""
	required_columns = ["id", "longitude", "latitude"]
	missing_columns = [col for col in required_columns if col not in gdf.columns]
	if missing_columns:
		raise ValueError(f"gdf_pontos_onibus está faltando colunas: {missing_columns}")
	return True
