#!/usr/bin/env python3
"""
Configuración de logging para el agente documentador.
Permite ajustar fácilmente los niveles de verbosidad.
"""

import logging

# Configuración de niveles de logging
LOGGING_CONFIG = {
    # Nivel general del agente (DEBUG, INFO, WARNING, ERROR)
    "AGENT_LEVEL": logging.INFO,
    
    # Nivel para la consola (lo que se muestra en pantalla)
    "CONSOLE_LEVEL": logging.INFO,
    
    # Nivel para el archivo de log (más detallado)
    "FILE_LEVEL": logging.DEBUG,
    
    # Nivel para herramientas (búsquedas, lecturas de archivos, etc.)
    "TOOLS_LEVEL": logging.INFO,
    
    # Nivel para el pensamiento del agente
    "THINKING_LEVEL": logging.INFO,
    
    # Suprimir logs verbosos de librerías externas
    "SUPPRESS_EXTERNAL_LIBS": True,
    
    # Mostrar progreso simplificado en consola
    "SIMPLE_PROGRESS": True,
    
    # Formato de timestamp para consola (más corto)
    "CONSOLE_TIME_FORMAT": "%H:%M:%S",
    
    # Formato de timestamp para archivo (completo)
    "FILE_TIME_FORMAT": "%Y-%m-%d %H:%M:%S"
}

# Configuración para modo debug (más verboso)
DEBUG_CONFIG = {
    "AGENT_LEVEL": logging.DEBUG,
    "CONSOLE_LEVEL": logging.DEBUG,
    "FILE_LEVEL": logging.DEBUG,
    "TOOLS_LEVEL": logging.DEBUG,
    "THINKING_LEVEL": logging.DEBUG,
    "SUPPRESS_EXTERNAL_LIBS": False,
    "SIMPLE_PROGRESS": False,
    "CONSOLE_TIME_FORMAT": "%H:%M:%S",
    "FILE_TIME_FORMAT": "%Y-%m-%d %H:%M:%S"
}

# Configuración para modo silencioso (mínimo output)
QUIET_CONFIG = {
    "AGENT_LEVEL": logging.WARNING,
    "CONSOLE_LEVEL": logging.WARNING,
    "FILE_LEVEL": logging.INFO,
    "TOOLS_LEVEL": logging.WARNING,
    "THINKING_LEVEL": logging.WARNING,
    "SUPPRESS_EXTERNAL_LIBS": True,
    "SIMPLE_PROGRESS": True,
    "CONSOLE_TIME_FORMAT": "%H:%M:%S",
    "FILE_TIME_FORMAT": "%Y-%m-%d %H:%M:%S"
}

def get_config(mode: str = "normal"):
    """
    Obtiene la configuración de logging según el modo especificado.
    
    Args:
        mode: "normal", "debug", o "quiet"
    
    Returns:
        dict: Configuración de logging
    """
    if mode == "debug":
        return DEBUG_CONFIG
    elif mode == "quiet":
        return QUIET_CONFIG
    else:
        return LOGGING_CONFIG 