import requests
import pandas as pd
import numpy as np
import re
from bs4 import BeautifulSoup, Comment
from functools import reduce
import time


def obtener_tabla_liga_principal(url_general: str) -> pd.DataFrame:
    """
    Extrae y limpia la tabla clasificatoria de una liga desde FBref.

    Args:
        url_general (str): URL (en inglés) de la página de clasificación de una liga en FBref.

    Return:
        pd.DataFrame: DataFrame limpio con la tabla clasificatoria, 
                      renombrando la columna 'Rk' a 'Position' y eliminando la columna 'Notes'.
    """
    try:
        tablas = pd.read_html(url_general)
        tabla = tablas[0]
        tabla = tabla.rename(columns={'Rk': 'Position'})
        if 'Notes' in tabla.columns:
            tabla = tabla.drop(columns=['Notes'])
        return tabla
    except Exception as e:
        print(f"[ERROR] No se pudo obtener la tabla principal de liga desde {url_general}: {e}")
        return pd.DataFrame()
#-------------------------------------------------------------------------------------------------------------

def obtener_tabla_equipos_estadistica_unica( url_general: str,  stats_vs: bool = False,   guardar_csv: bool = False,
    league: str = 'La Liga', season: str = '2024') -> pd.DataFrame:
    """
    Descarga y limpia la tabla de estadísticas de equipos desde una URL de FBref.

    Args:
        url_general (str): URL de la tabla de FBref.
        stats_vs (bool): True si la tabla deseada es la segunda (vs) en la página.
        guardar_csv (bool): True para guardar la tabla limpia en CSV.
        league (str): Nombre de la liga.
        season (str): Temporada.

    Returns:
        pd.DataFrame: Tabla limpia con columnas renombradas.
    """

    try:
        tablas = pd.read_html(url_general)
        df = tablas[1] if stats_vs else tablas[0]

        # Definir metrica_general siempre
        metrica_general = url_general.split('/')[-3].replace('-', '_').lower()

        # Procesar MultiIndex de columnas si existe
        if isinstance(df.columns, pd.MultiIndex):
            nuevas_columnas = []
            for col in df.columns:
                over_header = col[0].strip().replace(' ', '_').lower()
                data_stat = col[1].strip().replace(' ', '_').lower()
                nuevas_columnas.append(f"{data_stat}_{over_header}_{metrica_general}")

            df.columns = nuevas_columnas

        # Eliminar filas que contengan títulos o vacías
        if any(df.iloc[:, 0].astype(str).str.contains('Squad', case=False, na=False)):
            df = df[~df.iloc[:, 0].astype(str).str.contains('Squad', case=False, na=False)].copy()

        df.reset_index(drop=True, inplace=True)

    
        # Guardar CSV si solicitado
        if guardar_csv:
            league_clean = league.lower().replace(' ', '_')
            prefijo_vs = 'vs_' if stats_vs else ''
            nombre_archivo = f'./df_equipos_{prefijo_vs}{metrica_general}_{league_clean}_{season}.csv'
            df.to_csv(nombre_archivo, index=False)

        return df
    
    except Exception as e:
        print(f"[ERROR] Fallo al obtener estadísticas de equipos desde {url_general}: {e}")
        return pd.DataFrame()


#-----------------------------------------------------------------------------------------------------------------------------

def obtener_tabla_tiros_partido( url_partido: str,   tiros_por_equipo: bool = False) -> tuple[pd.DataFrame, pd.DataFrame | None, pd.DataFrame | None]:
    """
    Extrae las tablas de tiros de un partido de fútbol desde la URL de FBref.

    Args:
        url_partido (str): URL de la página del partido en FBref.
        tiros_por_equipo (bool): Si True, devuelve también tablas individuales de tiros por equipo.

    Return:
        tuple:
            - pd.DataFrame: Tabla de tiros general (ambos equipos).
            - pd.DataFrame | None: Tabla tiros equipo local (si se solicita).
            - pd.DataFrame | None: Tabla tiros equipo visitante (si se solicita).
    """
    try:
        tablas = pd.read_html(url_partido)

        # La tabla general está en el índice 17 (puede cambiar si FBref actualiza la página)
        tabla_tiros = tablas[17]
        tabla_tiros.columns = tabla_tiros.columns.droplevel(0)
    

        tabla_local = None
        tabla_visitante = None

        if tiros_por_equipo:
            tabla_local = tablas[18]
            tabla_local.columns = tabla_local.columns.droplevel(0)

            tabla_visitante = tablas[19]
            tabla_visitante.columns = tabla_visitante.columns.droplevel(0)

        return tabla_tiros, tabla_local, tabla_visitante
    
    except Exception as e:
        print(f"[ERROR] No se pudo obtener la tabla de tiros desde {url_partido}: {e}")
        return pd.DataFrame(), None, None
    
