from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
import requests
from datetime import datetime, timedelta
import os

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "https://robsonrvs1991.github.io",
    "https://robsonrvs1991.github.io/calculadorawsfront",
    "https://calculadora-rvs-production.up.railway.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir index.html
@app.get("/", response_class=HTMLResponse)
def raiz():
    try:
        with open("calculadorawsfront/index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="index.html não encontrado.")

# Serve arquivos estáticos (JS, CSS, etc.)
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "calculadorawsfront")), name="static")

# Chamada simplificada de teste
@app.get("/indices")
def get_indices_teste():
    return {"indice": 42}

# API real para buscar os índices
SGS_BASE_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{serie}/dados"
SERIES = {
    "selic": 432,
    "cdi": 12,
    "ipca": 433,
    "tr": 189,
}

def fetch_serie(serie_id):
    hoje = datetime.now()
    data_inicial = (hoje - timedelta(days=30)).strftime("%d/%m/%Y")
    data_final = hoje.strftime("%d/%m/%Y")
    url = SGS_BASE_URL.format(serie=serie_id)
    params = {"formato": "json", "dataInicial": data_inicial, "dataFinal": data_final}
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    dados = resp.json()
    return float(dados[-1]["valor"]) if dados else None

@app.get("/indices")
def get_indices():
    try:
        return {indice: fetch_serie(id_) for indice, id_ in SERIES.items()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/indices/{indice}")
def get_indice(indice: str):
    if indice not in SERIES:
        raise HTTPException(status_code=404, detail="Índice não encontrado")
    try:
        valor = fetch_serie(SERIES[indice])
        if valor is None:
            raise HTTPException(status_code=404, detail="Dados não encontrados")
        return {indice: valor}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
