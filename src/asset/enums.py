"""Asset enums"""

from enum import Enum


class DisposalReasonEnum(str, Enum):
    """Disposal reason enum"""

    DEVOLUCAO = "Devolução"
    DOACAO = "Doação"
    PERMUTA = "Permuta"
    SINISTRO = "Sinistro"
    TRANSFERENCIA = "Transferência"
    RECADASTRAMENTO = "Recadastramento"
    DESMEMBRAMENTO = "Desmembramento"
    OBSOLETO = "Obsoleto"
    EM_DESUSO = "Em desuso"
    IMPRESTAVEL = "Imprestável"
    VENDA = "Venda"


class AssetStatusEnum(int, Enum):
    """Asset status enum"""

    DISPONIVEL = 1
    EM_COMODATO = 2
    ESTOQUE_SP = 3
    ESTOQUE_BA = 4
    RESERVADO = 5
    INATIVO = 6
    EMPRESTIMO = 7
    DESCARTE = 8
    MANUTENCAO = 9
    MELHORIA = 10
    EM_COMODATO_TEMPORARIO = 11
