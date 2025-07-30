def buscar(
    lista: list,
    termo_busca: str,
    chave: str = 'name'
) -> dict:
    """Realiza uma busca por um termo exato

    Args:
        lista (list): qual a lista que se deseja buscar
        termo_busca (str): qual o termo a ser buscado
        chave (str, optional): qual a chave que se deseja buscar. Defaults to 'name'.

    Returns:
        dict: o dicionário do item buscado na lista
    """
    return next((
        item for item in lista
        if item.get(chave, '').lower() == termo_busca.lower()
    ), None)


def filtrar(
    lista: list,
    termo_busca: str,
    chave: str = 'name'
) -> GeneratorExit:
    """Filtra a lista para o termo escolhido com relação à chave escolhida ('name') por padrão

        Args:
            lista (list): qual a lista que se deseja filtrar
            termo_busca (str): qual o termo a ser buscado
            chave (str, optional): qual a chave que se deseja buscar. Defaults to 'name'.

        Returns:
            generator: um gerador com o resultado
    """
    return (
        item for item in lista
        if termo_busca.lower() in item.get(chave).lower()
    )


def filtrar_alcance(
    lista: list,
    chave: str,
    maior_que: int | float = float('-inf'),
    menor_que: int | float = float('inf'),
):
    """Filtra por alcance de valores, por exemplo: monstros com XP entre 100 e 300

    Args:
        lista (list): A lista a ser buscada
        chave (str): A chave para a consulta ('xp' no exemplo acima)
        maior_que (int | float, optional): O valor que a busca deve ser maior ou igual (100 no exemplo). Defaults to float('-inf').
        menor_que (int | float, optional): O valor que a busca deve ser menor ou igual (300 no exemplo). Defaults to float('inf').

    Returns:
        generator: um gerador com o resultado
    """
    pre_filtro = (
        item for item in lista
        if isinstance(item.get(chave), (int, float)) or
        (isinstance(item.get(chave), str) and item.get(chave).isdigit())
    )
    return (
        item for item in pre_filtro
        if maior_que <= float(item.get(chave)) <= menor_que
    )


def filtrar_por_exclusao(
    lista: list,
    termo_excluir: str,
    chave: str = 'name'
):
    """Filtra por itens que não coincidam com o termo

    Args:
        lista (list): A lista a ser buscada
        termo_excluir (str): O termo que não deve estar na lista
        chave (str, optional): Qual a chave a ser buscada na lista. Defaults to 'name'.

    Returns:
        generator: O gerador com o resultado
    """
    return (
        item for item in lista
        if termo_excluir.lower() not in item.get(chave).lower()
    )


def filtrar_livro_basico(lista: list):
    """Filtra por somente itens que existam nos três livros básicos

    Args:
        lista (list): qual a lista que deve ser filtrada

    Returns:
        generator: O gerador como resultado
    """
    return (
        item for item in lista
        if any('livros/lb' in fonte.get('digital_item_url', '') for fonte in item.get('fontes', []))
    )
