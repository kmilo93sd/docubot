"""
Paquete de herramientas para el agente LLM.
Este paquete contiene todos los módulos con herramientas disponibles para ser utilizadas por el agente.
"""

# Importar herramientas de búsqueda semántica
from tools.busqueda import buscar_codigo

# Importar herramientas de navegación del sistema de archivos
from tools.navegacion import (
    obtener_archivo,
    listar_directorio,
    encontrar_archivos,
    obtener_metadatos_archivo
)

# Importar herramientas de estadísticas y análisis
from tools.estadisticas import (
    estadisticas_repositorio,
    buscar_referencias,
    analizar_importaciones
)

# Importar herramientas de escritura de archivos
from tools.escritura import (
    escribir_markdown,
    crear_documentacion_repositorio,
    crear_reporte_analisis,
    agregar_contenido_markdown,
    crear_indice_archivos
)

# Lista de todas las herramientas disponibles para el agente
all_tools = [
    # Búsqueda semántica
    buscar_codigo,
    
    # Navegación del sistema de archivos
    obtener_archivo,
    listar_directorio,
    encontrar_archivos,
    obtener_metadatos_archivo,
    
    # Estadísticas y análisis
    estadisticas_repositorio,
    buscar_referencias,
    analizar_importaciones,
    
    # Escritura de archivos
    escribir_markdown,
    crear_documentacion_repositorio,
    crear_reporte_analisis,
    agregar_contenido_markdown,
    crear_indice_archivos
] 