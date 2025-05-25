#!/usr/bin/env python3
"""
Monitor de logs en tiempo real para el agente documentador.
Permite seguir la actividad del agente mientras trabaja.
"""
import argparse
from pathlib import Path
from datetime import datetime
import subprocess
import sys

def obtener_ultimo_log():
    """Obtiene el archivo de log más reciente."""
    logs_dir = Path("logs")
    
    if not logs_dir.exists():
        print("❌ No existe el directorio de logs. Ejecuta el agente primero.")
        return None
    
    # Buscar archivos de log
    log_files = list(logs_dir.glob("agente_documentador_*.log"))
    
    if not log_files:
        print("❌ No se encontraron archivos de log.")
        return None
    
    # Obtener el más reciente
    ultimo_log = max(log_files, key=lambda f: f.stat().st_mtime)
    return ultimo_log

def mostrar_estadisticas_log(log_file):
    """Muestra estadísticas del archivo de log."""
    if not log_file.exists():
        return
    
    with open(log_file, 'r', encoding='utf-8') as f:
        lineas = f.readlines()
    
    # Contar por tipo de log
    contadores = {
        'INFO': 0,
        'DEBUG': 0,
        'WARNING': 0,
        'ERROR': 0
    }
    
    herramientas_usadas = set()
    
    for linea in lineas:
        for nivel in contadores:
            if f'| {nivel}' in linea:
                contadores[nivel] += 1
                break
        
        # Detectar herramientas usadas
        if '🔧 INICIANDO HERRAMIENTA:' in linea:
            herramienta = linea.split('🔧 INICIANDO HERRAMIENTA:')[1].strip()
            herramientas_usadas.add(herramienta)
    
    print(f"\n📊 ESTADÍSTICAS DEL LOG:")
    print(f"   📄 Archivo: {log_file.name}")
    print(f"   📏 Total líneas: {len(lineas)}")
    print(f"   ℹ️  INFO: {contadores['INFO']}")
    print(f"   🐛 DEBUG: {contadores['DEBUG']}")
    print(f"   ⚠️  WARNING: {contadores['WARNING']}")
    print(f"   ❌ ERROR: {contadores['ERROR']}")
    print(f"   🛠️  Herramientas usadas: {len(herramientas_usadas)}")
    
    if herramientas_usadas:
        print(f"\n🔧 HERRAMIENTAS DETECTADAS:")
        for herramienta in sorted(herramientas_usadas):
            print(f"   • {herramienta}")

def validar_archivo_log(log_file):
    """Valida que el archivo de log sea seguro para monitorear."""
    # Convertir a Path para validación
    log_path = Path(log_file)
    
    # Verificar que esté en el directorio logs
    logs_dir = Path("logs").resolve()
    try:
        log_path_resolved = log_path.resolve()
        log_path_resolved.relative_to(logs_dir)
    except ValueError:
        raise ValueError(f"❌ Archivo de log fuera del directorio permitido: {log_file}")
    
    # Verificar que existe y es archivo
    if not log_path_resolved.exists():
        raise ValueError(f"❌ Archivo de log no existe: {log_file}")
    
    if not log_path_resolved.is_file():
        raise ValueError(f"❌ No es un archivo válido: {log_file}")
    
    # Verificar extensión
    if log_path_resolved.suffix != '.log':
        raise ValueError(f"❌ Tipo de archivo no permitido: {log_file}")
    
    return log_path_resolved

def seguir_log(log_file, filtro_nivel=None, solo_herramientas=False):
    """Sigue un archivo de log en tiempo real."""
    print(f"👀 Monitoreando: {log_file}")
    print(f"🕒 Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if filtro_nivel:
        print(f"🔍 Filtro de nivel: {filtro_nivel}")
    
    if solo_herramientas:
        print(f"🛠️  Solo mostrando actividad de herramientas")
    
    print("-" * 70)
    
    try:
        # Validar archivo antes de procesar
        log_path_validado = validar_archivo_log(log_file)
        
        # Usar tail para seguir el archivo con validación de comandos
        if sys.platform.startswith('win'):
            # En Windows, usar PowerShell con ruta validada
            cmd = ['powershell', '-Command', f'Get-Content "{log_path_validado}" -Wait -Tail 10']
        else:
            # En Unix/Linux/Mac con ruta validada
            cmd = ['tail', '-f', str(log_path_validado)]
        
        # Ejecutar con validación adicional
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            universal_newlines=True, 
            bufsize=1,
            shell=False  # Explícitamente deshabilitar shell
        )
        
        for linea in iter(process.stdout.readline, ''):
            linea = linea.strip()
            
            # Aplicar filtros
            if filtro_nivel and f'| {filtro_nivel}' not in linea:
                continue
            
            if solo_herramientas and 'Herramientas' not in linea:
                continue
            
            # Colorear la salida
            if '| ERROR' in linea:
                print(f"\033[91m{linea}\033[0m")  # Rojo
            elif '| WARNING' in linea:
                print(f"\033[93m{linea}\033[0m")  # Amarillo
            elif '| INFO' in linea:
                print(f"\033[92m{linea}\033[0m")  # Verde
            elif '| DEBUG' in linea:
                print(f"\033[94m{linea}\033[0m")  # Azul
            else:
                print(linea)
                
    except ValueError as e:
        print(f"\n❌ Error de validación: {e}")
        return
    except KeyboardInterrupt:
        print(f"\n⚠️  Monitoreo interrumpido por el usuario")
        if 'process' in locals():
            process.terminate()
    except Exception as e:
        print(f"\n❌ Error durante el monitoreo: {e}")

def main():
    """Función principal del monitor."""
    parser = argparse.ArgumentParser(description="Monitor de logs del agente documentador")
    parser.add_argument("--archivo", "-f", help="Archivo de log específico a monitorear")
    parser.add_argument("--nivel", "-n", choices=['INFO', 'DEBUG', 'WARNING', 'ERROR'], 
                       help="Filtrar por nivel de log")
    parser.add_argument("--herramientas", "-t", action="store_true", 
                       help="Solo mostrar actividad de herramientas")
    parser.add_argument("--stats", "-s", action="store_true", 
                       help="Solo mostrar estadísticas sin seguir el log")
    parser.add_argument("--listar", "-l", action="store_true", 
                       help="Listar archivos de log disponibles")
    
    args = parser.parse_args()
    
    # Listar archivos de log
    if args.listar:
        logs_dir = Path("logs")
        if logs_dir.exists():
            log_files = list(logs_dir.glob("agente_documentador_*.log"))
            if log_files:
                print("📋 ARCHIVOS DE LOG DISPONIBLES:")
                for log_file in sorted(log_files, key=lambda f: f.stat().st_mtime, reverse=True):
                    tamaño = log_file.stat().st_size
                    modificado = datetime.fromtimestamp(log_file.stat().st_mtime)
                    print(f"   📄 {log_file.name} ({tamaño} bytes) - {modificado.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print("❌ No se encontraron archivos de log.")
        else:
            print("❌ No existe el directorio de logs.")
        return
    
    # Determinar archivo de log
    if args.archivo:
        log_file = Path(args.archivo)
        if not log_file.exists():
            print(f"❌ El archivo {args.archivo} no existe.")
            return
    else:
        log_file = obtener_ultimo_log()
        if not log_file:
            return
    
    # Mostrar estadísticas
    if args.stats:
        mostrar_estadisticas_log(log_file)
        return
    
    # Seguir el log
    seguir_log(log_file, args.nivel, args.herramientas)

if __name__ == "__main__":
    main() 