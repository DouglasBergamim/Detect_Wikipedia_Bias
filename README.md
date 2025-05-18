# Nuvia - Análise de Artigos da Wikipedia

Uma aplicação web que permite buscar artigos relevantes da Wikipedia sobre tópicos específicos e analisar seu viés.

## Funcionalidades

- **Busca de Artigos**: Encontra artigos da Wikipedia sobre tópicos específicos, ordenados por relevância e visualizações
- **Análise de Viés**: Examina o nível de subjetividade/neutralidade em cada artigo selecionado
- **Interativo**: Interface amigável com Streamlit para fácil configuração e visualização de resultados

## Tecnologias Utilizadas

- **Streamlit**: Interface web interativa
- **Transformers (Hugging Face)**: Modelo BERT para análise de viés em textos
- **NLTK**: Processamento de linguagem natural
- **Pandas**: Manipulação de dados
- **APIs da Wikipedia**: Busca de artigos e dados de visualização

## Estrutura do Projeto

```
nuvia/
│
├── app/
│   ├── app.py                 # Aplicação Streamlit principal
│   ├── wiki_service.py        # Serviço de busca de artigos da Wikipedia
│   └── bias_detector.py       # Serviço para detectar viés em textos
│
├── models/                    # Pasta para armazenar modelos pré-treinados
│   └── .gitkeep
│
├── notebooks/                 # Notebooks de desenvolvimento e testes
│   ├── detect_bias.ipynb
│   └── wikipedia_articles.ipynb
│
├── requirements.txt          # Dependências do projeto
└── README.md                 # Este arquivo
```

## Requisitos

- Python 3.8+
- Bibliotecas listadas em `requirements.txt`

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/nuvia.git
cd nuvia
```

2. Crie um ambiente virtual e ative-o:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

## Execução

Execute a aplicação com o comando:
```bash
cd app
streamlit run app.py
```

Acesse a aplicação no navegador: http://localhost:8501

## Como Usar

1. Na barra lateral, defina seus tópicos de interesse (um por linha)
2. Ajuste o número de artigos a buscar e exibir conforme necessário
3. Clique em "Buscar Artigos" para iniciar a busca
4. Selecione um artigo e clique em "Analisar Viés" para ver a análise detalhada de subjetividade

## Observações

- O primeiro carregamento pode ser lento devido ao download do modelo BERT
- A busca de artigos pode levar alguns segundos ou minutos dependendo da quantidade de tópicos e artigos solicitados
- A análise de viés é realizada por sentença, o que permite uma visão detalhada do conteúdo 