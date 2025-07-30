from RPG.dado import Dado

def rolar_renda_inicial():
    """
    Gera a renda inicial

    Returns:
        tupla: retorna uma tupla com o total e os dados rolados
    """

    dado = Dado(3, 6)
    
    return dado.total * 10, dado.rolamento
