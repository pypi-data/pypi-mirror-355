import requests
import pandas as pd
import numpy as np
import re
from bs4 import BeautifulSoup, Comment
import time 
import random 


#--------------------------------------------------------------------------------------


def get_players_data(url: str, metrica_general: str = None) -> pd.DataFrame | None:
    """
    Extrae una tabla de estadísticas de jugadores desde una URL de FBref (o similar) y la convierte en un DataFrame.

    La función busca la tabla oculta dentro de comentarios HTML, estructura los encabezados combinando distintos niveles,
    y devuelve los datos en formato tabular. Es útil para scraping de métricas avanzadas como shooting, passing, etc.

    Args:
        url (str): URL de la página web que contiene la tabla de estadísticas de jugadores.
        metrica_general (str, opcional): Nombre de la métrica general (por ejemplo: 'Shooting', 'Passing').
            Si no se proporciona, se intentará inferir automáticamente desde la URL.

    Return:
        pd.DataFrame | None: DataFrame con los datos de los jugadores. Retorna None si no se encuentra la tabla.
    """

    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Inferir la métrica general desde la URL si no fue proporcionada

    if metrica_general is None:
        stat_match = re.search(r'/([^/]+)/\d{4}-\d{4}/[^/]+-Stats', url)
        if stat_match:
            metrica_general = stat_match.group(1).replace('-', ' ').title()
        else:
            raise ValueError(f"❌ No se pudo extraer 'metrica_general' desde la URL: {url}")


    metrica_general_clean = metrica_general.replace(' ', '_')

    # Buscar tablas comentadas dentro del HTML

    comments = soup.find_all(string=lambda text: isinstance(text, Comment))
    player_table = None

    for comment in comments:
        comment_soup = BeautifulSoup(comment, 'html.parser')
        tables = comment_soup.find_all('table')
        for table in tables:
            if table.find('td', {'data-stat': 'player'}):
                player_table = table
                break
        if player_table:
            break

    if not player_table:
        print("No se encontró la tabla de jugadores.")
        return None, None

    
    # Procesar encabezados para construir nombres únicos de columnas

    header_rows = player_table.find('thead').find_all('tr')
    last_header_row = header_rows[-1]

    columns_data = []
    column_names = []

    for th in last_header_row.find_all('th'):
        data_stat = th.get('data-stat')
        data_over_header = th.get('data-over-header') or 'General'
        data_over_header = data_over_header.replace(' ', '_')
        metrica_general_clean = metrica_general.replace(' ', '_')
        column_name = f"{data_stat}_{data_over_header}_{metrica_general_clean}"
        column_names.append(column_name)

        columns_data.append({
            'data-stat': data_stat,
            'data-over-header': data_over_header,
            'metrica-general': metrica_general
        })

    df_columns = pd.DataFrame(columns_data)


    # Extraer filas de jugadores desde el cuerpo de la tabla

    data_rows = []
    for row in player_table.find('tbody').find_all('tr'):
        row_data = []
        for cell in row.find_all(['th', 'td']):
            cell_text = cell.get_text(strip=True)
            row_data.append(cell_text)
        if row_data:  # Evitar filas vacías
            data_rows.append(row_data)

 
     # Crear y devolver el DataFrame final

    df_players = pd.DataFrame(data_rows, columns=column_names)

    return  df_players

 #------------------------------------------------------------------------------------------------

