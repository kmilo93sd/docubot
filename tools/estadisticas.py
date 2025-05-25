"""
Herramientas de estadísticas y análisis del repositorio para el agente LLM.
Este módulo contiene herramientas para obtener información estadística sobre el repositorio.
"""

import os
import logging
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List
from langchain.agents import tool

# Configurar logger específico para estadísticas
logger = logging.getLogger("Herramientas.Estadisticas")

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
def estadisticas_repositorio(directorio_base: str = ".") -> str:
    """
    Genera estadísticas completas del repositorio de código.
    
    Args:
        directorio_base: Directorio relativo dentro del repositorio a analizar (por defecto la raíz).
        
    Returns:
        String con estadísticas detalladas del repositorio.
    """
    logger.info(f"📊 Generando estadísticas del repositorio: {directorio_base}")
    
    try:
        # Validar que la ruta esté dentro del repositorio
        base_path = validar_ruta_en_repositorio(directorio_base)
        repo_path = obtener_ruta_repositorio()
        
        logger.debug(f"📍 Ruta base validada: {base_path}")
        
        if not base_path.exists() or not base_path.is_dir():
            return f"Error: '{directorio_base}' no es un directorio válido en el repositorio."
        
        # Contadores
        total_archivos = 0
        total_directorios = 0
        total_tamaño = 0
        archivos_por_extension = Counter()
        tamaño_por_extension = defaultdict(int)
        archivos_codigo = 0
        archivos_test = 0
        archivos_config = 0
        lineas_codigo_total = 0
        
        # Extensiones de código comunes
        extensiones_codigo = {'.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.cpp', '.c', '.h', '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt'}
        extensiones_test = {'test.', 'spec.', '.test', '.spec'}
        extensiones_config = {'.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf', '.env'}
        
        logger.debug("🔍 Escaneando archivos del repositorio...")
        
        # Recorrer recursivamente el directorio
        for item in base_path.rglob('*'):
            if item.is_file():
                total_archivos += 1
                tamaño = item.stat().st_size
                total_tamaño += tamaño
                extension = item.suffix.lower()
                
                archivos_por_extension[extension] += 1
                tamaño_por_extension[extension] += tamaño
                
                # Clasificar archivos
                if extension in extensiones_codigo:
                    archivos_codigo += 1
                    
                    # Contar líneas de código
                    try:
                        with open(item, 'r', encoding='utf-8') as f:
                            lineas = len(f.readlines())
                            lineas_codigo_total += lineas
                    except:
                        pass
                
                # Detectar archivos de test
                nombre_archivo = item.name.lower()
                if any(test_pattern in nombre_archivo for test_pattern in extensiones_test):
                    archivos_test += 1
                
                # Detectar archivos de configuración
                if extension in extensiones_config:
                    archivos_config += 1
                    
            elif item.is_dir():
                total_directorios += 1
        
        # Calcular ruta relativa desde el repositorio
        ruta_relativa = base_path.relative_to(repo_path) if base_path != repo_path else Path(".")
        
        logger.info(f"✅ Estadísticas generadas:")
        logger.info(f"   📄 Archivos: {total_archivos}")
        logger.info(f"   📁 Directorios: {total_directorios}")
        logger.info(f"   💻 Archivos de código: {archivos_codigo}")
        
        # Construir reporte
        resultado = f"=== ESTADÍSTICAS DEL REPOSITORIO: {ruta_relativa} ===\n\n"
        
        # Resumen general
        resultado += "📊 RESUMEN GENERAL:\n"
        resultado += f"   📄 Total de archivos: {total_archivos:,}\n"
        resultado += f"   📁 Total de directorios: {total_directorios:,}\n"
        resultado += f"   💾 Tamaño total: {_formatear_tamaño(total_tamaño)}\n"
        resultado += f"   💻 Archivos de código: {archivos_codigo:,}\n"
        resultado += f"   🧪 Archivos de test: {archivos_test:,}\n"
        resultado += f"   ⚙️  Archivos de configuración: {archivos_config:,}\n"
        resultado += f"   📝 Líneas de código total: {lineas_codigo_total:,}\n\n"
        
        # Top 10 extensiones por cantidad
        resultado += "🏆 TOP 10 EXTENSIONES (por cantidad):\n"
        top_extensiones = archivos_por_extension.most_common(10)
        for extension, cantidad in top_extensiones:
            if not extension:
                extension = "(sin extensión)"
            porcentaje = (cantidad / total_archivos) * 100 if total_archivos > 0 else 0
            resultado += f"   {extension}: {cantidad:,} archivos ({porcentaje:.1f}%)\n"
        
        # Top 5 extensiones por tamaño
        resultado += "\n💾 TOP 5 EXTENSIONES (por tamaño):\n"
        top_tamaños = sorted(tamaño_por_extension.items(), key=lambda x: x[1], reverse=True)[:5]
        for extension, tamaño in top_tamaños:
            if not extension:
                extension = "(sin extensión)"
            porcentaje = (tamaño / total_tamaño) * 100 if total_tamaño > 0 else 0
            resultado += f"   {extension}: {_formatear_tamaño(tamaño)} ({porcentaje:.1f}%)\n"
        
        return resultado
        
    except ValueError as e:
        logger.error(f"❌ Error de validación: {str(e)}")
        return str(e)
    except Exception as e:
        logger.error(f"❌ Error inesperado: {str(e)}")
        return f"Error al generar estadísticas del repositorio: {str(e)}"


