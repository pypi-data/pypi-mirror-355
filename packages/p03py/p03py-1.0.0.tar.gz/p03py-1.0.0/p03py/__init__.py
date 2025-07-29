import importlib.util
import sys
import os

# Caminho para o arquivo compilado .pyc
path = os.path.join(os.path.dirname(__file__), "balanca_com_estado.pyc")

# Carregamento dinâmico
spec = importlib.util.spec_from_file_location("balanca_com_estado", path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Expor interfaces diretamente no pacote
BalancaSerialInterface = mod.BalancaSerialInterface
BalancaTCPInterface = mod.BalancaTCPInterface
