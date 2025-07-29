from typing import Optional

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import LineString, Point


class Associador:
	MAX_DISTANCE = 1000  # metros - distância máxima aceitável
	REQUIRED_COLUMNS = {"latitude", "longitude"}

	def __init__(self, pontos_onibus: pd.DataFrame, linhas: gpd.GeoDataFrame, residencias: pd.DataFrame, init_crs: str | int, target_crs: str | int):
		"""
		Inicializa a classe com os dados necessários.

		Args:
			pontos_onibus (pd.DataFrame): DataFrame com coordenadas dos pontos de ônibus
			linhas (pd.DataFrame): DataFrame com as linhas de ônibus
			residencias (pd.DataFrame): DataFrame com coordenadas das residências
			init_crs (str): CRS inicial dos dados geoespaciais
			target_crs (str): CRS projetado dos dados geoespaciais
		"""
		self.gdf_residencias, self.gdf_pontos_onibus = self._criar_geodataframes(residencias, pontos_onibus, init_crs, target_crs)
		self.linhas = linhas.copy()

		self.coords_residencias, self.coords_pontos_onibus = self._extrair_coordenadas()

	def _verificar_formato_coordenadas(self, df: pd.DataFrame) -> bool:
		"""Verifica se as coordenadas estão no formato decimal padrão."""
		longitude_ok = (-180 <= df["longitude"].max() <= 180) and (-180 <= df["longitude"].min() <= 180)
		latitude_ok = (-90 <= df["latitude"].max() <= 90) and (-90 <= df["latitude"].min() <= 90)
		return longitude_ok and latitude_ok

	def _extrair_coordenadas(self) -> tuple[Optional[np.ndarray], Optional[np.ndarray]]:
		"""
		Extrai coordenadas dos GeoDataFrames e converte para arrays NumPy.

		Returns:
			Tuple[np.ndarray, np.ndarray]: Arrays com coordenadas das residências e pontos de ônibus
		"""
		if isinstance(self.gdf_pontos_onibus, gpd.GeoDataFrame) and isinstance(self.gdf_residencias, gpd.GeoDataFrame):
			coords_residencias = np.array([[geom.centroid.x, geom.centroid.y] for geom in self.gdf_residencias.geometry])

			coords_pontos_onibus = np.array([[geom.centroid.x, geom.centroid.y] for geom in self.gdf_pontos_onibus.geometry])

			return coords_residencias, coords_pontos_onibus
		return None, None

	def _criar_pontos(self, df: pd.DataFrame) -> gpd.GeoSeries:
		"""Função responsável por criar a geometria dos dados de residencias e pontos de onibus."""
		return gpd.GeoSeries([Point(xy) for xy in zip(df["longitude"], df["latitude"])])

	def _verificar_formato(self, residencias: pd.DataFrame, pontos_onibus: pd.DataFrame):
		"""Função responsável por verificar o formato dos dados recebidos."""
		if not self._verificar_formato_coordenadas(residencias):
			raise ValueError("Coordenadas dos pontos de residências estão em formato incorreto!")

		if not self._verificar_formato_coordenadas(pontos_onibus):
			raise ValueError("Coordenadas dos pontos de ônibus estão em formato incorreto!")

	def _formatar_geodataframes(self, data: pd.DataFrame, geometry: gpd.GeoSeries, init_crs: str | int, target_crs: str | int):
		gdf = gpd.GeoDataFrame(data=data, geometry=geometry, crs=init_crs).to_crs(target_crs)
		gdf.reset_index(inplace=True, names="indice")
		return gdf

	def _criar_geodataframes(
		self, df_residencias: pd.DataFrame, df_pontos_onibus: pd.DataFrame, init_crs: str | int, target_crs: str | int
	) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
		"""Converte DataFrames para GeoDataFrames."""
		residencias = df_residencias.copy()

		self._verificar_formato(residencias, df_pontos_onibus)

		geometry_residencias = self._criar_pontos(residencias)
		geometry_onibus = self._criar_pontos(df_pontos_onibus)

		gdf_residencias = self._formatar_geodataframes(residencias, geometry_residencias, init_crs, target_crs)
		gdf_pontos_onibus = self._formatar_geodataframes(df_pontos_onibus, geometry_onibus, init_crs, target_crs)

		return gdf_residencias, gdf_pontos_onibus

	def _distancia_euclidiana(self, coord1: np.ndarray, coord2: np.ndarray, axis: int = 1) -> np.ndarray:
		"""Calcula a distância euclidiana entre dois conjuntos de coordenadas."""
		return np.sqrt(np.sum(np.square(coord1 - coord2), axis=axis))

	def _linestring_to_array(self, linestring: LineString):
		"""Converte uma Linestring em um array numpy com formato [[[x1,y1]], [[x2,y2]], ...]."""
		coords = list(linestring.coords)
		array = np.array([[[x, y]] for x, y in coords])

		return array

	def associar_ponto_a_linha(self):
		"""Associa os pontos de ônibus as linhas de ônibus mais próximos."""
		if self.linhas is None:
			raise ValueError("Dados de linhas de ônibus não carregados")
		if self.coords_pontos_onibus is None:
			raise ValueError("Coordenadas dos pontos de ônibus não carregadas")

		relacionamento = {}
		for _, linha in self.linhas.iterrows():
			nome_linha: str = linha.id_linha
			geometria_linha = linha.geometria_linha

			pontos_linha = self._linestring_to_array(geometria_linha)

			distancia = self._distancia_euclidiana(pontos_linha, self.coords_pontos_onibus, axis=2)  # type: ignore
			indices_associados = set(np.argmin(distancia, axis=1))
			relacionamento[nome_linha] = indices_associados
		return relacionamento

	def associar_residencias_a_pontos(self) -> pd.DataFrame:
		"""Associa as residências aos pontos de ônibus mais próximos."""
		if self.coords_residencias is None:
			raise ValueError("Coordenadas das residências não carregadas")

		if self.coords_pontos_onibus is None:
			raise ValueError("Coordenadas dos pontos de ônibus não carregadas")

		num_residencias = len(self.coords_residencias)

		residencias = np.arange(num_residencias).tolist()
		pontos_onibus = []
		distancias = []

		for _, residencia in enumerate(self.coords_residencias):
			distancia_residencia = self._distancia_euclidiana(residencia.reshape(1, -1), self.coords_pontos_onibus)
			idx_ponto_mais_proximo = np.argmin(distancia_residencia)
			distancia_minima = distancia_residencia[idx_ponto_mais_proximo]

			pontos_onibus.append(idx_ponto_mais_proximo)
			distancias.append(distancia_minima)

		return pd.DataFrame({"residencia": residencias, "ponto_onibus": pontos_onibus, "distancia": distancias})

	def _calcular_proporcao_distancia(self, df: pd.DataFrame, limite=500):
		total_residencias = len(df)
		residencias_proximas = df[df["distância"] < limite].shape[0]
		proporcao = residencias_proximas / total_residencias
		return proporcao

	def consolidar_associacoes(self, limite_distancia=500) -> pd.DataFrame:
		"""
		Consolida todas as associações (linhas, pontos de ônibus e residências).

		Returns:
			list: Lista consolidada com linha, ponto de ônibus, residência e distância.
		"""
		try:
			residencias_pontos = self.associar_residencias_a_pontos()
			if residencias_pontos.empty:
				raise ValueError("Não foi possível obter associações entre residências e pontos de ônibus")

			pontos_linhas = self.associar_ponto_a_linha()

			if not pontos_linhas:
				raise ValueError("Não foi possível obter associações entre pontos de ônibus e linhas")

			consolidado = {"id_linha": [], "distancia": [], "proporcao": [], "num_residencias": []}

			for nome_linha, pontos_onibus_linha in pontos_linhas.items():
				distancias_associadas = residencias_pontos[residencias_pontos["ponto_onibus"].isin(pontos_onibus_linha)]

				if distancias_associadas.empty:
					consolidado["id_linha"].append(nome_linha)
					consolidado["distancia"].append(float("nan"))
					consolidado["proporcao"].append(0.0)
					consolidado["num_residencias"].append(0)
					continue

				media_distancia = distancias_associadas["distancia"].mean()

				proporcao = (distancias_associadas["distancia"] < limite_distancia).mean()

				consolidado["id_linha"].append(nome_linha)
				consolidado["distancia"].append(media_distancia)
				consolidado["proporcao"].append(proporcao)
				consolidado["num_residencias"].append(len(distancias_associadas))

			resultado = pd.DataFrame(consolidado)
			resultado = resultado.sort_values(by="proporcao", ascending=False)
			return resultado
		except Exception as e:
			print(f"Erro ao consolidar as associações: {e}")
			return pd.DataFrame()

	def get_geodataframe_com_distancia(self) -> gpd.GeoDataFrame:
		"""
		Faz o join entre os pontos de ônibus e as distâncias calculadas.

		das residências mais próximas, retornando um GeoDataFrame com
		latitude, longitude e distância média.

		Returns:
			gpd.GeoDataFrame: GeoDataFrame contendo as colunas
			'latitude', 'longitude', 'distancia_media'
		"""
		df_associacao = self.associar_residencias_a_pontos()

		gdf_resultado = self.gdf_residencias.reset_index().merge(df_associacao, left_index=True, right_on="residencia")

		gdf_resultado = gdf_resultado[["latitude", "longitude", "geometry", "distancia"]]

		return gdf_resultado
