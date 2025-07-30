# od2 - Old Dragon 2
Esse módulo de RPG é para uso do Old Dragons 2. Faz uso da API deles.

Depende do módulo TTRPGaag

## Changelog
- **1.0.0**: alterado a forma como os arquivos da API são puxados, já que o JSON não abre do módulo
- **0.1.1**: correção da abertura do arquivo
- **0.1.0**: lançamento com DATA, Monstro() e TesouroAleatorio()

## Atualizando a API
Para obter os json da API, rode o arquivo `converte_api.py` na raíz do projeto do módulo, baixe os arquivos e dê continuidade.

## DATA
Essa classe contém diversas propriedades com informações na formato python. Algumas propriedades são classes com parâmetros e métodos.

## `buscar(lista, termo_busca, chave)`
Essa função retorna um dicionário que esteja na `lista`, cujo valor da `chave` seja o `termo_busca`.

## `filtrar(lista, termo_busca, chave)`
Retorna um gerador com os resultados da filtragem da `lista`, atendendo o `termo_busca` em `chave`

## `filtrar_alcance(lista, chave, maior_que, menor_que)`
Retorna um gerador com os resultados da filtragem, buscando um valor entre o menor e o maior.

## `filtrar_por_exclusao(lista, termo_excluir, chave)`
Retorna um gerador com os itens que não correspondam ao termo.

## `filtrar_livro_basico(lista: list)`
Retorna um gerador somente com itens do livro básico.

## `rolar_atributos(estilo)`
Essa função vai retornar uma classe com os atributos rolados (ou para serem escolhidos, se for esse o método).

### `estilo`
- clássico (livro 1)
- aventureiro (livro 1)
- heroico (livro 1)

## `GeradorAtributos`
Essa classe gera os atributos para um personagem e permite atribuir os atributos conforme o estilo, mostrado acima.

### `.rolamento`
Lista com os atributos rolados

### `.rolar()`
Rola os atributos (já aplicado por padrão)

### `.atribuir_atributo(atributo, valor)`
- `atributo`: qual atributo vai receber o valor, os atributos são as siglas em maiúsculo. Não permite atribuir para um atributo já escolhido.
- `valor`: qual o valor rolado que vai ser escolhido

### `.zerar_atributo(atributo)`
Tira o valor escolhido para aquele atributo, permitindo que o valor e o atributo sejam escolhidos novamente.

### `.trocar_atributos(atributo1, atributo2)`
Troca o valor de um atributo com outro.

## `.rolar_renda_inicial()`
Rola os dados para a renda inicial. Retorna uma tupla com o primeiro valor sendo o valor em peças de ouro e o segundo valor os dados originais para ser usado como referência

## `TesouroAleatorio(tipo_tesouro)`
Rola o tesouro aleatório para o tipo escolhido conforme a tabela 9.5. Assim que chama a classe o tesouro já é rolado. mas alterar o tipo de tesouro, rola o tesouro novamente. Essa classe pode ser deixada para gerar vários tesouros separadamente, usando `rolar()` para isso.

### `.tipo`
O tipo do tesouro, pode ser alterado. Se alterar, o tesouro é rolado nvamente.

### `.tabela`
A tabela original desse tipo de tesouro, como uma lista

### `.tesouro_rapido`
Retorna o valor do tesouro rápido desse tipo de tesouro

### `.tesouro`
O resultado do rolamento do tesouro, incluindo moedas, itens mágicos, etc.

### `.rolar()`
Rola o tesouro. Esse rolamento é feito automaticamente ao criar a classe e também ao mudar o tipo de tesouro.

## `Monstro()`
Essa classe recebe um dicionário de um monstro base e diversos métodos como ataque, rolar tesouros, etc. As propriedades são tradução dos originais. Por exemplo `['attacks]` é `.ataques`