def limpieza_df_players(df: pd.DataFrame, url: str) -> pd.DataFrame:
    """
    Limpia y normaliza un DataFrame de jugadores extraído desde FBref (u origen similar).

    La limpieza incluye:
    - Inferencia automática de la métrica general desde la URL.
    - Eliminación de columnas irrelevantes (rankings, partidos).
    - Remoción de filas de encabezados repetidos (Player, Team, Totals).
    - Normalización de la nacionalidad.
    - Inclusión de la competición si no está presente.
    - Sustitución de valores vacíos por ceros.

    Args:
        df (pd.DataFrame): DataFrame original con los datos de jugadores.
        url (str): URL desde donde se extrajo el DataFrame, usada para inferir contexto.

    Return:
        pd.DataFrame: DataFrame limpio y listo para análisis.
    """

    #Extraer la métrica general automáticamente desde la URL

    stat_match = re.search(r'/([^/]+)/\d{4}-\d{4}/[^/]+-Stats', url)
    if stat_match:
        metrica_general = stat_match.group(1).replace('-', ' ').title()
    else:
        raise ValueError(f"❌ No se pudo extraer 'metrica_general' desde la URL: {url}")


    metrica_general_clean = metrica_general.replace(' ', '_')

     
    # Eliminar columnas irrelevantes: rankings, conteos de partidos, etc.

    columns_to_drop = [
    col for col in df.columns
    if col.startswith("ranker_") or col.startswith("matches_")
    ]

    if columns_to_drop:
        df = df.drop(columns=columns_to_drop)
    
    # Eliminar filas que repiten encabezados: 'Player', 'Team', 'Totals'

    player_cols = [col for col in df.columns if col.lower().startswith('player')]
    if player_cols:
        player_col = player_cols[0]
        df = df[~df[player_col].isin(['Player', 'Team', 'Totals'])]

    # Normalizar la nacionalidad: conservar solo el código de país (ej. ESP, BRA, ARG)

    nationality_col = [col for col in df.columns if 'nationality' in col]
    if nationality_col:
        col_name = nationality_col[0]
        df[col_name] = df[col_name].astype(str).str.extract(r'([A-Z]+)$')

    # Extraer el nombre de la competición desde la URL

    competition_name_match = re.search(r'/([^/]+)-Stats(?:/|$)', url)
    if competition_name_match:
        competition_name = competition_name_match.group(1).replace('-', ' ')
    else:
        competition_name = 'Desconocida'

    # Añadir la columna de competición si no existe

    competition_col = [col for col in df.columns if 'competition' in col]
    if not competition_col:
        df['competition'] = competition_name
    
    # Normalizar valores vacíos: convertir cadenas vacías a NaN y luego a 0

    df.replace('', np.nan, inplace=True)
    df.fillna(0, inplace=True)

    #Rasetear el indice

    df.reset_index(drop=True,inplace=True)

    
    return df

#-----------------------------------------------------------------------------------------------------------------------------

def creacion_df_jugadores_estadistica_unica(url: str,guardar_csv: bool = False, league: str = 'La Liga',
        season: str = '2024', metrica_general: str = None) -> pd.DataFrame | None:
    """
    Crea un DataFrame con estadísticas individuales de jugadores a partir de una URL específica.

    La función realiza el scraping de una tabla oculta en FBref (u otra fuente estructurada), 
    la limpia y opcionalmente guarda el resultado como archivo CSV.

    Args:
        url (str): URL de la página que contiene la tabla de estadísticas individuales.
        guardar_csv (bool): Si es True, guarda el DataFrame limpio como CSV.
        league (str): Nombre de la liga (usado para nombrar el archivo CSV).
        season (str): Temporada de la liga (formato '2023' o '2023-2024').
        metrica_general (str, opcional): Nombre de la métrica general (ej: 'passing'). Si no se proporciona, se infiere desde la URL.

    Return:
        pd.DataFrame | None: DataFrame limpio con estadísticas de jugadores, o None si ocurre un error.
    """ 

    try:

       # Obtener datos de la tabla cruda

        df_sucio = get_players_data(url)
        
        # Limpiar los datos de jugadores

        df_limpio = limpieza_df_players(df_sucio,  url=url) 

        # Inferir métrica general desde la URL si no se pasó explícitamente

        if metrica_general is None:

            metrica_general_match = re.search(r'/([^/]+)/\d{4}-\d{4}/[^/]+-Stats', url)
            if metrica_general_match:
                metrica_general = metrica_general_match.group(1)
            else:
                raise ValueError(f"❌ No se pudo extraer la métrica general desde la URL: {url}")


        # Suprimir espacios en el parámetro league
        league_clean = league.lower().replace(' ', '_')

        #Remplazar el guion entre los años de la temporada por guión bajo
        season_clean = season.replace('-', '_')

        # Guardar como CSV si se indica
        if guardar_csv:
            df_limpio.to_csv(f'./df_players_{metrica_general}_{league_clean}_{season_clean}.csv', index=False)
        
        return df_limpio
    
    except Exception as e:
        print(f"❌ Error en creacion_df_jugadores_estadistica_unica para {league} - {season} - {metrica_general}: {e}")
        return None


