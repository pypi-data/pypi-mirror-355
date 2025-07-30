from collections import namedtuple

ModAtributos = namedtuple('ModAtributo', ('mod', 'circulo_1', 'circulo_2', 'circulo_3'))

ATRIBUTOS = ('FOR', 'DES', 'CON', 'INT', 'SAB', 'CAR')
ATRIBUTOS_EXTENSO = ('Força', 'Destreza', 'Constituição', 'Inteligência', 'Sabedoria', 'Carisma')
ATRIBUTOS_MOD = {
    3: ModAtributos(-3, 0, 0, 0),
    5: ModAtributos(-2, 0, 0, 0),
    8: ModAtributos(-1, 0, 0, 0),
    12: ModAtributos(0, 0, 0, 0),
    14: ModAtributos(1, 1, 0, 0),
    16: ModAtributos(2, 1, 1, 0),
    18: ModAtributos(3, 2, 1, 1),
    20: ModAtributos(4, 2, 2, 1),
}
