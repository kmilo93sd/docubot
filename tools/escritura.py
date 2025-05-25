"""
Herramientas de escritura de archivos para el agente LLM.
Este módulo contiene herramientas para crear y escribir archivos Markdown y otros documentos.
"""

import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
from langchain.agents import tool

# Configurar logger específico para escritura
logger = logging.getLogger("Herramientas.Escritura")

def obtener_ruta_repositorio() -> Path:
    """
    Obtiene la ruta del repositorio configurada desde la variable de entorno.
    
    Returns:
        Path: Ruta absoluta al repositorio objetivo.
    """
    repo_path = os.getenv('DOCUMENTATOR_REPOSITORY_PATH')
    if not repo_path:
        raise ValueError("❌ No se ha configurado la ruta del repositorio. Variable DOCUMENTATOR_REPOSITORY_PATH no encontrada.")
    
    path = Path(repo_path)
    if not path.exists():
        raise ValueError(f"❌ El repositorio configurado no existe: {path}")
    
    return path

def validar_ruta_escritura_en_repositorio(ruta: str) -> Path:
    """
    Valida que una ruta de escritura esté dentro del repositorio configurado.
    Para escritura, permitimos crear archivos en el directorio actual del documentador.
    
    Args:
        ruta: Ruta a validar (puede ser relativa o absoluta).
        
    Returns:
        Path: Ruta absoluta validada para escritura.
    """
    # Para archivos de documentación, permitimos escribir en el directorio actual
    # (donde está el documentador) o en el repositorio objetivo
    
    target_path = Path(ruta)
    
    # Si es una ruta relativa, la resolvemos desde el directorio actual
    if not target_path.is_absolute():
        target_path = Path.cwd() / ruta
    
    # Resolver la ruta para eliminar .. y .
    target_path = target_path.resolve()
    
    logger.debug(f"📍 Ruta de escritura validada: {target_path}")
    
    return target_path

@tool
def escribir_markdown(ruta_archivo: str, contenido: str, sobrescribir: bool = False) -> str:
    """
    Escribe contenido en un archivo Markdown (.md) en el directorio de trabajo del documentador.
    
    Args:
        ruta_archivo: Ruta donde crear el archivo Markdown (debe terminar en .md).
        contenido: Contenido en formato Markdown a escribir en el archivo.
        sobrescribir: Si True, sobrescribe el archivo si ya existe. Si False, devuelve error si existe.
        
    Returns:
        String confirmando la creación del archivo o mensaje de error.
    """
    logger.info(f"📝 Iniciando escritura de archivo Markdown: {ruta_archivo}")
    logger.debug(f"   📏 Tamaño del contenido: {len(contenido)} caracteres")
    logger.debug(f"   🔄 Sobrescribir: {sobrescribir}")
    
    try:
        # Validar la ruta de escritura
        archivo_path = validar_ruta_escritura_en_repositorio(ruta_archivo)
        
        # Verificar que la extensión sea .md
        if archivo_path.suffix.lower() != '.md':
            logger.error(f"❌ Extensión incorrecta: {archivo_path.suffix} (debe ser .md)")
            return f"Error: El archivo debe tener extensión .md, recibido: {archivo_path.suffix}"
        
        # Verificar si el archivo ya existe
        if archivo_path.exists() and not sobrescribir:
            logger.warning(f"⚠️ Archivo ya existe y sobrescribir=False: {ruta_archivo}")
            return f"Error: El archivo '{ruta_archivo}' ya existe. Usa sobrescribir=True para reemplazarlo."
        
        # Crear directorios padre si no existen
        if not archivo_path.parent.exists():
            logger.debug(f"📁 Creando directorios padre: {archivo_path.parent}")
            archivo_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Escribir el contenido
        logger.debug("✍️ Escribiendo contenido al archivo...")
        with open(archivo_path, 'w', encoding='utf-8') as file:
            file.write(contenido)
        
        # Obtener información del archivo creado
        tamaño = archivo_path.stat().st_size
        lineas = contenido.count('\n') + 1
        
        logger.info(f"✅ Archivo creado exitosamente:")
        logger.info(f"   📄 Archivo: {archivo_path}")
        logger.info(f"   📏 Tamaño: {tamaño} bytes")
        logger.info(f"   📝 Líneas: {lineas}")
        
        resultado = f"✅ Archivo Markdown creado exitosamente:\n\n"
        resultado += f"📄 Archivo: {archivo_path}\n"
        resultado += f"📏 Tamaño: {tamaño} bytes\n"
        resultado += f"📝 Líneas: {lineas}\n"
        resultado += f"📁 Directorio: {archivo_path.parent}\n"
        resultado += f"🕒 Creado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        if sobrescribir and archivo_path.exists():
            resultado += f"⚠️  Archivo existente fue sobrescrito.\n"
            logger.info("🔄 Archivo existente sobrescrito")
        
        return resultado
        
    except ValueError as e:
        logger.error(f"❌ Error de validación: {str(e)}")
        return str(e)
    except PermissionError:
        logger.error(f"❌ Sin permisos para escribir: {ruta_archivo}")
        return f"Error: Sin permisos para escribir en '{ruta_archivo}'."
    except Exception as e:
        logger.error(f"❌ Error inesperado: {str(e)}")
        return f"Error inesperado al escribir '{ruta_archivo}': {str(e)}"


