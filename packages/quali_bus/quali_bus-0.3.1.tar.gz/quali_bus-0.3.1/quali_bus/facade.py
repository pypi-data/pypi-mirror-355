import geopandas as gpd
import pandas as pd

from .data_analysis import CalcularIndicadores
from .map_tools import MapaIQT
from .visualization import VisualizacaoBairros


class QualiBus:
	"""
	Classe Facade para orquestrar a análise de qualidade do transporte público usando a biblioteca QualiBus.
	"""

	def __init__(self, shapefile_path, initial_crs=31983, target_crs=4326):
		"""
		Inicializa a análise, carregando o shapefile dos limites da cidade.

		Args:
			shapefile_path (str): Caminho para o shapefile dos limites.
			initial_crs (int): CRS original do shapefile.
			target_crs (int): CRS para o qual o shapefile será convertido (geralmente WGS84).
		"""
		print("Inicializando QualiBus...")
		self.gdf_city = self._carregar_shapefile(shapefile_path, initial_crs, target_crs)

		# Instancia os componentes internos
		self._indicadores = CalcularIndicadores()
		self._map_routes = MapaIQT(self.gdf_city)
		self._visualizacao_bairros = VisualizacaoBairros()

		# Estado interno
		self._operacional_ok = False
		self._geo_ok = False
		self._iqt_ok = False

		print("Componentes internos inicializados.")

	def _carregar_shapefile(self, path: str, initial_crs=31983, target_crs=4326):
		"""Carrega um shapefile, define o CRS inicial e converte para o alvo."""
		try:
			gdf = gpd.read_file(path)
			gdf = gdf.set_crs(epsg=initial_crs)
			gdf = gdf.to_crs(target_crs)
			return gdf
		except Exception as e:
			print(f"Erro ao carregar shapefile '{path}': {e}")
			raise

	def _carregar_csv(self, path: str, **kwargs):
		"""Carrega um arquivo CSV."""
		try:
			return pd.read_csv(path, **kwargs)
		except FileNotFoundError:
			print(f"Erro: Arquivo não encontrado em {path}")
			raise
		except Exception as e:
			print(f"Erro ao ler {path}: {e}")
			raise

	def carregar_dados_operacionais(
		self, linhas_path, frequencia_path, pontualidade_path, init_crs: str | int = "EPSG:4326", target_crs: str | int = "EPSG:31983"
	):
		"""
		Carrega os dados operacionais das linhas, frequência e pontualidade.

		Args:
			linhas_path (str): Caminho para o CSV de dados das linhas.
			frequencia_path (str): Caminho para o CSV de frequência.
			pontualidade_path (str): Caminho para o CSV de pontualidade.
			init_crs (str): CRS inicial dos dados geoespaciais
			target_crs (str): CRS projetado dos dados geoespaciais
		"""
		print("Carregando dados operacionais...")
		df_linhas = self._carregar_csv(linhas_path)
		df_frequencia = self._carregar_csv(frequencia_path, delimiter=",")
		df_pontualidade = self._carregar_csv(pontualidade_path, delimiter=",")

		self._indicadores.carregar_dados(df_linhas, df_frequencia, df_pontualidade, init_crs, target_crs)
		self._operacional_ok = True
		print("Dados operacionais carregados.")

	def carregar_dados_geoespaciais(self, pontos_path, residencias_path, init_crs: str | int = "EPSG:4326", target_crs: str | int = "EPSG:31983"):
		"""
		Carrega os dados geoespaciais de pontos de ônibus e residências.

		Args:
			pontos_path (str): Caminho para o CSV de pontos de ônibus.
			residencias_path (str): Caminho para o CSV de residências.
			init_crs (str): CRS inicial dos dados geoespaciais
			target_crs (str): CRS projetado dos dados geoespaciais
		"""
		if not self._operacional_ok:
			raise RuntimeError("Carregue os dados operacionais primeiro.")

		print("Carregando dados geoespaciais...")
		df_pontos = self._carregar_csv(pontos_path)
		df_residencias = self._carregar_csv(residencias_path)

		self._indicadores.carregar_dados_geometrias(df_pontos, df_residencias, init_crs, target_crs)
		self._geo_ok = True
		print("Dados geoespaciais carregados.")

	def calcular_indicadores_iqt(self):
		"""
		Executa o cálculo dos indicadores e do IQT.

		Requer que os dados operacionais e geoespaciais tenham sido carregados.
		"""
		if not self._operacional_ok or not self._geo_ok:
			raise RuntimeError("Carregue todos os dados (operacionais e geo) primeiro.")

		print("Calculando IQT...")
		self._indicadores.classificar_linha()
		self._indicadores.processar_iqt()
		self._iqt_ok = True
		print("Cálculo de IQT concluído.")
		return self._indicadores.matriz

	def gerar_mapa_rotas_por_iqt(self, **kwargs):
		"""
		Gera e retorna um mapa das rotas classificadas por IQT.

		Args:
			**kwargs: Argumentos adicionais para a criação do mapa.

		Returns:
			object: O objeto do mapa gerado (ex: folium.Map).
		"""
		if not self._iqt_ok:
			raise RuntimeError("Calcule o IQT primeiro.")
		print("Gerando mapa de rotas por IQT...")
		# Nota: O original chama map_routes.classificar_rota_grupo.
		# Aqui, estamos assumindo que este método GERA e retorna o mapa.
		# Se ele apenas classifica e outro método gera, ajuste aqui.
		mapa = self._map_routes.classificar_rota_grupo(self._indicadores.dados_completos, **kwargs)
		return mapa

	def gerar_mapa_calor_acessibilidade(self, **kwargs):
		"""
		Gera e retorna um mapa de calor da acessibilidade.

		Args:
			**kwargs: Argumentos adicionais para a criação do mapa.

		Returns:
			object: O objeto do mapa gerado.
		"""
		if not self._geo_ok:
			raise RuntimeError("Carregue os dados geoespaciais primeiro.")
		print("Gerando mapa de calor...")
		mapa = self._map_routes.gerar_mapa_de_calor(self._indicadores.associador, **kwargs)
		return mapa

	def gerar_mapa_abrangencia_linha(self, id_linha, **kwargs):
		"""
		Gera e retorna um mapa mostrando a abrangência de uma linha específica.

		Args:
			id_linha (str): O identificador da linha.
			**kwargs: Argumentos adicionais para a criação do mapa.

		Returns:
			object: O objeto do mapa gerado.
		"""
		if not self._iqt_ok:  # Precisa do IQT ou apenas dos dados das linhas? Ajuste se necessário.
			raise RuntimeError("Calcule o IQT primeiro.")
		print(f"Gerando mapa de abrangência para a linha {id_linha}...")
		mapa = self._map_routes.mostrar_abrangencia_linha(id_linha, **kwargs)
		return mapa

	def gerar_visualizacao_distribuicao_bairros(self, **kwargs):
		"""
		Gera e retorna a visualização da distribuição de linhas por bairro.

		Returns:
			object: O objeto da visualização gerada (ex: um plot, mapa, etc.).
		"""
		if not self._operacional_ok:
			raise RuntimeError("Carregue os dados operacionais primeiro.")
		print("Gerando visualização de distribuição por bairro...")
		# Usa os dados_linhas já processados internamente
		vis = self._visualizacao_bairros.distribuicao_linhas_por_bairro(self.gdf_city, self._indicadores.dados_linhas, **kwargs)
		return vis

	def get_dados_completos(self):
		"""Retorna o GeoDataFrame completo com todos os dados e IQT."""
		return self._indicadores.dados_completos if self._iqt_ok else None

	def get_matriz_indicadores(self):
		"""Retorna o DataFrame com a matriz final de indicadores e IQT."""
		return self._indicadores.matriz if self._iqt_ok else None

	def get_associacoes(self):
		"""Retorna o DataFrame com as associações entre residências e pontos."""
		return self._indicadores.associador.associar_residencias_a_pontos() if self._geo_ok else None

	@property
	def associador(self):
		"""Permite acesso ao objeto Associador para análises mais detalhadas."""
		return self._indicadores.associador if self._geo_ok else None

	@property
	def mapa(self):
		"""Permite acesso ao objeto MapaIQT para observar a distribuição de linhas."""
		return self._map_routes
