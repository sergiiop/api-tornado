import json

import openai
from matplotlib import pyplot as plt
import pandas as pd
import plotly.io as pio
import plotly.express as px

from bs4 import BeautifulSoup
from googlesearch import search
from wordcloud import WordCloud
from wordcloud import STOPWORDS
from urllib.parse import urlparse
import requests
import folium
from folium.plugins import HeatMap
from db import ctor, cgaia, conectar


# Función para crear el mapa de calor
def generar_mapa_calor(df):
    df = df.dropna(subset=['long'])
    df = df.dropna(subset=['lat'])
    mapa = folium.Map(location=[df['lat'].mean(), df['long'].mean()], zoom_start=5)
    heat_data = [[row['lat'], row['long']] for index, row in df.iterrows()]
    HeatMap(heat_data).add_to(mapa)
    return mapa


def loadrecords(data=None, tipografica='mapa'):
    try:
        conexion = conectar(ctor)
        # Código para consultar la tabla del esquema empresas
        cursor = conexion.cursor()

        # print(data)

        cond1 = ''
        if data is not None and data['sizeCompany'] is not None and len(data['sizeCompany']) > 0:
            cond1 = ','.join("'{0}'".format(w.strip()) for w in data['sizeCompany'])
            cond1 = ' and c."TAM-EMPRESA" in (' + cond1 + ')'

        cciu = ''
        if data is not None and data['ciiu1'] is not None and len(data['ciiu1']) > 0:
            cond2 = ','.join("'{0}'".format(w.strip()) for w in data['ciiu1'])
            cond2 = ' where c.id in (' + cond2 + ')'
            sql = """select c.codigo, c.descripcion
            from empresa_master.ciiu c """ + cond2
            cursor.execute(sql)
            ciius1 = cursor.fetchall()
            cciu += ' and ("CIIU-1" IN ('
            for ciiu in ciius1:
                cciu = cciu + "'{0}',".format(ciiu['codigo'] + ' ** ' + ciiu['descripcion'])
            cciu = cciu + "'xx') "
            cciu += ' or "CIIU-2" IN ('
            for ciiu in ciius1:
                cciu = cciu + "'{0}',".format(ciiu['codigo'] + ' ** ' + ciiu['descripcion'])
            cciu = cciu + "'xx') "
            cciu += ' or "CIIU-3" IN ('
            for ciiu in ciius1:
                cciu = cciu + "'{0}',".format(ciiu['codigo'] + ' ** ' + ciiu['descripcion'])
            cciu = cciu + "'xx') "
            cciu += ' or "CIIU-4" IN ('
            for ciiu in ciius1:
                cciu = cciu + "'{0}',".format(ciiu['codigo'] + ' ** ' + ciiu['descripcion'])
            cciu = cciu + "'xx')) "

            # print(cciu)

        sql = """select c."MATRICULA" , 
        c."RAZON SOCIAL" , 
        c."NIT" , 
        c."MUN-COMERCIAL" , 
        c."CIIU-1",
        c."CIIU-2" , 
        c."CIIU-3" ,
        c."CIIU-4" ,
        c."ACTIVIDAD" ,
        c."TAM-EMPRESA" ,
        c."CIIU-TAM-EMPRESARIAL" ,
        c2.lat ,
        c2.long 
        from empresa_master.camaracomercio c 
        left join public.ciudad c2 
        on substring(c."MUN-COMERCIAL",1,5) = c2.codigo
        where 1=1 """  # LIMIT 100

        sql = sql + cond1 + cciu

        # print(sql)

        cursor.execute(sql)
        ccomercio = cursor.fetchall()
        # Obtener los nombres de las columnas del cursor
        nombres_columnas = [desc[0] for desc in cursor.description]

        pd.options.plotting.backend = "plotly"
        df = pd.DataFrame(ccomercio, columns=nombres_columnas)

        # Cerrar el cursor y la conexión a la base de datos
        cursor.close()
        conexion.close()

        # records = []
        # for cc in ccomercio:
        #     records.append(cc) # ['RAZON SOCIAL']

        # print(tipografica)

        if tipografica != 'mapa' and tipografica != 'heatmap':
            fig = df.groupby(['MUN-COMERCIAL']).size().plot(kind=tipografica)  # bar, barh
            # print(dfg)
            return pio.to_html(fig, full_html=False)
        else:
            # #######################################################################
            # gdatf = df['TAM-EMPRESA', 'long', 'lat']
            # gdatf.columns = ['TAM-EMPRESA', 'long', 'lat']
            if tipografica == 'mapa':
                dfg = df.groupby(['MUN-COMERCIAL', 'lat', 'long']).size().reset_index(name='N')
                figm = px.scatter_mapbox(dfg,
                                         lat="lat",
                                         lon="long",
                                         color="MUN-COMERCIAL",
                                         size="N",
                                         opacity=0.5,
                                         color_continuous_scale=px.colors.cyclical.IceFire,
                                         size_max=100,  # Tamaño máximo de los puntos
                                         zoom=7,  # Nivel de zoom inicial
                                         # mapbox_style="open-street-map",
                                         title="EMPRESAS CAMARA DE COMERCIO MONTERÍA",
                                         labels={"MUN-COMERCIAL": "Frecuencia"})

                # figm.update_layout(mapbox_style="stamen-terrain") # Estilo del mapa de fondo --> 'open-street-map', 'white-bg', 'carto-positron', 'carto-darkmatter', 'stamen-terrain', 'stamen-toner', 'stamen-watercolor'
                figm.update_layout(
                    mapbox_style="white-bg",
                    mapbox_layers=[
                        {
                            "below": 'traces',
                            "sourcetype": "raster",
                            "sourceattribution": "Open street Maps",
                            "source": [
                                # "https://tiles.stadiamaps.com/tiles/alidade_smooth/{z}/{x}/{y}.png"
                                "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
                            ]
                        }
                    ])
                figm.update_layout(showlegend=False)
                figm.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
                # #######################################################################
                return pio.to_html(figm, full_html=False)
            else:
                mapa = generar_mapa_calor(df)
                htmlmap = mapa.get_root()._repr_html_()  # render()

                return htmlmap  # '<div>'+htmlmap+'</div>'

    except Exception as e:
        return e.__str__()


