#? Arquivo gerado a partir de magias.json

magias = [{'access': 'complete',
  'arcane': None,
  'description': 'Uma bênção é concedida pela divindade do conjurador, '
                 'concedendo ao alvo tocado um bônus de +1 nas jogadas de '
                 'ataque e nas JPS a cada 3 níveis de conjurador.\n'
                 '\n'
                 '[Profanar] é a versão reversa para personagens caóticos, '
                 'concedendo uma penalidade de 1 nas jogadas de ataque e '
                 'Jogadas de Proteção do alvo tocado. Uma JPS nega tais '
                 'efeitos.\n',
  'divine': 2,
  'duration': '6 turnos',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 105}],
  'id': 'abencoar',
  'illusionist': None,
  'jp': 'especial',
  'name': 'Abençoar',
  'necromancer': None,
  'range': 'toque',
  'reverse': True,
  'reverse_spell': {'id': 'profanar',
                    'name': 'Profanar',
                    'reverse_spell_url': 'https://olddragon.com.br/magias/profanar.json'},
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:52.797-03:00',
  'url': 'https://olddragon.com.br/magias/abencoar.json'},
 {'access': 'complete',
  'arcane': 1,
  'description': 'Esta magia pode ser utilizada para dar acesso a qualquer '
                 'objeto fechado, trancado (mesmo à chave) ou emperrado pela '
                 'duração da magia (ou até ser dissipada).\n'
                 '\n'
                 '[Trancar] é a versão reversa que permite trancar um acesso a '
                 'qualquer objeto aberto.\n',
  'divine': None,
  'duration': 'permanente',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 105}],
  'id': 'abrir',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Abrir',
  'necromancer': None,
  'range': '18 metros',
  'reverse': True,
  'reverse_spell': {'id': 'trancar',
                    'name': 'Trancar',
                    'reverse_spell_url': 'https://olddragon.com.br/magias/trancar.json'},
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:52.907-03:00',
  'url': 'https://olddragon.com.br/magias/abrir.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'Pedindo ajuda para sua divindade, o conjurador recebe sinais '
                 'mostrando-lhe um caminho, uma verdade, um evento ou uma '
                 'atividade em específico.  A resposta desejada lhe será dada '
                 'de forma indireta, como um sinal, frase, um enigma, etc.\n',
  'divine': 4,
  'duration': 'especial',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 105}],
  'id': 'adivinhacao',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Adivinhação',
  'necromancer': None,
  'range': 'especial',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:52.987-03:00',
  'url': 'https://olddragon.com.br/magias/adivinhacao.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'Esta magia concede uma ajuda de sua divindade, anulando a '
                 'perda de até 1d4 pontos de vida +1 a cada 2 níveis do '
                 'conjurador, do próximo dano sofrido pelo conjurador. Pontos '
                 'de vida anulados que sobram após o próximo dano recebido '
                 'pelo conjurador, devem ser descartados.\n',
  'divine': 2,
  'duration': '2 turnos',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 105}],
  'id': 'ajuda',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Ajuda',
  'necromancer': None,
  'range': 'toque',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:53.030-03:00',
  'url': 'https://olddragon.com.br/magias/ajuda.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'Esta magia remove instantaneamente todas as maldições '
                 'impostas sobre uma criatura ou objeto.  Esta magia não '
                 'remove maldição de armas ou armaduras mágicas, mas permite '
                 'que a criatura usando um desses itens consiga se desfazer '
                 'deles e dos efeitos que ainda recaiam sobre si.\n'
                 '\n'
                 'Certas maldições exigem um determinado nível do conjurador '
                 'para serem removidas e, nesses casos, a não ser que esse '
                 'requisito seja cumprido, o Remover Maldição não funcionará.\n'
                 '\n'
                 '[Amaldiçoar] é a versão reversa e caótica impondo uma '
                 'maldição a uma vítima que não seja bem-sucedida numa JPS. O '
                 'alvo amaldiçoado pode sofrer de um dos quatro efeitos '
                 'possíveis, a escolha do conjurador:\n'
                 '\n'
                 '  * **Vulnerabilidade do Corpo**: o alvo perde 2 pontos na '
                 'sua Classe de Armadura;\n'
                 '\n'
                 '  * **Fluidez da Memória**: conjuradores possuem 1-2 chances '
                 'em 1d6 de se esquecer de qualquer magia que forem conjurar '
                 'antes desta ser conjurada.\n'
                 '\n'
                 '  * **Fraqueza da Alma**: o alvo perde metade dos seus '
                 'pontos de Constituição e dos possíveis pontos de vida extras '
                 'que um alto valor de Constituição pode conceder.\n'
                 '\n'
                 '  * **Ineficiência da Precisão**: todo ataque do alvo é um '
                 'teste difícil.\n'
                 '\n'
                 'Uma maldição mantém seus efeitos até ser removida por uma '
                 'magia Remover Maldições.\n',
  'divine': 4,
  'duration': 'instantânea',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 129}],
  'id': 'amaldicoar',
  'illusionist': None,
  'jp': 'especial',
  'name': 'Amaldiçoar',
  'necromancer': None,
  'range': 'toque',
  'reverse': True,
  'reverse_spell': {'id': 'remover-maldicao',
                    'name': 'Remover Maldição',
                    'reverse_spell_url': 'https://olddragon.com.br/magias/remover-maldicao.json'},
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:56.438-03:00',
  'url': 'https://olddragon.com.br/magias/amaldicoar.json'},
 {'access': 'complete',
  'arcane': 4,
  'description': 'O conjurador provoca um vertiginoso crescimento da '
                 'vegetação. As plantas afetadas se entrelaçam, ficando fortes '
                 'e vigorosas, espalhando-se e ocupando todo o espaço '
                 'disponível.\n'
                 '\n'
                 'Criaturas pequenas e médias levam 1 turno para abrir uma '
                 'picada com armas de corte e se deslocam apenas 1 metro. '
                 'Criaturas grandes conseguem abrir passagem deslocando-se 2 '
                 'metros por rodada.\n',
  'divine': 3,
  'duration': 'permanente',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 106}],
  'id': 'ampliar-plantas',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Ampliar Plantas',
  'necromancer': None,
  'range': '36 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-06-23T14:09:33.480-03:00',
  'url': 'https://olddragon.com.br/magias/ampliar-plantas.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'Com esta magia, o alvo tocado adquire a habilidade de andar '
                 'sobre líquidos e solos instáveis, como se fosse solo firme. '
                 'Se memorizada como uma magia de 5º círculo, o conjurador '
                 'poderá usá-la em até dois alvos tocados.\n',
  'divine': 4,
  'duration': '2 turnos +1/nível',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 106}],
  'id': 'andar-sobre-as-aguas',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Andar sobre as Águas',
  'necromancer': None,
  'range': 'toque',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:53.106-03:00',
  'url': 'https://olddragon.com.br/magias/andar-sobre-as-aguas.json'},
 {'access': 'complete',
  'arcane': 5,
  'description': 'O conjurador pode dar vida a um cadáver ou a uma ossada para '
                 'criar um zumbi ou um esqueleto, respectivamente. Os '
                 'mortos-vivos criados desta forma não reconhecem mestres, não '
                 'cumprem ordens ou aceitam comandos, atacando qualquer um '
                 'desavisado. Um conjurador pode manter apenas um único Animar '
                 'Cadáveres por vez no máximo de 1 turno por nível. Uma nova '
                 'conjuração dissipará a anterior. Mortos-vivos destruídos não '
                 'podem ser reanimados.\n',
  'divine': None,
  'duration': '1 turno/nível',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 106}],
  'id': 'animar-cadaveres',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Animar Cadáveres',
  'necromancer': None,
  'range': 'toque',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:53.136-03:00',
  'url': 'https://olddragon.com.br/magias/animar-cadaveres.json'},
 {'access': 'complete',
  'arcane': 9,
  'description': 'Esta poderosa magia tem como objetivo invocar uma criatura '
                 'extraplanar e aprisioná-la no plano material até esta '
                 'aceitar realizar uma tarefa para o conjurador. Quando a '
                 'tarefa é cumprida, a criatura é automaticamente enviada ao '
                 'seu plano original. O conjurador precisa conhecer o '
                 'verdadeiro nome da criatura convocada e a criatura, uma vez '
                 'aprisionada no plano material, pode ou não concordar com a '
                 'chantagem do conjurador, podendo inclusive atacá-lo.\n'
                 '\n'
                 'Se a criatura for bem-sucedida em uma JPS, a magia não '
                 'funcionará e a criatura permanecerá em seu plano original. A '
                 'melhor forma de se proteger é construir, em torno do portal, '
                 'um círculo de proteção com materiais místicos.  Esse círculo '
                 'custa 100 PO para cada dado de vida da criatura a ser '
                 'convocada.\n'
                 '\n'
                 'Mesmo assim, há sempre 1 chance em 1d6 do círculo de '
                 'proteção falhar.\n',
  'divine': None,
  'duration': 'especial',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 106}],
  'id': 'aprisionamento',
  'illusionist': None,
  'jp': 'JPS nega',
  'name': 'Aprisionamento',
  'necromancer': None,
  'range': '36 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:53.173-03:00',
  'url': 'https://olddragon.com.br/magias/aprisionamento.json'},
 {'access': 'complete',
  'arcane': 8,
  'description': 'Esta magia cria uma gema de aprisionamento etéreo com um '
                 'gatilho inscrito (a última palavra da execução da magia), '
                 'fazendo com que a alma de quem segurar a gema e pronunciar a '
                 'palavra nesta inscrita, tenha imediatamente sua alma sugada '
                 'para dentro da gema. O valor da gema deve ser proporcional '
                 'ao poder da alma aprisionada, custando 1.000 PO para cada '
                 'Dado de Vida da criatura. Almas aprisionadas não morrem e '
                 'podem retornar para qualquer outro corpo recém-morto, caso a '
                 'gema seja destruída.\n',
  'divine': None,
  'duration': 'permanente',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 106}],
  'id': 'aprisionar-alma',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Aprisionar Alma',
  'necromancer': None,
  'range': 'toque',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:53.204-03:00',
  'url': 'https://olddragon.com.br/magias/aprisionar-alma.json'},
 {'access': 'limited',
  'arcane': 6,
  'divine': None,
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/arkhi.json',
              'page': 105}],
  'id': 'arkhanima-petra',
  'illusionist': None,
  'name': 'ARKHãnima Petra',
  'necromancer': None,
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-06-15T20:42:04.529-03:00',
  'url': 'https://olddragon.com.br/magias/arkhanima-petra.json'},
 {'access': 'limited',
  'arcane': 5,
  'divine': None,
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/arkhi.json',
              'page': 105}],
  'id': 'arkhitectonismo',
  'illusionist': None,
  'name': 'ARKHItectonismo',
  'necromancer': None,
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-06-15T20:42:04.555-03:00',
  'url': 'https://olddragon.com.br/magias/arkhitectonismo.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'Esta magia permite ao conjurador abençoar qualquer arma não '
                 'mágica. Todo ataque com essa arma é um ataque fácil. Caso a '
                 'arma abençoada seja uma arma natural, de madeira ou de '
                 'pedra, receberá ainda um bônus de +1d4 no dano causado.\n',
  'divine': 1,
  'duration': '1 turno',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 107}],
  'id': 'arma-abencoada',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Arma Abençoada',
  'necromancer': None,
  'range': 'toque',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:53.235-03:00',
  'url': 'https://olddragon.com.br/magias/arma-abencoada.json'},
 {'access': 'complete',
  'arcane': 4,
  'description': 'Esta magia transforma uma arma mundana em uma arma '
                 'temporariamente mágica, com bônus de +1 nas jogadas de '
                 'ataque e +1 no dano.\n',
  'divine': None,
  'duration': '1 turno/nível',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 107}],
  'id': 'arma-encantada',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Arma Encantada',
  'necromancer': None,
  'range': 'toque',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:53.262-03:00',
  'url': 'https://olddragon.com.br/magias/arma-encantada.json'},
 {'access': 'complete',
  'arcane': 4,
  'description': 'O personagem cria uma armadilha engatilhada em qualquer '
                 'objeto que possa ser aberto (como um baú, livro, porta, '
                 'gaveta, etc.), explodindo-o em chamas assim que aberto. A '
                 'explosão causa a todos em um raio de 2m do objeto 1d4 pontos '
                 'de dano + 1 ponto de dano por nível do personagem '
                 'conjurador. Uma JPD reduz o dano pela metade.  O objeto '
                 'encantado com esta magia não é afetado pelos efeitos desta '
                 'explosão.\n',
  'divine': None,
  'duration': 'permanente',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 107}],
  'id': 'armadilha-de-fogo',
  'illusionist': None,
  'jp': 'JPD reduz',
  'name': 'Armadilha de Fogo',
  'necromancer': None,
  'range': 'toque',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:53.293-03:00',
  'url': 'https://olddragon.com.br/magias/armadilha-de-fogo.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'Todas as criaturas com menos de 2 dados de vida e dentro do '
                 'raio de alcance da magia ficarão automaticamente '
                 'aterrorizadas caso falhem em uma JPS. Criaturas '
                 'aterrorizadas tremem sem controle, deixando todos os seus '
                 'testes difíceis.\n',
  'divine': None,
  'duration': '1d6 turnos + 1/nível',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 107}],
  'id': 'aterrorizar',
  'illusionist': None,
  'jp': 'JPS nega',
  'name': 'Aterrorizar',
  'necromancer': 1,
  'range': '9m + 3m/nível',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:53.329-03:00',
  'url': 'https://olddragon.com.br/magias/aterrorizar.json'},
 {'access': 'complete',
  'arcane': 7,
  'description': 'Esta magia confere ao alvo uma espécie de escudo turvador '
                 'contra efeitos de invasão mental, como a realizada pela '
                 'magia Percepção Extrassensorial e Clarividência, ou contra a '
                 'espionagem realizada por um Olho Arcano, bola de cristal e '
                 'semelhantes.  Qualquer tentativa de localização mágica do '
                 'alvo resultará em uma falha como se este simplesmente não '
                 'existisse para esses propósitos.\n'
                 '\n'
                 'Adicionalmente, o alvo passa a realizar todas as Jogadas de '
                 'Proteção contra qualquer efeito mental, como encantamentos e '
                 'ilusões, como um teste muito fácil. Um alvo com o intuito de '
                 'resistir a esta magia precisa ser bem-sucedido em uma JPS '
                 'para negar seus efeitos.\n',
  'divine': None,
  'duration': '12 turnos',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 107}],
  'id': 'barreira-mental',
  'illusionist': None,
  'jp': 'JPS nega',
  'name': 'Barreira Mental',
  'necromancer': None,
  'range': 'toque',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:53.378-03:00',
  'url': 'https://olddragon.com.br/magias/barreira-mental.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'O conjurador pode transformar bastões ou gravetos não '
                 'mágicos de madeira em serpentes, as quais atacarão ao seu '
                 'comando. A quantidade convertida é de 1d4 bastões + 1 bastão '
                 'por nível do conjurador. Cada serpente possui 1 chance em '
                 '1d6 de ser venenosa.\n',
  'divine': 4,
  'duration': '6 turnos',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 107}],
  'id': 'bastao-em-serpente',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Bastão em Serpente',
  'necromancer': None,
  'range': '36 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:53.408-03:00',
  'url': 'https://olddragon.com.br/magias/bastao-em-serpente.json'},
 {'access': 'complete',
  'arcane': 3,
  'description': 'Um projétil semelhante a uma pequena bola de chamas com 20 '
                 'cm de diâmetro, disparado pelas mãos do conjurador e '
                 'explodindo em chamas no lugar alvo. O raio da explosão é de '
                 '6 metros e o dano é de 1d6 por nível do conjurador (máximo '
                 '10d6). A explosão é adaptada ao volume disponível.  Um '
                 'sucesso em uma JPD reduz o dano desta magia pela metade. Se '
                 'memorizada como uma magia de 7º círculo, a explosão pode ser '
                 'adiada por até 10 minutos.\n',
  'divine': None,
  'duration': 'instantânea',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 108}],
  'id': 'bola-de-fogo',
  'illusionist': None,
  'jp': 'JPD reduz',
  'name': 'Bola de Fogo',
  'necromancer': None,
  'range': '72 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:53.433-03:00',
  'url': 'https://olddragon.com.br/magias/bola-de-fogo.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'Com esta magia, o conjurador é capaz de abençoar 2d4 frutos '
                 'e torná-los mágicos. Quem comer destes frutos recuperará 1 '
                 'ponto de vida perdido por nível do conjurador. A cada 24 '
                 'horas, apenas 8 pontos de vida podem ser recuperados com '
                 'esta magia.\n',
  'divine': 2,
  'duration': 'especial',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 108}],
  'id': 'bom-fruto',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Bom Fruto',
  'necromancer': None,
  'range': 'toque',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:53.460-03:00',
  'url': 'https://olddragon.com.br/magias/bom-fruto.json'},
 {'access': 'complete',
  'arcane': 6,
  'description': 'Com esta magia, o conjurador consegue transformar pedaços de '
                 'pedra em carne. Criaturas petrificadas podem ser '
                 'restauradas, bem como seus equipamentos, com esta magia. '
                 'Criaturas de pedra alvos desta magia, como um Golem de '
                 'Pedra, podem realizar uma JP para negar os efeitos da magia '
                 'ou serão destruídas.\n'
                 '\n'
                 '[Carne em Pedra] é a versão reversa que permite petrificar '
                 'um alvo assim como todo o seu equipamento. Uma JPS '
                 'bem-sucedida pode negar os efeitos desta magia.\n',
  'divine': None,
  'duration': 'permanente',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 125}],
  'id': 'carne-em-pedra',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Carne em Pedra',
  'necromancer': None,
  'range': 'toque',
  'reverse': True,
  'reverse_spell': {'id': 'pedra-em-carne',
                    'name': 'Pedra em Carne',
                    'reverse_spell_url': 'https://olddragon.com.br/magias/pedra-em-carne.json'},
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:55.908-03:00',
  'url': 'https://olddragon.com.br/magias/carne-em-pedra.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'Esta magia cura as doenças e elimina qualquer condição '
                 'proveniente de uma doença em qualquer alvo vivo. Doenças '
                 'mundanas e doenças mágicas podem ser curadas por esta '
                 'magia.\n'
                 '\n'
                 'Curar Doenças também pode ser usada para curar e eliminar os '
                 'efeitos de uma paralisia.\n'
                 '\n'
                 '[Causar Doenças] é a versão reversa que permite causar uma '
                 'doença ao invés de curar. Se o alvo tocado não passar em uma '
                 'JPC, sofrerá dores terríveis e debilitantes.\n'
                 '\n'
                 'Todos os testes do alvo passam a ser difíceis, e uma cura '
                 'natural passa a demorar o dobro do tempo normal. Curas '
                 'mágicas não surtirão efeitos. O alvo morre em 2d12 dias se '
                 'não sofrer uma magia Curar Doenças.\n',
  'divine': 3,
  'duration': 'instantânea',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 111}],
  'id': 'causar-doencas',
  'illusionist': None,
  'jp': 'especial',
  'name': 'Causar Doenças',
  'necromancer': None,
  'range': 'toque',
  'reverse': True,
  'reverse_spell': {'id': 'curar-doencas',
                    'name': 'Curar Doenças',
                    'reverse_spell_url': 'https://olddragon.com.br/magias/curar-doencas.json'},
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:54.012-03:00',
  'url': 'https://olddragon.com.br/magias/causar-doencas.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'Cura 1d8 pontos de vida. Esta magia também pode ser '
                 'modificada e memorizada como uma magia de:\n'
                 '\n'
                 '  * **3º círculo**: para curar 2d8 pontos de vida;\n'
                 '\n'
                 '  * **5º círculo**: para curar 3d8 pontos de vida;\n'
                 '\n'
                 '  * **7º círculo**: para curar completamente os pontos de '
                 'vida do alvo, além de curar ferimentos mais específicos como '
                 'membros torcidos, ossos quebrados ou contundidos. Porém, não '
                 'pode regenerar membros amputados ou inutilizados como um '
                 'olho perfurado.\n'
                 '\n'
                 'Uma magia de Curar Ferimentos é capaz de remover uma '
                 'infecção causada pela mordida de um Zumbi, mas não remove os '
                 'efeitos da paralisia, não cura doenças e nem neutraliza '
                 'venenos ou elimina qualquer outra condição de saúde do alvo, '
                 'restaurando apenas pontos de vida perdidos.\n'
                 '\n'
                 '[Causar Ferimentos] é a versão reversa que permite causar '
                 'dano ao invés de curar. A versão de 7º círculo permite matar '
                 'o alvo. Uma JPC evita esses efeitos.\n',
  'divine': 1,
  'duration': 'instantânea',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 112}],
  'id': 'causar-ferimentos',
  'illusionist': None,
  'jp': 'JPC evita',
  'name': 'Causar Ferimentos',
  'necromancer': None,
  'range': 'toque',
  'reverse': True,
  'reverse_spell': {'id': 'curar-ferimentos',
                    'name': 'Curar Ferimentos',
                    'reverse_spell_url': 'https://olddragon.com.br/magias/curar-ferimentos.json'},
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:54.070-03:00',
  'url': 'https://olddragon.com.br/magias/causar-ferimentos.json'},
 {'access': 'complete',
  'arcane': 1,
  'description': 'Esta magia permite ao Mago travar qualquer porta ou janela.\n'
                 '\n'
                 'Qualquer criatura com 3 dados de vida a mais que o '
                 'conjurador será capaz de abrir à força uma porta/ janela '
                 'travada por esta magia, mas tão logo a pessoa passe por ela, '
                 'a porta/janela será novamente travada até a magia acabar ou '
                 'ser dissipada.\n'
                 '\n'
                 'Uma magia de Abrir pode destravar a porta/janela travada por '
                 'uma Cerrar Portas.\n',
  'divine': None,
  'duration': '2d6 turnos',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 108}],
  'id': 'cerrar-portas',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Cerrar Portas',
  'necromancer': None,
  'range': '3 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:53.485-03:00',
  'url': 'https://olddragon.com.br/magias/cerrar-portas.json'},
 {'access': 'complete',
  'arcane': 9,
  'description': 'Pequenos meteoros saem das mãos do conjurador e explodem em '
                 'bolas de fogo onde ele direcionar.  O conjurador pode jogar '
                 '4 bolas de fogo normais causando 10d6 pontos de dano, ou 8 '
                 'bolas de fogo de 3 metros de diâmetro causando 5d6 pontos de '
                 'dano. Uma JPD reduz o dano pela metade.\n',
  'divine': None,
  'duration': 'instantânea',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 108}],
  'id': 'chuva-de-meteoros',
  'illusionist': None,
  'jp': 'JPD reduz',
  'name': 'Chuva de Meteoros',
  'necromancer': None,
  'range': '72 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:53.511-03:00',
  'url': 'https://olddragon.com.br/magias/chuva-de-meteoros.json'},
 {'access': 'complete',
  'arcane': 3,
  'description': 'Esta magia permite ao conjurador se concentrar em um lugar '
                 'específico já conhecido por ele para visualizar o local como '
                 'se estivesse lá fisicamente por meio dos olhos de outra '
                 'criatura viva.\n'
                 '\n'
                 'Concentrando-se por 1 minuto, o conjurador pode detectar e '
                 'estabelecer uma conexão com o alvo no local escolhido em um '
                 'raio máximo de 18 metros.  Após a conexão estabelecida, o '
                 'conjurador consegue enxergar como se fosse o alvo por toda a '
                 'duração da magia e enquanto estiver concentrado.\n'
                 '\n'
                 'O conjurador pode alterar o alvo da magia saltando para '
                 'outro na mesma área de efeito, caso se concentre por mais um '
                 'minuto para estabelecer a conexão e desde que ainda esteja '
                 'dentro da duração inicial da magia.\n'
                 '\n'
                 'A magia não pode penetrar mais de 60 centímetros de pedra e '
                 'é bloqueada até mesmo pela mais fina folha de chumbo.\n',
  'divine': None,
  'duration': '12 turnos',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 108}],
  'id': 'clarividencia',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Clarividência',
  'necromancer': None,
  'range': '18 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:53.537-03:00',
  'url': 'https://olddragon.com.br/magias/clarividencia.json'},
 {'access': 'complete',
  'arcane': 8,
  'description': 'Por meio desta magia, o conjurador cria um clone perfeito do '
                 'alvo (incluindo pensamentos e conhecimento) ao retirar deste '
                 'um pedaço de carne.\n'
                 '\n'
                 'O clone cresce e estará pronto em até 1d4 dias. Se o clone '
                 'ficar pronto enquanto a criatura original ainda estiver '
                 'viva, o clone tentará de todas as maneiras matar o ser '
                 'original para substituí-lo.\n'
                 '\n'
                 'Se o clone ou o original não conseguir destruir o seu alter '
                 'ego, ambos ficarão completamente insanos em 1d4 meses.\n',
  'divine': None,
  'duration': 'especial',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 109}],
  'id': 'clone',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Clone',
  'necromancer': None,
  'range': 'toque',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:53.562-03:00',
  'url': 'https://olddragon.com.br/magias/clone.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'Esta magia faz com que poderes divinos e superiores '
                 'respondam a até 3 perguntas mentalmente ao conjurador. As '
                 'respostas devem ser sempre dadas com um “sim”, “não” ou '
                 '“talvez”. Esses poderes superiores apenas responderão a uma '
                 'tentativa de comunhão a cada 1d6+6 dias e a, no máximo, 4 '
                 'vezes a cada ano.\n'
                 '\n'
                 'O ritual para realizar uma comunhão é longo e leva 2d4 horas '
                 'para responder a cada uma das perguntas.\n',
  'divine': 5,
  'duration': 'especial',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 109}],
  'id': 'comunhao',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Comunhão',
  'necromancer': None,
  'range': 'pessoal',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:53.589-03:00',
  'url': 'https://olddragon.com.br/magias/comunhao.json'},
 {'access': 'complete',
  'arcane': 6,
  'description': 'Uma concha de força mágica envolve o conjurador, impedindo '
                 'que qualquer efeito mágico entre ou saia da concha. O '
                 'conjurador pode, mesmo dentro da concha, dissipá-la quando '
                 'desejar.\n',
  'divine': None,
  'duration': '12 turnos',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 109}],
  'id': 'concha-antimagia',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Concha Antimagia',
  'necromancer': None,
  'range': 'pessoal',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:53.618-03:00',
  'url': 'https://olddragon.com.br/magias/concha-antimagia.json'},
 {'access': 'complete',
  'arcane': 4,
  'description': 'Esta magia causa confusão mental em alvos inteligentes, os '
                 'quais passarão a agir de forma aleatória. Uma jogada de 2d6 '
                 'determinará o efeito: 2-5 atacarão o conjurador e seus '
                 'aliados; 6-8 ficarão inativos e confusos; 9-12 atacarão uns '
                 'aos outros. Confusão afeta no máximo 2d6 criaturas + 1 '
                 'criatura adicional a cada 4 níveis do conjurador. Essas '
                 'criaturas podem realizar uma JPS para não serem afetadas '
                 'pela magia.\n',
  'divine': None,
  'duration': '12 rodadas',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 109}],
  'id': 'confusao',
  'illusionist': None,
  'jp': 'JPS nega',
  'name': 'Confusão',
  'necromancer': None,
  'range': '36 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:53.645-03:00',
  'url': 'https://olddragon.com.br/magias/confusao.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'O conjurador convoca animais das redondezas como seus '
                 'aliados. Qual criatura será conjurada e a quantidade de '
                 'criaturas será determinada com uma jogada de 1d6 segundo a '
                 'lista abaixo.  Também deverá estar de acordo com a '
                 'localização do conjurador e com o tamanho do animal:\n'
                 '\n'
                 '  * **1-3**: 1d4+2 animais pequenos como Cobra, Hiena, Lobo '
                 'ou Raposa\n'
                 '\n'
                 '  * **4-5**: 1d3+1 animais médios como Tigre, Gorila ou '
                 'Águia\n'
                 '\n'
                 '  * **6**: 1d3 animais grandes como Búfalo, Rinoceronte ou '
                 'Urso\n'
                 '\n'
                 'Os animais obedecem aos comandos do conjurador até serem '
                 'feridos, maltratados ou dispensados.\n',
  'divine': 6,
  'duration': '2 turnos',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 109}],
  'id': 'conjurar-animais',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Conjurar Animais',
  'necromancer': None,
  'range': '18 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:53.671-03:00',
  'url': 'https://olddragon.com.br/magias/conjurar-animais.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'Consagrar um local faz com que uma área de 12 metros ao '
                 'redor do local tocado se torne sagrado com os seguintes '
                 'efeitos:\n'
                 '\n'
                 'Proteção: o local é protegido contra criaturas do '
                 'alinhamento oposto ao do conjurador.  Tais criaturas não '
                 'conseguem entrar, atacar, conjurar magias e nem influenciar '
                 'nada dentro da área consagrada;\n'
                 '\n'
                 'Consagração: qualquer corpo enterrado no local não se '
                 'levantará como morto-vivo.\n',
  'divine': 5,
  'duration': 'permanente',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 110}],
  'id': 'consagrar',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Consagrar',
  'necromancer': None,
  'range': 'toque',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:53.701-03:00',
  'url': 'https://olddragon.com.br/magias/consagrar.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'O conjurador consegue animar todas as plantas dentro do '
                 'alcance da magia para agarrarem e apertarem todos os seres '
                 'vivos que passem por ali. Ao tentarem se locomover, os seres '
                 'vivos terão sua movimentação reduzida em 1 para cada rodada '
                 'que permanecerem dentro da área de efeito.\n',
  'divine': 1,
  'duration': '1 turno',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 110}],
  'id': 'constricao',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Constrição',
  'necromancer': None,
  'range': '18 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:53.731-03:00',
  'url': 'https://olddragon.com.br/magias/constricao.json'},
 {'access': 'complete',
  'arcane': 6,
  'description': 'Com esta magia, o conjurador é capaz de modificar o clima de '
                 'acordo com sua vontade.  É capaz de extinguir ventos, '
                 'chuvas, nevascas, tornar o céu limpo, dissolver um tornado '
                 'ou até mesmo criar todas essas intempéries em uma área de '
                 'efeito de 100 metros de raio ao redor do conjurador por '
                 'nível.\n',
  'divine': 7,
  'duration': 'concentração',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 110}],
  'id': 'controlar-o-clima',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Controlar o Clima',
  'necromancer': None,
  'range': '240 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-06-21T13:55:00.332-03:00',
  'url': 'https://olddragon.com.br/magias/controlar-o-clima.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'Esta magia convoca uma nuvem de insetos que atacará um alvo '
                 'indicado pelo conjurador.  O alvo pode tentar se '
                 'desvencilhar dos insetos, reduzindo assim o tempo da duração '
                 'pela metade e levando apenas 1d3 pontos de dano por rodada. '
                 'Caso deseje ignorar a nuvem, o alvo recebe 1d4 pontos de '
                 'dano por rodada e todos os seus ataques são tidos como '
                 'difíceis.\n'
                 'O LB3: Monstros & Inimigos traz mais informações sobre '
                 'Enxame de Insetos.\n',
  'divine': 3,
  'duration': '1 rodada/nível',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 110}],
  'id': 'convocar-insetos',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Convocar Insetos',
  'necromancer': None,
  'range': '18 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:53.814-03:00',
  'url': 'https://olddragon.com.br/magias/convocar-insetos.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'Esta magia convoca relâmpagos a partir de um céu carregado '
                 'com nuvens negras e prestes a chover (Chuva Leve, Chuva '
                 'Pesada ou Tempestade), direcionando-os a um ponto '
                 'específico.\n'
                 '\n'
                 'Para convocar um relâmpago, o conjurador deve se concentrar '
                 'por um turno inteiro e, no início do próximo turno, o '
                 'relâmpago cairá em qualquer ponto escolhido por ele, desde '
                 'que dentro do alcance da magia. Todos dentro de um raio de 3 '
                 'metros em torno do local atingido pelo relâmpago, recebem '
                 '2d8 pontos de dano +1d8 pontos de dano adicionais por nível '
                 'do conjurador (máximo de 8d8). Uma JPD reduz esse dano pela '
                 'metade.\n'
                 '\n'
                 'O conjurador ainda pode convocar 1 relâmpago a cada 2 turnos '
                 '(1 para convocar e outro para direcionar) enquanto '
                 'concentrado e sem realizar nenhuma outra ação.\n',
  'divine': 3,
  'duration': '1 turno + 1/nível',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 110}],
  'id': 'convocar-relampagos',
  'illusionist': None,
  'jp': 'JPD reduz',
  'name': 'Convocar Relâmpagos',
  'necromancer': None,
  'range': '150 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:53.841-03:00',
  'url': 'https://olddragon.com.br/magias/convocar-relampagos.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'Esta magia cria uma pequena fonte de água limpa e fresca no '
                 'chão, em uma parede ou pedra, capaz de criar 200 litros de '
                 'água sustentando uma quantidade de 12 pessoas e suas '
                 'montarias por um dia inteiro.\n'
                 '\n'
                 'Esta magia também pode ser modificada e memorizada como uma '
                 'magia de 6º círculo, criando 600 litros de água para 36 '
                 'pessoas e suas montarias.\n',
  'divine': 3,
  'duration': 'permanente',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 111}],
  'id': 'criar-agua',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Criar Água',
  'necromancer': None,
  'range': '6 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:53.867-03:00',
  'url': 'https://olddragon.com.br/magias/criar-agua.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'Esta magia cria uma pequena quantidade de comida, o mínimo '
                 'para o consumo diário de até 2 homens por nível do '
                 'conjurador (até o máximo de 20 homens no 10° nível). Do 11º '
                 'nível em diante, o conjurador consegue criar alimentos '
                 'suficientes para 4 homens por nível até um total de 60 '
                 'homens para um conjurador de 15º nível.\n',
  'divine': 5,
  'duration': 'permanente',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 111}],
  'id': 'criar-alimentos',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Criar Alimentos',
  'necromancer': None,
  'range': '6 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:53.892-03:00',
  'url': 'https://olddragon.com.br/magias/criar-alimentos.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'O conjurador pode dar vida a um cadáver ou a uma ossada para '
                 'criar um zumbi ou um esqueleto, respectivamente. Os '
                 'mortos-vivos criados desta forma reconhecem seus criadores '
                 'como mestres e obedecerão a seus comandos falados de forma '
                 'permanente até serem destruídos. Mortosvivos destruídos não '
                 'podem ser recriados.\n'
                 '\n'
                 'Um conjurador só pode manter sob seu controle 2 DV de '
                 'mortos-vivos por nível, ou seja, um zumbi ou dois '
                 'esqueletos. Se uma quantidade maior for criada, esses '
                 'mortos-vivos ficarão descontrolados e agirão por conta '
                 'própria.\n',
  'divine': None,
  'duration': 'permanente',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 111}],
  'id': 'criar-mortos-vivos',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Criar Mortos-Vivos',
  'necromancer': 2,
  'range': 'toque',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:53.917-03:00',
  'url': 'https://olddragon.com.br/magias/criar-mortos-vivos.json'},
 {'access': 'complete',
  'arcane': 5,
  'description': 'Esta magia cria uma passagem temporária, como se fosse um '
                 'buraco através de rocha sólida (paredes, muros, portas) com '
                 'cerca de 2 metros de altura e 3 metros de largura. O '
                 'conjurador pode criar passagens em barreiras de até 2 metros '
                 'de espessura a cada 5 níveis.\n'
                 '\n'
                 'Após o encerramento da duração da magia, a passagem se '
                 'fecha, matando automaticamente todos que estiverem em seu '
                 'interior.\n',
  'divine': None,
  'duration': '3 turnos',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 111}],
  'id': 'criar-passagens',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Criar Passagens',
  'necromancer': None,
  'range': '9 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:53.943-03:00',
  'url': 'https://olddragon.com.br/magias/criar-passagens.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'Esta magia cura as doenças e elimina qualquer condição '
                 'proveniente de uma doença em qualquer alvo vivo. Doenças '
                 'mundanas e doenças mágicas podem ser curadas por esta '
                 'magia.\n'
                 '\n'
                 'Curar Doenças também pode ser usada para curar e eliminar os '
                 'efeitos de uma paralisia.\n'
                 '\n'
                 '[Causar Doenças] é a versão reversa que permite causar uma '
                 'doença ao invés de curar. Se o alvo tocado não passar em uma '
                 'JPC, sofrerá dores terríveis e debilitantes.\n'
                 '\n'
                 'Todos os testes do alvo passam a ser difíceis, e uma cura '
                 'natural passa a demorar o dobro do tempo normal. Curas '
                 'mágicas não surtirão efeitos. O alvo morre em 2d12 dias se '
                 'não sofrer uma magia Curar Doenças.\n',
  'divine': 3,
  'duration': 'instantânea',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 111}],
  'id': 'curar-doencas',
  'illusionist': None,
  'jp': 'especial',
  'name': 'Curar Doenças',
  'necromancer': None,
  'range': 'toque',
  'reverse': True,
  'reverse_spell': {'id': 'causar-doencas',
                    'name': 'Causar Doenças',
                    'reverse_spell_url': 'https://olddragon.com.br/magias/causar-doencas.json'},
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:53.973-03:00',
  'url': 'https://olddragon.com.br/magias/curar-doencas.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'Cura 1d8 pontos de vida. Esta magia também pode ser '
                 'modificada e memorizada como uma magia de:\n'
                 '\n'
                 '  * **3º círculo**: para curar 2d8 pontos de vida;\n'
                 '\n'
                 '  * **5º círculo**: para curar 3d8 pontos de vida;\n'
                 '\n'
                 '  * **7º círculo**: para curar completamente os pontos de '
                 'vida do alvo, além de curar ferimentos mais específicos como '
                 'membros torcidos, ossos quebrados ou contundidos. Porém, não '
                 'pode regenerar membros amputados ou inutilizados como um '
                 'olho perfurado.\n'
                 '\n'
                 'Uma magia de Curar Ferimentos é capaz de remover uma '
                 'infecção causada pela mordida de um Zumbi, mas não remove os '
                 'efeitos da paralisia, não cura doenças e nem neutraliza '
                 'venenos ou elimina qualquer outra condição de saúde do alvo, '
                 'restaurando apenas pontos de vida perdidos.\n'
                 '\n'
                 '[Causar Ferimentos] é a versão reversa que permite causar '
                 'dano ao invés de curar. A versão de 7º círculo permite matar '
                 'o alvo. Uma JPC evita esses efeitos.\n',
  'divine': 1,
  'duration': 'instantânea',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 112}],
  'id': 'curar-ferimentos',
  'illusionist': None,
  'jp': 'JPC evita',
  'name': 'Curar Ferimentos',
  'necromancer': None,
  'range': 'toque',
  'reverse': True,
  'reverse_spell': {'id': 'causar-ferimentos',
                    'name': 'Causar Ferimentos',
                    'reverse_spell_url': 'https://olddragon.com.br/magias/causar-ferimentos.json'},
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:54.030-03:00',
  'url': 'https://olddragon.com.br/magias/curar-ferimentos.json'},
 {'access': 'complete',
  'arcane': 9,
  'description': 'Tida como a magia mais poderosa já criada, Desejo pode ser '
                 'fonte de poderes e perigos inimagináveis, pois realiza '
                 'desejos ilimitados do conjurador. Porém, pode punir com '
                 'extrema rigidez desejos ambíguos e malfeitos. Se preparada '
                 'como uma magia de 9º círculo, o conjurador pode realizar '
                 'Desejos os quais emulam magias de até 8º círculo sem grandes '
                 'problemas. Mas desejos que almejam efeitos grandiosos e '
                 'complexos podem ser arriscados, pois a forma como o desejo é '
                 'realizado é de extrema importância. A intenção original do '
                 'conjurador pode ser distorcida, realizando um efeito '
                 'literalmente correto, porém indesejado.\n',
  'divine': None,
  'duration': 'especial',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 112}],
  'id': 'desejo',
  'illusionist': None,
  'jp': 'especial',
  'name': 'Desejo',
  'necromancer': None,
  'range': 'especial',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:54.090-03:00',
  'url': 'https://olddragon.com.br/magias/desejo.json'},
 {'access': 'complete',
  'arcane': 6,
  'description': '\n'
                 'Esta magia faz matéria (mundana ou mágica) desaparecer por '
                 'completo, virando pó. O alvo pode fazer uma JPC para evitar '
                 'a desintegração, sofrendo 8d8 pontos de dano.\n',
  'divine': None,
  'duration': 'instantânea',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 113}],
  'id': 'desintegrar',
  'illusionist': None,
  'jp': 'especial',
  'name': 'Desintegrar',
  'necromancer': None,
  'range': '18 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:54.125-03:00',
  'url': 'https://olddragon.com.br/magias/desintegrar.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'Esta magia possibilita ao conjurador se concentrar por um '
                 'turno inteiro para detectar a aura de uma pessoa ou objeto, '
                 'determinando, assim, o seu alinhamento.\n'
                 '\n'
                 'Alinhamentos magicamente ocultos são revelados sempre como '
                 'neutros.\n',
  'divine': 1,
  'duration': '6 turnos',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 113}],
  'id': 'detectar-alinhamento',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Detectar Alinhamento',
  'necromancer': None,
  'range': '36 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:54.152-03:00',
  'url': 'https://olddragon.com.br/magias/detectar-alinhamento.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'O conjurador consegue identificar magicamente qualquer '
                 'armadilha, mágica ou não, como se fosse um Ladrão, '
                 'fazendo-as brilhar com uma tênue luz azulada. Esta magia não '
                 'revela o funcionamento das armadilhas e nem como '
                 'desativá-las.\n',
  'divine': 2,
  'duration': '2 turnos',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 113}],
  'id': 'detectar-armadilhas',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Detectar Armadilhas',
  'necromancer': None,
  'range': '9 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:54.179-03:00',
  'url': 'https://olddragon.com.br/magias/detectar-armadilhas.json'},
 {'access': 'complete',
  'arcane': 2,
  'description': 'O conjurador consegue detectar objetos e criaturas '
                 'invisíveis como se fossem normalmente visíveis para ele.\n',
  'divine': None,
  'duration': '2 turnos',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 113}],
  'id': 'detectar-invisibilidade',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Detectar Invisibilidade',
  'necromancer': None,
  'range': '18 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:54.205-03:00',
  'url': 'https://olddragon.com.br/magias/detectar-invisibilidade.json'},
 {'access': 'complete',
  'arcane': 1,
  'description': 'Com esta magia, o conjurador cria um disco flutuante de 1 '
                 'metro de diâmetro para o seguir e carregar a sua carga. O '
                 'disco consegue carregar 50 quilos por nível de conjurador. O '
                 'disco flutua a 1 metro do chão e se mantém sempre reto. A '
                 'não ser que receba outro comando, o disco se manterá sempre '
                 'a 1,5 metro de distância de seu conjurador. Quando o efeito '
                 'da magia acaba, o disco simplesmente desaparece, derrubando '
                 'tudo o que estava sobre ele. O disco também desaparece '
                 'quando a distância entre ele e o conjurador for superior ao '
                 'alcance da magia ou quando existir uma distância superior a '
                 '1 metro entre ele e o chão sobre o qual paira.\n',
  'divine': None,
  'duration': '6 turnos',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 113}],
  'id': 'disco-flutuante',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Disco Flutuante',
  'necromancer': None,
  'range': '1,5 metro',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:54.234-03:00',
  'url': 'https://olddragon.com.br/magias/disco-flutuante.json'},
 {'access': 'complete',
  'arcane': 3,
  'description': 'Esta magia pode ser usada para dissipar completamente os '
                 'efeitos de outra magia, lançada sobre um objeto ou área. A '
                 'jogada para tentar dissipar a magia é de 1d20 + nível do '
                 'personagem que está lançando a magia, contra uma dificuldade '
                 'de 5 + círculo da magia a ser dissipada + nível do '
                 'personagem que lançou a magia a ser dissipada.\n'
                 '\n'
                 '> Exemplo: um conjurador de 9º nível que tenta dissipar uma '
                 'magia de 3º círculo lançada por outro conjurador de 8º '
                 'nível, deve jogar 1d20 e somar seu resultado ao seu nível '
                 '(9).  O resultado precisa ser igual ou maior que a '
                 'dificuldade de 5 + o círculo da magia a ser dissipada (3) + '
                 'o nível do conjurador da magia (8), ou seja, maior ou igual '
                 'a 16.\n'
                 '\n'
                 'Magos só podem dissipar magias arcanas e Clérigos só podem '
                 'dissipar magias divinas.  Esta magia não é capaz de '
                 'desencantar permanentemente um item mágico, mas suprime seus '
                 'efeitos por 1 turno.\n',
  'divine': 4,
  'duration': 'permanente',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 113}],
  'id': 'dissipar-magia',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Dissipar Magia',
  'necromancer': None,
  'range': '36 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-06-23T14:09:33.556-03:00',
  'url': 'https://olddragon.com.br/magias/dissipar-magia.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'Esta magia permite ao conjurador criar uma área dissipadora '
                 'do caos, afugentando ou destruindo todas as criaturas '
                 'caóticas que se aproximem do conjurador. Cada criatura '
                 'caótica a entrar na área deve ser bem-sucedida em uma JPS '
                 'para não ser destruída imediatamente. Se passar no teste, '
                 'conseguirá fugir e se afastar da área de efeito da magia o '
                 'mais rápido possível. O conjurador precisa ficar imóvel '
                 'entoando suas orações para sustentar a duração de um '
                 'Dissipar o Caos.\n',
  'divine': 6,
  'duration': '1 turno',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 114}],
  'id': 'dissipar-o-caos',
  'illusionist': None,
  'jp': 'especial',
  'name': 'Dissipar o Caos',
  'necromancer': None,
  'range': '9 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:54.285-03:00',
  'url': 'https://olddragon.com.br/magias/dissipar-o-caos.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'O alvo tocado pela mão do conjurador sofre os efeitos de um '
                 'ataque de Drenar Vida, drenando 1d4+1 para cada 3 níveis do '
                 'Necromante. Os pontos de vida perdidos dessa maneira pelo '
                 'alvo são imediatamente somados aos atuais pontos de vida do '
                 'Necromante. Pontos de vida recuperados desta forma não podem '
                 'ultrapassar o limite de pontos de vida total do Necromante. '
                 'Um alvo que tenha todos os seus pontos de vida drenados, '
                 'morrerá imediatamente. Um sucesso em uma JPC evita o efeito '
                 'desta magia.\n',
  'divine': None,
  'duration': 'instantânea',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 114}],
  'id': 'drenar-vida',
  'illusionist': None,
  'jp': 'JPC evita',
  'name': 'Drenar Vida',
  'necromancer': 3,
  'range': 'toque',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:54.310-03:00',
  'url': 'https://olddragon.com.br/magias/drenar-vida.json'},
 {'access': 'complete',
  'arcane': 6,
  'description': 'Esta magia é utilizada para imbuir efeitos mágicos a '
                 'qualquer item. Ela deve ser lançada sobre o objeto no início '
                 'do processo e permanecerá ativa pelo tempo de duração da '
                 'magia. Se lançada sobre um item mágico, todos os efeitos '
                 'serão realizados normalmente. Cabe ao Mestre determinar '
                 'eventuais custos e tempo necessário.\n',
  'divine': None,
  'duration': 'especial',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 114}],
  'id': 'encantar-item',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Encantar Item',
  'necromancer': None,
  'range': 'toque',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:54.337-03:00',
  'url': 'https://olddragon.com.br/magias/encantar-item.json'},
 {'access': 'complete',
  'arcane': 4,
  'description': 'Esta magia afeta 3d6 monstros não humanoides vivos, médios '
                 'ou pequenos com até 3 DV, ou uma única criatura com mais de '
                 '3 DV. O alvo passa a considerar o conjurador um amigo '
                 'respeitável e confiável, obedecendo todas as suas ordens, '
                 'desde que não haja uma clara ameaça à sua integridade.  '
                 'Ordens como atacar serão sempre seguidas, mesmo quando o '
                 'alvo a ser atacado for infinitamente mais poderoso do que o '
                 'alvo da magia.\n'
                 '\n'
                 'Um sucesso em uma JPS nega o efeito desta magia. Se a '
                 'criatura enfeitiçada for ferida, poderá realizar uma nova '
                 'JPS.\n'
                 '\n'
                 'Após enfeitiçada, o valor da JPS da criatura determina a '
                 'continuação da duração de Enfeitiçar Monstros.\n'
                 '\n'
                 '  * **JPS 3 ou menor**: uma JPS por mês.\n'
                 '\n'
                 '  * **JPS 5 ou menor**: uma JPS por semana.\n'
                 '\n'
                 '  * **JPS 8 ou menor**: uma JPS por dia.\n'
                 '\n'
                 '  * **JPS 10 ou menor**: uma JPS por hora.\n',
  'divine': None,
  'duration': 'especial',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 114}],
  'id': 'enfeiticar-monstros',
  'illusionist': None,
  'jp': 'JPS nega',
  'name': 'Enfeitiçar Monstros',
  'necromancer': None,
  'range': '36 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:54.363-03:00',
  'url': 'https://olddragon.com.br/magias/enfeiticar-monstros.json'},
 {'access': 'complete',
  'arcane': 1,
  'description': 'Esta magia afeta humanoides vivos, médios ou pequenos. O '
                 'alvo passa a considerar o conjurador como um amigo '
                 'respeitável e confiável, obedecendo todas as suas ordens, '
                 'desde que não haja uma clara ameaça à sua integridade. '
                 'Ordens como atacar serão sempre seguidas, mesmo quando o '
                 'alvo a ser atacado for infinitamente mais poderoso do que o '
                 'alvo da magia. Um sucesso em uma JPS nega o efeito desta '
                 'magia. Se a criatura enfeitiçada for ferida, poderá realizar '
                 'uma nova JPS.\n'
                 '\n'
                 'Após enfeitiçado, a Inteligência do alvo determina a '
                 'continuação da duração de Enfeitiçar Pessoas.\n'
                 '\n'
                 '  * **Inepto (3-8)**: uma JPS por mês.\n'
                 '\n'
                 '  * **Mediano (9-12)**: uma JPS por semana.\n'
                 '\n'
                 '  * **Inteligente (13-16)**: uma JPS por dia.\n'
                 '\n'
                 '  * **Gênio (17-18)**: uma JPS por hora.\n',
  'divine': None,
  'duration': 'especial',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 114}],
  'id': 'enfeiticar-pessoas',
  'illusionist': None,
  'jp': 'JPS nega',
  'name': 'Enfeitiçar Pessoas',
  'necromancer': None,
  'range': '36 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:54.389-03:00',
  'url': 'https://olddragon.com.br/magias/enfeiticar-pessoas.json'},
 {'access': 'complete',
  'arcane': 1,
  'description': 'O conjurador invoca um escudo invisível que o protege de '
                 'ataques físicos, sejam estes projéteis, ataques à distância, '
                 'ou corpo a corpo. O Escudo Arcano equivale a uma armadura '
                 'com bônus de +4 e absorve totalmente o dano causado por '
                 'mísseis mágicos. Se a Classe de Armadura do conjurador já '
                 'for 14 ou superior, esta não causa efeito, a não ser no que '
                 'diz respeito à absorção do dano dos mísseis mágicos.\n',
  'divine': None,
  'duration': '2 turnos',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 115}],
  'id': 'escudo-arcano',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Escudo Arcano',
  'necromancer': None,
  'range': 'pessoal',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:54.414-03:00',
  'url': 'https://olddragon.com.br/magias/escudo-arcano.json'},
 {'access': 'complete',
  'arcane': 1,
  'description': 'O objeto alvo tocado produz luz tão brilhante quanto uma '
                 'tocha, iluminando uma área com raio de 6 metros.\n'
                 '\n'
                 'Se conjurada nos olhos de um alvo a até 3m + 1,5m/nível do '
                 'conjurador, a vítima que não passar em uma JPS fica cega até '
                 'o final da duração da magia. Neste caso, a luz mágica se '
                 'apaga e não causa nenhum outro efeito.\n'
                 '\n'
                 '[Escuridão] é a versão reversa que permite interromper '
                 'qualquer fonte de luz, apagando tochas, velas, lâmpadas ou '
                 'até mesmo dissipando uma magia Luz lançada anteriormente e '
                 'criando uma área de 4,5 metros de raio de escuridão mágica, '
                 'deixando todos dentro da área cegos (mesmo se possuírem '
                 'Infravisão).\n'
                 '\n'
                 'Se conjurada nos olhos de um alvo tocado pelo conjurador, a '
                 'vítima que não passar em uma JPS fica cega até o final da '
                 'duração da magia.  Neste caso, a escuridão mágica some e não '
                 'causa nenhum outro efeito.\n',
  'divine': 1,
  'duration': '12 turnos',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 119}],
  'id': 'escuridao',
  'illusionist': None,
  'jp': 'JPS nega',
  'name': 'Escuridão',
  'necromancer': None,
  'range': 'especial',
  'reverse': True,
  'reverse_spell': {'id': 'luz',
                    'name': 'Luz',
                    'reverse_spell_url': 'https://olddragon.com.br/magias/luz.json'},
  'type': 'Spell',
  'updated_at': '2023-12-31T16:17:09.774-03:00',
  'url': 'https://olddragon.com.br/magias/escuridao.json'},
 {'access': 'complete',
  'arcane': 2,
  'description': 'Esta magia tem o mesmo efeito de uma magia Luz, mas com '
                 'duração contínua (enquanto desejado pelo conjurador). Se '
                 'conjurada nos olhos de um alvo a até 3m + 1,5m/nível do '
                 'conjurador, a vítima que não passar em uma JPS fica cega até '
                 'o final da duração da magia. Neste caso, a luz mágica se '
                 'apaga e não causa nenhum outro efeito.\n'
                 '\n'
                 '[Escuridão Contínua] é a versão reversa que cria uma área de '
                 'escuridão mágica permanente numa área de 4,5 metros de raio, '
                 'deixando todos dentro da área cegos, inclusive criaturas com '
                 'Infravisão.  Qualquer fonte de luz trazida para dentro da '
                 'área de escuridão será apagada. Uma Escuridão Contínua pode '
                 'ser usada para dissipar os efeitos de uma magia de Luz '
                 'Contínua.\n',
  'divine': None,
  'duration': 'permanente',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 120}],
  'id': 'escuridao-continua',
  'illusionist': None,
  'jp': 'JPS nega',
  'name': 'Escuridão Contínua',
  'necromancer': None,
  'range': '36 metros',
  'reverse': True,
  'reverse_spell': {'id': 'luz-continua',
                    'name': 'Luz Contínua',
                    'reverse_spell_url': 'https://olddragon.com.br/magias/luz-continua.json'},
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:55.183-03:00',
  'url': 'https://olddragon.com.br/magias/escuridao-continua.json'},
 {'access': 'complete',
  'arcane': 6,
  'description': 'Esta magia pode ser utilizada de três formas diferentes:\n'
                 '\n'
                 '  * **Esfera Congelante**: um pequeno globo de matéria '
                 'congelante se forma na mão do conjurador, podendo ser usada '
                 'para congelar todo e qualquer material líquido à base de '
                 'água com que entre em contato. Uma superfície de 30 m² com '
                 'até 20 cm de espessura por nível do conjurador pode ser '
                 'congelada.\n'
                 '\n'
                 '  * **Raio Gélido**: um pequeno e fino raio de energia '
                 'gelada sai dos dedos do conjurador para atingir uma única '
                 'vítima, causando 1d4 pontos de dano +1 de dano por nível. '
                 'Uma JPD reduz esse dano pela metade.\n'
                 '\n'
                 '  * **Globo de Frio**: uma pedra pequena, do tamanho de uma '
                 'pedra de funda, é criada. Ao ser arremessada, se quebra no '
                 'impacto causando 6d6 pontos de dano em todas as criaturas em '
                 'uma distância de até 3 metros do ponto da explosão.  Se o '
                 'globo não for arremessado, ele se quebrará em até 1d4+1 '
                 'rodadas causando o dano normalmente a todos em uma distância '
                 'de até 3 metros.  Uma JPD reduz esse dano pela metade.\n',
  'divine': None,
  'duration': 'especial',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 115}],
  'id': 'esfera-gelida',
  'illusionist': None,
  'jp': 'JPD reduz',
  'name': 'Esfera Gélida',
  'necromancer': None,
  'range': 'especial',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:54.439-03:00',
  'url': 'https://olddragon.com.br/magias/esfera-gelida.json'},
 {'access': 'complete',
  'arcane': 9,
  'description': 'Uma esfera multicolorida com 3 metros de diâmetro encobre o '
                 'conjurador como se fosse uma enorme bolha de proteção. Essa '
                 'esfera é formada por 7 camadas coloridas as quais absorvem '
                 'todos os ataques físicos direcionados ao conjurador.  Cada '
                 'camada possui características individuais e somem ao '
                 'absorver um ataque qualquer. Da mais externa para a mais '
                 'interna:\n'
                 '\n'
                 '  * **Vermelha**: causa 12 pontos de dano ao toque e '
                 'bloqueia magias de 1º círculo;\n'
                 '\n'
                 '  * **Laranja**: causa 24 pontos de dano ao toque e bloqueia '
                 'magias de 1º a 3º círculo;\n'
                 '\n'
                 '  * **Amarela**: causa 48 pontos de dano ao toque e bloqueia '
                 'magias de 1º a 4º círculo;\n'
                 '\n'
                 '  * **Verde**: causa morte instantânea ao toque (JPC evita) '
                 'e bloqueia magias de 1º a 5º círculo;\n'
                 '\n'
                 '  * **Azul**: petrifica ao toque (JPC evita) e bloqueia '
                 'todas as magias de 1º a 6º círculo;\n'
                 '\n'
                 '  * **Anil**: destrói a alma ao toque, causando a morte (sem '
                 'Jogada de Proteção), e bloqueia todas as magias divinas;\n'
                 '\n'
                 '  * **Violeta**: causa insanidade ao toque e bloqueia todas '
                 'as magias arcanas.\n',
  'divine': None,
  'duration': '1 turno/nível',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 115}],
  'id': 'esfera-prismatica',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Esfera Prismática',
  'necromancer': None,
  'range': 'pessoal',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:54.465-03:00',
  'url': 'https://olddragon.com.br/magias/esfera-prismatica.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'O conjurador pode entender e se comunicar na linguagem de um '
                 'tipo de animal escolhido pelo conjurador dentro de um raio '
                 'de 18 metros.  Esta magia não obriga o animal a falar com o '
                 'conjurador, permitindo apenas a capacidade de comunicação '
                 'entre eles.\n',
  'divine': 2,
  'duration': '6 turnos',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 116}],
  'id': 'falar-com-animais',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Falar com Animais',
  'necromancer': None,
  'range': 'pessoal',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:54.491-03:00',
  'url': 'https://olddragon.com.br/magias/falar-com-animais.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'O conjurador passa a entender uma linguagem falada por um '
                 'monstro específico e consegue se comunicar com ele. Esta '
                 'magia não obriga o monstro a falar com o conjurador, '
                 'permitindo apenas a capacidade de comunicação entre eles.\n',
  'divine': 6,
  'duration': '1 turno',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 116}],
  'id': 'falar-com-monstros',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Falar com Monstros',
  'necromancer': None,
  'range': 'pessoal',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:54.516-03:00',
  'url': 'https://olddragon.com.br/magias/falar-com-monstros.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'O conjurador pode fazer perguntas a um cadáver caso este '
                 'ainda possua uma boca para responder.  O morto responderá a '
                 'uma pergunta a cada dois níveis do conjurador, sempre '
                 'baseando-se em seu conhecimento quando vivo e sempre de '
                 'forma lacônica, curta e direta. Um cadáver de alinhamento '
                 'diferente do conjurador pode realizar uma JPS para se negar '
                 'a responder a uma pergunta.\n',
  'divine': 3,
  'duration': '1 turno',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 116}],
  'id': 'falar-com-mortos',
  'illusionist': None,
  'jp': 'especial',
  'name': 'Falar com Mortos',
  'necromancer': None,
  'range': 'pessoal',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:54.542-03:00',
  'url': 'https://olddragon.com.br/magias/falar-com-mortos.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'O conjurador é capaz de se comunicar, falar, ser entendido e '
                 'entender uma planta não mágica.  O conjurador pode fazer '
                 'perguntas, receber respostas e até solicitar favores, os '
                 'quais podem ser atendidos ou não, de acordo com o teste de '
                 'reação da planta. Apenas favores não ofensivos e realizáveis '
                 'serão atendidos.\n',
  'divine': 4,
  'duration': '6 turnos',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 116}],
  'id': 'falar-com-plantas',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Falar com Plantas',
  'necromancer': None,
  'range': 'pessoal',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:54.568-03:00',
  'url': 'https://olddragon.com.br/magias/falar-com-plantas.json'},
 {'access': 'complete',
  'arcane': 2,
  'description': 'O conjurador bem-sucedido em uma jogada de ataque a '
                 'distância acerta um projétil ácido no alvo, causando 1d4 de '
                 'dano ácido regressivo.  Um sucesso em uma JPD reduz o dano à '
                 'metade.\n',
  'divine': None,
  'duration': 'instantânea',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 116}],
  'id': 'flecha-acida',
  'illusionist': None,
  'jp': 'JPD reduz',
  'name': 'Flecha Ácida',
  'necromancer': None,
  'range': '45 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:54.595-03:00',
  'url': 'https://olddragon.com.br/magias/flecha-acida.json'},
 {'access': 'complete',
  'arcane': 3,
  'description': 'Com esta magia, o conjurador consegue criar e disparar de '
                 'suas mãos flechas de fogo (1 para cada 5 níveis do '
                 'conjurador). Cada flecha causa 1d6 pontos de dano pela '
                 'perfuração e outros 2d6 pontos de dano por fogo. Uma jogada '
                 'de ataque à distância é necessária para atingir os alvos com '
                 'essas flechas. O conjurador pode designar um alvo diferente '
                 'para cada flecha.\n',
  'divine': None,
  'duration': 'instantânea',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 116}],
  'id': 'flecha-de-chamas',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Flecha de Chamas',
  'necromancer': None,
  'range': '45 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:54.622-03:00',
  'url': 'https://olddragon.com.br/magias/flecha-de-chamas.json'},
 {'access': 'complete',
  'arcane': 2,
  'description': 'Pela duração da magia, o alvo recebe 1 ponto extra para cada '
                 '5 pontos de Força já possuídos.  Assim, um Guerreiro com '
                 'Força 16 teria seu atributo aumentado para 19, enquanto um '
                 'conjurador com Força 9 teria seu atributo aumentado para 10. '
                 'O cálculo deve ser sempre realizado com o valor original da '
                 'Força do personagem, sem levar em conta outras magias, itens '
                 'mágicos ou demais efeitos que ampliem o valor do atributo '
                 'original.\n',
  'divine': None,
  'duration': '3 turnos',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 116}],
  'id': 'forca-arcana',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Força Arcana',
  'necromancer': None,
  'range': 'toque',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:54.649-03:00',
  'url': 'https://olddragon.com.br/magias/forca-arcana.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'Enquanto concentrado, o conjurador cria a ilusão de uma '
                 'criatura, objeto ou cena, desde que já tenha a visto '
                 'anteriormente. A Ilusão é apenas visual e, apesar de possuir '
                 'movimentos, não emite sons, não possui cheiro e não irradia '
                 'temperatura.\n'
                 '\n'
                 'Se não for usada para criar um falso ataque, a ilusão '
                 'desaparecerá ao ser tocada. Se usada para atacar ou simular '
                 'um ataque, o alvo poderá realizar uma JPS para negar os '
                 'efeitos da ilusão.\n'
                 '\n'
                 'A Ilusão criada possui CA 11, o mesmo BA do conjurador e '
                 'desaparece após a concentração do conjurador ser '
                 'interrompida ou ao ser atingida com sucesso em combate.\n'
                 '\n'
                 'Uma ilusão nunca causa dano real. Ao ser “morto” por uma '
                 'ilusão, o oponente ficará inconsciente por 1d4 rodadas.\n',
  'divine': None,
  'duration': 'especial',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 117}],
  'id': 'ilusao',
  'illusionist': 1,
  'jp': 'JPS nega',
  'name': 'Ilusão',
  'necromancer': None,
  'range': 'especial',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:54.674-03:00',
  'url': 'https://olddragon.com.br/magias/ilusao.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'Enquanto concentrado e pelas próximas 1d3 rodadas após o '
                 'término da concentração, o conjurador cria a ilusão de uma '
                 'criatura, objeto ou cena já vista antes pelo conjurador. A '
                 'ilusão se movimenta, emite sons – embora não consiga falar '
                 'ou simular falas com palavras inteligíveis – e não irradia '
                 'temperatura.\n'
                 '\n'
                 'Se não for usada para criar um falso ataque, a ilusão '
                 'desaparece ao ser tocada. Se usada para atacar ou simular um '
                 'ataque, o alvo pode realizar uma JPS para negar os efeitos '
                 'da ilusão.\n'
                 '\n'
                 'A ilusão criada possui CA 14, o mesmo BA do conjurador e '
                 'desaparece em até 1d3 rodadas após a concentração do '
                 'conjurador ser interrompida ou ao ser atingida com sucesso '
                 'em combate.\n'
                 '\n'
                 'Uma ilusão nunca causa dano real. Ao ser “morto” por uma '
                 'ilusão, o oponente ficará inconsciente por 1d4+2 rodadas.\n',
  'divine': None,
  'duration': 'especial',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 117}],
  'id': 'ilusao-melhorada',
  'illusionist': 2,
  'jp': 'JPS nega',
  'name': 'Ilusão Melhorada',
  'necromancer': None,
  'range': 'especial',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:54.703-03:00',
  'url': 'https://olddragon.com.br/magias/ilusao-melhorada.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'Enquanto estiver ativa e até ser dissipada, o conjurador '
                 'cria a ilusão de uma criatura, objeto ou cena, mesmo se '
                 'nunca vista pelo conjurador. A ilusão movimenta-se, emite '
                 'sons – inclusive os da fala com palavras inteligíveis – '
                 'irradia temperatura, possui odor e é sensível ao toque dos '
                 'oponentes, já que não desaparece quando tocada. Se usada '
                 'para atacar ou simular um ataque, o alvo pode realizar uma '
                 'JPS para negar os efeitos da ilusão.\n'
                 '\n'
                 'A Ilusão criada possui CA 16, o mesmo BA do conjurador e '
                 'pontos de vida ilusórios iguais ao valor de inteligência do '
                 'conjurador. Esta ilusão só desaparece quando dissipada. Ao '
                 'ser atingida com sucesso em combate perde os pontos de vida '
                 'ilusórios até ser morta ilusoriamente.\n'
                 '\n'
                 'Uma ilusão nunca causa dano real, no entanto, em uma Ilusão '
                 'Permanente, há uma chance de 1 em 1d6 de que o alvo atingido '
                 '– que receba 15 ou mais pontos de dano da ilusão – morra de '
                 'verdade por acreditar estar seriamente ferido. Caso o alvo, '
                 'ainda que receba 15 ou mais pontos de dano da ilusão, não '
                 'morra pela chance de 1 em 1d6, cairá no chão inconsciente '
                 'por 1 turno.\n',
  'divine': None,
  'duration': 'permanente',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 117}],
  'id': 'ilusao-permanente',
  'illusionist': 5,
  'jp': 'JPS nega',
  'name': 'Ilusão Permanente',
  'necromancer': None,
  'range': 'especial',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:54.728-03:00',
  'url': 'https://olddragon.com.br/magias/ilusao-permanente.json'},
 {'access': 'limited',
  'arcane': 3,
  'divine': None,
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/arkhi.json',
              'page': 105}],
  'id': 'ima-de-carne',
  'illusionist': None,
  'name': 'Imã de Carne',
  'necromancer': None,
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-06-15T20:42:04.573-03:00',
  'url': 'https://olddragon.com.br/magias/ima-de-carne.json'},
 {'access': 'complete',
  'arcane': 5,
  'description': 'O personagem escolhe até 1d4 monstros não humanoides e vivos '
                 'de tamanho grande ou menor para ficarem imobilizados sem '
                 'conseguirem sair do lugar, como se estivessem paralisados. '
                 'Uma JPC evita este efeito.\n'
                 '\n'
                 'O conjurador também pode escolher um único monstro como alvo '
                 'para imobilizar. Nesse caso, deve realizar uma JPC difícil.\n'
                 '\n'
                 'Mortos-vivos e alvos com 4 DV a mais que o conjurador não '
                 'são afetados por esta magia.\n',
  'divine': 3,
  'duration': '6 turnos +1/nível',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 118}],
  'id': 'imobilizar-monstros',
  'illusionist': None,
  'jp': 'JPC evita',
  'name': 'Imobilizar Monstros',
  'necromancer': None,
  'range': '36 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-06-23T14:09:33.680-03:00',
  'url': 'https://olddragon.com.br/magias/imobilizar-monstros.json'},
 {'access': 'complete',
  'arcane': 3,
  'description': 'O conjurador escolhe até 1d4 pessoas (humano, semi-humano e '
                 'humanoides vivos de tamanho grande ou menor) para ficarem '
                 'imobilizadas sem conseguirem sair do lugar, como se '
                 'estivessem paralisadas. Uma JPC evita este efeito. Também '
                 'pode escolher uma única pessoa como alvo. Nesse caso, deve '
                 'realizar uma JPC difícil. Mortos-vivos e alvos com 4 DV a '
                 'mais que o conjurador não são afetados por esta magia.\n',
  'divine': 2,
  'duration': '1 turno por nível',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 117}],
  'id': 'imobilizar-pessoas',
  'illusionist': None,
  'jp': 'JPC evita',
  'name': 'Imobilizar Pessoas',
  'necromancer': None,
  'range': '36 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-06-23T14:09:33.620-03:00',
  'url': 'https://olddragon.com.br/magias/imobilizar-pessoas.json'},
 {'access': 'complete',
  'arcane': 8,
  'description': 'Com esta magia, o conjurador pode proteger uma criatura '
                 'contra efeitos mágicos para cada 4 níveis que possui. Essa '
                 'proteção confere ajuste nas jogadas de proteção:\n'
                 '\n'
                 '  * **Magias de 1º a 3º círculo**: falha apenas com um 20;\n'
                 '\n'
                 '  * **Magias de 4º a 6º círculo**: muito fácil;\n'
                 '\n'
                 '  * **Magias de 7º e 8º círculo**: fácil.\n',
  'divine': None,
  'duration': '1d4 turnos + 1/nível',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 118}],
  'id': 'imunidade-a-magia',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Imunidade à Magia',
  'necromancer': None,
  'range': 'toque',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:54.809-03:00',
  'url': 'https://olddragon.com.br/magias/imunidade-a-magia.json'},
 {'access': 'complete',
  'arcane': 3,
  'description': 'O alvo desta magia adquire infravisão de 18 metros, '
                 'exatamente como um elfo ou anão.\n',
  'divine': None,
  'duration': '24 horas',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 118}],
  'id': 'infravisao',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Infravisão',
  'necromancer': None,
  'range': 'toque',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:54.835-03:00',
  'url': 'https://olddragon.com.br/magias/infravisao.json'},
 {'access': 'complete',
  'arcane': 2,
  'description': 'O alvo desta magia, seja este uma pessoa ou objeto, se torna '
                 'totalmente invisível. Uma criatura invisível não pode ser '
                 'atacada, a menos que sua localização aproximada seja '
                 'conhecida.\n'
                 '\n'
                 'A magia é dissipada se o alvo invisível realizar qualquer '
                 'tipo de ataque ou lançar uma magia.\n',
  'divine': None,
  'duration': 'permanente',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 118}],
  'id': 'invisibilidade',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Invisibilidade',
  'necromancer': None,
  'range': 'toque',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:54.861-03:00',
  'url': 'https://olddragon.com.br/magias/invisibilidade.json'},
 {'access': 'complete',
  'arcane': 3,
  'description': 'Esta magia tem o mesmo efeito de uma magia Invisibilidade, '
                 'mas afetando todas as criaturas e objetos em uma área de 3 '
                 'metros de diâmetro de um alvo preferencial. Se uma criatura '
                 'ou objeto abandonar a área, deixarão de estar invisíveis e, '
                 'mesmo retornando a área, não recuperarão a invisibilidade.\n',
  'divine': None,
  'duration': 'permanente',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 118}],
  'id': 'invisibilidade-3-metros',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Invisibilidade 3 metros',
  'necromancer': None,
  'range': '36 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:54.887-03:00',
  'url': 'https://olddragon.com.br/magias/invisibilidade-3-metros.json'},
 {'access': 'complete',
  'arcane': 3,
  'description': 'Com esta magia, o conjurador é capaz de invocar 2d4 '
                 'criaturas presentes nas redondezas para lhe auxiliarem. '
                 'Essas criaturas o servirão até o fim da duração da magia ou '
                 'até a derrota de todas as criaturas. As criaturas invocadas '
                 'levam 1d4 turnos para aparecer e permanecerão por mais 6 '
                 'turnos. A quantidade de DV das criaturas invocadas é igual a '
                 'metade do nível do conjurador, ou seja, um conjurador de 5º '
                 'nível invoca 2d4 criaturas de no máximo 2 DV cada.\n',
  'divine': None,
  'duration': '6 turnos',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 118}],
  'id': 'invocar-criaturas',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Invocar criaturas',
  'necromancer': None,
  'range': 'especial',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:54.914-03:00',
  'url': 'https://olddragon.com.br/magias/invocar-criaturas.json'},
 {'access': 'complete',
  'arcane': 5,
  'description': 'Com esta magia, o conjurador consegue transformar 30 m² de '
                 'pedra em lama com 3 metros de profundidade, levando 3d6 dias '
                 'para endurecer.  Criaturas que tentam atravessar a lama têm '
                 'seu movimento reduzido à metade do normal.  Criaturas de '
                 'pedra que sejam alvos desta magia, como um Golem de Pedra, '
                 'podem realizar uma JP para negar os efeitos da magia ou '
                 'serão destruídas.\n'
                 '\n'
                 '[Lama em Pedra] é a versão reversa que permite endurecer até '
                 '3 m² de lama em pedra permanentemente.\n',
  'divine': None,
  'duration': 'especial',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 125}],
  'id': 'lama-em-pedra',
  'illusionist': None,
  'jp': 'especial',
  'name': 'Lama em Pedra',
  'necromancer': None,
  'range': 'toque',
  'reverse': True,
  'reverse_spell': {'id': 'pedra-em-lama',
                    'name': 'Pedra em Lama',
                    'reverse_spell_url': 'https://olddragon.com.br/magias/pedra-em-lama.json'},
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:55.964-03:00',
  'url': 'https://olddragon.com.br/magias/lama-em-pedra.json'},
 {'access': 'complete',
  'arcane': 3,
  'description': 'Todos dentro de uma área de 6 x 6 metros que não passarem em '
                 'uma JPC ficam lentos. Os deslocamentos ficam reduzidos pela '
                 'metade.  Os ataques deferidos pelo alvo são difíceis e os '
                 'contra o alvo, fáceis.\n'
                 '\n'
                 '[Velocidade] é a versão reversa na qual acelera extremamente '
                 'o metabolismo de até 1 criatura tocada para cada 3 níveis do '
                 'conjurador, concedendo ao alvo uma movimentação acima do '
                 'normal. Os deslocamentos ficam multiplicados por dois. Os '
                 'ataques deferidos pelo alvo são fáceis e os contra o alvo, '
                 'difíceis. Além disso, o alvo recebe um ataque extra por '
                 'rodada. A aceleração é prejudicial ao organismo do alvo, '
                 'envelhecendo-o 10% da idade atual.\n',
  'divine': None,
  'duration': '3 turnos',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 119}],
  'id': 'lentidao',
  'illusionist': None,
  'jp': 'JPC evita',
  'name': 'Lentidão',
  'necromancer': None,
  'range': '72 metros',
  'reverse': True,
  'reverse_spell': {'id': 'velocidade',
                    'name': 'Velocidade',
                    'reverse_spell_url': 'https://olddragon.com.br/magias/velocidade.json'},
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:54.940-03:00',
  'url': 'https://olddragon.com.br/magias/lentidao.json'},
 {'access': 'complete',
  'arcane': 1,
  'description': 'Esta magia permite ao conjurador decifrar direções, '
                 'instruções e fórmulas em idiomas desconhecidos. É '
                 'particularmente útil para mapas de tesouro, muito embora não '
                 'decifre nenhum enigma ou código, apenas permitindo ao '
                 'conjurador compreender o que está escrito.\n',
  'divine': None,
  'duration': '2 turnos',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 119}],
  'id': 'ler-idiomas',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Ler Idiomas',
  'necromancer': None,
  'range': 'pessoal',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:54.999-03:00',
  'url': 'https://olddragon.com.br/magias/ler-idiomas.json'},
 {'access': 'complete',
  'arcane': 2,
  'description': 'Com esta magia, o conjurador é capaz de se mover levitando '
                 'em uma linha reta vertical. Necessita apenas de uma palavra '
                 'para ser ativada, podendo ser evocada em qualquer situação, '
                 'até mesmo durante uma queda.\n',
  'divine': None,
  'duration': '6 turnos + 1/nível',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 119}],
  'id': 'levitacao',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Levitação',
  'necromancer': None,
  'range': 'pessoal',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:55.030-03:00',
  'url': 'https://olddragon.com.br/magias/levitacao.json'},
 {'access': 'complete',
  'arcane': 2,
  'description': 'Esta magia dá ao conjurador a direção correta até um objeto '
                 'do tipo especificado na descrição.\n'
                 '\n'
                 'O objeto não pode ser algo nunca visto pelo conjurador, '
                 'apesar de que a magia pode detectar um objeto em uma classe '
                 'geral de itens conhecidos do conjurador (cadeiras, ouro '
                 'etc.), mas com uma precisão ainda menor.\n'
                 '\n'
                 'Esta magia não permite a localização de criaturas vivas ou '
                 'animadas.\n',
  'divine': None,
  'duration': '2 turnos',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 119}],
  'id': 'localizar-objetos',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Localizar Objetos',
  'necromancer': None,
  'range': '18 metros + 2m/nível',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:55.056-03:00',
  'url': 'https://olddragon.com.br/magias/localizar-objetos.json'},
 {'access': 'complete',
  'arcane': 1,
  'description': 'O objeto alvo tocado produz luz tão brilhante quanto uma '
                 'tocha, iluminando uma área com raio de 6 metros.\n'
                 '\n'
                 'Se conjurada nos olhos de um alvo a até 3m + 1,5m/nível do '
                 'conjurador, a vítima que não passar em uma JPS fica cega até '
                 'o final da duração da magia. Neste caso, a luz mágica se '
                 'apaga e não causa nenhum outro efeito.\n'
                 '\n'
                 '[Escuridão] é a versão reversa que permite interromper '
                 'qualquer fonte de luz, apagando tochas, velas, lâmpadas ou '
                 'até mesmo dissipando uma magia Luz lançada anteriormente e '
                 'criando uma área de 4,5 metros de raio de escuridão mágica, '
                 'deixando todos dentro da área cegos (mesmo se possuírem '
                 'Infravisão).\n'
                 '\n'
                 'Se conjurada nos olhos de um alvo tocado pelo conjurador, a '
                 'vítima que não passar em uma JPS fica cega até o final da '
                 'duração da magia.  Neste caso, a escuridão mágica some e não '
                 'causa nenhum outro efeito.\n',
  'divine': 1,
  'duration': '12 turnos',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 119}],
  'id': 'luz',
  'illusionist': None,
  'jp': 'JPS nega',
  'name': 'Luz',
  'necromancer': None,
  'range': 'especial',
  'reverse': True,
  'reverse_spell': {'id': 'escuridao',
                    'name': 'Escuridão',
                    'reverse_spell_url': 'https://olddragon.com.br/magias/escuridao.json'},
  'type': 'Spell',
  'updated_at': '2023-06-23T14:09:33.741-03:00',
  'url': 'https://olddragon.com.br/magias/luz.json'},
 {'access': 'complete',
  'arcane': 2,
  'description': 'Esta magia tem o mesmo efeito de uma magia Luz, mas com '
                 'duração contínua (enquanto desejado pelo conjurador). Se '
                 'conjurada nos olhos de um alvo a até 3m + 1,5m/nível do '
                 'conjurador, a vítima que não passar em uma JPS fica cega até '
                 'o final da duração da magia. Neste caso, a luz mágica se '
                 'apaga e não causa nenhum outro efeito.\n'
                 '\n'
                 '[Escuridão Contínua] é a versão reversa que cria uma área de '
                 'escuridão mágica permanente numa área de 4,5 metros de raio, '
                 'deixando todos dentro da área cegos, inclusive criaturas com '
                 'Infravisão.  Qualquer fonte de luz trazida para dentro da '
                 'área de escuridão será apagada. Uma Escuridão Contínua pode '
                 'ser usada para dissipar os efeitos de uma magia de Luz '
                 'Contínua.\n',
  'divine': None,
  'duration': 'permanente',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 120}],
  'id': 'luz-continua',
  'illusionist': None,
  'jp': 'JPS nega',
  'name': 'Luz Contínua',
  'necromancer': None,
  'range': '36 metros',
  'reverse': True,
  'reverse_spell': {'id': 'escuridao-continua',
                    'name': 'Escuridão Contínua',
                    'reverse_spell_url': 'https://olddragon.com.br/magias/escuridao-continua.json'},
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:55.140-03:00',
  'url': 'https://olddragon.com.br/magias/luz-continua.json'},
 {'access': 'complete',
  'arcane': 9,
  'description': 'O conjurador consegue projetar a sua forma astral para '
                 'outros locais, ficando visível apenas a outras criaturas que '
                 'também estejam sob forma astral. Enquanto estiver nesta '
                 'forma, o conjurador pode lançar magias e se deslocar para '
                 'onde desejar a uma velocidade de 150 km/h, mas, caso '
                 'ultrapasse o limite de 1km de distância de seu corpo físico, '
                 'não conseguirá mais retornar ao seu corpo, ficando preso à '
                 'forma astral para sempre.\n'
                 '\n'
                 'Esta magia funciona enquanto o conjurador desejar ou até ser '
                 'dissipada.\n',
  'divine': None,
  'duration': 'permanente',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 120}],
  'id': 'magia-astral',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Magia Astral',
  'necromancer': None,
  'range': 'pessoal',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:55.204-03:00',
  'url': 'https://olddragon.com.br/magias/magia-astral.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'Um raio de energia negativa sai das mãos do conjurador, '
                 'matando 2d6 criaturas com 4 dados de vida ou menos as quais '
                 'estejam dentro do alcance da magia (a magia afeta por ordem '
                 'de proximidade em relação ao conjurador). Uma JPC evita os '
                 'efeitos desta magia. Esta magia faz o Necromante perder 90% '
                 'dos seus pontos de vida atuais. Um Necromante com 36 pontos '
                 'de vida seria reduzido imediatamente a 3 pontos de vida.\n',
  'divine': None,
  'duration': 'instantânea',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 121}],
  'id': 'magia-da-morte',
  'illusionist': None,
  'jp': 'JPC evita',
  'name': 'Magia da Morte',
  'necromancer': 5,
  'range': '3 metros + 1/nível',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:55.232-03:00',
  'url': 'https://olddragon.com.br/magias/magia-da-morte.json'},
 {'access': 'complete',
  'arcane': 1,
  'description': 'Ao formar um leque com as mãos, o conjurador emite um raio '
                 'triangular de fogo afetando todos na área de alcance da '
                 'magia. Cada criatura atingida recebe 1d3 pontos de dano +2 '
                 'pontos de dano adicionais por nível do conjurador até um '
                 'máximo de +20. Uma JPD reduz o dano pela metade.\n',
  'divine': None,
  'duration': 'instantânea',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 122}],
  'id': 'maos-flamejantes',
  'illusionist': None,
  'jp': 'JPD reduz',
  'name': 'Mãos Flamejantes',
  'necromancer': None,
  'range': '3 metros + 1/nível',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:55.258-03:00',
  'url': 'https://olddragon.com.br/magias/maos-flamejantes.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'Esta magia cria um martelo de energia o qual pode ser usado '
                 'pelo conjurador para atacar qualquer alvo dentro de seu '
                 'alcance. O martelo possui um bônus de ataque +1 para cada 5 '
                 'níveis do conjurador, e causa 1d4 pontos de dano além de '
                 'receber um bônus no dano de +1 por nível do conjurador.  Uma '
                 'JPC do conjurador deve ser realizada pelo conjurador sempre '
                 'que este for atacado. Uma falha significa que o martelo foi '
                 'dissipado.\n',
  'divine': 2,
  'duration': '1d6 turnos + 1/nível',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 120}],
  'id': 'martelo-espiritual',
  'illusionist': None,
  'jp': 'especial',
  'name': 'Martelo Espiritual',
  'necromancer': None,
  'range': '3m + 1,5m/nível',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:55.286-03:00',
  'url': 'https://olddragon.com.br/magias/martelo-espiritual.json'},
 {'access': 'complete',
  'arcane': 4,
  'description': 'Esta magia cria um sentimento aterrorizante nas criaturas '
                 'dentro de seu alcance. Uma falha na JPS faz as criaturas '
                 'afetadas saírem correndo por toda a duração da magia. Há 1-4 '
                 'chances em 1d6 de as criaturas soltarem qualquer objeto que '
                 'estejam segurando.\n',
  'divine': None,
  'duration': '1 rodada/nível',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 120}],
  'id': 'medo',
  'illusionist': None,
  'jp': 'JPS nega',
  'name': 'Medo',
  'necromancer': None,
  'range': '18 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:55.311-03:00',
  'url': 'https://olddragon.com.br/magias/medo.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'O conjurador pode escolher 1 alvo a cada 3 níveis para '
                 'sussurrar uma mensagem e receber uma resposta sem que as '
                 'outras criaturas fora do efeito percebam. Para funcionar, '
                 'todos os alvos da magia precisam compreender o idioma '
                 'falado.  Além disso, não pode haver nenhum obstáculo físico '
                 'ou mágico atrapalhando a comunicação.\n',
  'divine': 2,
  'duration': '1 turno + 1/nível',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 121}],
  'id': 'mensagem',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Mensagem',
  'necromancer': None,
  'range': '18 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:55.336-03:00',
  'url': 'https://olddragon.com.br/magias/mensagem.json'},
 {'access': 'complete',
  'arcane': 5,
  'description': 'O conjurador consegue modificar fisicamente a forma de uma '
                 'criatura (com no máximo o dobro dos DV do conjurador) para '
                 'que esta se pareça com outro tipo de criatura, mas não é '
                 'possível clonar um indivíduo específico. Uma JPC consegue '
                 'evitar esse efeito caso o alvo deseje resistir. O alvo '
                 'metamorfoseado mantém o mesmo número de DV e PV, mas adquire '
                 'as habilidades especiais, ataques e capacidades físicas do '
                 'novo tipo de criatura, assim como o comportamento, '
                 'alinhamento e inteligência. Um anão metamorfoseado em uma '
                 'gárgula não só se parecerá como uma, mas agirá e pensará '
                 'como uma gárgula, podendo inclusive voar. Todas as criaturas '
                 'metamorfoseadas retornam a sua forma original quando '
                 'mortas.\n',
  'divine': None,
  'duration': 'permanente',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 121}],
  'id': 'metamorfose',
  'illusionist': None,
  'jp': 'JPC evita',
  'name': 'Metamorfose',
  'necromancer': None,
  'range': '3m + 1,5m/nível',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:55.362-03:00',
  'url': 'https://olddragon.com.br/magias/metamorfose.json'},
 {'access': 'complete',
  'arcane': 4,
  'description': 'O conjurador consegue modificar fisicamente sua própria '
                 'forma para um tipo de criatura (com no máximo o dobro dos DV '
                 'do conjurador) para se parecer com outro tipo de criatura, '
                 'mas nunca para clonar um indivíduo específico.\n'
                 '\n'
                 'O conjurador mantém o mesmo número de DV, PV, JP. Adquire '
                 'ainda os ataques físicos e movimentos da criatura na qual se '
                 'metamorfoseou, mas não é capaz de usar suas habilidades '
                 'especiais não físicas, como imunidades, resistências, '
                 'baforadas etc. Enquanto está metamorfoseado, o conjurador '
                 'perde a capacidade de conjurar magias. Se morrer enquanto '
                 'metamorfoseado, retornará a sua forma original.\n',
  'divine': None,
  'duration': '6 turnos + 1/nível',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 121}],
  'id': 'metamorfosear-se',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Metamorfosear-se',
  'necromancer': None,
  'range': 'pessoal',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:55.388-03:00',
  'url': 'https://olddragon.com.br/magias/metamorfosear-se.json'},
 {'access': 'complete',
  'arcane': 4,
  'description': 'O conjurador se torna capaz de conjurar e arremessar 1 '
                 'esfera flamejante de fogo por nível, causando 2d4 pontos de '
                 'dano de fogo.  O conjurador deve ser bem-sucedido em uma '
                 'jogada de ataque à distância para atingir um alvo, sendo '
                 'capaz de arremessar um único meteoro por rodada.\n'
                 '\n'
                 'Quando conjurados, os meteoros ficam disponíveis para serem '
                 'arremessados por até 24 horas, até todos serem arremessados '
                 'ou até a magia ser dissipada. O conjurador não precisa se '
                 'concentrar para manter os meteoros disponíveis durante este '
                 'tempo.\n',
  'divine': None,
  'duration': 'especial',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 121}],
  'id': 'meteoros-instantaneos',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Meteoros Instantâneos',
  'necromancer': None,
  'range': '36 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:55.418-03:00',
  'url': 'https://olddragon.com.br/magias/meteoros-instantaneos.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'O conjurador cria uma ilusão a qual esconde, dentro da área '
                 'de alcance da magia, o verdadeiro terreno. Todos os sentidos '
                 'são afetados, mas os possíveis efeitos causados pelo terreno '
                 'verdadeiro não – um fosso de lava ainda é um fosso de lava '
                 'capaz de matar queimado qualquer desavisado, mesmo '
                 'aparentando ser um campo florido.\n'
                 '\n'
                 'Se a alteração do terreno criada pela ilusão for sutil, uma '
                 'JPS é permitida, no entanto, se a mudança causar suspeita, '
                 'uma JPS fácil é permitida para negar a ilusão. Apenas alvos '
                 'bem-sucedidos ficam livres dos efeitos, e a ilusão persiste '
                 'até o fim de sua duração.\n'
                 '\n'
                 'Caso uma criatura seja vítima da ilusão (caindo em um '
                 'precipício aparentando ser uma floresta, por exemplo), todos '
                 'os observadores recebem automaticamente o direito a uma JPS '
                 'muito fácil.\n',
  'divine': None,
  'duration': 'especial',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 121}],
  'id': 'miragem',
  'illusionist': 3,
  'jp': 'especial',
  'name': 'Miragem',
  'necromancer': None,
  'range': 'especial',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:55.446-03:00',
  'url': 'https://olddragon.com.br/magias/miragem.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'Esta magia obriga um alvo a realizar uma missão à escolha do '
                 'conjurador. Uma JPS nega esse efeito no alvo. Se o alvo se '
                 'desviar da missão ou se negar a cumpri-la, será acometido de '
                 'uma maldição que drena 1 ponto de Força por dia até que '
                 'volte a se empenhar na conclusão da missão. Se chegar à '
                 'Força 0, o alvo morrerá imediatamente.\n'
                 '\n'
                 '[Remover Missão] é a versão reversa que permite ao '
                 'conjurador remover qualquer efeito de uma Missão conjurada '
                 'em um alvo. Para surtir efeito, o conjurador precisa ter ao '
                 'menos 2 níveis a mais que o conjurador da magia Missão '
                 'original.\n',
  'divine': 5,
  'duration': 'especial',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 122}],
  'id': 'missao',
  'illusionist': None,
  'jp': 'JPS nega',
  'name': 'Missão',
  'necromancer': None,
  'range': 'toque',
  'reverse': True,
  'reverse_spell': {'id': 'remover-missao',
                    'name': 'Remover Missão',
                    'reverse_spell_url': 'https://olddragon.com.br/magias/remover-missao.json'},
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:55.473-03:00',
  'url': 'https://olddragon.com.br/magias/missao.json'},
 {'access': 'complete',
  'arcane': 1,
  'description': 'Um míssil mágico voa para onde o conjurador direcionar, '
                 'acertando automaticamente os alvos.  Para atingir uma '
                 'criatura, é preciso que ela esteja na linha de visão do '
                 'conjurador, o qual pode lançar 1 Míssil Mágico a cada 3 '
                 'níveis, causando um dano de 1d4 pontos +1 por nível, até um '
                 'máximo de +5. Assim, o conjurador conjura 2 mísseis no 4º '
                 'nível, 3 mísseis no 7º, 4 mísseis no 10º, e 5 mísseis no '
                 '13º. Esses mísseis adicionais podem ser direcionados para '
                 'alvos distintos desde que a distância entre os alvos não '
                 'seja superior a 18 metros.\n',
  'divine': None,
  'duration': 'instantânea',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 122}],
  'id': 'misseis-magicos',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Mísseis Mágicos',
  'necromancer': None,
  'range': '45 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:55.530-03:00',
  'url': 'https://olddragon.com.br/magias/misseis-magicos.json'},
 {'access': 'complete',
  'arcane': 4,
  'description': 'O conjurador cria uma muralha de energia invisível com até '
                 '90 centímetros de espessura, 15 metros de altura e 15 metros '
                 'de comprimento ao seu redor. Nenhum efeito mágico de um '
                 'conjurador de nível inferior é capaz de ultrapassar a '
                 'muralha, mas pessoas e projéteis sim.\n',
  'divine': None,
  'duration': '6 turnos + 1/nível',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 123}],
  'id': 'muralha-de-energia',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Muralha de Energia',
  'necromancer': None,
  'range': '18 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:55.556-03:00',
  'url': 'https://olddragon.com.br/magias/muralha-de-energia.json'},
 {'access': 'complete',
  'arcane': 5,
  'description': 'O conjurador cria uma muralha de ferro resistente com até 90 '
                 'centímetros de espessura, 15 metros de altura e 15 metros de '
                 'comprimento.  Nada que não seja normalmente capaz de '
                 'ultrapassar ferro nestas condições consegue ultrapassar a '
                 'muralha.\n',
  'divine': None,
  'duration': '6 turnos + 1/nível',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 123}],
  'id': 'muralha-de-ferro',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Muralha de Ferro',
  'necromancer': None,
  'range': '18 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:55.582-03:00',
  'url': 'https://olddragon.com.br/magias/muralha-de-ferro.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'Esta magia anula quaisquer efeitos de venenos em ação dentro '
                 'do corpo de um alvo vivo, mas não recupera pontos de vida '
                 'perdidos devido ao veneno e nem revive uma vítima morta '
                 'devido aos efeitos de um veneno.\n',
  'divine': 4,
  'duration': 'instantânea',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 123}],
  'id': 'neutralizar-veneno',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Neutralizar Veneno',
  'necromancer': None,
  'range': 'toque',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:55.608-03:00',
  'url': 'https://olddragon.com.br/magias/neutralizar-veneno.json'},
 {'access': 'complete',
  'arcane': 5,
  'description': 'Vapores sulfurosos e altamente venenosos formam uma pesada e '
                 'densa nuvem com 9 metros de diâmetro em todas as direções, '
                 'movendo-se a favor do vento por 6 metros por rodada, ou, '
                 'caso não haja vento, afastando-se do conjurador em linha '
                 'reta. Qualquer criatura a ter contato com a névoa sofrerá 1 '
                 'ponto de dano por rodada, e criaturas com menos de 5 DV '
                 'devem realizar também uma JPC para evitar a morte.\n'
                 '\n'
                 'A névoa, por ser mais pesada do que o ar, desce escadas, '
                 'fossos e alçapões, mas não é capaz de subir estes mesmos '
                 'obstáculos.\n',
  'divine': None,
  'duration': '1 rodada/nível',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 123}],
  'id': 'nevoa-mortal',
  'illusionist': None,
  'jp': 'especial',
  'name': 'Névoa Mortal',
  'necromancer': None,
  'range': '12 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:55.634-03:00',
  'url': 'https://olddragon.com.br/magias/nevoa-mortal.json'},
 {'access': 'complete',
  'arcane': 4,
  'description': 'O conjurador cria um olho flutuante e invisível com 2,5cm de '
                 'diâmetro o qual envia ao conjurador informações visuais.\n'
                 '\n'
                 'O Olho Arcano pode ser criado em qualquer lugar dentro da '
                 'linha de visão do conjurador, mas pode percorrer qualquer '
                 'distância sem limitação, movendo-se a 10 metros por rodada. '
                 'O Olho pode viajar em qualquer direção, mas não conseguirá '
                 'atravessar barreiras sólidas e nem viajar através dos '
                 'planos.\n'
                 '\n'
                 'O Olho só se move enquanto o conjurador mantiver a '
                 'concentração na magia. Se o conjurador for atacado, é '
                 'preciso fazer uma JPC para que o Olho não fique parado por '
                 'um turno.\n',
  'divine': None,
  'duration': '6 turnos',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 123}],
  'id': 'olho-arcano',
  'illusionist': None,
  'jp': 'especial',
  'name': 'Olho Arcano',
  'necromancer': None,
  'range': '72 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:55.659-03:00',
  'url': 'https://olddragon.com.br/magias/olho-arcano.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'Todos os aliados em um raio de até 9 metros do conjurador '
                 'passam a realizar suas Jogadas de Proteção com ajuste fácil, '
                 'enquanto seus inimigos declarados passam a fazer suas '
                 'Jogadas de Proteção com ajuste difícil.\n'
                 '\n'
                 'Esse bônus é ampliado quando o conjurador possui 10 níveis, '
                 'passando a ser muito fácil/muito difícil.\n'
                 '\n'
                 'Os efeitos desta magia dura 1 turno para cada 5 níveis do '
                 'conjurador.\n',
  'divine': 3,
  'duration': 'especial',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 124}],
  'id': 'oracao',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Oração',
  'necromancer': None,
  'range': 'pessoal',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:55.687-03:00',
  'url': 'https://olddragon.com.br/magias/oracao.json'},
 {'access': 'complete',
  'arcane': 7,
  'description': 'O conjurador é capaz de atordoar um alvo proferindo uma '
                 'única palavra, sem direito a uma Jogada de Proteção desde '
                 'que o alvo seja capaz de ouvir a palavra dita pelo '
                 'conjurador. O alvo não precisa compreendê-la. Se o alvo '
                 'estiver com:\n'
                 '\n'
                 '  * **6 DV ou menos**: fica atordoado por até 2d6+3 '
                 'rodadas.\n'
                 '\n'
                 '  * **7 a 9 DV**: fica atordoado por 1d6+1 rodadas.\n'
                 '\n'
                 '  * **10 DV ou mais**: não sofrerá os efeitos desta magia.\n'
                 '\n'
                 'Um personagem atordoado por esta magia mantém seus pontos de '
                 'vida, mas não consegue realizar nenhuma atividade física '
                 'como se mover, resistir, atacar ou conjurar magias, podendo '
                 'falar apenas hesitantemente um máximo de 1d4+2 palavras por '
                 'rodada.\n',
  'divine': None,
  'duration': 'especial',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 124}],
  'id': 'palavra-do-poder-atordoar',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Palavra do Poder: Atordoar',
  'necromancer': None,
  'range': '5 metros/nível',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:55.714-03:00',
  'url': 'https://olddragon.com.br/magias/palavra-do-poder-atordoar.json'},
 {'access': 'complete',
  'arcane': 9,
  'description': 'O conjurador é capaz de matar um alvo proferindo uma única '
                 'palavra, sem direito a uma Jogada de Proteção desde que o '
                 'alvo seja capaz de ouvir a palavra dita pelo conjurador. O '
                 'alvo não precisa compreendê-la. Se o alvo estiver com:\n'
                 '\n'
                 '  * **5O PV ou menos**: morre imediatamente.\n'
                 '\n'
                 '  * **51 PV ou mais**: não sofrerá os efeitos desta magia.\n',
  'divine': None,
  'duration': 'instantânea',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 124}],
  'id': 'palavra-do-poder-matar',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Palavra do Poder: Matar',
  'necromancer': None,
  'range': '3 metros/nível',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:55.740-03:00',
  'url': 'https://olddragon.com.br/magias/palavra-do-poder-matar.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'O conjurador é capaz de afetar um alvo proferindo apenas uma '
                 'única palavra, sem direito a uma Jogada de Proteção, desde '
                 'que o alvo seja capaz de ouvir a palavra dita pelo '
                 'conjurador. O alvo não precisa compreendê-la. Se o alvo '
                 'tiver:\n'
                 '\n'
                 '  * **4 DV ou menos**: morre imediatamente.\n'
                 '\n'
                 '  * **5 DV a 8 DV**: fica atordoado por até 2d6+3 rodadas.\n'
                 '\n'
                 '  * **9 DV a 12 DV**: fica atordoado por 1d6+1 rodadas.\n'
                 '\n'
                 '  * **13 DV ou mais**: não sofrerá os efeitos desta magia.\n'
                 '\n'
                 'Um personagem atordoado por esta magia mantém seus pontos de '
                 'vida, mas não consegue realizar nenhuma atividade física '
                 'como se mover, resistir, atacar ou conjurar magias, podendo '
                 'falar apenas hesitantemente um máximo de 1d4+2 palavras por '
                 'rodada.\n',
  'divine': 7,
  'duration': 'especial',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 124}],
  'id': 'palavra-sagrada',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Palavra Sagrada',
  'necromancer': None,
  'range': '18 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:55.767-03:00',
  'url': 'https://olddragon.com.br/magias/palavra-sagrada.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'Se diante de uma massa de água, o conjurador consegue '
                 'separá-la, abrindo um caminho seguro e seco para passagem. '
                 'Essa passagem se fechará tão logo termine a duração da magia '
                 'ou quando o conjurador assim desejar.\n',
  'divine': 6,
  'duration': '1 turno + 1/nível',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 124}],
  'id': 'partir-agua',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Partir Água',
  'necromancer': None,
  'range': '18 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:55.791-03:00',
  'url': 'https://olddragon.com.br/magias/partir-agua.json'},
 {'access': 'complete',
  'arcane': 7,
  'description': 'Esta magia cria uma passagem secreta e invisível em uma '
                 'parede, muro ou outra superfície com até 50 centímetros de '
                 'largura.\n'
                 '\n'
                 'O conjurador poderá conjurar essa magia apenas uma vez por '
                 'nível, ou seja, ao utilizá-la uma vez só poderá fazer uso '
                 'dela novamente após subir um nível na sua classe de '
                 'conjurador. A passagem criada fica ativa até o conjurador '
                 'usar esta magia novamente.\n',
  'divine': None,
  'duration': 'especial',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 124}],
  'id': 'passagem-secreta',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Passagem Secreta',
  'necromancer': None,
  'range': 'toque',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:55.817-03:00',
  'url': 'https://olddragon.com.br/magias/passagem-secreta.json'},
 {'access': 'complete',
  'arcane': 1,
  'description': 'Esta magia permite ao alvo andar sobre as paredes ou tetos '
                 'como se fossem um piso horizontal.  Nestas condições, um '
                 'teste de escalar não é necessário e o alvo pode se deslocar '
                 'com o seu movimento base sem nenhuma redução, porém os '
                 'efeitos da gravidade ainda são sentidos, ou seja, objetos '
                 'soltos nos bolsos ou na roupa do alvo podem se desprender e '
                 'cair normalmente.\n',
  'divine': None,
  'duration': '1 turno',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 125}],
  'id': 'patas-de-aranha',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Patas de Aranha',
  'necromancer': None,
  'range': 'toque',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:55.844-03:00',
  'url': 'https://olddragon.com.br/magias/patas-de-aranha.json'},
 {'access': 'complete',
  'arcane': 6,
  'description': 'Com esta magia, o conjurador consegue transformar pedaços de '
                 'pedra em carne. Criaturas petrificadas podem ser '
                 'restauradas, bem como seus equipamentos, com esta magia. '
                 'Criaturas de pedra alvos desta magia, como um Golem de '
                 'Pedra, podem realizar uma JP para negar os efeitos da magia '
                 'ou serão destruídas.\n'
                 '\n'
                 '[Carne em Pedra] é a versão reversa que permite petrificar '
                 'um alvo assim como todo o seu equipamento. Uma JPS '
                 'bem-sucedida pode negar os efeitos desta magia.\n',
  'divine': None,
  'duration': 'permanente',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 125}],
  'id': 'pedra-em-carne',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Pedra em Carne',
  'necromancer': None,
  'range': 'toque',
  'reverse': True,
  'reverse_spell': {'id': 'carne-em-pedra',
                    'name': 'Carne em Pedra',
                    'reverse_spell_url': 'https://olddragon.com.br/magias/carne-em-pedra.json'},
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:55.869-03:00',
  'url': 'https://olddragon.com.br/magias/pedra-em-carne.json'},
 {'access': 'complete',
  'arcane': 5,
  'description': 'Com esta magia, o conjurador consegue transformar 30 m² de '
                 'pedra em lama com 3 metros de profundidade, levando 3d6 dias '
                 'para endurecer.  Criaturas que tentam atravessar a lama têm '
                 'seu movimento reduzido à metade do normal.  Criaturas de '
                 'pedra que sejam alvos desta magia, como um Golem de Pedra, '
                 'podem realizar uma JP para negar os efeitos da magia ou '
                 'serão destruídas.\n'
                 '\n'
                 '[Lama em Pedra] é a versão reversa que permite endurecer até '
                 '3 m² de lama em pedra permanentemente.\n',
  'divine': None,
  'duration': 'especial',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 125}],
  'id': 'pedra-em-lama',
  'illusionist': None,
  'jp': 'especial',
  'name': 'Pedra em Lama',
  'necromancer': None,
  'range': 'toque',
  'reverse': True,
  'reverse_spell': {'id': 'lama-em-pedra',
                    'name': 'Lama em Pedra',
                    'reverse_spell_url': 'https://olddragon.com.br/magias/lama-em-pedra.json'},
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:55.925-03:00',
  'url': 'https://olddragon.com.br/magias/pedra-em-lama.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'Esta magia remove o fardo causado por pecados cometidos pelo '
                 'alvo, mesmo se cometidos sem consciência ou '
                 'involuntariamente.\n'
                 '\n'
                 'Ele deve estar efetivamente arrependido e buscando '
                 'penitência pelos seus atos, e deve aceitar a conjuração da '
                 'magia sobre ele.\n'
                 '\n'
                 'Esta magia pode restaurar os poderes de Paladinos caídos ou '
                 'Clérigos que tenham perdido a conexão com a sua fé.\n',
  'divine': 5,
  'duration': 'instantânea',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 126}],
  'id': 'penitencia',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Penitência',
  'necromancer': None,
  'range': 'toque',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:55.990-03:00',
  'url': 'https://olddragon.com.br/magias/penitencia.json'},
 {'access': 'complete',
  'arcane': 2,
  'description': 'Concentrando-se por 1 minuto, o conjurador pode detectar e '
                 'entender os pensamentos de outras criaturas dentro de um '
                 'raio máximo de 18 metros, ainda que não compartilhem o mesmo '
                 'idioma. A magia não pode penetrar mais de 60 centímetros de '
                 'pedra e é bloqueada até mesmo pela mais fina folha de '
                 'chumbo.\n'
                 '\n'
                 'Se mais de duas criaturas estiverem na área de efeito, o '
                 'conjurador precisa concentrar-se um turno adicional para '
                 'selecionar exatamente os pensamentos que deseja perceber.\n',
  'divine': None,
  'duration': '12 turnos',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 126}],
  'id': 'percepcao-extrassensorial',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Percepção Extrassensorial',
  'necromancer': None,
  'range': '18 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:56.015-03:00',
  'url': 'https://olddragon.com.br/magias/percepcao-extrassensorial.json'},
 {'access': 'complete',
  'arcane': 8,
  'description': 'Esta magia tem a habilidade de dar a qualquer magia arcana '
                 'de 1º, 2º e 3º círculos a duração permanente. Esta magia não '
                 'surte efeito em magias que originalmente possuem duração '
                 'instantânea e nem nas que causem dano diretamente como Bola '
                 'de Fogo ou Relâmpago.\n',
  'divine': None,
  'duration': 'permanente',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 126}],
  'id': 'permanencia',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Permanência',
  'necromancer': None,
  'range': 'especial',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:56.041-03:00',
  'url': 'https://olddragon.com.br/magias/permanencia.json'},
 {'access': 'complete',
  'arcane': 4,
  'description': 'Com esta magia, o conjurador abre um portal entre um local '
                 'visível e outro também visível a no máximo 100 metros um do '
                 'outro. O personagem sempre chega ao lugar desejado, desde '
                 'que dentro do alcance da magia e caso consiga visualizar seu '
                 'destino. O personagem pode levar pelo portal todo o '
                 'equipamento que conseguir carregar, além de uma criatura de '
                 'tamanho médio para cada 3 níveis do conjurador. Uma criatura '
                 'grande equivale a duas criaturas médias. Todas as criaturas '
                 'a serem transportadas devem estar em contato umas com as '
                 'outras e, caso o alvo esteja sendo transportado à força, '
                 'pode realizar uma JPS para não ser transportado.\n',
  'divine': 4,
  'duration': 'instantânea',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 126}],
  'id': 'porta-dimensional',
  'illusionist': None,
  'jp': 'JPS nega',
  'name': 'Porta Dimensional',
  'necromancer': None,
  'range': '3 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-06-23T14:09:33.761-03:00',
  'url': 'https://olddragon.com.br/magias/porta-dimensional.json'},
 {'access': 'complete',
  'arcane': 8,
  'description': 'Esta magia abre uma fenda dimensional com outro plano de '
                 'existência, permitindo ao personagem invocar um ser '
                 'específico chamando pelo seu nome. Existe 1 chance em 1d6 de '
                 'outra criatura aproveitar a oportunidade para ultrapassar o '
                 'portal, bem como 1 chance em 1d6 do ser escolhido não se '
                 'interessar pela invocação.  Seres invocados através de um '
                 'portal não serão necessariamente amistosos com o '
                 'conjurador.\n',
  'divine': None,
  'duration': '1d4 turnos + 1/nível',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 126}],
  'id': 'portal',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Portal',
  'necromancer': None,
  'range': '18 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:56.092-03:00',
  'url': 'https://olddragon.com.br/magias/portal.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'Esta magia convoca uma tempestade de insetos de todos os '
                 'tipos e formas sob o controle do conjurador. Esses insetos '
                 'impedem a visão para além de 3 metros, destroem toda a vida '
                 'vegetal por onde passam e trazem terror a pessoas e outras '
                 'criaturas. A nuvem cobre aproximadamente uma área com raio '
                 'de 24 metros. Qualquer criatura com 2 DV ou menos que entre '
                 'na nuvem, deve fugir aterrorizada sem direito a uma Jogada '
                 'de Proteção.\n'
                 '\n'
                 'A magia pode ser sustentada pelo conjurador por até um dia, '
                 'e será dissipada se o conjurador deixar de se concentrar '
                 'nela.\n',
  'divine': 5,
  'duration': '1 dia',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 126}],
  'id': 'praga-de-insetos',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Praga de Insetos',
  'necromancer': None,
  'range': '144 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:56.117-03:00',
  'url': 'https://olddragon.com.br/magias/praga-de-insetos.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'Uma bênção é concedida pela divindade do conjurador, '
                 'concedendo ao alvo tocado um bônus de +1 nas jogadas de '
                 'ataque e nas JPS a cada 3 níveis de conjurador.\n'
                 '\n'
                 '[Profanar] é a versão reversa para personagens caóticos, '
                 'concedendo uma penalidade de 1 nas jogadas de ataque e '
                 'Jogadas de Proteção do alvo tocado. Uma JPS nega tais '
                 'efeitos.\n',
  'divine': 2,
  'duration': '6 turnos',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 105}],
  'id': 'profanar',
  'illusionist': None,
  'jp': 'especial',
  'name': 'Profanar',
  'necromancer': None,
  'range': 'toque',
  'reverse': True,
  'reverse_spell': {'id': 'abencoar',
                    'name': 'Abençoar',
                    'reverse_spell_url': 'https://olddragon.com.br/magias/abencoar.json'},
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:52.875-03:00',
  'url': 'https://olddragon.com.br/magias/profanar.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'Escolha um alinhamento. Esta magia cria uma barreira de '
                 'proteção mágica invisível ao redor do conjurador, '
                 'protegendo-o de criaturas do alinhamento escolhido.\n'
                 '\n'
                 '**Jogada de Proteção**: dentro da barreira de proteção, '
                 'todas as Jogadas de Proteção contra efeitos oriundos do '
                 'alinhamento escolhido são consideradas como teste fácil.\n'
                 '\n'
                 '**Ataques**: criaturas do alinhamento escolhido que atacam o '
                 'conjurador dentro da barreira realizam um ataque difícil '
                 'para atingi-lo.\n'
                 '\n'
                 'Criaturas invocadas, convocadas ou enfeitiçadas por '
                 'conjurador do alinhamento escolhido não conseguem entrar '
                 'dentro da barreira, mas ainda podem desferir ataques '
                 'difíceis à distância contra o conjurador.\n',
  'divine': 1,
  'duration': '12 turnos',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 127}],
  'id': 'protecao-contra-alinhamento',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Proteção contra Alinhamento',
  'necromancer': None,
  'range': 'pessoal',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:56.170-03:00',
  'url': 'https://olddragon.com.br/magias/protecao-contra-alinhamento.json'},
 {'access': 'complete',
  'arcane': 3,
  'description': 'O conjurador cria um campo invisível repelente a projéteis '
                 'não mágicos, como flechas, pedras de funda e virotes de '
                 'bestas, além de armas arremessadas como adagas ou martelos.\n'
                 '\n'
                 'Esta magia não protege contra projéteis grandes, como pedras '
                 'arremessadas por um gigante ou munição de uma catapulta.\n',
  'divine': None,
  'duration': '12 turnos',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 128}],
  'id': 'protecao-contra-projeteis',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Proteção contra Projéteis',
  'necromancer': None,
  'range': 'pessoal',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:56.221-03:00',
  'url': 'https://olddragon.com.br/magias/protecao-contra-projeteis.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'Esta magia faz com que calor ou frio extremos se tornem '
                 'inofensivos para o alvo. Temperaturas de -25° a até 55° são '
                 'percebidas como temperaturas amenas. Além disso, todas as '
                 'Jogadas de Proteção para resistir a qualquer efeito mágico '
                 'ou não mágico provenientes de frio ou calor extremos, como '
                 'baforadas de dragão ou bolas de fogo, reduzem o dano sofrido '
                 'em 1 ponto por dado de dano recebido.\n'
                 '\n'
                 'Desta forma, um dano de 3d6, passará a causar 3d6-3 pontos '
                 'de dano. Já um dano de 2d4, passará a causar 2d4-2 de '
                 'dano.\n',
  'divine': 1,
  'duration': '1 turno + 1/nível',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 127}],
  'id': 'protecao-contra-temperatura',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Proteção contra Temperatura',
  'necromancer': None,
  'range': 'toque',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:56.196-03:00',
  'url': 'https://olddragon.com.br/magias/protecao-contra-temperatura.json'},
 {'access': 'complete',
  'arcane': 6,
  'description': 'Esta magia é utilizada para proteger uma fortaleza, '
                 'abrangendo uma área de até 200 m² por nível de conjurador, e '
                 'até 8 metros de altura.  Os diversos andares de uma '
                 'fortaleza podem ser protegidos com magias diferentes, e o '
                 'efeito dessa proteção é determinado pelo seu conjurador:\n'
                 '\n'
                 '  * **Neblina**: preenche todos os corredores, obscurecendo '
                 'a visão além de 2 metros. Uma criatura no meio da neblina e '
                 'a mais de 2 metros de distância é um alvo difícil de ser '
                 'atingido em um ataque.\n'
                 '\n'
                 '  * **Trancas mágicas**: todas as portas na área estão sob o '
                 'efeito da magia Trancar.\n'
                 '\n'
                 '  * **Teias**: ocupam todas as escadas do local, com '
                 'funcionamento semelhante ao da magia Teia.  Mesmo queimadas, '
                 'as teias crescem novamente em 10 minutos.\n'
                 '\n'
                 '  * **Confusão**: em todos os lugares em que houver uma '
                 'escolha a ser feita – cruzamentos de corredores, por exemplo '
                 '– as criaturas serão afetadas por uma confusão mental que dá '
                 '1-3 chances em 1d6 de acreditarem que estão seguindo na '
                 'direção errada. JPS nega esse efeito.\n'
                 '\n'
                 '  * **Portas secretas**: uma porta para cada nível do '
                 'conjurador é coberta por uma ilusão que faz com que seja '
                 'igual a uma parede. Essa magia impede que a porta secreta '
                 'seja localizada inclusive por elfos.\n',
  'divine': None,
  'duration': '1 turno + 1/nível',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 127}],
  'id': 'proteger-fortalezas',
  'illusionist': None,
  'jp': 'especial',
  'name': 'Proteger Fortalezas',
  'necromancer': None,
  'range': 'especial',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:56.143-03:00',
  'url': 'https://olddragon.com.br/magias/proteger-fortalezas.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'Esta magia purifica comida e água suficiente para doze '
                 'pessoas durante um dia, removendo apodrecimento, venenos, '
                 'contaminações ou qualquer outro efeito negativo não '
                 'mágico.\n',
  'divine': 1,
  'duration': 'permanente',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 128}],
  'id': 'purificar-alimentos',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Purificar Alimentos',
  'necromancer': None,
  'range': 'toque',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:56.255-03:00',
  'url': 'https://olddragon.com.br/magias/purificar-alimentos.json'},
 {'access': 'complete',
  'arcane': 2,
  'description': 'Esta magia faz com que alvos em queda livre caiam lentamente '
                 'até o chão, numa velocidade segura de 20 metros por rodada, '
                 'ou seja, lenta o suficiente para não causar dano.\n'
                 '\n'
                 'Esta magia pode ser conjurada com um gatilho formado por um '
                 'gesto ou palavra única, algo rápido o suficiente para '
                 'conjurá-la até mesmo no meio de uma queda inesperada e sem '
                 'gastar movimento ou ação durante um combate.\n'
                 '\n'
                 'Objetos arremessados ou disparados como pedras, flechas ou '
                 'adagas podem ser alvo de uma Queda Suave se pesarem até 100 '
                 'kg para cada 5 níveis do conjurador.\n'
                 '\n'
                 'Como esta magia atua apenas em objetos em queda livre, não é '
                 'possível conjurá-la para interromper voos ou para prejudicar '
                 'ataques de armas corpo a corpo ou rasantes de criaturas '
                 'voadoras.\n',
  'divine': None,
  'duration': '1 rodada/nível',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 128}],
  'id': 'queda-suave',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Queda Suave',
  'necromancer': None,
  'range': '10 metros/nível',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:56.291-03:00',
  'url': 'https://olddragon.com.br/magias/queda-suave.json'},
 {'access': 'complete',
  'arcane': 5,
  'description': 'O conjurador cria um recipiente arcano contendo sua própria '
                 'força vital, podendo ser usado para possuir o corpo de '
                 'outras criaturas. O recipiente deve ser um objeto inanimado '
                 'e deve estar a até 9 metros de distância do conjurador.\n'
                 '\n'
                 'Durante a transferência o conjurador entra num estado de '
                 'transe, próximo a um coma, e não é capaz de se defender ou '
                 'de realizar qualquer outra ação. Se o corpo do conjurador '
                 'for destruído, a sua força vital fica presa no recipiente '
                 'até conseguir realizar uma possessão. Se o recipiente for '
                 'destruído nesta fase, o conjurador morre imediatamente.\n'
                 '\n'
                 '  * **Possuindo**: quando a força vital do conjurador '
                 'estiver no recipiente, o conjurador pode tentar possuir o '
                 'corpo de outra criatura a até 36 metros do recipiente. A '
                 'vítima pode realizar uma JPS para negar a possessão.  Se '
                 'bem-sucedida, fica imune a uma nova possessão por um turno. '
                 'Se falhar, o conjurador consegue possuir o corpo da vítima '
                 'pelo tempo desejado por ele, retornando sua força vital para '
                 'seu próprio corpo no final do processo.\n'
                 '\n'
                 '  * **Possuído**: o conjurador passa a controlar totalmente '
                 'o corpo da vítima após possuí-lo, mas não conseguirá '
                 'conjurar magias durante uma possessão. Se o recipiente é '
                 'destruído durante a possessão, a força vital do conjurador '
                 'fica presa no corpo possuído, mas, se o corpo possuído '
                 'morrer, a força vital migra para o recipiente. Se ambos '
                 'forem destruídos ao mesmo tempo, o conjurador morre '
                 'imediatamente.\n',
  'divine': None,
  'duration': 'especial',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 128}],
  'id': 'recipiente-arcano',
  'illusionist': None,
  'jp': 'especial',
  'name': 'Recipiente Arcano',
  'necromancer': None,
  'range': 'pessoal',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:56.319-03:00',
  'url': 'https://olddragon.com.br/magias/recipiente-arcano.json'},
 {'access': 'complete',
  'arcane': 2,
  'description': 'A magia cria 1d4+1 reflexos do conjurador, que, como '
                 'espelhos, agem em perfeita sincronia com ele. Os atacantes '
                 'não podem distinguir os reflexos do original, podendo atacar '
                 'uma das imagens ao invés do conjurador verdadeiro. Em caso '
                 'de sucesso no ataque, haverá 1-3 chances em 1d6 do alvo '
                 'atingido ser o reflexo. Caso o ataque seja direcionado a uma '
                 'área na qual estejam tanto o conjurador quanto o seu '
                 'reflexo, essa jogada é dispensada.  Um reflexo atingido é '
                 'imediatamente dissipado.\n',
  'divine': None,
  'duration': '6 turnos',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 129}],
  'id': 'reflexos',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Reflexos',
  'necromancer': None,
  'range': 'pessoal',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:56.345-03:00',
  'url': 'https://olddragon.com.br/magias/reflexos.json'},
 {'access': 'complete',
  'arcane': 3,
  'description': 'Apontando o dedo para um alvo, o conjurador emite um raio de '
                 'sua mão causando 1d8 pontos de dano +1d8 de dano para cada 2 '
                 'níveis do conjurador até um máximo de 10d8. O relâmpago '
                 'ricocheteará no primeiro alvo e atingirá outra criatura à '
                 'escolha do conjurador (desde que esta criatura esteja a até '
                 '6 metros de distância do primeiro alvo), recebendo 1d6 '
                 'pontos de dano +1d6 pontos de dano a cada 2 níveis de '
                 'conjurador até um máximo de 10d6. O relâmpago poderá ainda '
                 'atingir uma terceira criatura à escolha do conjurador (desde '
                 'que esteja a até 6 metros de distância da segunda criatura '
                 'atingida), e receberá 1d4 pontos de dano a cada 2 níveis de '
                 'conjurador até um máximo de 10d4. Uma JPD reduz o dano desta '
                 'magia pela metade.\n',
  'divine': None,
  'duration': 'instantânea',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 129}],
  'id': 'relampago',
  'illusionist': None,
  'jp': 'JPD reduz',
  'name': 'Relâmpago',
  'necromancer': None,
  'range': '54 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:56.372-03:00',
  'url': 'https://olddragon.com.br/magias/relampago.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'Esta magia remove instantaneamente todas as maldições '
                 'impostas sobre uma criatura ou objeto.  Esta magia não '
                 'remove maldição de armas ou armaduras mágicas, mas permite '
                 'que a criatura usando um desses itens consiga se desfazer '
                 'deles e dos efeitos que ainda recaiam sobre si.\n'
                 '\n'
                 'Certas maldições exigem um determinado nível do conjurador '
                 'para serem removidas e, nesses casos, a não ser que esse '
                 'requisito seja cumprido, o Remover Maldição não funcionará.\n'
                 '\n'
                 '[Amaldiçoar] é a versão reversa e caótica impondo uma '
                 'maldição a uma vítima que não seja bem-sucedida numa JPS. O '
                 'alvo amaldiçoado pode sofrer de um dos quatro efeitos '
                 'possíveis, a escolha do conjurador:\n'
                 '\n'
                 '  * **Vulnerabilidade do Corpo**: o alvo perde 2 pontos na '
                 'sua Classe de Armadura;\n'
                 '\n'
                 '  * **Fluidez da Memória**: conjuradores possuem 1-2 chances '
                 'em 1d6 de se esquecer de qualquer magia que forem conjurar '
                 'antes desta ser conjurada.\n'
                 '\n'
                 '  * **Fraqueza da Alma**: o alvo perde metade dos seus '
                 'pontos de Constituição e dos possíveis pontos de vida extras '
                 'que um alto valor de Constituição pode conceder.\n'
                 '\n'
                 '  * **Ineficiência da Precisão**: todo ataque do alvo é um '
                 'teste difícil.\n'
                 '\n'
                 'Uma maldição mantém seus efeitos até ser removida por uma '
                 'magia Remover Maldições.\n',
  'divine': 4,
  'duration': 'instantânea',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 129}],
  'id': 'remover-maldicao',
  'illusionist': None,
  'jp': 'especial',
  'name': 'Remover Maldição',
  'necromancer': None,
  'range': 'toque',
  'reverse': True,
  'reverse_spell': {'id': 'amaldicoar',
                    'name': 'Amaldiçoar',
                    'reverse_spell_url': 'https://olddragon.com.br/magias/amaldicoar.json'},
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:56.398-03:00',
  'url': 'https://olddragon.com.br/magias/remover-maldicao.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'Esta magia tem dois efeitos: anular permanentemente qualquer '
                 'efeito de medo (oriundo de magia ou não) que esteja '
                 'incidindo no alvo; ou conceder aos alvos o benefício de '
                 'realizar testes muito fáceis de JPS para negar efeitos de '
                 'medo por 1 turno.\n'
                 '\n'
                 'O segundo efeito só será possível se o alvo não estiver '
                 'previamente sob efeito de qualquer tipo de medo.\n'
                 '\n'
                 'Esta magia afeta uma criatura tocada para cada 4 níveis do '
                 'conjurador.\n',
  'divine': 1,
  'duration': 'permanente',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 129}],
  'id': 'remover-medo',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Remover Medo',
  'necromancer': None,
  'range': 'toque',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:56.454-03:00',
  'url': 'https://olddragon.com.br/magias/remover-medo.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'Esta magia obriga um alvo a realizar uma missão à escolha do '
                 'conjurador. Uma JPS nega esse efeito no alvo. Se o alvo se '
                 'desviar da missão ou se negar a cumpri-la, será acometido de '
                 'uma maldição que drena 1 ponto de Força por dia até que '
                 'volte a se empenhar na conclusão da missão. Se chegar à '
                 'Força 0, o alvo morrerá imediatamente.\n'
                 '\n'
                 '[Remover Missão] é a versão reversa que permite ao '
                 'conjurador remover qualquer efeito de uma Missão conjurada '
                 'em um alvo. Para surtir efeito, o conjurador precisa ter ao '
                 'menos 2 níveis a mais que o conjurador da magia Missão '
                 'original.\n',
  'divine': 5,
  'duration': 'especial',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 122}],
  'id': 'remover-missao',
  'illusionist': None,
  'jp': 'JPS nega',
  'name': 'Remover Missão',
  'necromancer': None,
  'range': 'toque',
  'reverse': True,
  'reverse_spell': {'id': 'missao',
                    'name': 'Missão',
                    'reverse_spell_url': 'https://olddragon.com.br/magias/missao.json'},
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:55.513-03:00',
  'url': 'https://olddragon.com.br/magias/remover-missao.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'Esta magia confere ao alvo proteção limitada contra um tipo '
                 'específico de energia (ácido, frio, eletricidade, fogo, '
                 'sônico etc.). Toda JP de um alvo desta magia contra a '
                 'energia selecionada é considerada fácil.\n'
                 '\n'
                 'A magia também protege o equipamento do alvo.  Esta magia '
                 'amplia apenas os efeitos da resistência contra a energia. '
                 'Outros efeitos secundários, como o gelo escorregadio, '
                 'permanecem ativos.\n',
  'divine': 2,
  'duration': '6 turnos',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 130}],
  'id': 'resistir-a-energia',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Resistir à Energia',
  'necromancer': None,
  'range': 'toque',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:56.480-03:00',
  'url': 'https://olddragon.com.br/magias/resistir-a-energia.json'},
 {'access': 'complete',
  'arcane': 2,
  'description': 'Todos os alvos dentro do alcance desta magia poderão '
                 'respirar dentro da água pelas próximas 24 horas. Esta magia '
                 'não afeta a capacidade das pessoas de respirar normalmente '
                 'ao saírem da água e não confere qualquer habilidade para '
                 'nadar ou se deslocar dentro da água.\n',
  'divine': None,
  'duration': '24 horas',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 130}],
  'id': 'respirar-na-agua',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Respirar na Água',
  'necromancer': None,
  'range': '9 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:56.506-03:00',
  'url': 'https://olddragon.com.br/magias/respirar-na-agua.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'Esta magia concede ao conjurador a habilidade de restaurar '
                 '1d4 níveis e pontos de atributos perdidos no alvo tocado. '
                 'Pontos de Constituição perdidos devido à Reviver Mortos não '
                 'são recuperados com esta magia.\n',
  'divine': 7,
  'duration': 'instantânea',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 130}],
  'id': 'restauracao',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Restauração',
  'necromancer': None,
  'range': 'toque',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:56.531-03:00',
  'url': 'https://olddragon.com.br/magias/restauracao.json'},
 {'access': 'complete',
  'arcane': 7,
  'description': 'Esta magia faz com que tudo dentro do alcance da magia '
                 '“caia” para cima. Objetos soltos, pessoas, criaturas, tudo '
                 'sobe ao teto como se estivesse caindo. O dano normal para '
                 'queda deve ser aplicado. Objetos frágeis se quebrarão no '
                 'processo como se fossem no chão. Com o fim da magia, todos '
                 'cairão novamente ao solo, recebendo mais uma vez o dano de '
                 'queda.\n',
  'divine': None,
  'duration': '1 rodada/nível',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 130}],
  'id': 'reverter-gravidade',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Reverter Gravidade',
  'necromancer': None,
  'range': '5 metros/nível',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:56.560-03:00',
  'url': 'https://olddragon.com.br/magias/reverter-gravidade.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'Esta magia permite ao conjurador trazer um alvo de volta à '
                 'vida, desde que esteja de posse do cadáver intacto e que o '
                 'alvo não tenha morrido há mais de 5 dias. Ser trazido de '
                 'volta à vida desta forma faz com que 1d6 pontos de '
                 'Constituição sejam perdidos, sem possibilidade de '
                 'restauração.  Alvos revividos, para se recuperarem do trauma '
                 'da magia, precisam de 1 dia de repouso por ponto de '
                 'Constituição perdido. Durante este tempo de recuperação, o '
                 'alvo revivido fica em um estado semelhante ao coma, '
                 'totalmente desacordado.\n',
  'divine': 5,
  'duration': 'instantânea',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 130}],
  'id': 'reviver-mortos',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Reviver Mortos',
  'necromancer': None,
  'range': 'toque',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:56.585-03:00',
  'url': 'https://olddragon.com.br/magias/reviver-mortos.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'Esta magia encanta a roupa do conjurador, aumentando a sua '
                 'classe de armadura.  O conjurador recebe um bônus de +2 na '
                 'CA e um bônus de +1 a cada 3 níveis acima do nível 5. Esse '
                 'bônus é cumulativo com o bônus de armadura normal do '
                 'conjurador.\n',
  'divine': 3,
  'duration': '1 turno + 1/nível',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 130}],
  'id': 'roupa-encantada',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Roupa Encantada',
  'necromancer': None,
  'range': 'pessoal',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:56.611-03:00',
  'url': 'https://olddragon.com.br/magias/roupa-encantada.json'},
 {'access': 'limited',
  'arcane': None,
  'divine': 6,
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/kit-do-mestre.json',
              'page': 12}],
  'id': 'santificar-objetos',
  'illusionist': None,
  'name': 'Santificar Objetos',
  'necromancer': None,
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-06-15T20:42:04.589-03:00',
  'url': 'https://olddragon.com.br/magias/santificar-objetos.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'Esta magia cria uma aura de proteção no conjurador.  Todos '
                 'que desejarem atacar o conjurador, devem realizar uma JPS. '
                 'Caso falhem, não conseguirão atacá-lo, ignorando sua '
                 'presença até o final do efeito da magia.\n'
                 '\n'
                 'Santuário não protege do efeito de magias de área, e perde o '
                 'efeito (dissipando-se) caso o conjurador ataque ou conjure '
                 'magias de ataque.\n',
  'divine': 1,
  'duration': '1 turno + 1/nível',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 131}],
  'id': 'santuario',
  'illusionist': None,
  'jp': 'JPS nega',
  'name': 'Santuário',
  'necromancer': None,
  'range': 'pessoal',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:56.637-03:00',
  'url': 'https://olddragon.com.br/magias/santuario.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'Um silêncio mágico cai sobre uma área de 4,5 metros de raio '
                 'ao redor do alvo, ou objeto alvo, movendo-se com ele. Nenhum '
                 'barulho emitido dentro da área pode ser ouvido além de seus '
                 'limites, não importa o quão alto for. Não é possível '
                 'conjurar magias dentro de uma área sob o efeito da magia '
                 'Silêncio.\n',
  'divine': 2,
  'duration': '12 turnos',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 131}],
  'id': 'silencio',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Silêncio',
  'necromancer': None,
  'range': '54 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:56.662-03:00',
  'url': 'https://olddragon.com.br/magias/silencio.json'},
 {'access': 'complete',
  'arcane': 8,
  'description': 'Esta magia cria uma runa mágica similar a uma escrita que '
                 'pode ser instalada em um objeto como uma porta, muro, '
                 'passagem ou ainda flutuando, mas de forma fixa, em pleno ar. '
                 'Quando uma criatura viva (que não seja o próprio conjurador) '
                 'passar pelo símbolo ou tocar o objeto onde o símbolo está '
                 'instalado, o símbolo é ativado imediatamente.\n'
                 '\n'
                 'Uma vez instalado, é impossível mudar o tipo do símbolo ou a '
                 'sua localização. É preciso escolhê-lo durante a conjuração '
                 'da magia. Os símbolos mais conhecidos são:\n'
                 '\n'
                 '  * **Símbolo da Morte**: mata imediatamente qualquer '
                 'criatura com menos de 10 DV, sem direito a nenhuma JP. Nada '
                 'acontece com alvos de 10 DV ou mais.\n'
                 '\n'
                 '  * **Símbolo da Discórdia**: causa os mesmos efeitos da '
                 'magia Confusão, sem direito a nenhuma JP. Esta condição é '
                 'permanente ou até ser removida.\n'
                 '\n'
                 '  * **Símbolo do Medo**: causa os mesmos efeitos da magia '
                 'Medo, sem direito a nenhuma JP.\n'
                 '\n'
                 '  * **Símbolo da Loucura**: causa insanidade na vítima que '
                 'age desconexa com a realidade.  Ela não pode atacar, '
                 'conjurar magias, usar habilidades de raça ou classe e deve '
                 'ser vigiada de perto para não causar problemas ou mesmo '
                 'desaparecer. Esta condição é permanente ou até ser '
                 'removida.\n'
                 '\n'
                 '  * **Símbolo do Atordoamento**: atordoa imediatamente '
                 'qualquer criatura com menos de 10 DV, sem direito a nenhuma '
                 'JP. Nada acontece com alvos de 10 DV ou mais. Causa os '
                 'mesmos efeitos da magia Palavra do Poder: Atordoar. \n'
                 '\n'
                 '  * **Símbolo do Sono**: adormece imediatamente qualquer '
                 'criatura com menos de 10 DV, sem direito a nenhuma JP. Nada '
                 'acontece com alvos de 10 DV ou mais. Causa os mesmos efeitos '
                 'da magia Sono, mas com duração de 1d10+10 horas.\n',
  'divine': None,
  'duration': 'especial',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 131}],
  'id': 'simbolo',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Símbolo',
  'necromancer': None,
  'range': 'especial',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:56.687-03:00',
  'url': 'https://olddragon.com.br/magias/simbolo.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'O Símbolo de Proteção cria um gatilho de ativação '
                 'condicional em uma passagem ou objeto, protegendo-o de alvos '
                 'que não supram os requisitos para acessá-lo (como uma '
                 'determinada raça, classe, alinhamento, religião ou senha '
                 'secreta). Os efeitos do acesso não permitido devem ser dados '
                 'por outra magia conjurada em conjunto com Símbolo de '
                 'Proteção, ou, caso não use nenhuma outra magia, 1d4 de dano '
                 'por nível do conjurador que instalou o símbolo.\n',
  'divine': 3,
  'duration': 'permanente',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 131}],
  'id': 'simbolo-de-protecao',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Símbolo de Proteção',
  'necromancer': None,
  'range': 'toque',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:56.712-03:00',
  'url': 'https://olddragon.com.br/magias/simbolo-de-protecao.json'},
 {'access': 'complete',
  'arcane': 7,
  'description': 'O conjurador cria uma cópia de si próprio, ou de outro alvo '
                 'tocado, a partir de um boneco feito de qualquer material '
                 'sólido o suficiente para resistir ao ritual. O boneco então '
                 'é encantado e toma formas semelhantes às do alvo, sendo ao '
                 'mesmo tempo muito parecido com o original, mas nitidamente '
                 'diferente, caso comparados lado a lado.\n'
                 '\n'
                 'O simulacro é uma criatura mágica podendo ser detectada por '
                 'meio de magia e é quase idêntica ao alvo, com os poderes '
                 'equivalentes a uma criatura com 1/4 dos níveis do original + '
                 '1 nível. Ou seja, um simulacro de uma criatura com 8 DV '
                 'possui apenas 3 DV.\n'
                 '\n'
                 'O simulacro não copia poderes mágicos, embora consiga emular '
                 'poderes raciais e de classe, respeitando a limitação de '
                 'níveis.\n',
  'divine': None,
  'duration': 'permanente',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 132}],
  'id': 'simulacro',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Simulacro',
  'necromancer': None,
  'range': 'toque',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:56.738-03:00',
  'url': 'https://olddragon.com.br/magias/simulacro.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'Enquanto mantiver sua concentração, o conjurador cria uma '
                 'ilusão sonora de qualquer barulho, fala ou som, já ouvida '
                 'anteriormente por ele. O som ilusório pode se mover, '
                 'aumentar ou diminuir de volume, e o conjurador pode '
                 'controlá-lo enquanto concentrado. Uma JPS nega os efeitos.\n',
  'divine': None,
  'duration': 'especial',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 132}],
  'id': 'som-ilusorio',
  'illusionist': 1,
  'jp': 'JPS nega',
  'name': 'Som Ilusório',
  'necromancer': None,
  'range': '9 metros +1/nível',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:56.765-03:00',
  'url': 'https://olddragon.com.br/magias/som-ilusorio.json'},
 {'access': 'complete',
  'arcane': 1,
  'description': 'Esta magia coloca inimigos em um sono encantado, sem direito '
                 'a uma Jogada de Proteção.  Ela afeta criaturas baseada em '
                 'seus dados de vida, afetando 1d4+1 DV para cada 5 níveis do '
                 'conjurador. As primeiras criaturas afetadas são sempre as '
                 'com menos dados de vida dentro do alcance da magia. Dados de '
                 'vida remanescentes após a contagem são desperdiçados.\n'
                 '\n'
                 'Criaturas adormecidas por esta magia permanecem dormindo até '
                 'o final de sua duração, ou até serem acordadas. São atacadas '
                 'como se estivessem indefesas e despertarão após levarem o '
                 'dano.\n',
  'divine': None,
  'duration': '4d4 turnos',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 132}],
  'id': 'sono',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Sono',
  'necromancer': None,
  'range': '72 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:56.790-03:00',
  'url': 'https://olddragon.com.br/magias/sono.json'},
 {'access': 'complete',
  'arcane': 2,
  'description': 'Teias fibrosas e grudentas preenchem uma área de até 3 x 3 x '
                 '6 metros, tornando essa área extremamente difícil de ser '
                 'atravessada. Será considerada enredada qualquer pessoa que '
                 'entrar numa área preenchida por essa magia, além de não '
                 'poder realizar nenhuma outra ação física que não seja tentar '
                 'se desvencilhar da teia.\n'
                 '\n'
                 '**Desvencilhar**: para se desvencilhar é necessário ser '
                 'bem-sucedido em um teste de Força [D].\n'
                 '\n'
                 '**Inflamável**: a teia é um material altamente inflamável, '
                 'podendo queimar totalmente em duas rodadas. Criaturas presas '
                 'na teia recebem 1d6 de dano por rodada.\n',
  'divine': None,
  'duration': '48 turnos',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 132}],
  'id': 'teia',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Teia',
  'necromancer': None,
  'range': '3 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:56.819-03:00',
  'url': 'https://olddragon.com.br/magias/teia.json'},
 {'access': 'complete',
  'arcane': 5,
  'description': 'O conjurador é capaz de erguer e mover objetos ou criaturas '
                 'apenas com o poder da sua mente, enquanto concentrado. Se '
                 'perder a concentração ou levar dano, a magia se dissipará '
                 'imediatamente.\n'
                 '\n'
                 'A quantidade de peso que pode ser movida (com movimento 6) é '
                 'de até 10 kg por nível do conjurador.  Este também é capaz '
                 'de arremessar o que está sendo erguido, desde que tenha no '
                 'máximo ¼ do peso permitido, a até 15 metros de distância.  O '
                 'alvo desta magia pode realizar uma JPS para negar seus '
                 'efeitos.\n',
  'divine': None,
  'duration': '6 rodadas',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 132}],
  'id': 'telecinesia',
  'illusionist': None,
  'jp': 'JPS nega',
  'name': 'Telecinesia',
  'necromancer': None,
  'range': '36 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:56.845-03:00',
  'url': 'https://olddragon.com.br/magias/telecinesia.json'},
 {'access': 'complete',
  'arcane': 5,
  'description': 'Esta magia transporta o conjurador e/ou outro personagem '
                 'tocado, junto dos seus equipamentos, até um destino '
                 'determinado pelo conjurador e sem limite de distância, desde '
                 'que no mesmo plano de existência. Teleporte possui uma '
                 'chance de ser bem-sucedido e o conhecimento do conjurador '
                 'sobre o local influencia fortemente o resultado, mas pode '
                 'produzir resultados catastróficos:\n'
                 '\n'
                 '  * **Conhecimento Exato**: o conjurador já esteve no local, '
                 'conhece detalhadamente ou fez previamente um estudo '
                 'minucioso do destino.  Chance de 1-5 em 1d6.\n'
                 '\n'
                 '  * **Conhecimento Médio**: o conjurador nunca esteve no '
                 'local, mas sabe onde fica e como chegar lá, ou então estudou '
                 'por mapas ou outra forma de visualização. Chance de 1-3 em '
                 '1d6.\n'
                 '\n'
                 '  * **Conhecimento Fraco**: o conjurador não sabe onde o '
                 'destino fica e nem como chegar até lá, no máximo ouviu '
                 'descrições sobre o lugar.  Chance de 1-2 em 1d6.\n'
                 '\n'
                 'Em caso de sucesso no teste, o teleporte ocorre no nível do '
                 'solo, sem problemas e no local pretendido pelo conjurador.\n'
                 '\n'
                 '**Falha no teste**: caso o teste não seja bem-sucedido, '
                 'lance um dado para cada situação... \n'
                 '\n'
                 'chance de **1-4 em 1d6** do destino estar errado até 1d6 + 4 '
                 'km em qualquer direção;\n'
                 '\n'
                 'chance de **1-2 em 1d6** do destino estar 1d10 x 3 m acima '
                 'do nível do solo, podendo resultar em dano por queda;\n'
                 '\n'
                 'chance de **1 em 1d6** do destino estar abaixo do nível do '
                 'solo, resultando em morte imediata.\n'
                 '\n'
                 'O alvo desta magia pode realizar uma JPS para negar seus '
                 'efeitos.\n',
  'divine': None,
  'duration': 'instantânea',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 133}],
  'id': 'teleporte',
  'illusionist': None,
  'jp': 'JPS nega',
  'name': 'Teleporte',
  'necromancer': None,
  'range': '3 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:56.870-03:00',
  'url': 'https://olddragon.com.br/magias/teleporte.json'},
 {'access': 'complete',
  'arcane': 4,
  'description': 'Esta magia cria um vórtice cônico de gelo e neve com 6 '
                 'metros de diâmetro, causando 1d6 de dano por frio a todas as '
                 'criaturas dentro da tempestade. Adicionalmente, a tempestade '
                 'expele granizo em todas as direções, causando um dano '
                 'adicional de 1d6 (devido os estilhaços de gelo expelidos) em '
                 'quem estiver até 6 metros de distância do centro da '
                 'tempestade. Uma JPD reduz o dano pela metade.\n',
  'divine': None,
  'duration': 'instantânea',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 134}],
  'id': 'tempestade-glacial',
  'illusionist': None,
  'jp': 'JPD reduz',
  'name': 'Tempestade Glacial',
  'necromancer': None,
  'range': '72 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:56.897-03:00',
  'url': 'https://olddragon.com.br/magias/tempestade-glacial.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'O conjurador sacode o solo, mais precisamente um raio de 15 '
                 'metros + 1 metro/nível, fazendo-o tremer como se fosse um '
                 'grande terremoto.  Fissuras no solo são abertas, rios '
                 'transbordam, encostas caem, montanhas deslizam, avalanches '
                 'de neve são formadas, etc. Há uma chance de 1-5 em 1d6 de '
                 'construções pequenas e frágeis serem reduzidas a escombros, '
                 'e uma chance de 1-2 em 1d6 de construções resistentes terem '
                 'o mesmo fim.\n'
                 '\n'
                 'Criaturas na área de um terremoto precisam de sucesso numa '
                 'JPD para se manterem de pé e se deslocarem a um terço de sua '
                 'movimentação normal. Há ainda 1 chance em 1d6 de uma fenda '
                 'na terra se abrir e engolir qualquer criatura na área de '
                 'efeito.\n'
                 '\n'
                 'Criaturas alvos de uma fenda podem realizar um JPD para se '
                 'segurar em qualquer coisa, anulando assim a queda e a '
                 'morte.\n',
  'divine': 7,
  'duration': 'instantânea',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 134}],
  'id': 'terremoto',
  'illusionist': None,
  'jp': 'especial',
  'name': 'Terremoto',
  'necromancer': None,
  'range': '18 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:56.924-03:00',
  'url': 'https://olddragon.com.br/magias/terremoto.json'},
 {'access': 'complete',
  'arcane': None,
  'description': 'O conjurador bem-sucedido em um ataque de toque contra um '
                 'alvo vivo faz com que este perca 1d4 pontos de vida. '
                 'Adicionalmente, o alvo tem 1-3 chances em 1d6 de perder 1 '
                 'ponto de Força caso não seja bem-sucedido em uma JPC.\n'
                 '\n'
                 'Um alvo reduzido a zero pontos de Força morre '
                 'imediatamente.\n',
  'divine': None,
  'duration': 'instantânea',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 135}],
  'id': 'toque-sombrio',
  'illusionist': None,
  'jp': 'especial',
  'name': 'Toque Sombrio',
  'necromancer': 1,
  'range': 'toque',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:56.949-03:00',
  'url': 'https://olddragon.com.br/magias/toque-sombrio.json'},
 {'access': 'complete',
  'arcane': 1,
  'description': 'Esta magia pode ser utilizada para dar acesso a qualquer '
                 'objeto fechado, trancado (mesmo à chave) ou emperrado pela '
                 'duração da magia (ou até ser dissipada).\n'
                 '\n'
                 '[Trancar] é a versão reversa que permite trancar um acesso a '
                 'qualquer objeto aberto.\n',
  'divine': None,
  'duration': 'permanente',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 105}],
  'id': 'trancar',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Trancar',
  'necromancer': None,
  'range': '18 metros',
  'reverse': True,
  'reverse_spell': {'id': 'abrir',
                    'name': 'Abrir',
                    'reverse_spell_url': 'https://olddragon.com.br/magias/abrir.json'},
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:52.962-03:00',
  'url': 'https://olddragon.com.br/magias/trancar.json'},
 {'access': 'complete',
  'arcane': 3,
  'description': 'Todos dentro de uma área de 6 x 6 metros que não passarem em '
                 'uma JPC ficam lentos. Os deslocamentos ficam reduzidos pela '
                 'metade.  Os ataques deferidos pelo alvo são difíceis e os '
                 'contra o alvo, fáceis.\n'
                 '\n'
                 '[Velocidade] é a versão reversa na qual acelera extremamente '
                 'o metabolismo de até 1 criatura tocada para cada 3 níveis do '
                 'conjurador, concedendo ao alvo uma movimentação acima do '
                 'normal. Os deslocamentos ficam multiplicados por dois. Os '
                 'ataques deferidos pelo alvo são fáceis e os contra o alvo, '
                 'difíceis. Além disso, o alvo recebe um ataque extra por '
                 'rodada. A aceleração é prejudicial ao organismo do alvo, '
                 'envelhecendo-o 10% da idade atual.\n',
  'divine': None,
  'duration': '3 turnos',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 119}],
  'id': 'velocidade',
  'illusionist': None,
  'jp': 'JPC evita',
  'name': 'Velocidade',
  'necromancer': None,
  'range': '72 metros',
  'reverse': True,
  'reverse_spell': {'id': 'lentidao',
                    'name': 'Lentidão',
                    'reverse_spell_url': 'https://olddragon.com.br/magias/lentidao.json'},
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:54.979-03:00',
  'url': 'https://olddragon.com.br/magias/velocidade.json'},
 {'access': 'complete',
  'arcane': 1,
  'description': 'Qualquer som produzido com a boca pelo conjurador, e em '
                 'qualquer língua conhecida por ele, é transferido para outra '
                 'pessoa ou objeto dentro do alcance da magia.\n',
  'divine': None,
  'duration': '2 turnos',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 135}],
  'id': 'ventriloquismo',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Ventriloquismo',
  'necromancer': None,
  'range': '18 metros',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:56.975-03:00',
  'url': 'https://olddragon.com.br/magias/ventriloquismo.json'},
 {'access': 'complete',
  'arcane': 7,
  'description': 'Esta magia permite ao conjurador se concentrar em um local '
                 'tranquilo e obter respostas de uma pergunta em forma de uma '
                 'visão enviada por uma entidade superior.\n'
                 '\n'
                 'A qualidade da revelação da visão está ligada à como a '
                 'entidade se sentirá com a pergunta do conjurador. O Mestre '
                 'deve lançar em segredo 1d6 e montar a visão de resposta de '
                 'acordo com o resultado:\n'
                 '\n'
                 '  * **1**: A entidade se sente ultrajada e revela uma visão '
                 'falsa com informações falsas e desconexas.\n'
                 '\n'
                 '  * **2**: A entidade se sente desrespeitada com a '
                 'frivolidade da questão e ignora o conjurador.\n'
                 '\n'
                 '  * **3-5**: A entidade se mostra indiferente, mas envia uma '
                 'visão menor e interpretativa.\n'
                 '\n'
                 '  * **6**: A entidade se sente compelida a ajudar e envia '
                 'uma visão reveladora.\n',
  'divine': None,
  'duration': 'instantânea',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 135}],
  'id': 'visao',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Visão',
  'necromancer': None,
  'range': 'pessoal',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:57.003-03:00',
  'url': 'https://olddragon.com.br/magias/visao.json'},
 {'access': 'complete',
  'arcane': 6,
  'description': 'Esta magia permite ao conjurador ver dentro de um raio de 36 '
                 'metros as coisas como elas realmente são. O conjurador fica '
                 'imune a ilusões, escuridões mágicas ou normais; enxerga '
                 'criaturas e objetos invisíveis como se fossem visíveis e '
                 'também portas secretas ou camufladas; visualiza a forma '
                 'verdadeira de criaturas modificadas ou transformadas.\n'
                 '\n'
                 'Uma Visão da Verdade também pode ser usada para enxergar os '
                 'alinhamentos reais das criaturas e objetos, além de dar uma '
                 'noção aproximada do poder das criaturas dentro da área de '
                 'efeito.\n',
  'divine': 5,
  'duration': '1d4 turnos + 1/nível',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 135}],
  'id': 'visao-da-verdade',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Visão da Verdade',
  'necromancer': None,
  'range': 'pessoal',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-12-31T16:16:15.792-03:00',
  'url': 'https://olddragon.com.br/magias/visao-da-verdade.json'},
 {'access': 'complete',
  'arcane': 3,
  'description': 'Esta magia dá ao alvo tocado pelo conjurador o poder de voar '
                 'com movimento 18 enquanto a magia durar. O movimento de voo '
                 'é livre, podendo o alvo se mover em qualquer direção, subir '
                 'ou descer, assim como levitar ou pairar.\n',
  'divine': None,
  'duration': '1d6 turnos + 1/nível',
  'fontes': [{'compact': False,
              'digital_item_url': 'https://olddragon.com.br/livros/lb1.json',
              'page': 135}],
  'id': 'voo',
  'illusionist': None,
  'jp': 'nenhuma',
  'name': 'Voo',
  'necromancer': None,
  'range': 'toque',
  'reverse': False,
  'type': 'Spell',
  'updated_at': '2023-05-31T22:12:57.055-03:00',
  'url': 'https://olddragon.com.br/magias/voo.json'}]
