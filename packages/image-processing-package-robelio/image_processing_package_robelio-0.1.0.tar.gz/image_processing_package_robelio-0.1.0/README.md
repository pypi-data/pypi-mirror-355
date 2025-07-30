## Pacote de Processamento de Imagens

### Um pacote para processamento básico de imagens com funções para transformação, combinação e análise de imagens.

## Principais Funcionalidades

* ### Transformações: Redimensionamento, rotação, espelhamento
* ### Combinação: Fusão de imagens, mesclagem de canais
* ### Análise: Histogramas de cores, visualização

## Instalação

### Comando via terminal:
### pip install image-processing-package

## Dependências 

### Dependências Obrigatórias

- [Pillow](https://python-pillow.org) (>=9.0.0) - Para manipulação básica de imagens
- [numpy](https://numpy.org) (>=1.21.0) - Para Operações númericas 
- [matplotlib](https://matplotlib.org/) (>=3.5.0) - Para visualização e histogramas 

### Dependências de Desenvolvimento 

- [pytest](https://docs.pytest.org/) (>=7.0.0) - Para testes unitários
- [pytest-cov](https://pytest-cov.readhedocs.io) - Para relatório de cobertura
- [Sphinx](https://www.sphinx-doc.org/) (>=5.0.0) - Para documentação
- [twine](https://twine.readthedocs.io/) (>=4.0.0) - Para publicação no PyPI

## Como Instalar todas as dependências de desenvolvimento

### Comando via terminal:
### pip install -e ".[dev]"

## Como Instalar as dependências obrigatórias

### Comando via terminal:
### pip install -r requirements.txt

### importante: o arquivo requirements deve conter as dependências.

### Autor: Robélio Barreto
