from collections import Counter
import string


tipos_tesouro = string.ascii_uppercase[:string.ascii_uppercase.index('V') + 1]

#! Tabela 9.5
tesouro_aleatorio = [
    # Covil
    {
        'tipo': 'A',
        'categoria': 'covil',
        'tesouro_rapido': Counter({'po': 12000}),
        'po': {'chance': 2, 'rolamento': '2d6 * 1000'},
        'pp': {'chance': 2, 'rolamento': '1d6 * 1000'},
        'pc': {'chance': 1, 'rolamento': '1d6 * 1000'},
        'gemas': {'chance': 3, 'rolamento': '6d6'},
        'objetos_de_valor': {'chance': 3, 'rolamento': '6d6'},
        'itens_magicos': {'chance': 2, 'itens': Counter({'qualquer': 3})},
    },
    {
        'tipo': 'B',
        'categoria': 'covil',
        'tesouro_rapido': Counter({'po': 1400}),
        'po': {'chance': 1, 'rolamento': '1d3 * 1000'},
        'pp': {'chance': 1, 'rolamento': '1d6 * 1000'},
        'pc': {'chance': 3, 'rolamento': '1d8 * 1000'},
        'gemas': {'chance': 1, 'rolamento': '1d6'},
        'objetos_de_valor': {'chance': 1, 'rolamento': '1d6'},
        'itens_magicos': {'chance': 1, 'itens': Counter({'arma': 1})},
    },
    {
        'tipo': 'C',
        'categoria': 'covil',
        'tesouro_rapido': Counter({'po': 650}),
        'pp': {'chance': 2, 'rolamento': '1d4 * 1000'},
        'pc': {'chance': 2, 'rolamento': '1d12 * 1000'},
        'gemas': {'chance': 1, 'rolamento': '1d4'},
        'objetos_de_valor': {'chance': 1, 'rolamento': '1d4'},
        'itens_magicos': {'chance': 1, 'itens': Counter({'qualquer': 2})},
    },
    {
        'tipo': 'D',
        'categoria': 'covil',
        'tesouro_rapido': Counter({'po': 3400}),
        'po': {'chance': 3, 'rolamento': '1d6 * 1000'},
        'pp': {'chance': 1, 'rolamento': '1d12 * 1000'},
        'pc': {'chance': 1, 'rolamento': '1d8 * 1000'},
        'gemas': {'chance': 2, 'rolamento': '1d8'},
        'objetos_de_valor': {'chance': 2, 'rolamento': '1d8'},
        'itens_magicos': {'chance': 1, 'itens': Counter({'qualquer': 2, 'poção': 1})},
    },
    {
        'tipo': 'E',
        'categoria': 'covil',
        'tesouro_rapido': Counter({'po': 1800}),
        'po': {'chance': 1, 'rolamento': '1d8 * 1000'},
        'pp': {'chance': 2, 'rolamento': '1d12 * 1000'},
        'pc': {'chance': 1, 'rolamento': '1d10 * 1000'},
        'gemas': {'chance': 1, 'rolamento': '1d10'},
        'objetos_de_valor': {'chance': 1, 'rolamento': '1d10'},
        'itens_magicos': {'chance': 1, 'itens': Counter({'qualquer': 3, 'pergaminho': 1})},
    },
    {
        'tipo': 'F',
        'categoria': 'covil',
        'tesouro_rapido': Counter({'po': 4000}),
        'po': {'chance': 2, 'rolamento': '1d12 * 1000'},
        'pp': {'chance': 1, 'rolamento': '2d10 * 1000'},
        'gemas': {'chance': 1, 'rolamento': '2d12'},
        'objetos_de_valor': {'chance': 1, 'rolamento': '1d12'},
        'itens_magicos': {'chance': 2, 'itens': Counter({'poção': 1, 'pergaminho': 1, 'não arma': 3})},
    },
    {
        'tipo': 'G',
        'categoria': 'covil',
        'tesouro_rapido': Counter({'po': 14000}),
        'po': {'chance': 3, 'rolamento': '10d4 * 1000'},
        'gemas': {'chance': 1, 'rolamento': '3d6'},
        'objetos_de_valor': {'chance': 1, 'rolamento': '1d10'},
        'itens_magicos': {'chance': 2, 'itens': Counter({'qualquer': 4, 'pergaminho': 1})},
    },
    {
        'tipo': 'H',
        'categoria': 'covil',
        'tesouro_rapido': Counter({'po': 27000}),
        'po': {'chance': 3, 'rolamento': '10d6 * 1000'},
        'pp': {'chance': 3, 'rolamento': '1d10 * 1000'},
        'pc': {'chance': 1, 'rolamento': '3d8 * 1000'},
        'gemas': {'chance': 3, 'rolamento': '1d10'},
        'objetos_de_valor': {'chance': 3, 'rolamento': '10d4'},
        'itens_magicos': {'chance': 1, 'itens': Counter({'qualquer': 4, 'poção': 1, 'pergaminho': 1})},
    },
    {
        'tipo': 'I',
        'categoria': 'covil',
        'tesouro_rapido': Counter({'po': 2800}),
        'gemas': {'chance': 3, 'rolamento': '2d6'},
        'objetos_de_valor': {'chance': 3, 'rolamento': '2d6'},
        'itens_magicos': {'chance': 1, 'itens': Counter({'qualquer': 1})},
    },
    {
        'tipo': 'J',
        'categoria': 'covil',
        'tesouro_rapido': Counter({'po': 25}),
        'pp': {'chance': 1, 'rolamento': '1d3 * 1000'},
        'pc': {'chance': 1, 'rolamento': '1d4 * 1000'},
    },
    {
        'tipo': 'K',
        'categoria': 'covil',
        'tesouro_rapido': Counter({'po': 15}),
        'pp': {'chance': 1, 'rolamento': '1d2 * 1000'},
    },
    {
        'tipo': 'L',
        'categoria': 'covil',
        'tesouro_rapido': Counter({'po': 200}),
        'gemas': {'chance': 3, 'rolamento': '1d4'},
    },
    {
        'tipo': 'M',
        'categoria': 'covil',
        'tesouro_rapido': Counter({'po': 40000}),
        'po': {'chance': 5, 'rolamento': '8d10 * 1000'},
        'pp': {'chance': 3, 'rolamento': '10d6 * 1000'},
        'gemas': {'chance': 3, 'rolamento': '5d4'},
        'objetos_de_valor': {'chance': 2, 'rolamento': '2d6'},
    },
    {
        'tipo': 'N',
        'categoria': 'covil',
        'itens_magicos': {'chance': 2, 'itens': Counter({'poção': '2d4'})},
    },
    {
        'tipo': 'O',
        'categoria': 'covil',
        'itens_magicos': {'chance': 3, 'itens': Counter({'poção': '1d4'})},
    },
    # Individual
    {
        'tipo': 'P',
        'categoria': 'individual',
        'tesouro_rapido': Counter({'pp': 1}),
        'pc': {'chance': 6, 'rolamento': '3d8'},
    },
    {
        'tipo': 'Q',
        'categoria': 'individual',
        'tesouro_rapido': Counter({'po': 1}),
        'pp': {'chance': 6, 'rolamento': '3d6'},
    },
    {
        'tipo': 'R',
        'categoria': 'individual',
        'tesouro_rapido': Counter({'po': 3}),
        'po': {'chance': 6, 'rolamento': '1d6'},
        'equipamentos': {'chance': 2, 'rolamento': 1}
    },
    {
        'tipo': 'S',
        'categoria': 'individual',
        'tesouro_rapido': Counter({'po': 5}),
        'po': {'chance': 6, 'rolamento': '2d4'},
        'equipamentos': {'chance': 2, 'rolamento': 1}
    },
    {
        'tipo': 'T',
        'categoria': 'individual',
        'tesouro_rapido': Counter({'po': 17}),
        'po': {'chance': 6, 'rolamento': '1d6 * 5'},
        'equipamentos': {'chance': 2, 'rolamento': 2}
    },
    {
        'tipo': 'U',
        'categoria': 'individual',
        'tesouro_rapido': Counter({'po': 90}),
        'po': {'chance': 1, 'rolamento': '1d10'},
        'pp': {'chance': 1, 'rolamento': '1d10'},
        'pc': {'chance': 1, 'rolamento': '1d10'},
        'objetos_de_valor': {'chance': 1, 'rolamento': 1},
        'itens_magicos': {'chance': 1, 'itens': Counter({'qualquer': 1})},
        'equipamentos': {'chance': 1, 'rolamento': '1d4'}
    },
    {
        'tipo': 'V',
        'categoria': 'individual',
        'tesouro_rapido': Counter({'po': 175}),
        'po': {'chance': 2, 'rolamento': '1d10'},
        'pp': {'chance': 2, 'rolamento': '1d10'},
        'objetos_de_valor': {'chance': 1, 'rolamento': '1d4'},
        'itens_magicos': {'chance': 2, 'itens': Counter({'qualquer': 1})},
        'equipamentos': {'chance': 1, 'rolamento': '1d6'}
    }
]