def buildgraph(id_empresa, resumen):
    try:
        conexiong = conectar(cgaia)
        # Código para consultar la tabla del esquema empresas
        cursor = conexiong.cursor()

        cond = ""
        # cond = f" where re.epresa_a  = '{id_empresa}' or re.epresa_b  = '{id_empresa}' "


        # return {'empresa': id_empresa, 'resumen': resumen}

        if resumen == "1":
            sql = """select 
                true as is_active ,
                re.epresa_a ,
                ea.razonsocial as razonsocial_a ,
                ea.nombrecomercial as nombrecomercial_a ,
                re.epresa_b ,
                eb.razonsocial as razonsocial_b ,
                eb.nombrecomercial as nombrecomercial_b ,
                count(tr.id) as num_relaciones,
                string_agg(tr.nombre, ',') as relaciones,
                string_agg(tr.id::"varchar", ',') as idtipos
                from empresa_master.relacion_empresa re 
                inner join empresa_master.tipo_relacion tr 
                on (re.tipo_relacion = tr.id)
                inner join empresa_master.empresa ea 
                on (re.epresa_a = ea.id)
                inner join empresa_master.empresa eb 
                on (re.epresa_b = eb.id)
                """
            grb = """
                group by 
                re.epresa_a ,
                ea.razonsocial ,
                ea.nombrecomercial ,
                re.epresa_b ,
                eb.razonsocial ,
                eb.nombrecomercial
                """
            sql += cond + grb

        else:
            sql = """select re.id , 
                re.is_active ,
                re.epresa_a ,
                ea.razonsocial as razonsocial_a ,
                ea.nombrecomercial as nombrecomercial_a ,
                re.epresa_b ,
                eb.razonsocial as razonsocial_b ,
                eb.nombrecomercial as nombrecomercial_b ,
                tr.id as idtipo,
                tr.nombre as relacion, 
                tr.descripcion 
                from empresa_master.relacion_empresa re 
                inner join empresa_master.tipo_relacion tr 
                on (re.tipo_relacion = tr.id)
                inner join empresa_master.empresa ea 
                on (re.epresa_a = ea.id)
                inner join empresa_master.empresa eb 
                on (re.epresa_b = eb.id)    
                """  
            # LIMIT 100

            sql += cond

        # print(sql)
        cursor.execute(sql)
        relaciones = cursor.fetchall()
        # Obtener los nombres de las columnas del cursor
        # nombres_columnas = [desc[0] for desc in cursor.description]

        # Cerrar el cursor y la conexión a la base de datos
        cursor.close()
        conexiong.close()

        nodesv = []
        empresas = []
        nodes = []
        edges = []
        elements = []

        ne = 1

        for rel in relaciones:
            # print(rel)
            if rel['epresa_a'] not in nodesv:
                nodesv.append(rel['epresa_a'])
                if bool(rel['razonsocial_a']) and len(rel['razonsocial_a']) != 0:
                    empresas.append(rel['razonsocial_a'].capitalize())
                else:
                    empresas.append('Sin razón social') #  + rel['epresa_a']
            if rel['epresa_b'] not in nodesv:
                nodesv.append(rel['epresa_b'])
                if bool(rel['razonsocial_b']) and len(rel['razonsocial_b']) != 0:
                    empresas.append(rel['razonsocial_b'].capitalize())
                else:
                    empresas.append('Sin razón social') #  + rel['epresa_b']
            ecolor = 'red'
            if rel['is_active']:
                ecolor = 'gray'

            if resumen == "1":
                edge = {
                    'data': {'id': f"{rel['epresa_a']}-{rel['epresa_b']}-{str(ne)}", 'source': rel['epresa_a'],
                            'target': rel['epresa_b'], 'label': "Relaciones: " + str(rel['num_relaciones']), 'color': ecolor}
                }
            else:
                edge = {
                    'data': {'id': f"{rel['epresa_a']}-{rel['epresa_b']}-{rel['idtipo']}", 'source': rel['epresa_a'],
                            'target': rel['epresa_b'], 'label': rel['relacion'], 'color': ecolor}
                }
                # edge = {
                #     'source': rel['epresa_a'],
                #     'target': rel['epresa_b']
                # }
            edges.append(edge)
            ne +=1

        for i, node in enumerate(nodesv):
            color = '#698CBF'
            if node == id_empresa:
                color = '#23386D'
            # nodes.append({'id': node, 'color': color})
            nodes.append({'data': {'id': node}})
            elements.append({'data': {'id': node, 'label': empresas[i], 'color': color}})

        for ee in edges:
            elements.append(ee)

        return elements
        # return {'nodes': nodes, 'links': edges}

    except Exception as e:
        return e.__str__()
    