@tool
def buscar_referencias(simbolo: str, directorio_base: str = ".") -> str:
    """
    Busca referencias a un símbolo específico (función, clase, variable) en el código del repositorio.
    
    Args:
        simbolo: Nombre del símbolo a buscar (función, clase, variable, etc.).
        directorio_base: Directorio relativo dentro del repositorio donde buscar las referencias.
        
    Returns:
        String con las ubicaciones donde se encontró el símbolo.
    """
    logger.info(f"🔍 Buscando referencias del símbolo: {simbolo} en {directorio_base}")
    
    try:
        # Validar que la ruta esté dentro del repositorio
        base_path = validar_ruta_en_repositorio(directorio_base)
        repo_path = obtener_ruta_repositorio()
        
        logger.debug(f"📍 Ruta base validada: {base_path}")
        
        if not base_path.exists() or not base_path.is_dir():
            return f"Error: '{directorio_base}' no es un directorio válido en el repositorio."
        
        # Extensiones de archivos de código a buscar
        extensiones_codigo = {'.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.cpp', '.c', '.h', '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt'}
        
        referencias = []
        archivos_procesados = 0
        
        logger.debug(f"🎯 Buscando símbolo '{simbolo}' en archivos de código...")
        
        # Buscar en archivos de código
        for archivo in base_path.rglob('*'):
            if archivo.is_file() and archivo.suffix.lower() in extensiones_codigo:
                archivos_procesados += 1
                try:
                    with open(archivo, 'r', encoding='utf-8') as f:
                        lineas = f.readlines()
                        
                    for num_linea, linea in enumerate(lineas, 1):
                        if simbolo in linea:
                            # Obtener contexto (línea anterior y siguiente si existen)
                            contexto_antes = lineas[num_linea-2].strip() if num_linea > 1 else ""
                            contexto_despues = lineas[num_linea].strip() if num_linea < len(lineas) else ""
                            
                            # Calcular ruta relativa desde el repositorio
                            ruta_relativa = archivo.relative_to(repo_path)
                            
                            referencias.append({
                                'archivo': str(ruta_relativa),
                                'linea': num_linea,
                                'contenido': linea.strip(),
                                'contexto_antes': contexto_antes,
                                'contexto_despues': contexto_despues
                            })
                            
                except (UnicodeDecodeError, PermissionError):
                    continue
        
        logger.info(f"✅ Búsqueda completada:")
        logger.info(f"   📄 Archivos procesados: {archivos_procesados}")
        logger.info(f"   🎯 Referencias encontradas: {len(referencias)}")
        
        # Construir resultado
        resultado = f"=== REFERENCIAS A '{simbolo}' ===\n\n"
        
        if referencias:
            resultado += f"Se encontraron {len(referencias)} referencias en {archivos_procesados} archivos procesados:\n\n"
            
            for i, ref in enumerate(referencias, 1):
                resultado += f"--- Referencia {i} ---\n"
                resultado += f"📄 Archivo: {ref['archivo']}\n"
                resultado += f"�� Línea: {ref['linea']}\n"
                
                if ref['contexto_antes']:
                    resultado += f"   {ref['linea']-1}: {ref['contexto_antes']}\n"
                resultado += f"➤  {ref['linea']}: {ref['contenido']}\n"
                if ref['contexto_despues']:
                    resultado += f"   {ref['linea']+1}: {ref['contexto_despues']}\n"
                resultado += "\n"
        else:
            resultado += f"No se encontraron referencias al símbolo '{simbolo}' en {archivos_procesados} archivos procesados del repositorio."
        
        return resultado
        
    except ValueError as e:
        logger.error(f"❌ Error de validación: {str(e)}")
        return str(e)
    except Exception as e:
        logger.error(f"❌ Error inesperado: {str(e)}")
        return f"Error al buscar referencias de '{simbolo}': {str(e)}"


