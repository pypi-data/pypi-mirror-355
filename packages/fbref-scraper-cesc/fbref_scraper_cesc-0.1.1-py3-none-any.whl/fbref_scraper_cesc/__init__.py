"""
fbref_scraper_cesc

Librería para la extracción de datos de fútbol desde FBref mediante web scraping.
Proporciona funciones para obtener datos estructurados de jugadores, equipos y ligas,
listos para ser utilizados en análisis posteriores.
"""


from .league_manager import LeagueManager

from .player_data import (
    creacion_df_jugadores_estadistica_unica,
    creacion_df_players_torneo_fbref,
    creacion_df_porteros_torneo_fbref,
    obtener_jugadores_similares,
    obtener_tabla_datos_jugador_por90_percentiles,
    )

from .team_data import (
    obtener_tabla_liga_principal,
    obtener_tabla_equipos_estadistica_unica,
    obtener_tabla_tiros_partido,
    obtener_tabla_estadisticas_principales_partido,

    )

__all__ = [
    "LeagueManager",
    "creacion_df_jugadores_estadistica_unica",
    "creacion_df_players_torneo_fbref",
    "creacion_df_porteros_torneo_fbref",
    "obtener_jugadores_similares",
    "obtener_tabla_datos_jugador_por90_percentiles",

    "obtener_tabla_liga_principal",
    "obtener_tabla_equipos_estadistica_unica",
    "obtener_tabla_tiros_partido",
    "obtener_tabla_estadisticas_principales_partido",

    ]