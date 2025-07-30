def _checar_conversao(texto: str):
    try:
        int(texto)
        return True
    except (ValueError, TypeError):
        return False
    
def converter_para_numero(texto: str):
    if _checar_conversao(texto):
        return int(texto)
    return texto

def converter_para_texto(numero: int | None):
    if numero == None or numero == 0:
        return ''
    return f'{numero}' if numero < 0 else f'+{numero}'
