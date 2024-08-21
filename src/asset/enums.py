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
