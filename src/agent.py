from dotenv import load_dotenv
load_dotenv()

import os
import boto3
import pandas as pd
from pyathena import connect
from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic
from typing import TypedDict, Optional

# ─── Configurações ───────────────────────────────────────────
REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
DATABASE = os.getenv("ATHENA_DATABASE")
S3_OUTPUT = os.getenv("ATHENA_S3_OUTPUT")

llm = ChatAnthropic(model="claude-opus-4-8")

aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")

conn = connect(
    s3_staging_dir=S3_OUTPUT,
    region_name=REGION,
    schema_name=DATABASE,
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key
)

# ─── Schema das tabelas Gold ──────────────────────────────────
SCHEMA_CONTEXT = """
Você tem acesso às seguintes tabelas no Amazon Athena (database: home_credit_bronze):

- gold_default_by_contract: inadimplência por tipo de contrato
  Colunas: name_contract_type, total_clientes, total_default, taxa_default_pct, renda_media, credito_medio

- gold_default_by_gender: inadimplência por gênero
  Colunas: code_gender, total_clientes, total_default, taxa_default_pct

- gold_default_by_income_range: inadimplência por faixa de renda
  Colunas: faixa_renda, total_clientes, total_default, taxa_default_pct, renda_media

- gold_bureau_features: features de histórico de crédito por cliente
  Colunas: SK_ID_CURR, aggregações de bureau

- gold_credit_features: features de cartão de crédito por cliente
  Colunas: SK_ID_CURR, aggregações de cartão

- gold_installments_features: features de parcelas por cliente
  Colunas: SK_ID_CURR, aggregações de parcelas

- gold_previous_application_features: features de aplicações anteriores
  Colunas: SK_ID_CURR, aggregações de aplicações

Use APENAS SQL válido para Amazon Athena (Presto/Trino).
Sempre use LIMIT 100 nas queries.
Retorne apenas o SQL, sem explicações.
"""
# ─── Estado do agente ─────────────────────────────────────────
class AgentState(TypedDict):
    question: str
    sql: Optional[str]
    result: Optional[str]
    answer: Optional[str]

# ─── Nós do grafo ─────────────────────────────────────────────
def generate_sql(state: AgentState) -> AgentState:
    prompt = f"{SCHEMA_CONTEXT}\n\nPergunta: {state['question']}\n\nSQL:"
    response = llm.invoke(prompt)
    sql = response.content.strip().replace("```sql", "").replace("```", "").strip()
    print(f"\n📝 SQL gerado:\n{sql}\n")
    return {**state, "sql": sql}

def run_query(state: AgentState) -> AgentState:
    try:
        df = pd.read_sql(state["sql"], conn)
        result = df.to_string(index=False)
        print(f"\n📊 Resultado:\n{result}\n")
    except Exception as e:
        result = f"Erro na query: {str(e)}"
        print(f"\n❌ {result}\n")
    return {**state, "result": result}

def generate_answer(state: AgentState) -> AgentState:
    prompt = f"""
Pergunta do usuário: {state['question']}

Resultado da query:
{state['result']}

Com base nos dados acima, responda de forma clara e objetiva em português.
"""
    response = llm.invoke(prompt)
    return {**state, "answer": response.content}

# ─── Grafo LangGraph ──────────────────────────────────────────
graph = StateGraph(AgentState)
graph.add_node("generate_sql", generate_sql)
graph.add_node("run_query", run_query)
graph.add_node("generate_answer", generate_answer)

graph.set_entry_point("generate_sql")
graph.add_edge("generate_sql", "run_query")
graph.add_edge("run_query", "generate_answer")
graph.add_edge("generate_answer", END)

agent = graph.compile()

# ─── Loop de conversa ─────────────────────────────────────────
if __name__ == "__main__":
    print("🤖 Agente Home Credit — powered by Claude Opus 4.8 + Athena")
    print("Digite 'sair' para encerrar\n")

    while True:
        question = input("Você: ").strip()
        if question.lower() == "sair":
            break

        result = agent.invoke({"question": question})
        print(f"\n🤖 Resposta: {result['answer']}\n")
        print("-" * 60)