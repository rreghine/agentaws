# AgentAWS — Credit Risk Intelligence

> Agente de IA para análise de risco de crédito com linguagem natural, construído sobre uma pipeline cloud-native AWS e Claude Opus 4.8.

---

## Demo

![AgentAWS — Credit Risk Intelligence](docs/preview.PNG)

Faça uma pergunta em linguagem natural → o agente gera SQL → consulta o Amazon Athena → retorna insights analíticos.

**Exemplos:**
- *"Qual a taxa de inadimplência por tipo de contrato?"*
- *"Qual gênero tem maior risco de default?"*
- *"Qual faixa de renda apresenta maior inadimplência?"*

---

## Arquitetura

```
CSV Raw (Kaggle)
    │
    ▼
S3 Bronze          ← dados brutos em Parquet
    │
    ▼ S3 Event Notification
    │
AWS Lambda         ← trigger automático ao detectar novo arquivo
    │
    ▼ Glue ETL (PySpark)
    │
S3 Silver          ← dados limpos e tipados
    │
    ▼ Athena CTAS
    │
S3 Gold            ← tabelas analíticas agregadas
    │
    ▼
LangGraph Agent    ← orquestração do fluxo
    │
    ├── Claude Opus 4.8  ← geração de SQL + análise
    └── Amazon Athena    ← execução das queries
    │
    ▼
Flask API + HTML Interface (EC2 t3.micro)
```

---

## Stack

| Camada | Tecnologia |
|---|---|
| Data Lake | Amazon S3 (Bronze / Silver / Gold) |
| Catalogação | AWS Glue Crawler + Data Catalog |
| ETL | AWS Glue Jobs (PySpark) |
| Automação | AWS Lambda (trigger S3 → Glue) |
| Query Engine | Amazon Athena (Presto/Trino) |
| Agente IA | LangGraph + Claude Opus 4.8 |
| API | Flask (Python) |
| Deploy | Amazon EC2 t3.micro |
| Dataset | [Home Credit Default Risk](https://www.kaggle.com/c/home-credit-default-risk) |

---

## Dataset

**Home Credit Default Risk** — Kaggle

| Tabela | Registros |
|---|---|
| application_train | 307.511 |
| application_test | 48.744 |
| bureau | 1.716.428 |
| bureau_balance | 27.299.925 |
| credit_card_balance | 3.840.312 |
| installments_payments | 13.605.401 |
| pos_cash_balance | 10.001.358 |
| previous_application | 1.670.214 |
| **Total** | **~58M registros** |

---

## Tabelas Gold

Criadas via Athena CTAS a partir do Silver:

| Tabela | Descrição |
|---|---|
| `gold_default_by_contract` | Inadimplência por tipo de contrato |
| `gold_default_by_gender` | Inadimplência por gênero |
| `gold_default_by_income_range` | Inadimplência por faixa de renda |
| `gold_bureau_features` | Features agregadas de histórico de crédito |
| `gold_credit_features` | Features agregadas de cartão de crédito |
| `gold_installments_features` | Features agregadas de parcelas |
| `gold_previous_application_features` | Features de aplicações anteriores |

---

## Automação com Lambda

Um AWS Lambda function monitora o bucket S3 Bronze via S3 Event Notification. Ao detectar a chegada de um novo arquivo, dispara automaticamente o Glue ETL job — eliminando a necessidade de execução manual do pipeline.

```
Novo arquivo → S3 Bronze → S3 Event → Lambda → Glue ETL → Silver atualizado
```

---

## Principais Insights

- **Taxa de inadimplência geral:** 8,1%
- **Cash loans** têm taxa de default de 8,35% vs 5,48% em Revolving loans
- **Homens** apresentam 10,14% de inadimplência vs 7,00% das mulheres
- **Renda média** lidera em inadimplência (8,55%) — maior que a faixa de renda baixa
- **Renda muito alta** tem menor risco: 5,82%

---

## Como rodar localmente

### Pré-requisitos

- Python 3.9+
- AWS CLI configurada (`aws configure`)
- Conta AWS com acesso a S3, Glue e Athena
- Chave de API da Anthropic

### Instalação

```bash
git clone https://github.com/rreghine/agentaws
cd agentaws
pip install -r requirements.txt
```

### Variáveis de ambiente

Crie um arquivo `.env` na raiz:

```
ANTHROPIC_API_KEY=sua_chave_aqui
AWS_ACCESS_KEY_ID=sua_access_key
AWS_SECRET_ACCESS_KEY=sua_secret_key
AWS_DEFAULT_REGION=us-east-1
```

### Executar

```bash
python src/app.py
```

Acesse: [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## Estrutura do projeto

```
agentaws/
├── src/
│   ├── agent.py        # Agente LangGraph (CLI)
│   └── app.py          # API Flask + rota HTML
├── index.html          # Interface web
├── .env                # Variáveis de ambiente (não versionado)
├── requirements.txt
└── README.md
```

---

## Fluxo do agente

```
Pergunta (linguagem natural)
        │
        ▼
  generate_sql        ← Claude Opus 4.8 gera SQL a partir do schema
        │
        ▼
  run_query           ← Executa no Amazon Athena via PyAthena
        │
        ▼
  generate_answer     ← Claude Opus 4.8 analisa os dados e gera insight
        │
        ▼
  Resposta em português com análise e recomendações
```

---

## Autor

**Rafael Reghine Munhoz** — Analytics Engineer

- LinkedIn: [linkedin.com/in/rafaelreghine](https://linkedin.com/in/rafaelreghine)
- GitHub: [github.com/rreghine](https://github.com/rreghine)
- MBA Data Science & Analytics — USP