def buildgraph_by_category(id_empresa):
    try:
        # Establecer la conexión y el cursor usando 'with' para asegurar el cierre
        with conectar(cgaia) as conexiong:
            with conexiong.cursor() as cursor:
                cond = f"WHERE relation.epresa_a = '{id_empresa}'"

                sql = f"""
                SELECT 
                    relation.id,
                    relation.is_active,
                    relation.epresa_a,
                    empresa.razonsocial AS razonsocial_a,
                    empresa.nombrecomercial AS nombrecomercial_a,
                    se_a.id AS sector_empresa_id_a,
                    se_a.descripcion AS sector_empresa_a,
                    se_b.id AS sector_empresa_id_b,
                    se_b.descripcion AS sector_empresa_b,
                    relation.epresa_b,
                    empresab.razonsocial AS razonsocial_b,
                    empresab.nombrecomercial AS nombrecomercial_b
                FROM empresa_master.relacion_empresa relation
                INNER JOIN empresa_master.empresa empresa
                    ON (relation.epresa_a = empresa.id)
                INNER JOIN empresa_master.empresa empresab
                    ON (relation.epresa_b = empresab.id)
                LEFT JOIN empresa_master.sector_empresa se_a
                    ON (se_a.id = empresa.sector_empresa_id)
                LEFT JOIN empresa_master.sector_empresa se_b
                    ON (se_b.id = empresab.sector_empresa_id)
                {cond}
                GROUP BY relation.id, relation.is_active, relation.epresa_a, empresa.razonsocial, empresa.nombrecomercial, relation.epresa_b, empresab.razonsocial, empresab.nombrecomercial, se_a.id, se_b.id, se_a.descripcion, se_b.descripcion
                """

                cursor.execute(sql)
                relaciones = cursor.fetchall()

         # Procesamiento de los resultados
        nodesv = set()
        edges = []
        elements = []

        nodos_principales = {
            2: '#034078',  # Azul - Academia
            1: '#FF7F11',  # Naranja - Sector Productivo
            4: '#2ca02c',  # Verde - Aglomeracion
            3: '#d62728',   # Rojo - Hibrido
            5: '#9467bd'   # Morado
        }

        empresas_por_sector = {
            2: [],  # SECTOR ACADEMICO
            1: [],  # SECTOR PRODUCTIVO
            4: [],  # HIBRIDO
            3: []   # ESTADO
        }
 
        def add_empresa(empresa_id, razonsocial, sector_id):
            if empresa_id not in nodesv:
                nodesv.add(empresa_id)
                color = '#23386D' if empresa_id == id_empresa else nodos_principales[rel['sector_empresa_id_b']]
 
                empresa_nodo = {
                    'data': {'id': empresa_id, 'label': razonsocial if razonsocial else 'Sin razón social', 'color': color}
                }

                if sector_id in empresas_por_sector:
                    empresas_por_sector[sector_id].append(empresa_nodo)
                else:
                    empresas_por_sector[None].append(empresa_nodo)

        empresas_b_vistas = set()
        edges_vistas = set()

        for rel in relaciones:
            print(rel)
            add_empresa(rel['epresa_a'], rel['razonsocial_a'], rel['sector_empresa_id_a'])

            if rel['epresa_b'] not in empresas_b_vistas:
                add_empresa(rel['epresa_b'], rel['razonsocial_b'], rel['sector_empresa_id_b'])
                empresas_b_vistas.add(rel['epresa_b'])

            edge_id = (rel['epresa_a'], rel['epresa_b'])
            if edge_id not in edges_vistas:
                ecolor = nodos_principales[rel['sector_empresa_id_b']] if rel['sector_empresa_id_b'] in nodos_principales else '#FF0000'
                edge = {
                    'data': {
                        'id': f"{rel['epresa_a']}-{rel['epresa_b']}-{rel['id']}",
                        'source': rel['epresa_a'],
                        'target': rel['epresa_b'],
                        'color': ecolor,
                    }
                }
                edges.append(edge)
                edges_vistas.add(edge_id)

        for sector_id in sorted(empresas_por_sector.keys()):
            elements.extend(empresas_por_sector[sector_id])
        # Adición de bordes al gráfico
        elements.extend(edges)

        return elements

    except Exception as e:
        print(e)
        return str(e)
    
