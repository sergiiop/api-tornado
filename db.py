import psycopg2
from psycopg2.extras import RealDictCursor

ctor = {
        'user': "postgres",
        'password':"G@t3w@yTI-31416",
        'host': "localhost",
        'port': "5432",
        'database': "tornado",
        'cursor_factory': RealDictCursor
}

cgaia = {
        'user': "postgres",
        'password':"G@t3w@yTI-31416",
        'host': "129.213.167.145",
        'port': "5432",
        'database': "tornado-dev",
        'cursor_factory': RealDictCursor
}

cmaster = {
        'user': "postgres",
        'password':"G@t3w@yTI-31416",
        'host': "158.101.100.172",
        'port': "5432",
        'database': "mastermind",
        'cursor_factory': RealDictCursor
}

# Configuración de la conexión a la base de datos PostgreSQL
def conectar(c):
    conexion = psycopg2.connect(
        user=c['user'],
        password=c['password'],
        host=c['host'],
        port=c['port'],
        database=c['database'],
        cursor_factory=c['cursor_factory']
    )
    return conexion
