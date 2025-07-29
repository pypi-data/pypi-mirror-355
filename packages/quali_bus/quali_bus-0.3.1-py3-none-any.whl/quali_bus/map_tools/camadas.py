import fiona
import folium
import geopandas as gpd
import pandas as pd

# from shapely import wkt
# from shapely.geometry import LineString
from ..utils.cores import GeradorCores


def carregar_camadas_linhas(path_lines: str) -> gpd.GeoDataFrame:
	"""Carrega camadas de linhas de um arquivo KML, excluindo a camada 'Linhas prontas'.

	Args:
		path_lines (str): Caminho para o arquivo KML contendo as camadas de linhas.

	Returns:
		gpd.GeoDataFrame: GeoDataFrame contendo todas as camadas de linhas concatenadas,
		exceto a camada 'Linhas prontas'.
	"""
	gdf_list = []
	for layer in fiona.listlayers(path_lines):
		if layer == "Linhas prontas":
			continue
		gdf = gpd.read_file(path_lines, driver="LIBKML", layer=layer)
		gdf_list.append(gdf)
	gdf_lines = gpd.GeoDataFrame(pd.concat(gdf_list, ignore_index=True))
	return gdf_lines


def filtrar_linhas(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
	"""Filtra o GeoDataFrame para manter apenas geometrias do tipo LineString.

	Args:
		gdf (gpd.GeoDataFrame): GeoDataFrame contendo diferentes tipos de geometrias.

	Returns:
		gpd.GeoDataFrame: GeoDataFrame filtrado contendo apenas geometrias do tipo LineString.
	"""
	return gdf[gdf.geometry.type == "LineString"]


def calcular_distancias(gdf_lines: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
	"""Calcula o comprimento de cada LineString no GeoDataFrame.

	Args:
		gdf_lines (gpd.GeoDataFrame): GeoDataFrame contendo geometrias do tipo LineString.

	Returns:
		gpd.GeoDataFrame: GeoDataFrame original com uma nova coluna 'distances' contendo
		o comprimento de cada linha.
	"""
	gdf_lines["distances"] = gdf_lines.apply(lambda row: row.geometry.length, axis=1)
	return gdf_lines


def calcular_distancias_2(gdf_lines: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
	"""Calcula distâncias em metros e quilômetros usando projeção Web Mercator (EPSG:3857).

	Args:
		gdf_lines (gpd.GeoDataFrame): GeoDataFrame contendo geometrias do tipo LineString.

	Returns:
		gpd.GeoDataFrame: GeoDataFrame com novas colunas:
			- 'distancia_metros': comprimento da linha em metros
			- 'distancia_km': comprimento da linha em quilômetros
		O GeoDataFrame é retornado na projeção WGS84 (EPSG:4326).
	"""
	gdf_lines = gdf_lines.to_crs(3857)
	gdf_lines["distancia_metros"] = gdf_lines.length
	gdf_lines["distancia_km"] = gdf_lines["distancia_metros"] / 1000
	return gdf_lines.to_crs(4326)


def criar_popup(line: pd.Series) -> str:
	"""Cria um popup HTML contendo informações sobre a linha.

	Args:
		line (pd.Series): Série contendo os atributos da linha.

	Returns:
		str: String HTML representando o conteúdo do popup.
	"""
	popup_content = f"""
	<div style="max-width:300px;">
		<h4 style="margin-bottom:10px;">{line.id_linha}</h4>
		<table style="width:100%; border-collapse:collapse;">
	"""
	for idx, value in line.items():
		if idx != "geometria_linha":
			value = round(value, 2) if isinstance(value, float) else value
			popup_content += f"""
			<tr style="border-bottom:1px solid #ddd;">
				<td style="padding:5px;"><strong>{idx}</strong></td>
				<td style="padding:5px;">{value}</td>
			</tr>
			"""
	popup_content += "</table></div>"
	return popup_content


def adicionar_linha_ao_mapa(line: pd.Series, group: folium.FeatureGroup, color: str = "") -> None:
	"""Adiciona uma linha ao mapa Folium com grupo específico.

	Args:
		line (pd.Series): Série contendo a geometria da linha e seus atributos.
		group (folium.FeatureGroup): Grupo de features do Folium onde a linha será agrupada.
		color (str, optional): Cor da linha. Se não for fornecida, será gerada uma cor aleatória.
	"""
	color = color if color else GeradorCores.cor_aleatoria()
	folium.PolyLine(
		locations=[(lat, lon) for lon, lat, *rest in line.geometria_linha.coords],
		color=color,
		weight=2.5,
		opacity=1,
		tooltip=line.id_linha,
		popup=criar_popup(line),
	).add_to(group)


# def _coordenadas_pontos_linhas(line: gpd.GeoSeries) -> list[tuple[float, float]]:
# 	"""Extrai as coordenadas de uma linha do tipo LineString.

# 	Args:
# 		line (gpd.GeoSeries): Série contendo a geometria da linha.

# 	Returns:
# 		list[tuple[float, float]]: Lista de tuplas com as coordenadas (latitude, longitude) da linha.
# 	"""
# 	return [(lat, lon) for lon, lat, *rest in line.coords]
