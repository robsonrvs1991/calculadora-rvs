from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from datetime import datetime, timedelta, date
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://robsonrvs1991.github.io",
        "http://localhost:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Preflight OPTIONS
@app.options("/{rest_of_path:path}")
async def preflight_handler(rest_of_path: str, request: Request):
    return {}

# Servir index.html
@app.get("/", response_class=HTMLResponse)
def raiz():
    index_path = os.path.join(os.path.dirname(__file__), "calculadorawsfront", "index.html")
    try:
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="index.html não encontrado.")

# Arquivos estáticos
app.mount("/static", StaticFiles(directory="/home/robsonrvs/calculadorawsfront"), name="static")

# Constantes da API do Bacen
SGS_BASE_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{serie}/dados"
SERIES = {
    "selic": 432,
    "cdi": 12,
    "ipca": 433,
    "tr": 189,
}

# Cache diário
ultimo_fetch = None
cache_indices = {}

def fetch_serie(serie_id):
    hoje = datetime.now()
    data_inicial = (hoje - timedelta(days=30)).strftime("%d/%m/%Y")
    data_final = hoje.strftime("%d/%m/%Y")
    url = SGS_BASE_URL.format(serie=serie_id)
    params = {
        "formato": "json",
        "dataInicial": data_inicial,
        "dataFinal": data_final,
    }
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    dados = resp.json()
    if dados:
        return float(dados[-1]["valor"].replace(",", "."))
    return None

@app.get("/indices")
def get_indices():
    global ultimo_fetch, cache_indices
    hoje = date.today()

    if ultimo_fetch != hoje:
        try:
            cache_indices = {
                "selic": fetch_serie(SERIES["selic"]),
                "cdi": fetch_serie(SERIES["cdi"]),
                "ipca": fetch_serie(SERIES["ipca"]),
                "tr": fetch_serie(SERIES["tr"]),
            }
            ultimo_fetch = hoje
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao consultar API Bacen: {e}")

    return JSONResponse(
        content=cache_indices,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "*"
        }
    )

@app.get("/indices/{indice}")
# Classe de entrada para o cálculo
class CalculoRequest(BaseModel):
    investimento_inicial: float
    aporte_mensal: float
    meses: int
    cdi: float
    ipca: float
    poupanca: float

@app.post("/calcular")
def calcular_rendimento(dados: CalculoRequest):
    P = dados.investimento_inicial
    A = dados.aporte_mensal
    n = dados.meses

    def calcula_montante(taxa_anual):
        i = (1 + taxa_anual / 100) ** (1/12) - 1  # taxa mensal
        montante_aportes = A * (((1 + i) ** n - 1) / i)
        montante_total = P * (1 + i) ** n + montante_aportes
        return round(montante_total, 2)

    total_cdi = calcula_montante(dados.cdi)
    total_ipca = calcula_montante(dados.ipca)
    total_poupanca = calcula_montante(dados.poupanca * 12)  # a.m. → a.a.

    return {
        "total_cdi": total_cdi,
        "total_ipca": total_ipca,
        "total_poupanca": total_poupanca
    }

def get_indice(indice: str):
    if indice not in SERIES:
        raise HTTPException(status_code=404, detail="Índice não encontrado")
    try:
        valor = fetch_serie(SERIES[indice])
        if valor is None:
            raise HTTPException(status_code=404, detail="Dados não encontrados")
        return JSONResponse(
            content={indice: valor},
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Methods": "*"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Classe de entrada para o cálculo
class CalculoRequest(BaseModel):
    investimento_inicial: float
    aporte_mensal: float
    meses: int
    cdi: float
    ipca: float
    poupanca: float

@app.post("/calcular")
def calcular_rendimento(dados: CalculoRequest):
    P = dados.investimento_inicial
    A = dados.aporte_mensal
    n = dados.meses

    def calcula_montante(taxa_anual):
        i = (1 + taxa_anual / 100) ** (1/12) - 1  # taxa mensal
        montante_aportes = A * (((1 + i) ** n - 1) / i)
        montante_total = P * (1 + i) ** n + montante_aportes
        return round(montante_total, 2)

    total_cdi = calcula_montante(dados.cdi)
    total_ipca = calcula_montante(dados.ipca)
    total_poupanca = calcula_montante(dados.poupanca * 12)  # a.m. → a.a.

    return {
        "total_cdi": total_cdi,
        "total_ipca": total_ipca,
        "total_poupanca": total_poupanca
    }