@tool
def analizar_importaciones(ruta_archivo: str) -> str:
    """
    Analiza las importaciones y dependencias de un archivo específico dentro del repositorio.
    
    Args:
        ruta_archivo: Ruta relativa al archivo dentro del repositorio a analizar.
        
    Returns:
        String con el análisis de importaciones del archivo.
    """
    logger.info(f"📦 Analizando importaciones de: {ruta_archivo}")
    
    try:
        # Validar que la ruta esté dentro del repositorio
        archivo_path = validar_ruta_en_repositorio(ruta_archivo)
        repo_path = obtener_ruta_repositorio()
        
        logger.debug(f"📍 Ruta absoluta validada: {archivo_path}")
        
        if not archivo_path.exists():
            return f"Error: El archivo '{ruta_archivo}' no existe en el repositorio."
        
        if not archivo_path.is_file():
            return f"Error: '{ruta_archivo}' no es un archivo válido."
        
        # Calcular ruta relativa desde el repositorio
        ruta_relativa = archivo_path.relative_to(repo_path)
        
        # Leer el archivo
        try:
            with open(archivo_path, 'r', encoding='utf-8') as f:
                lineas = f.readlines()
        except UnicodeDecodeError:
            return f"Error: No se puede leer '{ruta_archivo}' - archivo binario o codificación no compatible."
        
        # Analizar según la extensión del archivo
        extension = archivo_path.suffix.lower()
        
        if extension == '.py':
            importaciones = _analizar_importaciones_python(lineas)
        elif extension in ['.js', '.ts', '.tsx', '.jsx']:
            importaciones = _analizar_importaciones_javascript(lineas)
        else:
            return f"Análisis de importaciones no soportado para archivos {extension}."
        
        logger.info(f"✅ Análisis completado: {len(importaciones)} importaciones encontradas")
        
        # Construir resultado
        resultado = f"=== ANÁLISIS DE IMPORTACIONES: {ruta_relativa} ===\n\n"
        
        if importaciones:
            resultado += f"Se encontraron {len(importaciones)} importaciones:\n\n"
            
            # Agrupar por tipo
            importaciones_por_tipo = defaultdict(list)
            for imp in importaciones:
                importaciones_por_tipo[imp['tipo']].append(imp)
            
            for tipo, lista_imp in importaciones_por_tipo.items():
                resultado += f"📦 {tipo.upper()}:\n"
                for imp in lista_imp:
                    resultado += f"   📍 Línea {imp['linea']}: {imp['modulo']}\n"
                    if imp['elementos']:
                        resultado += f"      └─ Elementos: {', '.join(imp['elementos'])}\n"
                resultado += "\n"
        else:
            resultado += "No se encontraron importaciones en este archivo."
        
        return resultado
        
    except ValueError as e:
        logger.error(f"❌ Error de validación: {str(e)}")
        return str(e)
    except Exception as e:
        logger.error(f"❌ Error inesperado: {str(e)}")
        return f"Error al analizar importaciones de '{ruta_archivo}': {str(e)}"


