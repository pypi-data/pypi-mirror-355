from dataclasses import dataclass
from typing import Literal


moedas = Literal['pc', 'pp', 'po']

CAMBIO = {
    'pc': 1,
    'pp': 10,
    'po': 100
}

PESO = 1/100


def converter_moedas(valor: int, de: moedas = 'pp', para: moedas = 'po'):
    maior = CAMBIO[de] > CAMBIO[para]
    atual, resto = 0, 0

    if maior:
        atual = valor * (CAMBIO[de] / CAMBIO[para])

    else:
        atual = valor / (CAMBIO[para] / CAMBIO[de])
        resto = valor % (CAMBIO[para] / CAMBIO[de])

    return int(atual), int(resto)


@dataclass
class Moedas:
    pc: int = 0
    pp: int = 0
    po: int = 0

    @property
    def carga(self):
        volume = self.pc + self.pp + self.po
        return int(volume * PESO)
    
    @property
    def saldo_po(self):
        pc = converter_moedas(self.pc, 'pc', 'po')
        pp = converter_moedas(self.pp, 'pp', 'po')

        po = 0
        pc = pc[0] + pc[1] / 100
        pp = pp[0] + pp[1] / 10

        troco = pc + pp

        if troco > 100:
            po = int(troco/100)
            troco = troco % 100

        return self.po + po + troco
    

    #! Métodos de conversão
    def pc_para_po(self, valor: int):
        # se o valor for maior, só converte o que pode
        if valor > self.pc:
            valor = self.pc
        
        self.pc -= valor

        po, pc = converter_moedas(valor, 'pc', 'po')
        print(po, pc)

        self.pc += pc
        self.po += po

    def pp_para_po(self, valor: int):
        # se o valor for maior, só converte o que pode
        if valor > self.pp:
            valor = self.pp

        self.pp -= valor

        po, pp = converter_moedas(valor, 'pp', 'po')

        self.pp += pp
        self.po += po

    def pp_para_pc(self, valor: int):
        # se o valor for maior, só converte o que pode
        if valor > self.pp:
            valor = self.pp

        self.pp -= valor

        pc, _ = converter_moedas(valor, 'pp', 'pc')

        self.pc += pc

    def pc_para_pp(self, valor: int):
        # se o valor for maior, só converte o que pode
        if valor > self.pc:
            valor = self.pc

        self.pc -= valor

        pp, pc = converter_moedas(valor, 'pc', 'pp')

        self.pc += pc
        self.pp += pp

    def po_para_pp(self, valor: int):
        # se o valor for maior, só converte o que pode
        if valor > self.po:
            valor = self.po

        self.po -= valor

        pp, _ = converter_moedas(valor, 'po', 'pp')

        self.pp += pp

    def po_para_pc(self, valor: int):
        # se o valor for maior, só converte o que pode
        if valor > self.po:
            valor = self.po

        self.po -= valor

        pc, _ = converter_moedas(valor, 'po', 'pc')

        self.pc += pc

    #! Outros métodos
    def otimizar_carga(self):
        """Reduz a quantidade de moedas carregadas, mantendo o saldo
        """
        self.pc_para_pp(self.pc)
        self.pp_para_po(self.pp)

    def comprar(self, valor_pc: int):
        """Compra um item, com a base do valor em peças de cobre, que é o padrão
        da API. Retorna o valor final otimizado

        Args:
            valor_pc (int): o valor do item a ser comprado
        """
        if converter_moedas(valor_pc, 'pc', 'po')[0] < self.saldo_po:
            self.po_para_pc(self.po)
            self.pp_para_pc(self.pp)

            self.pc -= valor_pc

            self.otimizar_carga()
        
        else:
            print('sem saldo')
        