def buildgraphv2(id_empresa, resumen):
    try:
        conexiong = conectar(cgaia)
        # Código para consultar la tabla del esquema empresas
        cursor = conexiong.cursor()

        cond = ""
        # cond = f" where re.epresa_a  = '{id_empresa}' or re.epresa_b  = '{id_empresa}' "


        # return {'empresa': id_empresa, 'resumen': resumen}

        

        if resumen == "1":
            sql = """select 
                true as is_active ,
                re.epresa_a ,
                ea.razonsocial as razonsocial_a ,
                ea.nombrecomercial as nombrecomercial_a ,
                re.epresa_b ,
                eb.razonsocial as razonsocial_b ,
                eb.nombrecomercial as nombrecomercial_b ,
                count(tr.id) as num_relaciones,
                string_agg(tr.nombre, ',') as relaciones,
                string_agg(tr.id::"varchar", ',') as idtipos
                from empresa_master.relacion_empresa re 
                inner join empresa_master.tipo_relacion tr 
                on (re.tipo_relacion = tr.id)
                inner join empresa_master.empresa ea 
                on (re.epresa_a = ea.id)
                inner join empresa_master.empresa eb 
                on (re.epresa_b = eb.id)
                """
            grb = """
                group by 
                re.epresa_a ,
                ea.razonsocial ,
                ea.nombrecomercial ,
                re.epresa_b ,
                eb.razonsocial ,
                eb.nombrecomercial
                """
            sql += cond + grb

        else:
            sql = """select re.id , 
                re.is_active ,
                re.epresa_a ,
                ea.razonsocial as razonsocial_a ,
                ea.nombrecomercial as nombrecomercial_a ,
                re.epresa_b ,
                eb.razonsocial as razonsocial_b ,
                eb.nombrecomercial as nombrecomercial_b ,
                tr.id as idtipo,
                tr.nombre as relacion, 
                tr.descripcion 
                from empresa_master.relacion_empresa re 
                inner join empresa_master.tipo_relacion tr 
                on (re.tipo_relacion = tr.id)
                inner join empresa_master.empresa ea 
                on (re.epresa_a = ea.id)
                inner join empresa_master.empresa eb 
                on (re.epresa_b = eb.id)    
                """  
            # LIMIT 100

            sql += cond

        # print(sql)
        cursor.execute(sql)
        relaciones = cursor.fetchall()
        # Obtener los nombres de las columnas del cursor
        # nombres_columnas = [desc[0] for desc in cursor.description]

        # Cerrar el cursor y la conexión a la base de datos
        cursor.close()
        conexiong.close()

        nodesv = []
        empresas = []
        nodes = []
        edges = []
        elements = []

        ne = 1

        for rel in relaciones:
            # print(rel)
            if rel['epresa_a'] not in nodesv:
                nodesv.append(rel['epresa_a'])
                if bool(rel['razonsocial_a']) and len(rel['razonsocial_a']) != 0:
                    empresas.append(rel['razonsocial_a'].capitalize())
                else:
                    empresas.append('Sin razón social') #  + rel['epresa_a']
            if rel['epresa_b'] not in nodesv:
                nodesv.append(rel['epresa_b'])
                if bool(rel['razonsocial_b']) and len(rel['razonsocial_b']) != 0:
                    empresas.append(rel['razonsocial_b'].capitalize())
                else:
                    empresas.append('Sin razón social') #  + rel['epresa_b']
            ecolor = 'red'
            if rel['is_active']:
                ecolor = 'gray'

            if resumen == "1":
                edge = {
                    'data': {'id': f"{rel['epresa_a']}-{rel['epresa_b']}-{str(ne)}", 'source': rel['epresa_a'],
                            'target': rel['epresa_b'], 'label': "Relaciones: " + str(rel['num_relaciones']), 'color': ecolor}
                }
            else:
                edge = {
                    'data': {'id': f"{rel['epresa_a']}-{rel['epresa_b']}-{rel['idtipo']}", 'source': rel['epresa_a'],
                            'target': rel['epresa_b'], 'label': rel['relacion'], 'color': ecolor}
                }
                # edge = {
                #     'source': rel['epresa_a'],
                #     'target': rel['epresa_b']
                # }
            edges.append(edge)
            ne +=1

        for i, node in enumerate(nodesv):
            color = '#698CBF'
            if node == id_empresa:
                color = '#23386D'
            # nodes.append({'id': node, 'color': color})
            nodes.append({'data': {'id': node}})
            elements.append({'data': {'id': node, 'label': empresas[i], 'color': color}})

        for ee in edges:
            elements.append(ee)

        return elements
        # return {'nodes': nodes, 'links': edges}

    except Exception as e:
        return e.__str__()


