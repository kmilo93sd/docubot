"""
Herramientas de navegación del sistema de archivos para el agente LLM.
Este módulo contiene herramientas para explorar y navegar por el repositorio de código.
"""

import os
import glob
import logging
from pathlib import Path
from typing import List, Dict
from langchain.agents import tool

# Configurar logger específico para navegación
logger = logging.getLogger("Herramientas.Navegacion")

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

def validar_ruta_en_repositorio(ruta: str) -> Path:
    """
    Valida que una ruta esté dentro del repositorio configurado.
    
    Args:
        ruta: Ruta a validar (puede ser relativa o absoluta).
        
    Returns:
        Path: Ruta absoluta validada dentro del repositorio.
        
    Raises:
        ValueError: Si la ruta está fuera del repositorio.
    """
    repo_path = obtener_ruta_repositorio()
    
    # Convertir la ruta a Path
    if Path(ruta).is_absolute():
        target_path = Path(ruta)
    else:
        # Si es relativa, la resolvemos desde el repositorio
        target_path = repo_path / ruta
    
    # Resolver la ruta para eliminar .. y .
    target_path = target_path.resolve()
    
    # Verificar que esté dentro del repositorio
    try:
        target_path.relative_to(repo_path)
    except ValueError:
        raise ValueError(f"❌ Acceso denegado: La ruta '{ruta}' está fuera del repositorio permitido: {repo_path}")
    
    return target_path

@tool
def obtener_archivo(ruta_archivo: str) -> str:
    """
    Obtiene el contenido completo de un archivo específico dentro del repositorio.
    
    Args:
        ruta_archivo: Ruta relativa al archivo dentro del repositorio que se quiere leer.
        
    Returns:
        String con el contenido completo del archivo o mensaje de error.
    """
    logger.info(f"📖 Leyendo archivo: {ruta_archivo}")
    
    try:
        # Validar que la ruta esté dentro del repositorio
        archivo_path = validar_ruta_en_repositorio(ruta_archivo)
        
        logger.debug(f"📍 Ruta absoluta validada: {archivo_path}")
        
        # Verificar que el archivo existe
        if not archivo_path.exists():
            logger.error(f"❌ Archivo no existe: {ruta_archivo}")
            return f"Error: El archivo '{ruta_archivo}' no existe en el repositorio."
        
        # Verificar que es un archivo (no un directorio)
        if not archivo_path.is_file():
            logger.error(f"❌ No es un archivo válido: {ruta_archivo}")
            return f"Error: '{ruta_archivo}' no es un archivo válido."
        
        # Leer el contenido del archivo
        logger.debug("📄 Leyendo contenido del archivo...")
        with open(archivo_path, 'r', encoding='utf-8') as file:
            contenido = file.read()
        
        # Información adicional sobre el archivo
        tamaño = archivo_path.stat().st_size
        lineas = contenido.count('\n') + 1
        
        # Calcular ruta relativa desde el repositorio
        repo_path = obtener_ruta_repositorio()
        ruta_relativa = archivo_path.relative_to(repo_path)
        
        logger.info(f"✅ Archivo leído exitosamente:")
        logger.info(f"   📏 Tamaño: {tamaño} bytes")
        logger.info(f"   📝 Líneas: {lineas}")
        
        resultado = f"=== Archivo: {ruta_relativa} ===\n"
        resultado += f"Tamaño: {tamaño} bytes | Líneas: {lineas}\n"
        resultado += f"{'='*50}\n\n"
        resultado += contenido
        
        return resultado
        
    except ValueError as e:
        logger.error(f"❌ Error de validación: {str(e)}")
        return str(e)
    except UnicodeDecodeError:
        logger.error(f"❌ Error de codificación: {ruta_archivo}")
        return f"Error: No se puede leer '{ruta_archivo}' - archivo binario o codificación no compatible."
    except PermissionError:
        logger.error(f"❌ Sin permisos de lectura: {ruta_archivo}")
        return f"Error: Sin permisos para leer '{ruta_archivo}'."
    except Exception as e:
        logger.error(f"❌ Error inesperado: {str(e)}")
        return f"Error inesperado al leer '{ruta_archivo}': {str(e)}"