#! Tabela 9.6
equipamentos_raridade = [
    ((2, 2), "raro"),
    ((3, 3), "raro"),
    ((4, 4), "incomum"),
    ((5, 5), "incomum"),
    ((6, 6), "comum"),
    ((7, 7), "comum"),
    ((8, 8), "comum"),
    ((9, 9), "comum"),
    ((10, 10), "incomum"),
    ((11, 11), "incomum"),
    ((12, 12), "raro")
]
equipamentos_tipos = [
    ((2, 2), {
        "comum": "símbolo divino",
        "incomum": "aljava (1d6 flechas)",
        "raro": "porta mapas"
    }),
    ((3, 3), {
        "comum": "saco de dormir",
        "incomum": "martelo",
        "raro": "pena e tinta"
    }),
    ((4, 4), {
        "comum": "ração de viagem (1d4)",
        "incomum": "óleo",
        "raro": "corrente"
    }),
    ((5, 5), {
        "comum": "pederneira",
        "incomum": "água benta",
        "raro": "algema"
    }),
    ((6, 6), {
        "comum": "corda de cânhamo (15m)",
        "incomum": "pá ou picareta",
        "raro": "giz"
    }),
    ((7, 7), {
        "comum": "tochas (1d4)",
        "incomum": "arpéu",
        "raro": "caixa pequena"
    }),
    ((8, 8), {
        "comum": "mochila",
        "incomum": "lamparina",
        "raro": "coberta de inverno"
    }),
    ((9, 9), {
        "comum": "odre",
        "incomum": "vela (1d4)",
        "raro": "espelho"
    }),
    ((10, 10), {
        "comum": "saco de estopa",
        "incomum": "cravos ou ganchos (1d4)",
        "raro": "cadeado"
    }),
    ((11, 11), {
        "comum": "traje de exploração",
        "incomum": "traje de inverno",
        "raro": "traje nobre"
    }),
    ((12, 12), {
        "comum": "ferramenta de ladrão",
        "incomum": "lanterna furta-fogo",
        "raro": "rede"
    })
]

