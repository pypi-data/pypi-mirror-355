import folium
import geopandas as gpd
import matplotlib.pyplot as plt
from folium.plugins import GroupedLayerControl, HeatMap
from matplotlib.patches import Patch

from ..data_analysis.classificar_indicadores import ClassificarIndicadores
from ..utils.associador import Associador
from .camadas import adicionar_linha_ao_mapa


class MapaIQT:
	"""Classe para criar e gerenciar mapas interativos de Índice de Qualidade do Transporte (IQT).

	Esta classe fornece funcionalidades para inicializar um mapa centrado em uma cidade,
	adicionar camadas de rotas e classificá-las de acordo com o IQT (Índice de Qualidade
	do Transporte).

	Attributes:
		gdf_city (gpd.GeoDataFrame): GeoDataFrame contendo as geometrias dos bairros da cidade.
		mapa (folium.Map): Objeto de mapa Folium inicializado.
		legenda (str): String contendo informações sobre a legenda do mapa.
	"""

	def __init__(self, gdf_city: gpd.GeoDataFrame):
		"""Inicializa um mapa centrado na cidade com uma camada base de bairros.

		Args:
			gdf_city (gpd.GeoDataFrame): GeoDataFrame contendo as geometrias dos bairros da cidade. Deve conter uma coluna 'geometry' com os polígonos dos bairros.
		"""
		self.gdf_city = gdf_city.copy()
		self.mapa = self._inicializar_mapa(self.gdf_city)
		self.mapa_de_calor = self._inicializar_mapa(self.gdf_city)
		# self.base_map = self._criar_mapa_base()
		self.linhas = gpd.GeoDataFrame()
		self.legenda = ""

	def _inicializar_mapa(self, gdf_city: gpd.GeoDataFrame) -> folium.Map:
		"""Inicializa um mapa Folium centrado na cidade com uma camada base de bairros."""
		bounds = gdf_city.total_bounds

		center_lat = (bounds[1] + bounds[3]) / 2
		center_lon = (bounds[0] + bounds[2]) / 2

		map_routes = folium.Map(location=[center_lat, center_lon], zoom_start=12, tiles="CartoDB Voyager")

		folium.GeoJson(
			gdf_city, style_function=lambda feature: {"fillColor": "white", "color": "black", "weight": 0.7, "fillOpacity": 0.5}, name="Bairros"
		).add_to(map_routes)

		map_routes.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

		return map_routes

	def classificar_rota_grupo(self, gdf_routes: gpd.GeoDataFrame) -> folium.Map | None:
		"""Adiciona rotas ao mapa base, classificadas por cor e organizadas em grupos de camadas.

		Esta função agrupa as rotas com base em sua classificação IQT, cria grupos de
		camadas no mapa e adiciona controles para ativar/desativar grupos de camadas.

		Args:
			gdf_routes (gpd.GeoDataFrame): GeoDataFrame contendo as rotas a serem adicionadas.
				Deve conter as seguintes colunas:
				- geometria_linha: geometria do tipo LineString
				- id_linha: nome da rota para o tooltip
				- iqt: índice de qualidade para determinação da cor

		Returns:
			folium.Map: Mapa Folium com as rotas adicionadas, classificadas por cor
				e organizadas em grupos de camadas de acordo com o IQT.
			None: Se ocorrer algum erro no processo.

		Example:
			>>> gdf_city = gpd.read_file("caminho/para/bairros.geojson")
			>>> gdf_routes = gpd.read_file("caminho/para/rotas.geojson")
			>>> mapa_iqt = MapaIQT(gdf_city)
			>>> mapa_final = mapa_iqt.classificar_rota_grupo(gdf_routes)
			>>> mapa_final.save("mapa_rotas_grupos.html")
		"""
		grupos = {}
		self.linhas = gdf_routes.copy().to_crs(4326)
		classificador = ClassificarIndicadores()
		listas_grupo = []

		for _, line in self.linhas.iterrows():
			classificao_iqt = classificador.classificacao_iqt_pontuacao(line.iqt)

			grupo = grupos.get(classificao_iqt, None)
			if grupo is None:
				grupo = folium.FeatureGroup(name=classificao_iqt)
				listas_grupo.append(grupo)
				self.mapa.add_child(grupo)
				grupos[classificao_iqt] = grupo
			adicionar_linha_ao_mapa(line, grupo)

		GroupedLayerControl(groups={"classificacao": listas_grupo}, collapsed=False).add_to(self.mapa)

		return self.mapa

	def gerar_mapa_de_calor(self, associador: Associador):
		"""Função para gerar o mapa de calor."""
		dados = associador.get_geodataframe_com_distancia()
		pontos = [[row["latitude"], row["longitude"], row["distancia"]] for _, row in dados.iterrows()]

		HeatMap(pontos, radius=25, blur=15, max_zoom=1).add_to(self.mapa_de_calor)

		return self.mapa_de_calor

	def _get_informacoes_mapa(self):
		"""Função para obter as informações do mapa."""
		limites = self.gdf_city.total_bounds
		quantidade_bairros = self.gdf_city.shape[0]
		return limites, quantidade_bairros

	def mostrar_abrangencia_linha(self, id_linha: str):
		"""
		Mostra a abrangência de uma linha de ônibus específica no mapa.
		"""
		linha = self.linhas[self.linhas["id_linha"] == id_linha]

		if linha.empty:
			print(f"Não foi encontrada nenhuma linha com o ID {id_linha}.")
			return

		linha_utm = linha.to_crs(epsg=31983)

		buffer_500m = linha_utm.buffer(500)

		gdf_buffer = gpd.GeoDataFrame(geometry=buffer_500m, crs="EPSG:31983").to_crs(epsg=4326)

		fig, ax = plt.subplots(figsize=(10, 10))

		self.gdf_city.plot(ax=ax, color="lightgray", edgecolor="black")

		self.gdf_city["numero"] = range(1, len(self.gdf_city) + 1)

		for _, row in self.gdf_city.iterrows():
			plt.text(row.geometry.centroid.x, row.geometry.centroid.y, str(row["numero"]), fontsize=8, ha="center")

		gdf_buffer.plot(ax=ax, color="blue", alpha=0.3, label="Buffer")
		linha.plot(ax=ax, color="red", linewidth=2, label="Linha")

		legend_elements = [
			Patch(facecolor="lightgray", edgecolor="black", label="Bairros"),
			Patch(facecolor="blue", edgecolor="blue", alpha=0.3, label="Buffer"),
			Patch(facecolor="red", edgecolor="red", label="Linha"),
		]

		plt.legend(handles=legend_elements)

		plt.title("Linha com Buffer (500 m) sobre Bairros")
		# plt.savefig("mapa_com_buffer.png", dpi=300)
		plt.show()