#-----------------------------------------------------------------------------------------------------------------------------

def limpiar_df_estadisticas_partido(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpia y normaliza un DataFrame de estadísticas de partido.

    - Extrae el código de nacionalidad en mayúsculas si existe.
    - Extrae la edad como número entero antes de un guion si existe.

    Args:
        df (pd.DataFrame): DataFrame original con estadísticas de partido.

    Return:
        pd.DataFrame: DataFrame limpio y normalizado.
    """
    columnas_lower = [col.lower() for col in df.columns]

    # Procesar columna de nacionalidad
    cols_nacion = [df.columns[i] for i, col in enumerate(columnas_lower) if 'nation' in col]
    if cols_nacion:
        col = cols_nacion[0]
        df[col] = df[col].astype(str).str.extract(r'([A-Z]+)$')

    # Procesar columna de edad
    cols_edad = [df.columns[i] for i, col in enumerate(columnas_lower) if 'age' in col]
    if cols_edad:
        col = cols_edad[0]
        df[col] = df[col].astype(str).str.split('-').str[0]

    return df

def bajada_nivel_porteros(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza columnas de un DataFrame de porteros, bajando nivel de MultiIndex si existe.

    Args:
        df (pd.DataFrame): DataFrame con columnas MultiIndex o normales.

    Return:
        pd.DataFrame: DataFrame con columnas normalizadas a un solo nivel.
    """
    if isinstance(df.columns, pd.MultiIndex):
        nuevas_columnas = []
        for col in df.columns:
            over_header = str(col[0]).strip().replace(' ', '_').lower()
            data_stat = str(col[1]).strip().replace(' ', '_').lower()
            nuevas_columnas.append(f"{data_stat}_{over_header}")
        df.columns = nuevas_columnas
    else:
        df.columns = [str(col).strip().replace(' ', '_').lower() for col in df.columns]
    return df

def obtener_tabla_estadisticas_principales_partido(url_partido: str,    keepers: bool = False
        ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame | None, pd.DataFrame | None]:
    """
    Extrae y limpia las estadísticas principales de un partido de fútbol desde FBref.

    Args:
        url_partido (str): URL de la página del partido en FBref.
        keepers (bool): Extraer estadísticas de porteros si True.

    Return:
        tuple:
            - estadisticas_local (pd.DataFrame): Estadísticas equipo local.
            - estadisticas_visitante (pd.DataFrame): Estadísticas equipo visitante.
            - keeper_local (pd.DataFrame | None): Estadísticas portero local.
            - keeper_visitante (pd.DataFrame | None): Estadísticas portero visitante.
    """

    try:
        tablas = pd.read_html(url_partido)

        # Estadísticas equipo local
        estad_local = tablas[3]
        estad_local.columns = estad_local.columns.droplevel(0)
        estad_local = estad_local.iloc[:-1, :].copy()
        estad_local = limpiar_df_estadisticas_partido(estad_local)

        # Estadísticas equipo visitante
        estad_visit = tablas[10]
        estad_visit.columns = estad_visit.columns.droplevel(0)
        estad_visit = estad_visit.iloc[:-1, :].copy()
        estad_visit = limpiar_df_estadisticas_partido(estad_visit)

        keeper_local = None
        keeper_visitante = None

        if keepers:
            keeper_local_raw = tablas[9]
            keeper_local = bajada_nivel_porteros(keeper_local_raw)
            keeper_local = limpiar_df_estadisticas_partido(keeper_local)

            keeper_visitante_raw = tablas[16]
            keeper_visitante = bajada_nivel_porteros(keeper_visitante_raw)
            keeper_visitante = limpiar_df_estadisticas_partido(keeper_visitante)

        return estad_local, estad_visit, keeper_local, keeper_visitante
    
    except Exception as e:
        print(f"[ERROR] Fallo al obtener estadísticas principales del partido desde {url_partido}: {e}")
        return pd.DataFrame(), pd.DataFrame(), None, None















