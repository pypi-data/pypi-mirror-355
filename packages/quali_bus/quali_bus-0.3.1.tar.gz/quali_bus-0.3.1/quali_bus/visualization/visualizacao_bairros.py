import contextily as ctx
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

from ..utils.cores import GeradorCores


class VisualizacaoBairros:
	"""
	Classe para visualizar dados de bairros e linhas de transporte público.
	"""

	def distribuicao_linhas_por_bairro(self, bairros: gpd.GeoDataFrame, linestrings: gpd.GeoDataFrame, num_classes: int | None = None) -> None:
		"""
		Distribui linhas de transporte público por bairros, gera um mapa e otimiza o processo com sjoin.
		"""
		if bairros.crs != linestrings.crs:
			linestrings = linestrings.to_crs(bairros.crs)

		bairros_com_linhas = gpd.sjoin(bairros, linestrings, how="left", predicate="intersects")

		contagem_linhas = bairros_com_linhas.groupby(bairros_com_linhas.index).size()

		bairros["num_linhas"] = contagem_linhas.reindex(bairros.index, fill_value=0).astype(int)

		bairros_web = bairros.to_crs(epsg=3857)
		fig, ax = plt.subplots(1, 1, figsize=(15, 15))

		# Determina o número de classes para o mapa
		classes = num_classes if num_classes is not None else len(bairros["num_linhas"].unique())

		cores = GeradorCores.gerar_cores_pasteis(classes)
		cmap = LinearSegmentedColormap.from_list("custom_cmap", cores)
		# cmap = "viridis"

		# O Geopandas cuida da legenda para nós!
		bairros_web.plot(
			column="num_linhas",
			ax=ax,
			cmap=cmap,
			scheme="quantiles",
			k=classes,
			legend=True,
			legend_kwds={"title": "Nº de Linhas por Bairro", "loc": "lower right", "frameon": True, "shadow": True},
			edgecolor="black",
			linewidth=0.5,
		)

		ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron)

		# O resto do seu código para estatísticas está ótimo!
		plt.title("Distribuição de Linhas de Ônibus por Bairro", fontsize=16)
		plt.tight_layout()

		total_linestrings = len(linestrings)
		max_linestrings = bairros["num_linhas"].max()
		min_linestrings = bairros["num_linhas"].min()
		mean_linestrings = bairros["num_linhas"].mean()

		stats_text = (
			f"Total de linhas de transporte: {total_linestrings}\n"
			f"Máximo de linhas em um bairro: {max_linestrings}\n"
			f"Mínimo de linhas em um bairro: {min_linestrings}\n"
			f"Média de linhas por bairro: {mean_linestrings:.2f}"
		)

		ax.text(0.02, 0.02, stats_text, transform=ax.transAxes, fontsize=12, bbox={"facecolor": "white", "alpha": 0.8, "pad": 5})

		plt.show()