#------------------------------------------------------------------------------------------------------------
def creacion_df_players_torneo_fbref( league: str = 'La Liga', season: str = "2024-2025", stat_list: list = None,  player_urls: dict = None, 
                guardar_csv: bool = False, guardar_csv_individuales: bool = False) -> pd.DataFrame:
    
    """
    Crea un DataFrame consolidado con estadísticas individuales de jugadores de una liga y temporada específica,
    combinando múltiples métricas desde FBref.

    La función recorre una lista de estadísticas (standard, shooting, passing, etc.), obtiene los datos desde 
    sus URLs respectivas, los limpia, concatena horizontalmente y, si se solicita, guarda el resultado como CSV.

    Args:
        league (str): Nombre de la liga (por ejemplo: 'La Liga').
        season (str): Temporada (formato 'YYYY-YYYY', por ejemplo: '2024-2025').
        stat_list (list): Lista de métricas a procesar (ejemplo: ['Shooting', 'Passing']). Si es None, se utiliza una lista por defecto.
        player_urls (dict): Diccionario anidado que contiene las URLs para cada estadística, por liga y temporada.
        guardar_csv (bool): Si es True, guarda el DataFrame combinado como archivo CSV.
        guardar_csv_individuales (bool): Si es True, guarda también los CSV individuales por métrica procesada.

    Return:
        pd.DataFrame: DataFrame final con todas las estadísticas combinadas. Devuelve un DataFrame vacío si no se pudo procesar ninguna métrica.
    """
    
    if stat_list is None:
        stat_list = ["Standard Stats", "Shooting", "Passing", "Pass Types", 
                     "Goal and Shot Creation", "Defensive Actions", 
                     "Possession", "Miscellaneous Stats"]

    dfs = []

    for stat_name in stat_list:

        # Obtener URL correspondiente a la estadística

        try:
            url_actual = player_urls[league][season][stat_name]
        except KeyError:
            print(f"⚠️ No se encontró URL para la estadística '{stat_name}'. Se omite.")
            continue
        
        try: 

            # Obtener DataFrame limpio de jugadores

            df_temp = creacion_df_jugadores_estadistica_unica(
                url=url_actual,
                guardar_csv=guardar_csv_individuales,
                league=league,
                season=season,
                metrica_general=stat_name
            )
            if df_temp is not None:
                if 'competition' in df_temp.columns:
                    df_temp = df_temp.drop(columns=['competition'])
                dfs.append(df_temp)
            else:
                print(f"⚠️ No se pudo procesar '{stat_name}'. Se omite.")
        
        except Exception as e:
            print(f"❌ Error procesando '{stat_name}' para {league} - {season}: {e}")

        # Pausa aleatoria entre requests para evitar bloqueos

        time.sleep(random.uniform(2, 5))

    # Validación: No se obtuvo ningún DataFrame

    if not dfs:
        print("⚠️ No se generó ningún DataFrame.")
        return pd.DataFrame()

    # Concatenar horizontalmente y eliminar columnas duplicadas

    df_general_final = pd.concat(dfs, axis=1)
    df_general_final = df_general_final.loc[:, ~df_general_final.columns.duplicated(keep='first')]

    # Insertar columna de competencia (liga)
    
    df_general_final.insert(3, 'competition', league)

    #Remplazar el guion entre los años de la temporada por guión bajo
    season_clean= season.replace('-', '_')

    # Guardar archivo final si se requiere
    
    if guardar_csv:
        league_clean = league.lower().replace(' ', '_')
        df_general_final.to_csv(f'estadisticas_jugadores_{league_clean}_{season_clean}.csv', index=False)


    return df_general_final
#------------------------------------------------------------------------------------------------------------

def creacion_df_porteros_torneo_fbref( league: str = 'La Liga',  season: str = "2024-2025", stat_list: list = None, player_urls: dict = None,
            guardar_csv: bool = False, guardar_csv_individuales: bool = False) -> pd.DataFrame:
    
    """
    Crea un DataFrame consolidado con estadísticas de porteros para una liga y temporada específica,
    utilizando los datos extraídos desde FBref.

    La función recorre una lista de métricas específicas de porteros (por defecto: Goalkeeping y Advanced Goalkeeping),
    obtiene los datos desde sus respectivas URLs, los limpia, concatena horizontalmente, 
    y opcionalmente guarda el resultado en archivos CSV.

    Args:
        league (str): Nombre de la liga (por ejemplo: 'La Liga').
        season (str): Temporada (formato 'YYYY-YYYY', por ejemplo: '2024-2025').
        stat_list (list): Lista de métricas de porteros a procesar. Si es None, se utilizará una lista por defecto.
        player_urls (dict): Diccionario anidado que contiene las URLs para cada estadística, por liga y temporada.
        guardar_csv (bool): Si es True, guarda el DataFrame final combinado como archivo CSV.
        guardar_csv_individuales (bool): Si es True, guarda también los CSV individuales por métrica procesada.

    Returns:
        pd.DataFrame: DataFrame final con todas las estadísticas de porteros combinadas. Devuelve un DataFrame vacío si no se pudo procesar ninguna métrica.
    """
    
    if stat_list is None:
        stat_list = ['Goalkeeping', 'Advanced Goalkeeping']

    dfs = []

    for stat_name in stat_list:

        try:

            # Obtener URL correspondiente a la estadística
            url_actual = player_urls[league][season][stat_name]
        except KeyError:
            print(f"⚠️ No se encontró URL para la estadística '{stat_name}'. Se omite.")
            continue
        
        try:

            # Obtener y limpiar el DataFrame correspondiente a la estadística

            df_temp = creacion_df_jugadores_estadistica_unica(
                url=url_actual,
                guardar_csv=guardar_csv_individuales,
                league=league,
                season=season,
                metrica_general=stat_name,
                )
            
            if df_temp is not None:
                if 'competition' in df_temp.columns:
                    df_temp = df_temp.drop(columns=['competition'])
                dfs.append(df_temp)
            else:
                print(f"⚠️ No se pudo procesar '{stat_name}'. Se omite.")
        
        except Exception as e:
            print(f"❌ Error procesando '{stat_name}' para {league} - {season}: {e}")

        # Pausa aleatoria entre requests

        time.sleep(random.uniform(2, 5))

    # Validación: no se generó ningún DataFrame

    if not dfs:
        print("⚠️ No se generó ningún DataFrame.")
        return pd.DataFrame()

    # Concatenar horizontalmente y eliminar columnas duplicadas

    df_general_final = pd.concat(dfs, axis=1)
    df_general_final = df_general_final.loc[:, ~df_general_final.columns.duplicated(keep='first')]

    # Insertar columna de competición

    df_general_final.insert(3, 'competition', league)

    #Remplazar el guion entre los años de la temporada por guión bajo

    season_clean= season.replace('-', '_')

    # Guardar CSV final si se solicitaa
    if guardar_csv:
        league_clean = league.lower().replace(' ', '_')
        df_general_final.to_csv(f'estadisticas_porteros_{league_clean}_{season_clean}.csv', index=False)


    return df_general_final

