"""
Validação de artefatos.
"""

from .cpf import validate_cpf
from .cnpj import validate_cnpj

__all__ = [
    "validate_cpf", 
    "validate_cnpj"
    ]


from .cpf import validate_cpf
from .cnpj import validate_cnpj

__all__ = ["validate_cpf", "validate_cnpj"]