#! Tabela 9.7
objetos_valor_raridade = [
    ((2, 3), "obras de arte"),
    ((4, 5), "utensílios"),
    ((6, 7), "mercadoria"),
    ((8, 9), "mercadoria"),
    ((10, 11), "louças"),
    ((12, 12), "joias")
]
objetos_valor_tipos = [
    ((2, 3), {
        "mercadoria": "peles de animais raros *",
        "louças": "objetos de vidro soprado",
        "utensílios": "religiosos de cobre",
        "obras de arte": "móveis com marchetaria *",
        "joias": "cordão de prata"
    }),
    ((4, 5), {
        "mercadoria": "objetos de marfim",
        "louças": "copos de vidro e com prata",
        "utensílios": "talheres de prata",
        "obras de arte": "tapeçaria fina *",
        "joias": "brincos de prata"
    }),
    ((6, 7), {
        "mercadoria": "sacas de especiaria *",
        "louças": "baixelas de louça",
        "utensílios": "candelabros de prata",
        "obras de arte": "livro raro",
        "joias": "bracelete de prata"
    }),
    ((8, 9), {
        "mercadoria": "sacas de incenso *",
        "louças": "baixelas de porcelana com ouro",
        "utensílios": "cutelaria fina",
        "obras de arte": "escultura *",
        "joias": "pingente de pedraria"
    }),
    ((10, 11), {
        "mercadoria": "tecidos nobres *",
        "louças": "vasos de porcelana",
        "utensílios": "cálices de ouro",
        "obras de arte": "tela pintada *",
        "joias": "camafeu de ouro"
    }),
    ((12, 12), {
        "mercadoria": "metros de fina seda *",
        "louças": "cálices de vidro com pedra",
        "utensílios": "religiosos de ouro",
        "obras de arte": "estatueta em bronze *",
        "joias": "tiara de pedra rara"
    })
]