@tool
def listar_directorio(ruta_directorio: str = ".") -> str:
    """
    Muestra los archivos y subdirectorios en un directorio específico dentro del repositorio.
    
    Args:
        ruta_directorio: Ruta relativa del directorio a listar dentro del repositorio (por defecto la raíz del repositorio).
        
    Returns:
        String con la lista de archivos y directorios organizados.
    """
    logger.info(f"📁 Listando directorio: {ruta_directorio}")
    
    try:
        # Validar que la ruta esté dentro del repositorio
        dir_path = validar_ruta_en_repositorio(ruta_directorio)
        
        logger.debug(f"📍 Ruta absoluta validada: {dir_path}")
        
        # Verificar que el directorio existe
        if not dir_path.exists():
            logger.error(f"❌ Directorio no existe: {ruta_directorio}")
            return f"Error: El directorio '{ruta_directorio}' no existe en el repositorio."
        
        # Verificar que es un directorio
        if not dir_path.is_dir():
            logger.error(f"❌ No es un directorio válido: {ruta_directorio}")
            return f"Error: '{ruta_directorio}' no es un directorio válido."
        
        # Obtener lista de elementos
        logger.debug("🔍 Escaneando contenido del directorio...")
        elementos = list(dir_path.iterdir())
        
        # Separar directorios y archivos
        directorios = [elem for elem in elementos if elem.is_dir()]
        archivos = [elem for elem in elementos if elem.is_file()]
        
        # Ordenar alfabéticamente
        directorios.sort(key=lambda x: x.name.lower())
        archivos.sort(key=lambda x: x.name.lower())
        
        # Calcular ruta relativa desde el repositorio
        repo_path = obtener_ruta_repositorio()
        ruta_relativa = dir_path.relative_to(repo_path) if dir_path != repo_path else Path(".")
        
        logger.info(f"✅ Directorio escaneado:")
        logger.info(f"   📁 Subdirectorios: {len(directorios)}")
        logger.info(f"   📄 Archivos: {len(archivos)}")
        
        # Construir resultado
        resultado = f"=== Contenido de: {ruta_relativa} ===\n\n"
        
        # Mostrar directorios
        if directorios:
            resultado += "📁 DIRECTORIOS:\n"
            for directorio in directorios:
                resultado += f"  📁 {directorio.name}/\n"
            resultado += "\n"
        
        # Mostrar archivos
        if archivos:
            resultado += "📄 ARCHIVOS:\n"
            for archivo in archivos:
                tamaño = archivo.stat().st_size
                extension = archivo.suffix
                resultado += f"  📄 {archivo.name} ({tamaño} bytes) {extension}\n"
        
        if not directorios and not archivos:
            resultado += "El directorio está vacío.\n"
        
        resultado += f"\nTotal: {len(directorios)} directorios, {len(archivos)} archivos"
        
        return resultado
        
    except ValueError as e:
        logger.error(f"❌ Error de validación: {str(e)}")
        return str(e)
    except PermissionError:
        logger.error(f"❌ Sin permisos de acceso: {ruta_directorio}")
        return f"Error: Sin permisos para acceder al directorio '{ruta_directorio}'."
    except Exception as e:
        logger.error(f"❌ Error inesperado: {str(e)}")
        return f"Error inesperado al listar '{ruta_directorio}': {str(e)}"


@tool
def encontrar_archivos(patron: str, directorio_base: str = ".") -> str:
    """
    Busca archivos que coincidan con un patrón glob específico dentro del repositorio.
    
    Args:
        patron: Patrón glob para buscar archivos (ej: "*.py", "**/*.tsx", "test_*.js").
        directorio_base: Directorio relativo donde iniciar la búsqueda dentro del repositorio (por defecto la raíz).
        
    Returns:
        String con la lista de archivos encontrados que coinciden con el patrón.
    """
    logger.info(f"🔍 Buscando archivos con patrón: {patron} en {directorio_base}")
    
    try:
        # Validar que la ruta esté dentro del repositorio
        base_path = validar_ruta_en_repositorio(directorio_base)
        
        logger.debug(f"📍 Ruta base validada: {base_path}")
        
        # Verificar que el directorio base existe
        if not base_path.exists():
            return f"Error: El directorio base '{directorio_base}' no existe en el repositorio."
        
        if not base_path.is_dir():
            return f"Error: '{directorio_base}' no es un directorio válido."
        
        # Buscar archivos usando glob
        logger.debug(f"🎯 Ejecutando búsqueda con patrón: {patron}")
        archivos_encontrados = list(base_path.glob(patron))
        
        # Filtrar solo archivos (no directorios)
        archivos = [archivo for archivo in archivos_encontrados if archivo.is_file()]
        
        # Ordenar por ruta
        archivos.sort(key=lambda x: str(x))
        
        # Calcular rutas relativas desde el repositorio
        repo_path = obtener_ruta_repositorio()
        
        logger.info(f"✅ Búsqueda completada: {len(archivos)} archivos encontrados")
        
        # Construir resultado
        resultado = f"=== Búsqueda: '{patron}' en '{directorio_base}' ===\n\n"
        
        if archivos:
            resultado += f"Se encontraron {len(archivos)} archivos:\n\n"
            
            for archivo in archivos:
                # Calcular ruta relativa desde el repositorio
                try:
                    ruta_relativa = archivo.relative_to(repo_path)
                except ValueError:
                    ruta_relativa = archivo
                
                tamaño = archivo.stat().st_size
                extension = archivo.suffix
                resultado += f"📄 {ruta_relativa} ({tamaño} bytes) {extension}\n"
        else:
            resultado += f"No se encontraron archivos que coincidan con el patrón '{patron}'."
        
        return resultado
        
    except ValueError as e:
        logger.error(f"❌ Error de validación: {str(e)}")
        return str(e)
    except Exception as e:
        logger.error(f"❌ Error inesperado: {str(e)}")
        return f"Error inesperado al buscar archivos: {str(e)}"


