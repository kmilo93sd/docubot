#!/usr/bin/env python3
"""
Agente LLM automatizado utilizando LangGraph y AWS Bedrock Claude 4
para generar documentación funcional de código de forma autónoma.
"""

import os
import sys
import boto3
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from langchain_aws import ChatBedrockConverse
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver

# Importar herramientas desde el paquete tools
from tools import all_tools

# Importar configuración de logging
from logging_config import get_config

# Cargar variables de entorno
load_dotenv()

# Configuración de AWS Bedrock
REGION_NAME = os.getenv("AWS_REGION", "us-east-1")
MODEL_ID = "us.anthropic.claude-sonnet-4-20250514-v1:0"  # Modelo Claude 4 Sonnet

# Variable global para el directorio del repositorio
REPOSITORY_PATH = None

def configurar_logging(mode: str = "normal"):
    """Configura el sistema de logging para el agente con niveles optimizados."""
    
    # Obtener configuración según el modo
    config = get_config(mode)
    
    # Crear directorio de logs si no existe
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Nombre del archivo de log con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"agente_documentador_{timestamp}.log"
    
    # Configurar el logger principal
    logger = logging.getLogger("AgenteLLM")
    logger.setLevel(config["AGENT_LEVEL"])
    
    # Limpiar handlers existentes
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Formatter simplificado para consola
    console_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt=config["CONSOLE_TIME_FORMAT"]
    )
    
    # Formatter detallado para archivo
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-12s | %(message)s',
        datefmt=config["FILE_TIME_FORMAT"]
    )
    
    # Handler para archivo
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(config["FILE_LEVEL"])
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setLevel(config["CONSOLE_LEVEL"])
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Configurar loggers específicos
    
    # Logger para herramientas
    tools_logger = logging.getLogger("Herramientas")
    tools_logger.setLevel(config["TOOLS_LEVEL"])
    tools_logger.addHandler(file_handler)
    if config["TOOLS_LEVEL"] <= config["CONSOLE_LEVEL"]:
        tools_logger.addHandler(console_handler)
    
    # Logger para pensamiento del agente
    thinking_logger = logging.getLogger("Pensamiento")
    thinking_logger.setLevel(config["THINKING_LEVEL"])
    thinking_logger.addHandler(file_handler)
    if config["THINKING_LEVEL"] <= config["CONSOLE_LEVEL"]:
        thinking_logger.addHandler(console_handler)
    
    # Suprimir logs verbosos de librerías externas si está configurado
    if config["SUPPRESS_EXTERNAL_LIBS"]:
        logging.getLogger("boto3").setLevel(logging.WARNING)
        logging.getLogger("botocore").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("langchain").setLevel(logging.WARNING)
        logging.getLogger("langgraph").setLevel(logging.WARNING)
    
    return logger, log_file

def configurar_herramientas_para_repositorio(repository_path: str):
    """
    Configura las herramientas para trabajar únicamente en el repositorio especificado.
    
    Args:
        repository_path: Ruta absoluta al repositorio que se debe documentar.
    """
    global REPOSITORY_PATH
    REPOSITORY_PATH = Path(repository_path).resolve()
    
    # Configurar variable de entorno para que las herramientas la usen
    os.environ['DOCUMENTATOR_REPOSITORY_PATH'] = str(REPOSITORY_PATH)
    
    return REPOSITORY_PATH

def mostrar_progreso(mensaje: str, tipo: str = "info"):
    """Muestra mensajes de progreso de forma clara y concisa."""
    iconos = {
        "inicio": "🚀",
        "progreso": "⚙️",
        "exito": "✅",
        "error": "❌",
        "info": "ℹ️"
    }
    icono = iconos.get(tipo, "ℹ️")
    print(f"{icono} {mensaje}")

