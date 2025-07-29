import pandas as pd


class ClassificarIndicadores:
	"""
	Classe para classificar os indicadores de qualidade do transporte público.

	Esta classe contém métodos para calcular o Índice de Qualidade do Transporte (IQT)
	e avaliar diferentes aspectos do serviço de transporte público, como pontualidade,
	infraestrutura e atendimento.
	"""

	def _pontualidade_pontuacao(self, pontualidade: float) -> int:
		"""
		Calcula a pontuação para o indicador de pontualidade.

		Args:
			pontualidade (float): Valor entre 0 e 1 representando a taxa de pontualidade.

		Returns:
			int: Pontuação atribuída de acordo com a taxa de pontualidade.
		"""
		if 0.95 <= pontualidade:
			return 3
		elif 0.90 <= pontualidade < 0.95:
			return 2
		elif 0.80 <= pontualidade < 0.90:
			return 1
		else:
			return 0

	def _abrangencia_rede_pontuacao(self, proporcao: float) -> int:
		"""
		Calcula a pontuação para o indicador de abrangência da rede de transporte.

		Args:
			proporcao (float): Proporção da cobertura da rede.

		Returns:
			int: Pontuação atribuída com base na cobertura da rede.
		"""
		if proporcao == 1.0:
			return 3
		elif 0.95 < proporcao <= 0.99:
			return 2
		elif 0.85 < proporcao <= 0.95:
			return 1
		else:
			return 0

	def _porcentagem_vias_pavimentadas_pontuacao(self, porcentagem: float) -> int:
		"""
		Calcula a pontuação para o indicador de vias pavimentadas.

		Args:
			porcentagem (float): Valor entre 0 e 1 representando a porcentagem de vias pavimentadas.

		Returns:
			int: Pontuação atribuída com base na proporção de vias pavimentadas.
		"""
		if 1 <= porcentagem:
			return 3
		elif 0.95 <= porcentagem < 0.99:
			return 2
		elif 0.85 <= porcentagem < 0.95:
			return 1
		else:
			return 0

	def _distancia_pontos_pontuacao(self, distancia: float) -> int:
		"""
		Calcula a pontuação para o indicador de distância entre pontos de parada.

		Args:
			distancia (float): Distância em metros entre os pontos de parada.

		Returns:
			int: Pontuação atribuída com base na distância entre pontos.
		"""
		if 100 >= distancia:
			return 3
		elif 100 <= distancia < 200:
			return 2
		elif 200 <= distancia < 400:
			return 1
		else:
			return 0

	def _integracao_municipal_pontuacao(self, integracao: str) -> int:
		"""
		Calcula a pontuação para o indicador de integração municipal.

		Args:
			integracao (str): Descrição da integração do transporte municipal.

		Returns:
			int: Pontuação baseada na integração do sistema de transporte.
		"""
		match integracao.strip():
			case (
				"Sistema de transporte público totalmente integrado com terminais com o uso de bilhete eletrônico para integração intra e intermodal"
			):
				return 3
			case (
				"Sistema de transporte público totalmente integrado com terminais com o uso de bilhete eletrônico para integração intramodal somente"
			):
				return 2
			case "Integração tarifária temporal ocorre em determinados pontos, apenas com transferências intramodais":
				return 1
			case _:
				return 0

	def _frequencia_atendimento_pontuacao(self, frequencia: float) -> int:
		"""
		Calcula a pontuação para o indicador de frequência de atendimento.

		Args:
			frequencia (float): Tempo em minutos entre atendimentos.

		Returns:
			int: Pontuação atribuída conforme a frequência do serviço.
		"""
		if frequencia <= 10:
			return 3
		elif frequencia <= 15:
			return 2
		elif 15 < frequencia <= 30:
			return 1
		else:
			return 0

	def _treinamento_capacitacao_pontuacao(self, treinamento: float) -> int:
		"""
		Calcula a pontuação para o indicador de treinamento e capacitação.

		Args:
			treinamento (float): Valor entre 0 e 1 representando o nível de treinamento dos motoristas.

		Return:
			int: Pontuação atribuída:
		"""
		if 1 <= treinamento:
			return 3
		elif 0.95 <= treinamento <= 0.98:
			return 2
		elif 0.90 <= treinamento <= 0.95:
			return 1
		else:
			return 0

	def classificacao_iqt_pontuacao(self, iqt: float) -> str:
		"""
		Classifica o Índice de Qualidade do Transporte (IQT) em categorias qualitativas.

		Args:
			iqt (float): Valor do IQT.

		Returns:
			str: Classificação qualitativa do IQT.
		"""
		if iqt >= 3.0:
			return "Excelente"
		elif 2 <= iqt < 3.0:
			return "Bom"
		elif 1.0 <= iqt < 2:
			return "Suficiente"
		else:
			return "Insuficiente"

	def _cumprimento_itinerarios_pontuacao(self, etinerario: float) -> int:
		"""
		Calcula a pontuação para o indicador de cumprimento de etinerários.

		Args:
			etinerario (float): Valor do cumprimento de etinerários.

		Returns:
			int: Pontuação atribuída:
		"""
		if 1 <= etinerario:
			return 3
		elif 0.8 <= etinerario <= 0.9:
			return 2
		elif 0.5 <= etinerario <= 0.7:
			return 1
		else:
			return 0

	def _informacao_internet_pontuacao(self, informacao: str) -> int:
		"""Retorna a pontuação com base na atualização das informações online.

		Args:
			informacao (str): Descrição do estado das informações no site/aplicativo.

		Returns:
			int: Pontuação correspondente à atualização das informações.
		"""
		match informacao:
			case "Possuir informações em site e aplicativo atualizados":
				return 3
			case "Possuir informações em site parcialmente atualizado":
				return 2
			case "Possuir informação em site desatualizado":
				return 1
			case _:
				return 0

	def _valor_tarifa_pontuacao(self, informacao_tarifa: str) -> int:
		"""Retorna a pontuação com base na política de aumento da tarifa.

		Args:
			informacao_tarifa (str): Descrição do aumento da tarifa.

		Returns:
			int: Pontuação correspondente ao impacto do aumento tarifário.
		"""
		match informacao_tarifa:
			case "Não houve aumento da tarifa":
				return 3
			case "Aumento inferior ao índice":
				return 2
			case "Aumento equivalente ao índice":
				return 1
			case _:
				return 0

	def classificar_linhas(self, dados_linhas: pd.DataFrame) -> pd.DataFrame:
		"""
		Classifica as linhas de transporte público com base nos indicadores avaliados.

		Args:
			dados_linhas (pd.DataFrame): DataFrame contendo os dados das linhas e seus indicadores.

		Returns:
			pd.DataFrame: DataFrame contendo as classificações de cada linha.
		"""
		classificacao = {"id_linha": [], "I1": [], "I2": [], "I3": [], "I4": [], "I5": [], "I6": [], "I7": [], "I8": [], "I9": [], "I10": []}

		for _, linha in dados_linhas.iterrows():
			classificacao["id_linha"].append(linha["id_linha"])
			classificacao["I1"].append(self._porcentagem_vias_pavimentadas_pontuacao(linha["indicador_via_pavimentada"]))
			classificacao["I2"].append(self._distancia_pontos_pontuacao(linha["distancia"]))
			classificacao["I3"].append(self._integracao_municipal_pontuacao(linha["tipo_integracao"]))
			classificacao["I4"].append(self._pontualidade_pontuacao(linha["pontualidade"]))
			classificacao["I5"].append(self._frequencia_atendimento_pontuacao(linha["frequencia_atendimento_pontuacao"]))
			classificacao["I6"].append(self._cumprimento_itinerarios_pontuacao(linha["cumprimento_itinerario"]))
			classificacao["I7"].append(self._abrangencia_rede_pontuacao(linha["proporcao"]))
			classificacao["I8"].append(self._treinamento_capacitacao_pontuacao(linha["indicador_treinamento_motorista"]))
			classificacao["I9"].append(self._informacao_internet_pontuacao(linha["disponibilidade_informacao"].strip()))
			classificacao["I10"].append(self._valor_tarifa_pontuacao(linha["valor_tarifa"]))

		return pd.DataFrame(classificacao)