@tool
def obtener_metadatos_archivo(ruta_archivo: str) -> str:
    """
    Obtiene información detallada (metadatos) sobre un archivo específico dentro del repositorio.
    
    Args:
        ruta_archivo: Ruta relativa al archivo dentro del repositorio del cual obtener metadatos.
        
    Returns:
        String con información detallada del archivo.
    """
    logger.info(f"📊 Obteniendo metadatos de: {ruta_archivo}")
    
    try:
        # Validar que la ruta esté dentro del repositorio
        archivo_path = validar_ruta_en_repositorio(ruta_archivo)
        
        logger.debug(f"📍 Ruta absoluta validada: {archivo_path}")
        
        # Verificar que el archivo existe
        if not archivo_path.exists():
            logger.error(f"❌ Archivo no existe: {ruta_archivo}")
            return f"Error: El archivo '{ruta_archivo}' no existe en el repositorio."
        
        # Verificar que es un archivo
        if not archivo_path.is_file():
            logger.error(f"❌ No es un archivo válido: {ruta_archivo}")
            return f"Error: '{ruta_archivo}' no es un archivo válido."
        
        # Obtener estadísticas del archivo
        stats = archivo_path.stat()
        
        # Calcular ruta relativa desde el repositorio
        repo_path = obtener_ruta_repositorio()
        ruta_relativa = archivo_path.relative_to(repo_path)
        
        # Información básica
        resultado = f"=== Metadatos de: {ruta_relativa} ===\n\n"
        resultado += f"📄 Nombre: {archivo_path.name}\n"
        resultado += f"📁 Directorio: {ruta_relativa.parent}\n"
        resultado += f"🔗 Ruta en repositorio: {ruta_relativa}\n"
        resultado += f"📏 Tamaño: {stats.st_size} bytes\n"
        resultado += f"🏷️  Extensión: {archivo_path.suffix}\n"
        
        # Fechas (convertir timestamps a formato legible)
        import datetime
        fecha_modificacion = datetime.datetime.fromtimestamp(stats.st_mtime)
        fecha_acceso = datetime.datetime.fromtimestamp(stats.st_atime)
        fecha_creacion = datetime.datetime.fromtimestamp(stats.st_ctime)
        
        resultado += f"📅 Última modificación: {fecha_modificacion.strftime('%Y-%m-%d %H:%M:%S')}\n"
        resultado += f"👁️  Último acceso: {fecha_acceso.strftime('%Y-%m-%d %H:%M:%S')}\n"
        resultado += f"🆕 Creación: {fecha_creacion.strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        # Información adicional para archivos de texto
        try:
            with open(archivo_path, 'r', encoding='utf-8') as file:
                contenido = file.read()
                lineas = contenido.count('\n') + 1
                caracteres = len(contenido)
                palabras = len(contenido.split())
                
                resultado += f"\n📊 ESTADÍSTICAS DE CONTENIDO:\n"
                resultado += f"   Líneas: {lineas}\n"
                resultado += f"   Caracteres: {caracteres}\n"
                resultado += f"   Palabras: {palabras}\n"
                
                # Detectar tipo de archivo por contenido
                if archivo_path.suffix in ['.py', '.js', '.ts', '.tsx', '.jsx']:
                    resultado += f"   Tipo: Archivo de código ({archivo_path.suffix})\n"
                elif archivo_path.suffix in ['.md', '.txt']:
                    resultado += f"   Tipo: Archivo de texto ({archivo_path.suffix})\n"
                elif archivo_path.suffix in ['.json', '.yaml', '.yml']:
                    resultado += f"   Tipo: Archivo de configuración ({archivo_path.suffix})\n"
                
        except UnicodeDecodeError:
            resultado += f"\n⚠️  Archivo binario - no se pueden obtener estadísticas de contenido.\n"
        except Exception:
            resultado += f"\n⚠️  No se pudieron obtener estadísticas de contenido.\n"
        
        logger.info(f"✅ Metadatos obtenidos exitosamente para: {ruta_relativa}")
        
        return resultado
        
    except ValueError as e:
        logger.error(f"❌ Error de validación: {str(e)}")
        return str(e)
    except PermissionError:
        logger.error(f"❌ Sin permisos de acceso: {ruta_archivo}")
        return f"Error: Sin permisos para acceder al archivo '{ruta_archivo}'."
    except Exception as e:
        logger.error(f"❌ Error inesperado: {str(e)}")
        return f"Error inesperado al obtener metadatos de '{ruta_archivo}': {str(e)}" 