#------------------------------------------------------------------------------------------------------------

def obtener_jugadores_similares(url_jugador: str)-> pd.DataFrame:
    """
    Extrae y limpia la tabla de jugadores similares del informe de reclutamiento de un jugador en FBref.

    Args:
        url_jugador (str): URL (en inglés) del informe de reclutamiento del jugador en FBref.

    Return:
        pd.DataFrame: DataFrame limpio con los jugadores similares, sin columnas irrelevantes y con la nacionalidad normalizada.
    """
    
    #Lee todas las tablas HTML de la página del informe de reclutamiento

    tablas = pd.read_html(url_jugador)
    
    #Selecciona la segunda tabla (índice 1), que suele contener los jugadores similares

    tabla_sucia = tablas[1]
    
    #Elimina las columnas 'RL' y 'Comparar', que no aportan información relevante

    tabla_limpia = tabla_sucia.drop(columns=['Rk', 'Compare'])
    
    #Normaliza la columna de nacionalidad: extrae solo el código de país en mayúsculas
    
    nationality_col = [col for col in tabla_limpia.columns if 'Nation' in col]
    if nationality_col:
        col_name = nationality_col[0]
        tabla_limpia[col_name] = tabla_limpia[col_name].astype(str).str.extract(r'([A-Z]+)$')
    
    #Devuelve el DataFrame limpio
    
    return tabla_limpia
    

#------------------------------------------------------------------------------------------------------------

def obtener_tabla_datos_jugador_por90_percentiles(url_jugador: str)-> pd.DataFrame:
    """
    Extrae y limpia la tabla de percentiles 'Per 90' de un informe de reclutamiento de jugador en FBref.

    Args:
        url_jugador (str): URL (en inglés) del informe de reclutamiento del jugador en FBref.

    Returns:
        pd.DataFrame: DataFrame limpio con los datos de percentiles 'Per 90' del jugador.
    """


    #Lee todas las tablas HTML de la página del informe de reclutamiento

    tablas = pd.read_html(url_jugador)

    #Selecciona la tercera tabla (índice 2), que suele contener los percentiles 'Per 90'

    tabla_sucia = tablas[2]

    #Elimina el primer nivel del MultiIndex de columnas si existe

    tabla_sucia.columns = tabla_sucia.columns.droplevel(0)

    #Elimina filas completamente vacías

    tabla_sucia = tabla_sucia.dropna()

    #Filtra filas para quedarse solo con las que tienen valores numéricos en 'Per 90'

    tabla_sucia = tabla_sucia[~tabla_sucia['Per 90'].str.contains(r'[a-zA-Z]', na=False)] 

    #Limpia la columna 'Per 90': elimina el símbolo '%' y convierte a numérico

    tabla_sucia['Per 90'] = tabla_sucia['Per 90'].str.replace('%', '', regex=True)
    tabla_sucia['Per 90'] = pd.to_numeric(tabla_sucia['Per 90'], errors='coerce')

    #Convierte la columna 'Percentil' a tipo numérico

    tabla_sucia['Percentile'] = pd.to_numeric(tabla_sucia['Percentile'], errors='coerce')

    #Reinicia el índice del DataFrame limpio

    tabla_limpia = tabla_sucia.reset_index(drop=True)

    #Devuelve el DataFrame limpio
    
    return tabla_limpia 
#------------------------------------------------------------------------------------------------------------