@tool
def crear_documentacion_repositorio(nombre_archivo: str = "ANALISIS_REPOSITORIO.md") -> str:
    """
    Crea un archivo de documentación completo del repositorio basado en análisis automático.
    
    Args:
        nombre_archivo: Nombre del archivo de documentación a crear.
        
    Returns:
        String confirmando la creación del archivo de documentación.
    """
    logger.info(f"📋 Creando documentación del repositorio: {nombre_archivo}")
    
    try:
        # Obtener la ruta del repositorio
        repo_path = obtener_ruta_repositorio()
        
        # Importar herramientas necesarias
        from tools.estadisticas import estadisticas_repositorio
        from tools.navegacion import listar_directorio, encontrar_archivos
        
        logger.debug("📊 Obteniendo estadísticas del repositorio...")
        # Obtener estadísticas del repositorio (usando "." como directorio base relativo)
        stats = estadisticas_repositorio(".")
        
        logger.debug("📁 Obteniendo estructura principal...")
        # Obtener estructura principal
        estructura = listar_directorio(".")
        
        logger.debug("🔍 Buscando archivos importantes...")
        # Buscar archivos importantes
        archivos_config = encontrar_archivos("*.json", ".")
        archivos_python = encontrar_archivos("*.py", ".")
        archivos_readme = encontrar_archivos("README*", ".")
        archivos_typescript = encontrar_archivos("**/*.ts", ".")
        archivos_react = encontrar_archivos("**/*.tsx", ".")
        
        # Generar contenido del documento
        contenido = f"""# Análisis del Repositorio

*Documento generado automáticamente el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

**Repositorio analizado:** `{repo_path}`

## 📊 Estadísticas Generales

{stats}

## 📁 Estructura Principal

{estructura}

## 🔧 Archivos de Configuración

{archivos_config}

## 🐍 Archivos Python

{archivos_python}

## 📘 Archivos TypeScript

{archivos_typescript}

## ⚛️ Componentes React

{archivos_react}

## 📖 Documentación Existente

{archivos_readme}

## 🔍 Análisis Detallado

### Tecnologías Detectadas

- **Repositorio objetivo**: {repo_path}
- **Análisis automático**: Herramientas de navegación y estadísticas
- **Documentación**: Generación automática de manuales funcionales

### Arquitectura del Análisis

Este análisis fue realizado por un agente automatizado que:

1. **Exploración**: Navega por la estructura del repositorio
2. **Análisis**: Examina archivos y extrae información relevante
3. **Documentación**: Genera manuales funcionales orientados al negocio
4. **Estadísticas**: Proporciona métricas del código

### Próximos Pasos

- ✅ Análisis de estructura completado
- 🔄 Análisis funcional por módulos en progreso
- 📝 Generación de documentación específica por funcionalidad

---

*Este documento fue generado automáticamente por el agente de análisis de código.*
"""
        
        logger.debug("✍️ Escribiendo archivo de documentación...")
        # Escribir el archivo
        resultado_escritura = escribir_markdown(nombre_archivo, contenido, sobrescribir=True)
        
        logger.info("✅ Documentación del repositorio creada exitosamente")
        
        return f"📋 Documentación del repositorio creada:\n\n{resultado_escritura}"
        
    except Exception as e:
        logger.error(f"❌ Error al crear documentación: {str(e)}")
        return f"Error al crear documentación del repositorio: {str(e)}"


@tool
def crear_reporte_analisis(titulo: str, contenido_analisis: str, ruta_archivo: str = None) -> str:
    """
    Crea un reporte de análisis en formato Markdown con estructura profesional.
    
    Args:
        titulo: Título del reporte de análisis.
        contenido_analisis: Contenido principal del análisis.
        ruta_archivo: Ruta del archivo (opcional, se genera automáticamente si no se proporciona).
        
    Returns:
        String confirmando la creación del reporte.
    """
    try:
        # Generar nombre de archivo automáticamente si no se proporciona
        if ruta_archivo is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            titulo_archivo = titulo.lower().replace(' ', '_').replace('/', '_')
            ruta_archivo = f"reporte_{titulo_archivo}_{timestamp}.md"
        
        # Generar contenido del reporte
        contenido = f"""# {titulo}

**Fecha de análisis**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Generado por**: Agente de Análisis de Código

---

## 📋 Resumen Ejecutivo

{contenido_analisis}

## 🔍 Detalles del Análisis

### Metodología

Este análisis fue realizado utilizando:
- Búsqueda semántica en base de datos vectorial
- Análisis estático de código
- Exploración sistemática del repositorio
- Herramientas automatizadas de análisis

### Hallazgos Principales

{contenido_analisis}

## 📊 Métricas y Estadísticas

*Las métricas específicas se incluyen en el contenido del análisis arriba.*

## 🎯 Conclusiones

Este reporte proporciona una visión detallada basada en el análisis automatizado del código y la estructura del repositorio.

## 📝 Notas Adicionales

- Este reporte fue generado automáticamente
- Para análisis más específicos, consulte con el agente usando consultas dirigidas
- Los resultados se basan en el estado actual del repositorio

---

*Reporte generado por el Sistema de Análisis de Código Automatizado*
"""
        
        # Escribir el archivo
        resultado_escritura = escribir_markdown(ruta_archivo, contenido, sobrescribir=True)
        
        return f"📊 Reporte de análisis creado:\n\n{resultado_escritura}"
        
    except Exception as e:
        return f"Error al crear reporte de análisis: {str(e)}"


