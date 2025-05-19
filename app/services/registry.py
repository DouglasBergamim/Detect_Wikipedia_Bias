from functools import lru_cache
from .wiki import WikiService
from .bias import BiasDetector
from .analyse_args import ArgumentAnalyzer
from .debias import DebiasService

@lru_cache(maxsize=1)
def _services():
    """Inicializa os serviços apenas uma vez"""
    return WikiService(), BiasDetector(), ArgumentAnalyzer(), DebiasService()

wiki, bias, args_analyzer, debias = _services() 