#! Tabela 9.8
gemas = [
    ((2, 3), {"categoria": "preciosa", "valor": 500}),
    ((4, 5), {"categoria": "ornamental", "valor": 50}),
    ((6, 7), {"categoria": "decorativa", "valor": 10}),
    ((8, 9), {"categoria": "decorativa", "valor": 10}),
    ((10, 11), {"categoria": "semipreciosa", "valor": 100}),
    ((12, 12), {"categoria": "joia", "valor": 1000})
]
gema_modificador = [
    ((1, 2), {'qualidade':'bruta', 'modificador': 0.75}),
    ((3, 3), {'qualidade':'trincada', 'modificador': 0.5}),
    ((4, 6), {'qualidade':'lapidada', 'modificador': 1}),
]

#! Tabela 8.2
qualquer = [
    ((1, 20), "espada"),
    ((21, 30), "outra arma"),
    ((31, 40), "armadura"),
    ((41, 65), "poção"),
    ((66, 85), "pergaminho"),
    ((86, 90), "anel"),
    ((91, 95), "haste mágica"),
    ((96, 100), "itens mágicos gerais")
]
nao_arma = [
    ((1, 14), "armadura"),
    ((15, 50), "poção"),
    ((51, 85), "pergaminho"),
    ((86, 90), "anel"),
    ((91, 95), "haste mágica"),
    ((96, 100), "itens mágicos gerais")
]
arma = [
    ((1, 65), "espada"),
    ((66, 100), "outra arma")
]

#! Tabela 8.3
espada_tipo = [
    ((1, 79), "espada longa"),
    ((80, 89), "espada curta"),
    ((90, 94), "cimitarra"),
    ((95, 99), "espada bastarda"),
    ((100, 100), "montante")
]
espada_bonus = [
    ((1, 3), "-2 amaldiçoada"),
    ((4, 10), "-1 amaldiçoada"),
    ((11, 64), "+1"),
    ((65, 84), "+2"),
    ((85, 94), "+3 (+5% na escolha do talento)"),
    ((95, 99), "+4 (+10% na escolha do talento)"),
    ((100, 100), "+5 (+20% na escolha do talento)")
]
espada_talento = [
    ((1, 59), "Nenhum Talento"),
    ((60, 62), "Matadora de licantropos"),
    ((63, 65), "Matadora de orcs"),
    ((66, 68), "Matadora de mortos-vivos"),
    ((69, 71), "Matadora de usuários de magia"),
    ((72, 74), "Matadora de gigantes"),
    ((75, 77), "Matadora de regeneradores"),
    ((78, 79), "Matadora de dragões"),
    ((80, 81), "Matadora de extraplanares"),
    ((82, 83), "Defensora"),
    ((84, 85), "da Cura"),
    ((86, 87), "de Drenar Energia"),
    ((88, 89), "da Luz"),
    ((90, 91), "Flamejante"),
    ((92, 93), "Gélida"),
    ((94, 95), "da Respiração"),
    ((96, 97), "da Velocidade"),
    ((98, 99), "Vorpal"),
    ((100, 100), "Inteligente")
]

#! Tabela 8.4
espada_inteligente = [
    ((7, 7), {
        "comunicação": "empatia",
        "idiomas": None,
        "poderes de detecção": 1,
        "poderes maiores": None
    }),
    ((8, 8), {
        "comunicação": "empatia",
        "idiomas": None,
        "poderes de detecção": 2,
        "poderes maiores": None
    }),
    ((9, 9), {
        "comunicação": "empatia",
        "idiomas": None,
        "poderes de detecção": 3,
        "poderes maiores": None
    }),
    ((10, 10), {
        "comunicação": "fala",
        "idiomas": "1d3",
        "poderes de detecção": 3,
        "poderes maiores": None
    }),
    ((11, 11), {
        "comunicação": "fala",
        "idiomas": "1d4",
        "poderes de detecção": 3,
        "poderes maiores": None
    }),
    ((12, 12), {
        "comunicação": "fala",
        "idiomas": "1d6",
        "poderes de detecção": 3,
        "poderes maiores": 1
    })
]

#! Tabela 8.5
arma_tipo = [
    ((1, 3), "flecha"),
    ((4, 4), "arco curto"),
    ((5, 5), "arco longo"),
    ((6, 6), "besta de mão"),
    ((7, 7), "besta"),
    ((8, 9), "funda (2d10+4 unidades de munição)"),
    ((10, 19), "adaga"),
    ((20, 21), "alabarda"),
    ((22, 23), "azagaia"),
    ((24, 25), "bordão/cajado"),
    ((26, 30), "lança"),
    ((31, 40), "lança montada"),
    ((41, 50), "maça"),
    ((51, 60), "machado"),
    ((61, 65), "machado de arremesso"),
    ((66, 80), "machado de batalha"),
    ((81, 85), "mangual"),
    ((86, 95), "martelo de batalha"),
    ((96, 98), "pique"),
    ((99, 100), "porrete/clava")
]
arma_bonus = [
    ((1, 3), "-2 amaldiçoada (caótica)"),
    ((4, 10), "-1 amaldiçoada (caótica)"),
    ((11, 74), "+1"),
    ((75, 94), "+2"),
    ((95, 100), "+3 (+5% no teste de talento)")
]
arma_talento = [
    ((1, 90), "nenhum talento"),
    ((91, 100), "especial (por tipo de arma)")
]

