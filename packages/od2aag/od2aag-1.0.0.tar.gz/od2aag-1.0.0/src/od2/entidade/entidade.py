class EntidadeBase:
    def __init__(self,
                 pv: int
                 ):
        self._pv: int = pv
        self._pv_atual: int = pv

        self.esta_morto: bool = False

    #? Propriedades
    @property
    def pv_atual(self):
        return self._pv_atual

    @pv_atual.setter
    def pv_atual(self, valor: int):
        self._pv_atual = valor
        self._pv_atual = 0 if self._pv_atual < 0 else self._pv_atual
        self._pv_atual = self._pv if self._pv_atual > self._pv else self._pv_atual

        self.esta_morto = True if self._pv_atual == 0 else False


    #? Métodos
    def ferir(self, valor: int):
        self.pv_atual -= valor

    def curar(self, valor: int):
        self.pv_atual += valor