def _formatear_tamaño(tamaño_bytes: int) -> str:
    """Convierte bytes a formato legible (KB, MB, GB)."""
    for unidad in ['B', 'KB', 'MB', 'GB', 'TB']:
        if tamaño_bytes < 1024.0:
            return f"{tamaño_bytes:.1f} {unidad}"
        tamaño_bytes /= 1024.0
    return f"{tamaño_bytes:.1f} PB"


def _analizar_importaciones_python(lineas: List[str]) -> List[Dict]:
    """Analiza importaciones en archivos Python."""
    import re
    importaciones = []
    
    for num_linea, linea in enumerate(lineas, 1):
        linea = linea.strip()
        
        # import modulo
        match = re.match(r'^import\s+([^\s]+)', linea)
        if match:
            modulo = match.group(1)
            tipo = 'externa' if not modulo.startswith('.') and '.' not in modulo else 'local'
            if modulo.startswith('.'):
                tipo = 'relativa'
            
            importaciones.append({
                'linea': num_linea,
                'modulo': modulo,
                'elementos': [],
                'tipo': tipo
            })
            continue
        
        # from modulo import elementos
        match = re.match(r'^from\s+([^\s]+)\s+import\s+(.+)', linea)
        if match:
            modulo = match.group(1)
            elementos_str = match.group(2)
            elementos = [elem.strip() for elem in elementos_str.split(',')]
            
            tipo = 'externa' if not modulo.startswith('.') and '.' not in modulo else 'local'
            if modulo.startswith('.'):
                tipo = 'relativa'
            
            importaciones.append({
                'linea': num_linea,
                'modulo': modulo,
                'elementos': elementos,
                'tipo': tipo
            })
    
    return importaciones


def _analizar_importaciones_javascript(lineas: List[str]) -> List[Dict]:
    """Analiza importaciones en archivos JavaScript/TypeScript."""
    import re
    importaciones = []
    
    for num_linea, linea in enumerate(lineas, 1):
        linea = linea.strip()
        
        # import ... from 'modulo'
        match = re.match(r'^import\s+.*from\s+[\'"]([^\'"]+)[\'"]', linea)
        if match:
            modulo = match.group(1)
            
            # Determinar tipo de importación
            if modulo.startswith('./') or modulo.startswith('../'):
                tipo = 'relativa'
            elif modulo.startswith('/') or modulo.startswith('@/'):
                tipo = 'local'
            else:
                tipo = 'externa'
            
            # Extraer elementos importados
            elementos = []
            if '{' in linea and '}' in linea:
                elementos_match = re.search(r'\{([^}]+)\}', linea)
                if elementos_match:
                    elementos = [elem.strip() for elem in elementos_match.group(1).split(',')]
            
            importaciones.append({
                'linea': num_linea,
                'modulo': modulo,
                'elementos': elementos,
                'tipo': tipo
            })
            continue
        
        # require('modulo')
        match = re.search(r'require\([\'"]([^\'"]+)[\'"]\)', linea)
        if match:
            modulo = match.group(1)
            
            if modulo.startswith('./') or modulo.startswith('../'):
                tipo = 'relativa'
            elif modulo.startswith('/'):
                tipo = 'local'
            else:
                tipo = 'externa'
            
            importaciones.append({
                'linea': num_linea,
                'modulo': modulo,
                'elementos': [],
                'tipo': tipo
            })
    
    return importaciones 