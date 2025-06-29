from fastapi.responses import JSONResponse
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
import requests
from datetime import datetime, timedelta
import os

app = FastAPI()

# Liberação de CORS com regex + preflight
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*(\.railway\.app|\.github\.io)$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rota extra para lidar com preflight OPTIONS
@app.options("/{rest_of_path:path}")
async def preflight_handler(rest_of_path: str, request: Request):
    return {}

# Servir index.html na raiz
@app.get("/", response_class=HTMLResponse)
def raiz():
    index_path = os.path.join(os.path.dirname(__file__), "calculadorawsfront", "index.html")
    try:
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="index.html não encontrado.")

# Montar arquivos estáticos
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "calculadorawsfront")), name="static")

# Constantes de API
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
        return float(dados[-1]["valor"].replace(",", "."))
    return None

@app.get("/indices")
def get_indices():
    try:
        selic = fetch_serie(SERIES["selic"])
        cdi = fetch_serie(SERIES["cdi"])
        ipca = fetch_serie(SERIES["ipca"])
        tr = fetch_serie(SERIES["tr"])

        response = JSONResponse(content={
            "selic": selic,
            "cdi": cdi,
            "ipca": ipca,
            "tr": tr,
        })
        # FORÇA O CORS FUNCIONAR
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "*"
        return response
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
        response = JSONResponse(content={indice: valor})
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "*"
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
