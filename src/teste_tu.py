class Pessoa:

    idade = 0

    def __init__(self, idade) -> None:
        self.idade = idade

    @classmethod
    def mais_um_ano(cls):
        print(cls.idade)
        cls.idade += 1

    @staticmethod
    def mostra_nome(nome):
        print(nome)


p = Pessoa(20)
print(p.idade)
p.mais_um_ano()
print(p.idade)
p.mostra_nome("Eduardo")