#! Tabela 8.6
armadura_tipo = [
    ((1, 40), "escudo"),
    ((41, 45), "armadura acolchoada"),
    ((46, 50), "armadura de couro"),
    ((51, 55), "armadura de couro batido"),
    ((56, 85), "cota de malha"),
    ((86, 95), "armadura de placas"),
    ((96, 100), "armadura completa")
]
armadura_bonus = [
    ((1, 3), "-2 amaldiçoada"),
    ((4, 10), "-1 amaldiçoada"),
    ((11, 74), "+1"),
    ((75, 94), "+2"),
    ((95, 100), "+3 (+5% no teste de talento)")
]
armadura_talento = [
    ((1, 93), "nenhum talento"),
    ((94, 94), "da absorção"),
    ((95, 95), "da velocidade"),
    ((96, 96), "curadora"),
    ((97, 97), "da retribuição"),
    ((98, 98), "da invisibilidade"),
    ((99, 99), "da reflexão"),
    ((100, 100), "contra projéteis")
]

#! Tabela 8.7
pocoes = [
    ((1, 5), "poção amaldiçoada"),
    ((6, 15), "poção de placebo"),
    ((16, 50), "poção de cura"),
    ((51, 64), ["poção de controle de animais", "poção de controle de humanos", "poção de controle de plantas"]),
    ((65, 66), "poção da diminuição"),
    ((67, 68), "poção da forma gasosa"),
    ((69, 70), "poção da força gigante"),
    ((71, 72), "poção do crescimento"),
    ((73, 74), "poção da invisibilidade"),
    ((75, 76), "veneno"),
    ((77, 78), "antídoto"),
    ((79, 80), "poção de defesa"),
    ((81, 82), "poção da metamorfose"),
    ((83, 84), "poção da velocidade"),
    ((85, 86), "poção da clarividência"),
    ((87, 88), "poção da percepção extrassensorial"),
    ((89, 90), "poção da resistência ao fogo"),
    ((91, 92), "poção do voo"),
    ((93, 94), "poção do heroísmo"),
    ((95, 96), "poção de respirar na água"),
    ((97, 98), "poção da sorte"),
    ((99, 100), "poção do salto")
]

#! Tabela 8.8
pergaminhos = [
    ((1, 15), "pergaminho amaldiçoado"),
    ((16, 30), "pergaminho arcano (1 círculo)"),
    ((31, 40), "pergaminho arcano (3 círculos)"),
    ((41, 45), "pergaminho arcano (4 círculos)"),
    ((46, 48), "pergaminho arcano (7 círculos)"),
    ((49, 50), "pergaminho arcano (9 círculos)"),
    ((51, 60), "pergaminho divino (1 círculo)"),
    ((61, 63), "pergaminho divino (3 círculos)"),
    ((64, 65), "pergaminho divino (7 círculos)"),
    ((66, 67), "pergaminho de proteção ao caos"),
    ((68, 69), "pergaminho de proteção à ordem"),
    ((70, 71), "pergaminho de proteção à magia"),
    ((72, 73), "pergaminho de proteção à mortos-vivos"),
    ((74, 74), "pergaminho de proteção à licantropos"),
    ((75, 75), "pergaminho de proteção à elementais"),
    ((76, 78), "mapa do tesouro (tipo a)"),
    ((79, 81), "mapa do tesouro (tipo b)"),
    ((82, 84), "mapa do tesouro (tipo c)"),
    ((85, 87), "mapa do tesouro (tipo d)"),
    ((88, 90), "mapa do tesouro (tipo e)"),
    ((91, 93), "mapa do tesouro (tipo f)"),
    ((94, 96), "mapa do tesouro (tipo g)"),
    ((97, 99), "mapa do tesouro (tipo h)"),
    ((100, 100), "mapa do tesouro (tipo m)")
]

