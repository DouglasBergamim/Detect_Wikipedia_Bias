# Nuvia - Análise de Artigos da Wikipedia

Aplicativo web para análise de artigos da Wikipedia, incluindo detecção de viés usando técnicas de NLP.

## Estrutura do Projeto

```
app/
├── main.py               # Arquivo principal de orquestração e layout 
├── config.py             # Configurações e constantes globais
├── ui/                   # Componentes da interface do usuário
│   ├── sidebar.py        # Barra lateral de configurações
│   ├── article_cards.py  # Layout em cards para exibir artigos
│   └── bias_report.py    # Relatório de análise de viés
├── services/             # Camadas de acesso a dados e ML
│   ├── wiki.py           # Acesso à API da Wikipedia
│   └── bias.py           # Detector de viés usando BERT
├── utils/                # Funções utilitárias
│   ├── highlights.py     # Formatação de destaques em textos
│   └── state.py          # Gerenciamento de estado da sessão
└── download_model.py     # Script para download prévio do modelo
```

## Requisitos

- Python 3.9+
- Bibliotecas: streamlit, transformers, tensorflow, aiohttp, nltk, pandas

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/nuvia.git
cd nuvia
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. (Opcional) Baixe o modelo de ML antecipadamente:
```bash
python app/download_model.py
```

## Executando a Aplicação

```bash
streamlit run app/main.py
```

## Características

- Busca de artigos por tópicos e período
- Detecção de viés em textos usando um modelo BERT pré-treinado
- Exibição de artigos em formato de cards paginados
- Destaque de seções subjetivas nos textos analisados
- Métricas e estatísticas sobre o nível de viés nos artigos 