def crear_agente_con_logging(repository_path: str, logging_mode: str = "normal"):
    """Crea y retorna un agente LLM con herramientas y logging completo."""
    
    # Configurar logging
    logger, log_file = configurar_logging(logging_mode)
    thinking_logger = logging.getLogger("Pensamiento")
    
    logger.info("🚀 INICIANDO AGENTE DOCUMENTADOR")
    logger.info(f"📁 Archivo de log: {log_file}")
    logger.info(f"🤖 Modelo: {MODEL_ID}")
    logger.info(f"🌍 Región AWS: {REGION_NAME}")
    
    # Configurar herramientas para el repositorio específico
    repo_path = configurar_herramientas_para_repositorio(repository_path)
    logger.info(f"📂 Repositorio objetivo: {repo_path}")
    
    # Verificar que el repositorio existe
    if not repo_path.exists():
        raise ValueError(f"❌ El repositorio especificado no existe: {repo_path}")
    
    if not repo_path.is_dir():
        raise ValueError(f"❌ La ruta especificada no es un directorio: {repo_path}")
    
    logger.info(f"✅ Repositorio verificado exitosamente")
    
    # Configurar el cliente de AWS Bedrock
    logger.debug("🔧 Configurando cliente AWS Bedrock...")
    session = boto3.Session(region_name=REGION_NAME)
    bedrock_client = session.client(
        service_name="bedrock-runtime",
        region_name=REGION_NAME
    )
    
    # Configurar el modelo de Claude 4 Sonnet con ChatBedrockConverse
    logger.debug("🧠 Configurando modelo Claude 4 Sonnet...")
    model = ChatBedrockConverse(
        client=bedrock_client,
        model_id=MODEL_ID,
        temperature=0,
        max_tokens=4000
    )
    
    # Usar las herramientas originales sin wrapper
    logger.info(f"🛠️  Configurando {len(all_tools)} herramientas...")
    for tool in all_tools:
        tool_name = getattr(tool, 'name', str(tool))
        logger.debug(f"   ✓ Herramienta disponible: {tool_name}")
    
    # Configurar el checkpointer para memoria
    logger.debug("💾 Configurando memoria del agente...")
    checkpointer = InMemorySaver()
    
    # Prompt mejorado con instrucciones de logging y repositorio específico
    prompt_con_logging = f"""
        
        <persona>
        Actúa como un especialista en producto y documentación funcional. Tienes más de 15 años de experiencia traduciendo sistemas complejos en documentación comprensible para áreas comerciales, clientes, usuarios finales y equipos de ventas. Sabes cómo interpretar código para extraer funcionalidades clave, procesos de negocio y reglas funcionales reales y verificables.
        </persona>

        <objetivo>
        Tu objetivo es generar un manual funcional del sistema a partir del análisis directo del código fuente de un repositorio. Este manual debe:
        - Incluir una vista panorámica general del sistema.
        - Documentar los módulos funcionales más importantes.
        - Usar lenguaje claro, accesible y orientado al negocio.
        - Ser completamente fidedigno: jamás debes inventar o suponer información que no esté explícitamente representada en el código. Si algo no puede ser determinado con certeza, indícalo claramente como ausencia de información.
        </objetivo>

        <restricciones>
        - Trabaja exclusivamente con los archivos ubicados en la ruta: {repo_path}.
        - No analices archivos fuera de esta ruta.
        - No edites ni modifiques el código.
        - Solo documenta lo que puedas confirmar con evidencia clara del código.
        - Si una herramienta falla, no la reintentes más de una vez.
        </restricciones>

        <estilo>
        - Siempre responde en español.
        - Usa formato Markdown para toda la documentación generada.
        - Usa etiquetas estructuradas como <section>, <modulo>, <regla> internamente si lo necesitas para organizar el razonamiento y generar contenido consistente.
        - Mantén consistencia estructural entre módulos.
        - Puedes usar hasta 3500 tokens por archivo Markdown. Sé tan detallado como sea necesario.
        </estilo>

        <estilo_adicional>
        IMPORTANTE: La documentación debe estar redactada en lenguaje funcional, natural y orientado al negocio. Bajo ninguna circunstancia debes incluir:

        - Nombres de variables, atributos o campos internos (como balanceType, clientId, reminderStatusId, etc.).
        - Identificadores numéricos o valores de enums.
        - Fragmentos de código, objetos JSON o estructuras de datos técnicas.
        - Nombres de modelos, clases o interfaces (por ejemplo, no mencionar clientModel, contact[], documents[]).

        En su lugar, traduce toda la información al lenguaje que usaría un usuario de negocio o un cliente. Por ejemplo:

        - ❌ Incorrecto: reminderStatusId: 3
        - ✅ Correcto: "Recordatorios que no pudieron ser enviados por un error"

        - ❌ Incorrecto: clientIdentificationValue
        - ✅ Correcto: "RUT del cliente"

        - ❌ Incorrecto: estructura de objeto con claves
        - ✅ Correcto: "Cada cliente tiene un nombre, contactos asociados y un historial de pagos"

        Si una regla está basada en un ID o código interno, no lo muestres. Describe el comportamiento que ese ID representa de manera natural. El lector de esta documentación no tiene contexto técnico ni debe tenerlo.
        </estilo_adicional>

        <estructura_global>
        1. Genera un archivo inicial: 01_resumen_general.md
        Este archivo debe incluir:
        - # Vista general del sistema
        - ## ¿Qué funcionalidades ofrece este sistema?
        - ## ¿A quién está dirigido este sistema?
        - ## ¿Qué valor aporta al negocio?
        - ## Lista de módulos funcionales identificados
            - Formato: - [Nombre del módulo] → archivo: 02_modulo_[slug].md

        2. Para cada módulo funcional detectado, genera un archivo nombrado: 02_modulo_[slug-del-nombre-del-modulo].md

        Usa esta estructura Markdown para cada módulo:
        Sección: [Nombre del módulo o funcionalidad]
        ¿Qué es esta funcionalidad?
        Explica su propósito funcional desde una perspectiva de negocio. Si no hay información suficiente, indica:

        "No se encontró suficiente información en el código para completar esta sección."

        ¿Qué puede hacer un usuario aquí?
        Lista las acciones visibles y accesibles para el usuario final. Ejemplo:

        Crear registros

        Buscar y filtrar resultados

        Descargar informes

        ¿Qué reglas se aplican?
        <section id="reglas"> Debes ser extremadamente detallado en esta sección. Puedes usar hasta 3500 tokens si es necesario. Describe exhaustivamente: - Validaciones y restricciones visibles en el código. - Flujos de trabajo y procesos de negocio. - Condiciones, permisos y roles explícitos. - Lógica de cálculos y transformaciones de datos. - Comportamientos especiales o excepciones. - Integraciones o dependencias entre módulos. - Cualquier lógica funcional relevante observable en el código. Usa ejemplos reales solo si puedes deducirlos directamente. No incluyas identificadores ni estructuras internas. </section>
        ¿Por qué es útil esta funcionalidad?
        Describe el valor comercial o funcional del módulo, si está claramente inferido del código.

        markdown
        Copy
        Edit

        3. Si detectas secciones sin información suficiente:
        - Decláralo en la sección correspondiente del Markdown.
        - Además, registra ese hallazgo en un archivo llamado: 99_resumen_puntos_sin_documentar.md
        - Ejemplo:
            - Módulo: Reportes de desempeño → No se encontró información suficiente sobre las acciones del usuario ni reglas aplicadas.
        </estructura_global>

        <flujo_de_trabajo>
        1. Realiza una exploración inicial del repositorio para detectar los módulos funcionales clave.
        2. Genera 01_resumen_general.md con la vista panorámica del sistema.
        3. Luego, para cada módulo identificado, crea su archivo correspondiente según la estructura dada.
        4. No te detengas hasta haber documentado todos los módulos relevantes.
        </flujo_de_trabajo>

        <importante>
        Toma una respiración profunda y trabaja en este problema paso a paso.
        </importante>
        """
    
    # Crear un agente usando langgraph
    logger.debug("🤖 Creando agente con LangGraph...")
    agent = create_react_agent(
        model=model,
        tools=all_tools,  # Usar herramientas originales
        prompt=prompt_con_logging,
        checkpointer=checkpointer,
        debug=False,  # Activar modo debug para más información
    )
    
    logger.info("✅ Agente creado exitosamente con logging completo")
    
    return agent, logger, thinking_logger

