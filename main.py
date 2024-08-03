import json
from typing import List

from fastapi import FastAPI, Form, Request
from fastapi.responses import Response
from lib import loadrecords, Obtener_Fuentes_datos, buildgraph, buildorbital
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "https://developer.gatewayit.co",
    "http://localhost",
    "http://localhost:5173",
    "http://localhost:5174",
    "https://gaia.appgatewayit.co",
    "https://tornado.gatewayit.co",
    "https://masterminds.gatewayit.co",
    "https://api.gatewayit.co",
    "https://ia.gatewayit.co"
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
    data_graph = buildgraph(id_empresa=idempresa, resumen=resumeng)
    return data_graph

@app.get("/grafo/{idempresa}")
async def getgraph(idempresa):
    data_graph = buildgraph(id_empresa=idempresa, resumen=0)
    return data_graph

@app.get("/orbital/{idempresa}")
async def getorbital(idempresa=None):
    data_orb = buildorbital(id_empresa=idempresa)
    return data_orb
