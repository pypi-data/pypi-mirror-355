"""
Appserver SDK Validation Package
Pacote de validação de artefatos referentes ao Brasil.
"""

__version__ = "0.1.1"
__author__ = "Appserver SDK"
__email__ = "suporte@appserver.com.br"

from .cpf import validate_cpf
from .cnpj import validate_cnpj

__all__ = [
    "validate_cpf", 
    "validate_cnpj"
    ]
