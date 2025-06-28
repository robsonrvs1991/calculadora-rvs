from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
import requests
from datetime import datetime, timedelta
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

# Permitir acesso do seu domínio frontend
origins = [
    "http://localhost:3000",
    "https://robsonrvs1991.github.io",
    "https://calculadora-rvs.up.railway.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar frontend estático em /static (não sobrescreve rotas da API)
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "calculadorawsfront"), html=True), name="static")

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
    params = {
        "formato": "json",
        "dataInicial": data_inicial,
        "dataFinal": data_final,
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    dados = resp.json()
    if dados:
        return float(dados[-1]["valor"])
    else:
        return None

@app.get("/indices")
def get_indices():
    try:
        selic = fetch_serie(SERIES["selic"])
        cdi = fetch_serie(SERIES["cdi"])
        ipca = fetch_serie(SERIES["ipca"])
        tr = fetch_serie(SERIES["tr"])
        return {
            "selic": selic,
            "cdi": cdi,
            "ipca": ipca,
            "tr": tr,
        }
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