def buildorbital(id_empresa=None):
    try:
        conexiong = conectar(cgaia)
        # Código para consultar la tabla del esquema empresas
        cursor = conexiong.cursor()

        sql = f"""select * from
        (
        select re.epresa_a as miempresaid,
        ea.razonsocial as mirazonsocial ,
        ea.nombrecomercial as minombrecomercial ,
        eb.razonsocial as razonsocialpar ,
        eb.nombrecomercial as nombrecomercialpar ,
        count(re.epresa_b) as nrels,
        string_agg(tr.nombre , ', ') as relaciones
        from empresa_master.relacion_empresa re 
        inner join empresa_master.tipo_relacion tr 
        on (re.tipo_relacion = tr.id)
        inner join empresa_master.empresa ea 
        on (re.epresa_a = ea.id)
        inner join empresa_master.empresa eb 
        on (re.epresa_b = eb.id) 
        where re.epresa_a = '{id_empresa}'
        and re.is_active = true
        group by re.epresa_a ,
        ea.razonsocial,
        ea.nombrecomercial,
        eb.razonsocial,
        eb.nombrecomercial
        union 
        select re.epresa_b as miempresaid,
        eb.razonsocial as mirazonsocial ,
        eb.nombrecomercial as minombrecomercial ,
        ea.razonsocial as razonsocialpar ,
        ea.nombrecomercial as nombrecomercialpar ,
        count(re.epresa_a) as nrels,
        string_agg(tr.nombre , ', ') as relaciones
        from empresa_master.relacion_empresa re 
        inner join empresa_master.tipo_relacion tr 
        on (re.tipo_relacion = tr.id)
        inner join empresa_master.empresa ea 
        on (re.epresa_a = ea.id)
        inner join empresa_master.empresa eb 
        on (re.epresa_b = eb.id) 
        where re.epresa_b = '{id_empresa}'
        and re.is_active = true
        group by re.epresa_b ,
        eb.razonsocial,
        eb.nombrecomercial,
        ea.razonsocial,
        ea.nombrecomercial
        ) as X 
        order by X.nrels DESC """  # LIMIT 100

        # print(sql)
        cursor.execute(sql)
        relaciones = cursor.fetchall()
        # Obtener los nombres de las columnas del cursor
        # nombres_columnas = [desc[0] for desc in cursor.description]

        if len(relaciones) == 0:
            return [[]]  # No hay registros

        # Cerrar el cursor y la conexión a la base de datos
        cursor.close()
        conexiong.close()

        blue_palette = [
            '#0000FF',  # Azul puro
            '#0000CC',  # Azul oscuro
            '#000099',  # Azul más oscuro
            '#000066',  # Azul aún más oscuro
            '#000033',  # Azul muy oscuro
            '#0033FF',  # Azul claro con un toque de verde
            '#0066FF',  # Azul claro
            '#0099FF',  # Azul cielo
            '#00CCFF',  # Azul cielo claro
            '#00FFFF',  # Cian, que es un azul verdoso claro
            '#33CCFF',  # Azul claro con más verde
            '#6699FF',  # Azul pastel
            '#3366FF',  # Azul medio
            '#003366',  # Azul petróleo
            '#003399',  # Azul royal oscuro
            '#0033CC',  # Azul royal
            '#336699',  # Azul acero
            '#3399CC',  # Azul acero claro
            '#6699CC',  # Azul polvo
            '#99CCFF'  # Azul bebé
        ]

        data = []
        nivel = 0
        vrel = []
        nrels = int(relaciones[0]['nrels'])

        for i, rel in enumerate(relaciones):
            if nrels != int(rel['nrels']):
                nrels = int(rel['nrels'])
                data.append(vrel)
                nivel = + 1
                vrel = []

            razonsc = 'Sin razon social definida'
            if bool(rel['razonsocialpar']) and len(rel['razonsocialpar']) != 0:
                razonsc = rel['razonsocialpar'].capitalize()

            vrel.append({'color': blue_palette[nivel], 'size': 0.25, 'label': razonsc, 'n': nrels,
                         'relaciones': rel['relaciones']})

        data.append(vrel)  # el ultimo

        return data

    except Exception as e:
        return e.__str__()