#! Tabela 8.9
aneis = [
    ((1, 15), "anel amaldiçoado"),
    ((16, 45), "anel de proteção +1"),
    ((46, 65), "anel de proteção +2"),
    ((66, 68), "anel de proteção +3"),
    ((69, 69), "anel de proteção +4"),
    ((70, 71), "anel do controle de animais"),
    ((72, 73), "anel do controle de humanos"),
    ((74, 75), "anel do controle de plantas"),
    ((76, 77), "anel da regeneração"),
    ((78, 79), "anel da invisibilidade"),
    ((80, 81), "anel da resistência ao fogo"),
    ((82, 83), "anel da telecinesia"),
    ((84, 85), "anel de andar sobre as águas"),
    ((86, 87), "anel de refletir magias"),
    ((88, 89), "anel de armazenar magia"),
    ((90, 91), "anel da anti-ilusão"),
    ((92, 93), "anel da verdade"),
    ((94, 95), "anel do ouro de tolo"),
    ((96, 97), "anel da santidade"),
    ((98, 99), "anel da visão de raio-x"),
    ((100, 100), "anel do desejo")
]

#! Tabela 8.10
hastes = [
    ((1, 15), "haste amaldiçoada"),
    ((16, 22), "varinha de detecção de inimigos"),
    ((23, 30), "varinha de detecção de magia"),
    ((31, 37), "varinha de detecção de armadilhas"),
    ((38, 44), "varinha de paralisação"),
    ((45, 51), "varinha de bola de fogo"),
    ((52, 58), "varinha do medo"),
    ((59, 65), "varinha do congelamento"),
    ((66, 72), "varinha da ilusão"),
    ((73, 79), "varinha do relâmpago"),
    ((80, 86), "varinha da transformação"),
    ((87, 88), "cajado da cura"),
    ((89, 90), "cajado de ataque"),
    ((91, 92), "cajado da serpente"),
    ((93, 94), "cajado da anulação"),
    ((95, 96), "cajado do controle"),
    ((97, 97), "bastão do governante"),
    ((98, 98), "bastão do bloqueio"),
    ((99, 99), "bastão do armamento"),
    ((100, 100), "bastão do cancelamento")
]

#! Tabela 8.11
itens_magicos_gerais = [
    ((1, 4), "livro dos grandes feitos"),
    ((5, 8), "bestiário: o livro dos monstros"),
    ((9, 12), "grande livro da conjuração"),
    ((13, 16), "medalhão da PES"),
    ((17, 20), "camafeu do aprisionamento"),
    ((21, 24), "manto do deslocamento"),
    ((25, 28), "manto élfico"),
    ((29, 32), "bota da levitação"),
    ((33, 36), "bota élfica"),
    ((37, 40), "manoplas da força do ogro"),
    ((41, 44), "elmo da mudança de alinhamento (caótico)"),
    ((45, 48), "cinto da força do gigante"),
    ((49, 52), "elmo da telepatia"),
    ((53, 56), "tambores do pânico (caótico)"),
    ((57, 60), "trombeta da destruição (caótica)"),
    ((61, 64), "sacola devoradora (caótica)"),
    ((65, 68), "sacola guardiã"),
    ((69, 72), "buraco portátil"),
    ((73, 76), "corda da escalada"),
    ((77, 80), "vassoura de voo"),
    ((81, 84), "bola de cristal"),
    ((85, 88), "baralho das maravilhas (caótico)"),
    ((89, 92), "baralho da navegação planar"),
    ((93, 96), "garrafa do gênio"),
    ((97, 100), "tapete voador")
]

#! Talentos de armas
adagas = ['de prata', 'do retorno', 'crítica', 'flamejante']
armas_haste = ['do desarme', 'defensora', 'vigilante']
pique = ['do desarme', 'defensor', 'vigilante']
lanca = ['do retorno', 'do desarme', 'defensora']
cajado = ['defensor', 'curador', 'do desarme']
impacto = ['do retorno', 'da explosão', 'do voo', 'do desarme']
machado = ['crítico', 'da velocidade', 'de arremesso', 'matador']
machado_arremesso = ['crítico', 'da velocidade', 'do retorno', 'matador']
projeteis = ['do atordoamento', 'do desarme', 'penetrante', 'da explosão']
matador = ['de orcs', 'de mortos-vivos', 'de gigantes', 'de usuários de magia']
flecha = ['flecha de caça', 'flecha de guerra', 'virote', 'virote pequeno']
qtd_flecha = '2d6+6'
qtd_funda = '2d10+6'
