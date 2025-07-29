from typing import Optional

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import LineString
from shapely.wkt import loads

from ..utils import Associador, modelos
from ..utils.config import config
from ..utils.cores import cor_iqt
from .classificar_indicadores import ClassificarIndicadores


class CalcularIndicadores:
	"""
	Classe para cálculo e avaliação de indicadores de qualidade do transporte público.

	Esta classe contém métodos para calcular o Índice de Qualidade do Transporte (IQT)
	e avaliar diferentes aspectos do serviço de transporte público, como pontualidade,
	infraestrutura e atendimento.
	"""

	def __init__(self):
		"""
		Inicializa a classe com os valores predefinidos dos indicadores e suas prioridades.
		"""

	def carregar_dados(
		self, df_linhas: pd.DataFrame, df_frequencia: pd.DataFrame, df_pontualidade: pd.DataFrame, init_crs: str | int, target_crs: str | int
	):
		"""Carrega todos os dados necessários para o cálculo dos indicadores.

		Args:
			df_linhas (pd.DataFrame): DataFrame contendo os dados das linhas de transporte.
			df_frequencia (pd.DataFrame): DataFrame contendo os dados de frequência de atendimento.
			df_pontualidade (pd.DataFrame): DataFrame contendo os dados de pontualidade.
			df_cumprimento (pd.DataFrame): DataFrame contendo os dados de cumprimento de itinerário.
			init_crs (str): CRS inicial dos dados geoespaciais
			target_crs (str): CRS projetado dos dados geoespaciais
		"""
		self.dados_linhas = self.carregar_dados_linha(df_linhas, init_crs, target_crs)
		self.frequencia = self.carregar_frequencia_atendimento_pontuacao(df_frequencia)
		self.pontualidade = self.carregar_pontualidade(df_pontualidade)
		self.cumprimento = self.carregar_cumprimento(df_pontualidade)

	def carregar_dados_geometrias(self, df_pontos_onibus: pd.DataFrame, df_residencias: pd.DataFrame, init_crs: str | int, target_crs: str | int):
		"""Carrega os dados geométricos de pontos de ônibus e residências.

		Args:
			df_pontos_onibus (pd.DataFrame): DataFrame contendo os dados dos pontos de ônibus.
			df_residencias (pd.DataFrame): DataFrame contendo os dados das residências.
			init_crs (str): CRS inicial dos dados geoespaciais.
			target_crs (str): CRS projetado dos dados geoespaciais.
		"""
		self.associador = Associador(df_pontos_onibus, self.dados_linhas.copy(), df_residencias, init_crs, target_crs)
		self.dados_geograficos = self.associador.consolidar_associacoes()

	def carregar_dados_linha(self, df_line: pd.DataFrame, init_crs: str | int, target_crs: str | int) -> gpd.GeoDataFrame:
		"""
		Carrega os dados de frequência de atendimento a partir de um DataFrame.

		Args:
			df_line (pd.DataFrame): DataFrame contendo os dados de frequência de atendimento.
			init_crs (str): CRS inicial dos dados geoespaciais
			target_crs (str): CRS projetado dos dados geoespaciais

		Returns:
			gpd.GeoDataFrame: GeoDataFrame com a coluna geometry convertida para LineString 2D.
		"""
		try:
			if not modelos.validar_df_dados_linhas(df_line):
				raise

			df_copy = df_line.copy()

			dados_linhas = gpd.GeoDataFrame(df_copy)
			if not self._validar_geometry_wkt(dados_linhas).all():
				raise

			return self._converter_geometry_para_linestring(dados_linhas, init_crs, target_crs)
		except Exception as error:
			print("Erro ao carregar dados de linha: ", error)
			return gpd.GeoDataFrame()

	def _validar_geometry_wkt(self, df, coluna="geometria_linha"):
		"""
		Valida se os valores da coluna geometria_linha são strings WKT.

		Args:
			df (pd.DataFrame): DataFrame contendo a coluna geometria_linha.
			coluna (str): Nome da coluna geometria_linha.

		Returns:
			bool: True se todos os valores forem strings WKT, False caso contrário.
		"""
		return df[coluna].apply(lambda x: isinstance(x, str) and x.startswith("LINESTRING"))

	def _converter_geometry_para_linestring(
		self, df: pd.DataFrame, init_crs: str | int, target_crs: str | int, coluna: str = "geometria_linha"
	) -> gpd.GeoDataFrame:
		"""
		Converte strings WKT em objetos LineString 2D e retorna um GeoDataFrame.

		Args:
			df (pd.DataFrame): DataFrame contendo a coluna geometria_linha.
			coluna (str): Nome da coluna que contém as geometrias.
			init_crs (str): CRS inicial dos dados geoespaciais
			target_crs (str): CRS projetado dos dados geoespaciais

		Returns:
			gpd.GeoDataFrame: GeoDataFrame com a coluna geometria_linha convertida para LineString 2D.

		Raises:
			ValueError: Se a coluna especificada não existir no DataFrame.
		"""
		if coluna not in df.columns:
			raise ValueError(f"Coluna '{coluna}' não encontrada no DataFrame")

		df_copy = df.copy()

		def converter_para_2d(geom):
			if geom is None:
				return LineString()

			# Se for uma string, tenta carregar a geometria
			if isinstance(geom, str):
				geom = loads(geom)

			# Garantir que é uma geometria do tipo esperado
			if not isinstance(geom, LineString):
				raise ValueError("Geometria inválida ou inesperada")

			# Acessa as coordenadas
			coords_2d = [(x, y) for x, y, *_ in geom.coords]

			return LineString(coords_2d)

		df_copy[coluna] = df_copy[coluna].apply(converter_para_2d)  # type: ignore

		df_copy = df_copy.astype({"id_linha": "string"})

		gdf = gpd.GeoDataFrame(data=df_copy, geometry=coluna, crs=init_crs).to_crs(target_crs)  # type: ignore
		return gdf

	def carregar_cumprimento(self, df_cumprimento: pd.DataFrame) -> pd.DataFrame:
		"""
		Carrega os dados de cumprimento do itinerário a partir de um DataFrame.
		"""
		try:
			if not modelos.validar_df_cumprimento(df_cumprimento):
				raise
			return self.cumprimento_itinerario(df_cumprimento)
		except Exception as error:
			print("Erro ao carregar dados de cumprimento: ", error)
			return pd.DataFrame()

	def carregar_frequencia_atendimento_pontuacao(self, df_frequencia: pd.DataFrame) -> pd.DataFrame:
		"""
		Carrega os dados de frequência de atendimento a partir de um DataFrame.
		"""
		try:
			if not modelos.validar_df_frequencia(df_frequencia):
				raise
			return self.frequencia_atendimento_pontuacao(df_frequencia)
		except Exception as error:
			print("Erro ao carregar dados de frequência: ", error)
			return pd.DataFrame()

	def carregar_pontualidade(self, df_pontualidade: pd.DataFrame) -> pd.DataFrame:
		"""
		Carrega os dados de pontualidade a partir de um DataFrame.
		"""
		try:
			if not modelos.validar_df_pontualidade(df_pontualidade):
				raise
			return self.calcular_pontualidade(df_pontualidade)
		except Exception as error:
			print("Erro ao carregar dados de pontualidade: ", error)
			return pd.DataFrame()

	def cumprimento_itinerario(self, df_cumprimento: pd.DataFrame):
		"""
		Função responsável por verificar o cumprimento de itinerário.

		Args:
			df_cumprimento (pd.DataFrame): _description_

		"""
		df_temp = df_cumprimento.copy()

		df_temp = df_temp.dropna(subset=["km_executado"])
		df_temp["km_executado"] = pd.to_numeric(df_temp["km_executado"], errors="coerce")
		df_temp = df_temp.groupby(["id_linha"])["km_executado"].mean().reset_index()

		df_temp = df_temp.astype({"id_linha": "string", "km_executado": "float64"})

		return df_temp

	def calcular_pontualidade(self, df_pontualidade: pd.DataFrame) -> pd.DataFrame:
		"""
		Calcula a pontuação para o indicador de pontualidade.
		"""
		try:
			df_temp = df_pontualidade.copy()
			df_temp["sentido"] = df_temp["sentido"].replace({"ida": "IDA", "volta": "VOLTA"})
			df_temp = df_temp.drop("descricao_trajeto", axis=1)
			df_temp = df_temp.replace("-", pd.NA)
			df_temp["com_horario"] = df_temp[["chegada_planejada", "chegada_real", "partida_planejada", "partida_real"]].notna().any(axis=1)
			df_temp = df_temp.groupby("id_linha")["com_horario"].value_counts(normalize=False).unstack(fill_value=0)
			if True not in df_temp.columns:
				df_temp[True] = 0
			if False not in df_temp.columns:
				df_temp[False] = 0
			df_temp.columns = ["com_horario", "sem_horario"]
			df_temp["pontualidade"] = df_temp["com_horario"] / (df_temp["sem_horario"] + df_temp["com_horario"])
			df_temp = df_temp.drop(["com_horario", "sem_horario"], axis=1)

			df_temp = df_temp.reset_index()

			df_temp = df_temp.astype({"id_linha": "string", "pontualidade": "float64"})

			return df_temp
		except Exception as error:
			print("Erro ao calcular pontualidade: ", error)
			return pd.DataFrame()

	def frequencia_atendimento_pontuacao(self, df_frequencia: pd.DataFrame) -> pd.DataFrame:
		"""Calcula o tempo médio de operação por rota (linha).

		Args:
			df_frequencia (pd.DataFrame): DataFrame contendo a coluna 'id_linha' para identificar a rota e colunas de tempo.

		Returns:
			pd.DataFrame: DataFrame com o tempo médio de operação por rota.
		"""
		df_temp = df_frequencia.copy()

		df_temp["horario_inicio_jornada"] = pd.to_datetime(df_temp["horario_inicio_jornada"], format="%H:%M:%S")
		df_temp["horario_fim_jornada"] = pd.to_datetime(df_temp["horario_fim_jornada"], format="%H:%M:%S")

		df_temp["frequencia_atendimento_pontuacao"] = df_temp["horario_fim_jornada"] - df_temp["horario_inicio_jornada"]
		df_temp["frequencia_atendimento_pontuacao"] = df_temp["frequencia_atendimento_pontuacao"].apply(lambda x: int(x.total_seconds() / 60))

		df_temp["data_jornada"] = pd.to_datetime(df_temp["data_jornada"], format="%d/%m/%Y")

		df_temp = df_temp.groupby(["id_linha"])["frequencia_atendimento_pontuacao"].mean().reset_index()

		df_temp = df_temp.astype({"id_linha": "string", "frequencia_atendimento_pontuacao": "float64"})

		return df_temp

	def merge_dados(self):
		"""Combina todos os dados carregados em um único DataFrame."""
		try:
			if not isinstance(self.dados_linhas, gpd.GeoDataFrame):
				raise
			crs_original = self.dados_linhas.crs

			self.dados_linhas = self.dados_linhas.to_crs(epsg=31983)

			if not isinstance(self.dados_linhas, gpd.GeoDataFrame):
				raise

			self.dados_linhas["distancia_km"] = self.dados_linhas.length / 1000

			if not crs_original:
				raise

			self.dados_linhas = self.dados_linhas.to_crs(crs_original)

			if not isinstance(self.dados_linhas, gpd.GeoDataFrame):
				raise

			self.dados_completos = pd.merge(self.dados_linhas, self.cumprimento, on=["id_linha"])
			self.dados_completos = pd.merge(self.dados_completos, self.frequencia, on=["id_linha"])
			self.dados_completos = pd.merge(self.dados_completos, self.pontualidade, on=["id_linha"])
			self.dados_completos = pd.merge(self.dados_completos, self.dados_geograficos, on=["id_linha"])

			self.dados_completos["cumprimento_itinerario"] = self.dados_completos["km_executado"].astype(float) / self.dados_completos[
				"distancia_km"
			].astype(float)

			self.dados_completos = gpd.GeoDataFrame(self.dados_completos)

		except Exception as e:
			print(f"Erro ao mesclar os dados: {e}")

	def classificar_linha(self):
		"""Classifica as linhas de acordo com os indicadores calculados."""
		classificador = ClassificarIndicadores()
		self.merge_dados()
		self.classificao_linhas = classificador.classificar_linhas(self.dados_completos)

	def calcular_iqt(self, linha: list) -> float:
		"""Calcula o Índice de Qualidade do Transporte (IQT) para uma linha específica.

		Args:
			linha (list): Lista contendo os valores dos indicadores para uma linha específica. O primeiro elemento é ignorado, e os demais devem corresponder aos indicadores na ordem definida em indicadores_prioridades.

		Returns:
			float: Valor do IQT calculado.
		"""
		try:
			prioridades = config.PRIORIDADE
			soma_ponderada = np.dot(linha, prioridades)

			desvio_padrao_prioridades = np.std(prioridades)

			iqt = soma_ponderada / (desvio_padrao_prioridades * len(prioridades))
			return iqt
		except Exception as e:
			print(f"Erro ao calcular IQT: {e}")
			return 0.0

	def processar_iqt(self):
		"""Processa o cálculo do IQT para todas as linhas classificadas."""
		valores_iqt, cores = [], []
		for _, row in self.classificao_linhas.iterrows():
			valores_indicadores = row.iloc[1:].tolist()

			iqt = self.calcular_iqt(valores_indicadores)
			cor = cor_iqt(iqt)
			valores_iqt.append(iqt)
			cores.append(cor)
		self.dados_completos["iqt"] = valores_iqt
		self.dados_completos["cor"] = cores
		self._gerar_matriz()

	def _gerar_matriz(self):
		df_matriz = self.dados_completos.drop(columns=["geometria_linha"])

		mapeamento = dict(zip(config.INDICADOR, config.NOMECLATURA))

		df_matriz = df_matriz.rename(columns=mapeamento)

		colunas_para_manter = ["id_linha"] + list(mapeamento.values()) + ["iqt"]
		self.matriz = df_matriz[colunas_para_manter]
