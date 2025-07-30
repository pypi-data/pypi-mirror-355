from collections import namedtuple
from RPG import d20, d6


Rolagem = namedtuple('Rolagem', ('rolamento', 'numero_alvo', 'sucesso'))
Ataque = namedtuple('Ataque', ('rolamento', 'total', 'sucesso', 'critico'))
ChanceEm6 = namedtuple('chance_em_6', ('rolamento', 'sucesso'))


def teste_atributo(valor_atributo: int, modificador: int = 0):
    numero_alvo = valor_atributo + modificador

    rolamento = d20()
    resultado = rolamento <= numero_alvo

    if rolamento == 20:
        resultado = False

    if rolamento == 1:
        resultado = True
    
    return Rolagem(rolamento, numero_alvo, resultado)


def jogada_protecao(valor_protecao: int, modificador: int = 0):
    return teste_atributo(valor_protecao, modificador)


def jogada_ataque(ba: int, ca_alvo: int, modificador: int = 0, alcance_crit: int = 20):
    rolamento = d20()
    rolamento_modificado = rolamento + modificador + ba
    resultado = rolamento_modificado > ca_alvo
    critico = rolamento >= alcance_crit or rolamento == 1

    return Ataque(rolamento, rolamento_modificado, resultado, critico)

def x_em_d6(x: int):
    """Rola a chance em d6

    Args:
        x (int): A chance de rolamento bem sucedido, coloque o valor maior. Exemplo: 1-2 em 1d6 vai receber 2 como parâmetro

    Returns:
        ChanceEm6: namedtuple -> .rolamento (int, o dado rolado), .sucesso (bool, se teve sucesso)
    """
    rolamento = d6()
    resultado = rolamento <= x

    return ChanceEm6(rolamento, resultado)