# ------------------------------------------------ VIGILANCIA TECNOLOGICA -----------------------------------------------------

def Obtener_Fuentes_datos(keywords, cantidad_fuentes):
    query = '"Empresas"+"Servicios"'
    text = " "
    for i in keywords:
        query += ' ' + i + ' '
    fuente_datos_automatica = []
    mt = []
    for i in search(query, stop=cantidad_fuentes, num=cantidad_fuentes, safe='on', start=0):
        fuente_datos_automatica.append(i)
    fuente_datos_automatica_ = []
    for i in fuente_datos_automatica:
        u = i.split('/')[2].split('www.')
        if len(u) > 1:
            fuente_datos_automatica_.append(u[1])
        else:
            fuente_datos_automatica_.append(u[0])
    fuente_datos = []
    for url in fuente_datos_automatica_:
        try:
            response = requests.get('http://' + url)
            soup = BeautifulSoup(response.content, features="html.parser")
            if (soup.title):
                title = soup.title.string
            else:
                title = soup.title
            meta = soup.find_all('meta')
            metas = []
            for tag in meta:
                if 'name' in tag.attrs.keys() and tag.attrs['name'].strip().lower() in ['description', 'keywords']:
                    description = tag.attrs['content']
                    metas.append(description)
            fuente_datos.append({'Url': url, 'Titulo': title, 'metadatos': metas})
            mt.append(metas)
        except Exception as exc:  # requests.exceptions.ConnectionError
            print(exc)
            pass

        for i in mt:
            if len(i) > 0:
                text += i[0]

    stopwords = set(STOPWORDS)
    if text.strip() != '':
        wordcloud = WordCloud(stopwords=stopwords, background_color="white", min_word_length=4).generate(text)
        plt.figure(figsize=(15, 10))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis("off")
        # plt.show()
        import io
        import base64
        s = io.BytesIO()
        plt.savefig(s, format='png', bbox_inches="tight")
        plt.close()
        s = base64.b64encode(s.getvalue()).decode("utf-8").replace("\n", "")
    else:
        s = ''

    data = {
        'data_sources': fuente_datos,
        'wordcloud': s
    }

    return (data)


