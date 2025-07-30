from RPG import Dado, d20, rolar_dado_notacao
from collections import namedtuple

from .entidade import EntidadeBase
from ..helpers import converter_para_numero, converter_para_texto, jogada_ataque
from ..data import DATA, buscar
from ..utils import TesouroAleatorio

class Monstro(EntidadeBase):
    # Mapeamento de chaves do dicionário original para atributos em português
    mapa_de_atributos = {
        'name': 'nome',
        'xp': 'xp',
        'dv': 'dv',
        'dv_bonus': 'dv_bonus',
        'pv': 'pv',
        'ca': 'ca',
        'jp': 'jp',
        'mv': 'movimento',
        'mo': 'moral',
        'attacks': 'ataques',
        'alignment': 'alinhamento',
        'size': 'tamanho',
        'habitats': 'habitats',
        'type': 'tipo',
        'id': 'id',
        'url': 'url',
        'picture': 'imagem',
        'thumb_picture': 'miniatura',
        'treasure': 'tesouro',
        'treasure_lair': 'tesouro_covil',
        'encounters': 'encontros',
        'encounters_lair': 'encontros_covil',
        'variant': 'variacao',
        'variant_modifications': 'variante_modificadores',
        'access': 'acesso',
        'concept': 'conceito',
        'flavor': 'flavor',
        'fontes': 'fontes',
        'description': 'descricao',
        'mvc': 'movimento_cavando',
        'mve': 'movimento_escalando',
        'mvn': 'movimento_nadando',
        'mvo': 'movimento_outros',
        'mvv': 'movimento_voo',
    }

    def __init__(self, monstro: dict | str):
        self._dados = dict(monstro if isinstance(monstro, dict) else buscar(DATA.MONSTROS, monstro))

        for chave_original, nome_em_portugues in self.mapa_de_atributos.items():
            setattr(self, nome_em_portugues, self._dados.get(chave_original))


        # Estatísticas
        self.xp = converter_para_numero(self._dados.get('xp'))
        self.dv = self._retornar_dv(self._dados.get('dv'))
        self.dv_bonus = self._retornar_mod_dv(self._dados.get('dv_bonus'))
        self.pv = converter_para_numero(self._dados.get('pv'))
        self.ca = self._retornar_ca(self._dados.get('ca'))

        # Propriedades para alteração privada
        super().__init__(self.pv)

    #? Propriedades
    @property
    def dados(self):
        return dict(self._dados)


    def __repr__(self):
        return f"<Monstro(nome={self.nome})>"

    def __str__(self):
        ataques_str = 'Nenhum ataque'
        mod_dv = '' if not self.dv_bonus else self.dv_bonus
        mod_dv = f'+{mod_dv}' if mod_dv and mod_dv > 0 else mod_dv

        if self.ataques:
            ataques_str = ', '.join(
                a.get('text', 'Ataque desconhecido') for a in self.ataques)

        return (
            f"{self.nome} ({self.xp} xp). "
            f"DV {self.dv}{mod_dv} ({self.pv} pv), "
            f"CA {self.ca}, JP {self.jp}, "
            f"MV {self.movimento}, MO {self.moral}. "
            f"Ataques: {ataques_str}"
        )
    
    def __setattr__(self, nome, valor):
        # Se o atributo estiver no mapeamento, sincroniza com _dados
        if 'mapa_de_atributos' in self.__dict__ or nome in ('_dados', 'mapa_de_atributos'):
            # Durante __init__, permite setar normalmente
            super().__setattr__(nome, valor)
        else:
            # Verifica se é um atributo mapeado em português
            chave_original = None
            for k, v in self.mapa_de_atributos.items():
                if v == nome:
                    chave_original = k
                    break

            # Atualiza _dados se encontrar correspondência
            if chave_original and '_dados' in self.__dict__:
                self._dados[chave_original] = valor

            super().__setattr__(nome, valor)
    
    
    #? Métodos privados
    def _retornar_dv(self, dv_original: str):
        if dv_original == '½':
            return 0.5
        return converter_para_numero(dv_original)


    def _retornar_mod_dv(self, dv_original: str):
        if not dv_original:
            return 0
        return converter_para_numero(dv_original)


    def _retornar_ca(self, ca: str):
        convertido = converter_para_numero(ca)

        if isinstance(convertido, int):
            return convertido
        
        if '/' in ca:
            cas = ca.split('/')
            return list(int(c) for c in cas)

        return ca


    def _retornar_dano_causado(self, rolamento_ataque, rolamento_dano, mod_aditivo, mod_multiplicativo):
        dano_total = 0

        if rolamento_ataque.sucesso:
            dano_total = rolamento_dano.total if not rolamento_ataque.critico else (
                rolamento_dano.total_dados * 2) + rolamento_dano.modificador

            dano_total += mod_aditivo
            dano_total *= mod_multiplicativo

        return dano_total


    def _retornar_encontro(self, texto_encontro: str):
        if texto_encontro == '-' or isinstance(texto_encontro, type(None)):
            return 0
        
        if 'd' in texto_encontro:
            return rolar_dado_notacao(texto_encontro)
        
        return int(texto_encontro)


    def _retornar_tesouro(self, tipo: str):
        return TesouroAleatorio(tipo)


    #? Métodos públicos
    def calcular_vida(self):
        """Recalcula a vida, para o caso de mudar o HD da criatura
        """
        vida_base = 5 * self.dv
        
        self.pv = vida_base + self.dv_bonus


    def escolher_ca(self, indice: int = 0):
        """Escolhe qual a armadura do monstro atual caso haja mais de uma opção

        Args:
            indice (int, optional): Qual o índice da armadura na lista de opções. Defaults to 0.

        Raises:
            TypeError: Caso a armadura não possua opções a serem escolhidas indica isso
        """
        if isinstance(self.ca, list):
            self.ca = self.ca[indice]
        else:
            raise TypeError(f'CA não pode ser escolhida, valor de CA: {self.ca}')


    def escolher_arma(self, arma: dict | str):
        """Escolhe a arma que o monstro usa, caso ele tenha essa opção

        Args:
            arma (dict | str): A arma a ser usada, seja o dicionário da mesma ou o nome
        """
        if isinstance(arma, str):
            arma = buscar(DATA.EQUIPAMENTOS, arma, 'name')

        for ataque in self.ataques:
            if ataque.get('weapon') == True:
                nome = arma.get('name')

                ataque['damage'] = arma.get('damage')
                ataque['damage_description'] = f'{ataque['damage']}{converter_para_texto(ataque['damage_bonus'])}'
                ataque['description'] = nome
                ataque['text'] = f"{ataque['times']} × {nome} {converter_para_texto(ataque['ba'])} ({ataque['damage_description']})"


    def rolar_moral(self):
        """Rola a moral do monstro

        Returns:
            ResultadoMoral: tupla nomeada -> 'total' (o valor total do 2d6), 'rolamento' (os dois dados rolados) e 'sucesso' (bool, se passou no teste)
        """
        ResultadoMoral = namedtuple('ResultadoMoral', ('total', 'dados', 'sucesso'))

        dados = Dado(2, 6)
        rolamento = dados.rolamento
        total = dados.total
        sucesso = total <= self.moral

        return ResultadoMoral(total, rolamento, sucesso)


    def rolar_ataque(self, indice_ataque: int = 0, modificador_ataque: int = 0, ca_alvo: int = 10):
        """Executa o rolamento de ataque contra a ac de um alvo

        Args:
            indice_ataque (int, optional): O índice do ataque na lista de ataques. Defaults to 0.
            modificador_ataque (int, optional): Modificador situacional ao ataque. Defaults to 0.
            ca_alvo (int, optional): A CA do alvo para determinar se houve sucesso. Defaults to 10.

        Raises:
            ValueError: Quando se escolhe um índice de ataque inapropriado

        Returns:
            Ataque: named tuple: .rolamento (quanto que rolou no dado), .rolamento_modificado (o valor total do ataque), .resultado (tupla, indicando se acertou ou errou), .critico (tupla, indicando se foi acerto ou falha crítica)
        """
        if indice_ataque >= len(self.ataques):
            raise IndexError(
                f'O índice {indice_ataque} não está disponível. Valor máximo: {len(self.ataques) - 1}')
        ba = self.ataques[indice_ataque].get('ba')
        
        return jogada_ataque(ba, ca_alvo, modificador_ataque)


    def rolar_dano(self, indice_ataque: int = 0):
        """Rola o dano de um determinado ataque, escolhido dentre os ataques do monstro

        Args:
            indice_ataque (int, optional): Qual o índice do ataque escolhido. Defaults to 0.

        Raises:
            ValueError: Se o índice não está no alcance dos ataques

        Returns:
            ResultadoDano: namedtuple: .total (o dano total rolado), .total_dados (a soma dos dados rolados), .dados (os dados invididuais), .modificador (o modificador aplicado no dano)
        """
        ResultadoDano = namedtuple('ResultadoDano', ('total', 'total_dados', 'dados', 'modificador'))

        if indice_ataque >= len(self.ataques):
            raise IndexError(
                f'O índice {indice_ataque} não está disponível. Valor máximo: {len(self.ataques) - 1}')

        qtd, face = self.ataques[indice_ataque]['damage'].split('d')
        dado = Dado(int(qtd), int(face))
        mod = self.ataques[indice_ataque]['damage_bonus']
        mod = mod if mod else 0

        dano_total = dado.total + mod
        dano_total = dano_total if dano_total > 0 else 1

        return ResultadoDano(dano_total, dado.total, dado.rolamento, mod)


    def atacar(self,
               alvo,
               indice_ataque: int = 0,
               mod_ataque: int = 0,
               mod_dano_aditivo: int = 0,
               mod_dano_multiplicativo: int = 1
               ):
        """Ataca um alvo específico e reduz os pvs dele caso haja um acerto

        Args:
            alvo (Monstro | PC): O alvo do ataque, que tenha as propriedades .ca e .pv_atual
            indice_ataque (int, optional): O índice do ataque na lista de .ataques. Defaults to 0.
            mod_ataque (int, optional): Qual o modificador circunstancial do ataque. Defaults to 0.
            mod_dano_aditivo (int, optional): Modificado aditivo de dano. Defaults to 0.
            mod_dano_multiplicativo (int, optional): Modificador multiplicado do dano final. Defaults to 1.

        Returns:
            dict: Um dicionário com as chaves para referência do ataque
        """
        rolamento_ataque = self.rolar_ataque(indice_ataque, mod_ataque, alvo.ca)
        rolamento_dano = self.rolar_dano(indice_ataque)

        dano_total = self._retornar_dano_causado(rolamento_ataque, rolamento_dano, mod_dano_aditivo, mod_dano_multiplicativo)
        alvo.ferir(dano_total)

        resultado = {
            'dano final': dano_total,
            'ataque': rolamento_ataque,
            'dano': rolamento_dano,
        }

        return resultado


    def rolar_tesouro(self, covil: bool = False, tesouro_rapido: bool = False):
        tipo = self.tesouro if not covil else self.tesouro_covil

        if not tipo:
            return 'Sem tesouro'

        tesouro = self._retornar_tesouro(tipo[0])

        if len(tipo) == 3:
            operacao = tipo[1]

            if operacao == 'x':
                repeticao = eval(tipo[2])
                for _ in range(1, repeticao):
                    tesouro + self._retornar_tesouro(tipo[0])

            if operacao == '+':
                tesouro + self._retornar_encontro(tipo[2])


        if tesouro_rapido:
            return tesouro.tesouro_rapido
        
        return tesouro.tesouro


    def rolar_quantidade_encontro(self, covil: bool = False):
        dado = self.encontros if not covil else self.encontros_covil

        return self._retornar_encontro(dado)

