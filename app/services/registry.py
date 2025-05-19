"""
Registro centralizado de serviços para evitar múltiplas inicializações
"""
from functools import lru_cache
from .wiki import WikiService
from .bias import BiasDetector
from .analyse_args import ArgumentAnalyzer

@lru_cache(maxsize=1)
def _services():
    """Inicializa os serviços apenas uma vez"""
    return WikiService(), BiasDetector(), ArgumentAnalyzer()

# Exporta os serviços como variáveis globais
wiki, bias, args_analyzer = _services() 