def buscar_servicios(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content)
    url_service_1 = []
    url_service_2 = []
    for a in soup.find_all('a', href=True):
        if a['href'].__contains__('servicio') or a['href'].__contains__('servicios') or a['href'].__contains__(
                'service') or a['href'].__contains__('services'):
            if len(url_service_1) == 0:
                url_service_1.append(a['href'])
                res = requests.get(url, headers=headers)
                html_page = res.content
                soup = BeautifulSoup(html_page, 'html.parser')
                text = soup.find_all(text=True)
                output = ''
                blacklist = ['noscript', 'head', 'input', 'script', 'style', 'header', '[document]', 'html', 'meta', ]
                for t in text:
                    if t.parent.name not in blacklist:
                        output += '{} '.format(t)
                response_descr = openai.Completion.create(model="text-davinci-003", prompt=output.replace('\n',
                                                                                                          '') + " Describeme esta empresa en 100 palabras solo con el texto que te estoy dando habla en tercera persona:",
                                                          temperature=0.7, max_tokens=300, top_p=1, frequency_penalty=0,
                                                          presence_penalty=0)
                response_lista_servicios = openai.Completion.create(model="text-davinci-003",
                                                                    prompt=output.replace('\n',
                                                                                          '') + " Listame los servicios que esta empresa ofrece habla en tercera persona:",
                                                                    temperature=0.7, max_tokens=400, top_p=1,
                                                                    frequency_penalty=0, presence_penalty=0)
                response_lista_servicios_list = openai.Completion.create(model="text-davinci-003",
                                                                         prompt=response_lista_servicios['choices'][0][
                                                                                    'text'].replace('\r',
                                                                                                    '') + " lista los servicios:",
                                                                         temperature=0.7, max_tokens=400, top_p=1,
                                                                         frequency_penalty=0, presence_penalty=0)
                return {
                    'titulo': urlparse(url).netloc.split('.')[0].upper(),
                    'url': url,
                    'descripcion': response_descr['choices'][0]['text'].replace('\n', '').replace('\r', ''),
                    'servicios': response_lista_servicios_list['choices'][0]['text'].replace('\r', '')
                }
        else:
            if len(url_service_2) == 0:
                url_service_2.append(url)
                res = requests.get(url, headers=headers)
                html_page = res.content
                soup = BeautifulSoup(html_page, 'html.parser')
                text = soup.find_all(text=True)
                output = ''
                blacklist = ['noscript', 'head', 'input', 'script', 'style', 'header', '[document]', 'html', 'meta', ]
                for t in text:
                    if t.parent.name not in blacklist:
                        output += '{} '.format(t)
                output = output.replace('\n', '')
                response_descr = openai.Completion.create(model="text-davinci-003", prompt=output.replace('\n',
                                                                                                          '') + " Describeme esta empresa en 100 palabras solo con el texto que te estoy dando habla en tercera persona:",
                                                          temperature=0.7, max_tokens=300, top_p=1, frequency_penalty=0,
                                                          presence_penalty=0)
                response_lista_servicios = openai.Completion.create(model="text-davinci-003",
                                                                    prompt=output.replace('\n',
                                                                                          '') + " Listame los servicios que esta empresa ofrece habla en tercera persona:",
                                                                    temperature=0.7, max_tokens=400, top_p=1,
                                                                    frequency_penalty=0, presence_penalty=0)
                response_lista_servicios_list = openai.Completion.create(model="text-davinci-003",
                                                                         prompt=response_lista_servicios['choices'][0][
                                                                                    'text'].replace('\r',
                                                                                                    '') + " lista los servicios:",
                                                                         temperature=0.7, max_tokens=400, top_p=1,
                                                                         frequency_penalty=0, presence_penalty=0)
                return {
                    'titulo': urlparse(url).netloc.split('.')[0].upper(),
                    'url': url,
                    'descripcion': response_descr['choices'][0]['text'].replace('\n', '').replace('\r', ''),
                    'servicios': response_lista_servicios_list['choices'][0]['text'].replace('\r', '')
                }

            # ------------------------------------------------------------------------------------------------------------


