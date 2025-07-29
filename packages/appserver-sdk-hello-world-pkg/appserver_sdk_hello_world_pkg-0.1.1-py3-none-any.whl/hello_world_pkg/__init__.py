"""
Hello World Package
Um pacote exemplo que retorna hello world
"""

__version__ = "0.1.0"
__author__ = "Iran"
__email__ = "iranribeiro22@gmail.com"

def hello():
    """Retorna uma saudação hello world"""
    return "hello world"

def hello_with_name(name: str) -> str:
    """Retorna uma saudação personalizada"""
    return f"Hello {name}! How are you?"

# Torna as funções disponíveis quando o pacote for importado
__all__ = ["hello", "hello_with_name"]