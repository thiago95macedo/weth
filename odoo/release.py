RELEASE_LEVELS = [ALPHA, BETA, RELEASE_CANDIDATE, FINAL] = ['alpha', 'beta', 'candidate', 'final']
RELEASE_LEVELS_DISPLAY = {ALPHA: ALPHA,
                          BETA: BETA,
                          RELEASE_CANDIDATE: 'rc',
                          FINAL: ''}

# formato do version_info: (MAJOR, MINOR, MICRO, RELEASE_LEVEL, SERIAL)
# inspirado no próprio sys.version_info do Python, para ser
# devidamente comparável usando operadores normais, por exemplo:
#  (25,1,0,'beta',0) < (25,1,0,'candidato',1) < (25,1,0,'candidato',2)
#  (25,1,0,'candidato',2) < (25,1,0,'final',0) < (25,1,2,'final',0)
version_info = (25, 0, 0, FINAL, 0, '')
version = '.'.join(str(s) for s in version_info[:2]) + RELEASE_LEVELS_DISPLAY[version_info[3]] + str(version_info[4] or '') + version_info[5]
series = serie = major_version = '.'.join(str(s) for s in version_info[:2])

product_name = 'WETH'
description = 'Servidor WETH'
long_desc = '''O WETH é um ERP e CRM completo. As principais funcionalidades incluem contabilidade (analítica
e financeira), gestão de estoque, gestão de vendas e compras, automação de tarefas,
campanhas de marketing, help desk, PDV, etc. Os recursos técnicos incluem
um servidor distribuído, um banco de dados orientado a objetos, uma interface gráfica dinâmica,
relatórios personalizáveis e interfaces XML-RPC.
'''
classifiers = """Status de Desenvolvimento :: 5 - Produção/Estável
Licença :: Aprovado pela OSI :: GNU Lesser General Public License v3
Linguagem de Programação :: Python
"""
url = 'https://www.weth.com.br'
author = 'WETH Tecnologia da Informação Ltda.'
author_email = 'contato@weth.com.br'
license = 'LGPL-3'
nt_service_name = "weth-server-" + series.replace('~', '-')