def grafo():
    import json
    import networkx as nx
    import matplotlib.pyplot as plt

    # Lee la matriz de adyacencia desde un archivo JSON o cualquier otra fuente de datos
    # Por ejemplo, aquí asumimos que el JSON tiene un formato como este:
    # {
    #   "nodos": ["A", "B", "C", "D"],
    #   "matriz": [[0, 1, 1, 0],
    #              [1, 0, 1, 1],
    #              [1, 1, 0, 1],
    #              [0, 1, 1, 0]]
    # }

    with open("matriz_adyacencia.json", "r") as file:
        data = json.load(file)

    nodos = data["nodos"]
    matriz_adyacencia = data["matriz"]

    # Crea un grafo dirigido desde la matriz de adyacencia
    G = nx.DiGraph()

    # Agrega nodos al grafo
    G.add_nodes_from(nodos)

    # Agrega aristas al grafo basado en la matriz de adyacencia
    for i in range(len(nodos)):
        for j in range(len(nodos)):
            if matriz_adyacencia[i][j] == 1:
                G.add_edge(nodos[i], nodos[j])

    # Dibuja el grafo utilizando la disposición spring_layout para una mejor visualización
    pos = nx.spring_layout(G)

    # Dibuja los nodos y las aristas del grafo
    nx.draw_networkx_nodes(G, pos, node_size=700, node_color="skyblue", alpha=0.7)
    nx.draw_networkx_edges(G, pos, width=1.0, alpha=0.5, edge_color="gray")
    nx.draw_networkx_labels(G, pos, font_size=12, font_weight="bold")

    # Muestra el grafo
    plt.title("Grafo desde Matriz de Adyacencia")
    plt.axis("off")
    plt.show()