@tool
def agregar_contenido_markdown(ruta_archivo: str, nuevo_contenido: str, posicion: str = "final") -> str:
    """
    Agrega contenido a un archivo Markdown existente.
    
    Args:
        ruta_archivo: Ruta al archivo Markdown existente.
        nuevo_contenido: Contenido a agregar al archivo.
        posicion: Dónde agregar el contenido ("inicio", "final").
        
    Returns:
        String confirmando la adición del contenido.
    """
    try:
        archivo_path = Path(ruta_archivo)
        
        # Verificar que el archivo existe
        if not archivo_path.exists():
            return f"Error: El archivo '{ruta_archivo}' no existe."
        
        # Verificar que es un archivo Markdown
        if archivo_path.suffix.lower() != '.md':
            return f"Error: El archivo debe ser .md, encontrado: {archivo_path.suffix}"
        
        # Leer contenido existente
        with open(archivo_path, 'r', encoding='utf-8') as file:
            contenido_existente = file.read()
        
        # Agregar nuevo contenido según la posición
        if posicion.lower() == "inicio":
            contenido_final = nuevo_contenido + "\n\n" + contenido_existente
        else:  # final por defecto
            contenido_final = contenido_existente + "\n\n" + nuevo_contenido
        
        # Escribir el contenido actualizado
        with open(archivo_path, 'w', encoding='utf-8') as file:
            file.write(contenido_final)
        
        # Obtener información actualizada
        tamaño = archivo_path.stat().st_size
        lineas = contenido_final.count('\n') + 1
        
        resultado = f"✅ Contenido agregado exitosamente:\n\n"
        resultado += f"📄 Archivo: {ruta_archivo}\n"
        resultado += f"📏 Nuevo tamaño: {tamaño} bytes\n"
        resultado += f"📝 Líneas totales: {lineas}\n"
        resultado += f"📍 Posición: {posicion}\n"
        resultado += f"🕒 Actualizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        return resultado
        
    except PermissionError:
        return f"Error: Sin permisos para modificar '{ruta_archivo}'."
    except Exception as e:
        return f"Error inesperado al agregar contenido a '{ruta_archivo}': {str(e)}"


@tool
def crear_indice_archivos(directorio_base: str = ".", patron_archivos: str = "*.md", nombre_indice: str = "INDICE.md") -> str:
    """
    Crea un índice de archivos Markdown en el directorio especificado.
    
    Args:
        directorio_base: Directorio donde buscar archivos.
        patron_archivos: Patrón de archivos a incluir en el índice.
        nombre_indice: Nombre del archivo de índice a crear.
        
    Returns:
        String confirmando la creación del índice.
    """
    try:
        from tools.navegacion import encontrar_archivos
        
        # Buscar archivos que coincidan con el patrón
        archivos_encontrados = encontrar_archivos(patron_archivos, directorio_base)
        
        # Generar contenido del índice
        contenido = f"""# Índice de Archivos

*Índice generado automáticamente el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

## 📚 Archivos Encontrados

Patrón de búsqueda: `{patron_archivos}`  
Directorio base: `{directorio_base}`

{archivos_encontrados}

## 🔗 Enlaces Rápidos

"""
        
        # Agregar enlaces a los archivos encontrados (si es posible extraerlos)
        base_path = Path(directorio_base)
        try:
            archivos = list(base_path.glob(patron_archivos))
            if archivos:
                contenido += "### Archivos de Documentación\n\n"
                for archivo in archivos:
                    if archivo.name != nombre_indice:  # No incluir el propio índice
                        ruta_relativa = archivo.relative_to(base_path)
                        nombre_sin_extension = archivo.stem.replace('_', ' ').replace('-', ' ').title()
                        contenido += f"- [{nombre_sin_extension}]({ruta_relativa})\n"
        except:
            pass
        
        contenido += f"""

---

*Este índice fue generado automáticamente por el agente de análisis de código.*
*Para actualizar este índice, ejecuta nuevamente la herramienta crear_indice_archivos.*
"""
        
        # Escribir el archivo de índice
        resultado_escritura = escribir_markdown(nombre_indice, contenido, sobrescribir=True)
        
        return f"📑 Índice de archivos creado:\n\n{resultado_escritura}"
        
    except Exception as e:
        return f"Error al crear índice de archivos: {str(e)}" 