def main(repository_path: str = None, logging_mode: str = "normal"):
    """
    Función principal para ejecutar el agente de forma automática.
    
    Args:
        repository_path: Ruta al repositorio que se debe documentar.
                        Si no se proporciona, se toma del primer argumento de línea de comandos.
        logging_mode: Modo de logging ("normal", "debug", "quiet").
    """
    
    mostrar_progreso("Iniciando agente documentador automático", "inicio")
    mostrar_progreso(f"Repositorio objetivo: {repository_path}", "info")
    mostrar_progreso("El agente analizará el código y generará documentación funcional", "info")
    mostrar_progreso("Este proceso puede tomar varios minutos dependiendo del tamaño del proyecto", "info")
    print("-" * 70)
    
    try:
        # Crear el agente con logging
        agente, logger, thinking_logger = crear_agente_con_logging(repository_path, logging_mode)
        
        # Configuración para la sesión
        thread_id = "documentacion_automatica"
        config = {
            "configurable": {"thread_id": thread_id},
            "recursion_limit": 150  # Aumentar límite de recursión para tareas intensivas
        }
        
        logger.info(f"🎯 Iniciando sesión de documentación (ID: {thread_id})")
        
        # Mensaje inicial para activar el agente
        mensaje_inicial = f"""
        Comienza tu trabajo de documentación funcional. Analiza el código del repositorio ubicado en: {repository_path}
        
        Genera la documentación según tus instrucciones. Recuerda que eres completamente autónomo y debes seguir tu flujo de trabajo paso a paso.
        
        IMPORTANTE: 
        - Trabaja ÚNICAMENTE con archivos del repositorio especificado
        - Mantén un flujo narrativo claro explicando qué herramientas usas y por qué
        - Todas las herramientas están configuradas para trabajar en el directorio correcto
        """
        
        logger.info("📤 Enviando instrucciones iniciales al agente...")
        thinking_logger.info("💭 INICIO DEL PROCESO DE DOCUMENTACIÓN")
        
        # Ejecutar el agente
        respuesta = agente.invoke(
            {"messages": [{"role": "user", "content": mensaje_inicial}]},
            config
        )
        
        logger.info("✅ El agente ha completado su trabajo de documentación.")
        logger.info("📁 Revisa los archivos Markdown generados en el directorio del proyecto.")
        thinking_logger.info("💭 PROCESO DE DOCUMENTACIÓN COMPLETADO")
        
        mostrar_progreso("El agente ha completado su trabajo de documentación", "exito")
        mostrar_progreso("Revisa los archivos Markdown generados en el directorio del proyecto", "info")
        mostrar_progreso(f"Logs detallados disponibles en: logs/", "info")
        
    except KeyboardInterrupt:
        mostrar_progreso("Proceso interrumpido por el usuario", "error")
        if 'logger' in locals():
            logger.warning("⚠️ Proceso interrumpido por el usuario")
    except Exception as e:
        mostrar_progreso(f"Error durante la ejecución: {e}", "error")
        mostrar_progreso(f"Tipo de error: {type(e).__name__}", "error")
        if 'logger' in locals():
            logger.error(f"❌ Error durante la ejecución: {e}")
            logger.error(f"🔧 Tipo de error: {type(e).__name__}")
        import traceback
        print("\n📋 Detalles del error:")
        traceback.print_exc()

if __name__ == "__main__":
    # Obtener la ruta del repositorio desde argumentos de línea de comandos
    if len(sys.argv) < 2:
        print("❌ Error: Debes proporcionar la ruta del repositorio como argumento.")
        print("📋 Uso: python agent.py <ruta_del_repositorio>")
        print("📋 Ejemplo: python agent.py \"C:\\Users\\usuario\\mi_proyecto\"")
        sys.exit(1)
    
    repository_path = sys.argv[1]
    
    # Verificar si se especificó un modo de logging
    logging_mode = "normal"
    if len(sys.argv) > 2:
        logging_mode = sys.argv[2]
    
    main(repository_path, logging_mode) 