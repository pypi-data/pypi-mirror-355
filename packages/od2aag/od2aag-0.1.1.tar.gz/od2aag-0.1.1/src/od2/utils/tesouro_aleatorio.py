import string
import re
from collections import Counter
from random import choice
from RPG import rolar_dado_notacao, rolar_tabela, d6, d100

from ..helpers import x_em_d6
from ..data import DATA

tesouro_aleatorio = DATA.TESOURO_ALEATORIO
equipamento_raridade = DATA.TESOURO_EQUIPAMENTOS_RARIDADE
equipamento_tipo = DATA.TESOURO_EQUIPAMENTOS
objetos_valor_raridade = DATA.TESOURO_OBJ_VALOR_RARIDADE
objetos_valor_tipo = DATA.TESOURO_OBJ_VALOR
tipos_item = DATA.TESOURO_MAGICO
tesouro_gemas = DATA.TESOURO_GEMA
gemas_qualidade = DATA.TESOURO_GEMA_QUALIDADE

class TesouroAleatorio:
    def __init__(self, tipo_tesouro: str):
        """Gera um tesouro aleatório baseado no tipo, na tabela 9.5.\n
        O tesouro é rolado automaticamente, bastando criar um objeto com a classe,
        mas é possível rolar novamente caso queira rolar mais de um tesouro do mesmo tipo
        através do método .rolar()

        Args:
            tipo_tesouro (str): qual o tipo do tesouro rolado

        Raises:
            ValueError: Levanta um erro no caso do tipo do tesouro não existir

        Returns:
            .tesouro: os dados do tesouro rolado
            .tesouro_rapido: o conteúdo do tesouro rápido
        """

        self._tipo = self._retornar_tipo(tipo_tesouro)
        self._rapido = Counter(self.tabela.get('tesouro_rapido'))
        self._tesouro = {}
        self.rolar()

    def __str__(self):
        texto_final = []

        #* moedas
        pc = self.tesouro.get('pc', 0)
        pp = self.tesouro.get('pp', 0)
        po = self.tesouro.get('po', 0)

        if pc:
            texto_final.append(f'{pc}pc')
        if pp:
            texto_final.append(f'{pp}pp')
        if po:
            texto_final.append(f'{po}po')


        #* gemas
        gemas = self.tesouro.get('gemas').get('descrição') if self.tesouro.get('gemas') else ''
        gemas = f'Gemas: {gemas}' if gemas else ''
        if gemas:
            texto_final.append(gemas)

        #* objetos de valor
        bens = self.tesouro.get('objetos de valor')
        total = sum([bem.get('valor', 0) for bem in bens])
        bens = f'Objetos de valor: {len(bens)} itens no valor total de {total}PO.' if bens else ''
        if bens:
            texto_final.append(bens)

        #* equipamentos
        equipamentos = ', '.join(self.tesouro.get('equipamentos'))
        equipamentos = f'Equipamentos: {equipamentos}.' if equipamentos else ''
        if equipamentos:
            texto_final.append(equipamentos)

        #* itens mágicos
        itens_magicos = [list(item.values())[0] for item in self.tesouro.get('itens mágicos')]
        itens_magicos = ', '.join(itens_magicos)
        itens_magicos = f'Itens mágicos: {itens_magicos}.' if itens_magicos else ''
        if itens_magicos:
            texto_final.append(itens_magicos)

        #* final
        if texto_final:
            texto_final.insert(0, 'Tesouro:')
            return '\n'.join(texto_final)
        else:
            return 'Sem tesouro'
    
    def __repr__(self):
        return f'<TesouroAleatorio(tipo={self.tipo})>'
    
    def __add__(self, other):
        self.tesouro_rapido += other.tesouro_rapido
        self._tesouro['po'] += other._tesouro['po']
        self._tesouro['pp'] += other._tesouro['pp']
        self._tesouro['pc'] += other._tesouro['pc']
        self._tesouro['gemas'] += other._tesouro['gemas']
        self._tesouro['objetos de valor'] += other._tesouro['objetos de valor']
        self._tesouro['equipamentos'] += other._tesouro['equipamentos']
        self._tesouro['valor total'] += other._tesouro['valor total']
        self._tesouro['itens mágicos'] += other._tesouro['itens mágicos']
    

    #? Propriedades
    @property
    def tipo(self):
        return self._tipo

    @tipo.setter
    def tipo(self, tipo_tesouro: str):
        self._tipo = self._retornar_tipo(tipo_tesouro)
        self.rolar()

    @property
    def tabela(self):
        return [i for i in tesouro_aleatorio if i.get('tipo') == self.tipo][0]

    @property
    def tesouro_rapido(self):
        """O tesouro rápido de apenas moedas, pegando a média das chances (primeiro item da tabela 9.5)"""
        return self._rapido

    @tesouro_rapido.setter
    def tesouro_rapido(self, valor: dict | Counter):
        valor = valor if isinstance(valor, Counter) else Counter(valor)
        self._rapido = valor

    @property
    def tesouro(self):
        return self._tesouro
    
    #? Métodos privados
    def _retornar_tipo(self, tipo: str):
        tipo = tipo.upper()

        if tipo not in string.ascii_uppercase[:string.ascii_uppercase.index('V') + 1]:
            raise ValueError(
                f'O tipo "{tipo}" não existe na tabela de tesouro. Escolha entre "A" até "V"')

        return tipo

    def _verificar_se_tem_item(self, tabela: dict):
        return x_em_d6(tabela.get('chance', 0)).sucesso if tabela else False

    def _rolar_quantidade(self, dados: str):
        return rolar_dado_notacao(dados) if isinstance(dados, str) else int(dados)

    def _retornar_lista_bens(self, tabela: str, tabela_raridade: list, tabela_tipo: list):
        base = self.tabela.get(tabela)
        tem_item = self._verificar_se_tem_item(base)
        resultado = []

        if tem_item:
            qtd_itens = base.get('rolamento')
            qtd_itens = self._rolar_quantidade(qtd_itens)

            for _ in range(qtd_itens):
                raridade = rolar_tabela(tabela_raridade, d6(2))
                item = rolar_tabela(tabela_tipo, d6(2), raridade, rolar_dados=True)
                resultado.append(item)

        return resultado

    def _substituir_notacao_dado(self, texto: str):
        regex = r'\d*d\d+(?:[-+*/]\d+)?'
        dado = re.search(regex, texto)
        dado = str(rolar_dado_notacao(dado.group())) if dado else ''

        return re.sub(regex, dado, texto)

    def _retornar_moedas(self, chave: str):
        base = self.tabela.get(chave)
        tem_item_valor = self._verificar_se_tem_item(base)

        if not tem_item_valor:
            return 0
        
        return rolar_dado_notacao(base.get('rolamento'))

    def _retornar_gema(self):
        base = self.tabela.get('gemas')
        tem_gema = self._verificar_se_tem_item(base)

        if tem_gema:
            qtd_gemas = base.get('rolamento')
            qtd_gemas = self._rolar_quantidade(qtd_gemas)

            gema = rolar_tabela(tesouro_gemas, d6(2))
            qualidade = rolar_tabela(gemas_qualidade, d6())
            nome = f'{gema['categoria']} {qualidade['qualidade']}'
            valor = int(gema['valor'] * qualidade['modificador'])
            qtd = f'({qtd_gemas}) ' if qtd_gemas > 1 else ''

            return Counter({
                'categoria': nome,
                'valor': valor,
                'quantidade': qtd_gemas,
                'descrição': f'{qtd}{nome}, valor {valor} PO.'
            })

        return Counter()

    def _retornar_obj_valor(self):
        objetos_valor = self._retornar_lista_bens(
            'objetos_de_valor',
            objetos_valor_raridade, 
            objetos_valor_tipo)
        
        for i, objeto in enumerate(objetos_valor):
            valor = d6(2) * 100
            peso = 1 if objeto[-1] == '*' else 0
            texto = objeto.replace(' *', '')
            objetos_valor[i] = Counter({
                'objeto': texto,
                'valor': valor,
                'carga': peso,
                'descrição': f'{texto}, {valor} PO (carga: {peso})'
            })
        
        return objetos_valor

    def _retornar_equipamentos(self):
        equipamentos = self._retornar_lista_bens(
            'equipamentos',
            equipamento_raridade,
            equipamento_tipo)
        return [self._substituir_notacao_dado(item) for item in equipamentos]

    def _retornar_valor_tesouro(self):
        gemas = self.tesouro.get('gemas')
        valor_gemas = gemas.get('quantidade', 0) * gemas.get('valor', 0)
        valor_bens = sum([item['valor'] for item in self.tesouro.get('objetos de valor')])
        valor_moedas = self.tesouro.get('po') + int(self.tesouro.get('pp') / 10) + int(self.tesouro.get('pc') / 100)

        return valor_gemas + valor_bens + valor_moedas

    def _retorna_itens_magicos(self):
        base = self.tabela.get('itens_magicos')
        tem_item = self._verificar_se_tem_item(base)
        resultado = []

        if tem_item:
            itens = base.get('itens')
            resultado = self._retornar_lista_itens_magicos(itens)

        return resultado

    def _retornar_tesouro(self):
        self._tesouro['po'] = self._retornar_moedas('po')
        self._tesouro['pp'] = self._retornar_moedas('pp')
        self._tesouro['pc'] = self._retornar_moedas('pc')
        self._tesouro['gemas'] = self._retornar_gema()
        self._tesouro['objetos de valor'] = self._retornar_obj_valor()
        self._tesouro['equipamentos'] = self._retornar_equipamentos()
        self._tesouro['valor total'] = self._retornar_valor_tesouro()
        self._tesouro['itens mágicos'] = self._retorna_itens_magicos()

    #? Métodos privados para geração de itens
    def _retornar_lista_itens_magicos(self, itens):
        categoria_itens = Counter({chave: self._rolar_quantidade(qtd) for chave, qtd in itens.items()})
        return self._determinar_tipos_itens(categoria_itens)
    
    def _retornar_tipo_modificador(self, tipo_tesouro: str):
        tipo = rolar_tabela(tipos_item[f'{tipo_tesouro} tipo'], d100())
        mod_magico = rolar_tabela(tipos_item[f'{tipo_tesouro} bônus'], d100())

        return tipo, mod_magico
    
    def _retornar_mod_rolamento_talento(self, mod_magico: str):
        mod_talento = 0

        if '+3' in mod_magico:
            mod_magico = '+3'
            mod_talento = 5
        if '+4' in mod_magico:
            mod_magico = '+4'
            mod_talento = 10
        if '+5' in mod_magico:
            mod_magico = '+5'
            mod_talento = 20

        return mod_magico, mod_talento
    
    def _retornar_talento(self, item, mod_talento, mod_magico):
        talento = rolar_tabela(tipos_item[f'{item} talento'], d100() + mod_talento).lower()
        return '' if talento == 'nenhum talento' or 'amaldiçoad' in mod_magico else f' {talento}'

    def _determinar_tipos_itens(self, categoria_itens: dict):
        resultado = []
        for tipo, qtd in categoria_itens.items():
            for _ in range(qtd):
                resultado.append(tipo)

        tipos = [self._rolar_categoria_tesouro(tipo) for tipo in resultado]
        return [self._rolar_tesouro(item) for item in tipos]
    
    def _rolar_categoria_tesouro(self, tipo: str):
        tabela_base = ['qualquer', 'arma', 'não arma']
        return rolar_tabela(tipos_item[tipo], d100()) if tipo in tabela_base else tipo

    def _rolar_tesouro(self, tipo: str):
        tipos_especiais = ['armadura', 'outra arma', 'espada']

        if tipo in tipos_especiais:
            if tipo == 'armadura':
                item = self._rolar_armaduras()
            if tipo == 'espada':
                item = self._rolar_espada()
            if tipo == 'outra arma':
                item = self._rolar_arma()
        else:
            item = rolar_tabela(tipos_item[tipo], d100())

        return {tipo: item if isinstance(item, str) else choice(item)}

    def _rolar_armaduras(self):
        tipo, mod_magico = self._retornar_tipo_modificador('armadura')
        mod_magico, mod_talento = self._retornar_mod_rolamento_talento(mod_magico)
        talento = self._retornar_talento('armadura', mod_talento, mod_magico)
        
        # ajusta para o masculino
        if tipo in ['escudo']:
            mod_magico = mod_magico.replace('amaldiçoada', 'amaldiçoado')
            talento = talento.replace('curadora', 'curador')

        return f'{tipo} {mod_magico}{talento}'
    
    def _rolar_espada(self):
        tipo, mod_magico = self._retornar_tipo_modificador('espada')
        mod_magico, mod_talento = self._retornar_mod_rolamento_talento(mod_magico)
        talento = self._retornar_talento('espada', mod_talento, mod_magico)

        # ajusta para o masculino
        if tipo.lower() in ['montante']:
            talento = talento.lower().replace('amaldiçoada', 'amaldiçoado')
            talento = talento.lower().replace('matadora', 'matador')
            talento = talento.lower().replace('defensora', 'defensor')
            talento = talento.lower().replace('gélida', 'gélido')

        return f'{tipo} {mod_magico}{talento}'

    def _rolar_arma(self):
        tipo, mod_magico = self._retornar_tipo_modificador('arma')
        mod_magico, mod_talento = self._retornar_mod_rolamento_talento(mod_magico)
        talento = self._retornar_talento('arma', mod_talento, mod_magico)

        # Ajusta mjnições
        qtd = ''
        if 'flecha' in tipo or 'virote' in tipo:
            tipo = choice(tipos_item['tipo flecha'])
            qtd = f' ({rolar_dado_notacao(tipos_item.get('qtd flecha'))})'
        if 'funda' in tipo:
            tipo = 'funda'
            qtd = f' ({rolar_dado_notacao(tipos_item.get('qtd funda'))})'

        # Pega o talento
        talento = choice(tipos_item.get(f'arma talento'))

        # Ajusta o talento matador
        if 'matador' in talento:
            talento += ' ' + choice(tipos_item['talento matador'])


        return f'{tipo}{qtd} {mod_magico}{talento}'


    #? Métodos públicos
    def rolar(self):
        """Rola o tesouro (rolado automaticamente na criação da classe, pode ser rolado novamente)
        """
        self._retornar_tesouro()
