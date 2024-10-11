import json
from typing import List

from fastapi import FastAPI, Form, Request
from fastapi.responses import Response
from lib import *
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "https://developer.gatewayit.co",
    "http://localhost",
    "http://localhost:5173",
    "http://localhost:5174",
    "https://gaia.appgatewayit.co",
    "https://tornado.gatewayit.co",
    "https://api.gatewayit.co",
    "https://ia.gatewayit.co",
    "https://masterminds-co.com/",
    "https://dev.masterminds-co.com/"
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/allrecords/{tipografica}")
async def getrecords(tipografica=None):
    todo = loadrecords(tipografica=tipografica)
    return Response(todo)


@app.post("/estadcc/{tipografica}")
async def getrecords(request: Request, tipografica=None):
    data = await request.json()
    todo = loadrecords(data=data, tipografica=tipografica)
    return Response(todo)


@app.get("/datasources/{keywords}/{cantidad_fuentes}")
async def getrecords(keywords=None, cantidad_fuentes=None):
    # keywords = request.get("keywords").split()
    cantidad_fuentes = int(cantidad_fuentes)
    data_sources = Obtener_Fuentes_datos(keywords, cantidad_fuentes)
    return data_sources

@app.get("/grafo/{idempresa}/{resumeng}")
async def getgraph(idempresa, resumeng):
    data_graph = buildgraph_by_category(id_empresa=idempresa)
    return data_graph

@app.get("/grafo/{idempresa}")
async def getgraph(idempresa):
    data_graph = buildgraph_by_category(id_empresa=idempresa, resumen=0)
    return data_graph

@app.get("/orbital/{idempresa}")
async def getorbital(idempresa=None):
    data_orb = buildorbital(id_empresa=idempresa, is_mastermind=False)
    return data_orb

@app.get("/orbital-mastermind/{idempresa}")
async def getorbital(idempresa=None):
    data_orb = buildorbital(id_empresa=idempresa, is_mastermind=True)
    return data_orb

@app.get("/grafo-by-session/{idsession}")
async def get_graph_by_session(idsession):
    data_graph = buildgraph_by_session(idsession)
    return data_graph

@app.get("/grafo-mastermind")
async def getgraph():
    data_graph = getGrafoByAllCompanies()
    return data_graph

@app.get("/grafo-mastermind-actividad")
async def getgraph2():
    data_graph = groupByActivityEconomic()
    return data_graph
