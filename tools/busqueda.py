"""
Herramienta de búsqueda semántica para el agente LLM.
Este módulo contiene herramientas para buscar en ChromaDB usando embeddings de AWS Bedrock.
"""

import os
import json
import logging
import chromadb
from chromadb.config import Settings
import boto3
from typing import List, Dict
from langchain.agents import tool

# Configurar logger específico para búsqueda
logger = logging.getLogger("Herramientas.Busqueda")

# Constantes
CHROMA_PERSIST_DIR = "./chroma_db"
COLLECTION_NAME = "react_typescript_code"
BEDROCK_MODEL_ID = "amazon.titan-embed-text-v1"
MAX_RESULTS = 5


class BuscadorSemantico:
    """Clase para realizar búsquedas semánticas en ChromaDB usando vectores de Amazon Bedrock."""

    def __init__(self):
        # Configurar cliente AWS Bedrock
        self.bedrock_client = boto3.client(
            'bedrock-runtime',
            region_name=os.getenv("AWS_REGION", "us-east-1")
        )
        
        # Configurar cliente ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=CHROMA_PERSIST_DIR,
            settings=Settings(allow_reset=False)
        )
        
        # Obtener colección
        try:
            self.collection = self.chroma_client.get_collection(COLLECTION_NAME)
        except Exception as e:
            raise ValueError(f"No se pudo encontrar la colección en ChromaDB: {e}")

    def _validar_respuesta_bedrock(self, response_body: dict) -> List[float]:
        """Valida la respuesta de AWS Bedrock para embeddings."""
        if not isinstance(response_body, dict):
            raise ValueError("Respuesta AWS no es un diccionario válido")
        
        if 'embedding' not in response_body:
            raise ValueError("Respuesta AWS no contiene campo 'embedding'")
        
        embedding = response_body['embedding']
        if not isinstance(embedding, list):
            raise ValueError("El embedding no es una lista válida")
        
        if not embedding:
            raise ValueError("El embedding está vacío")
        
        # Verificar que todos los elementos son números
        if not all(isinstance(x, (int, float)) for x in embedding):
            raise ValueError("El embedding contiene valores no numéricos")
        
        return embedding

    def generar_embedding(self, texto: str) -> List[float]:
        """Genera un vector de embedding usando Amazon Bedrock."""
        try:
            # Validar entrada
            if not texto or not isinstance(texto, str):
                raise ValueError("Texto de entrada inválido para embedding")
            
            # Preparar la petición para el modelo Titan Embeddings
            response = self.bedrock_client.invoke_model(
                modelId=BEDROCK_MODEL_ID,
                body=json.dumps({
                    "inputText": texto
                })
            )
            
            # Procesar la respuesta con validación
            response_body = json.loads(response.get('body').read())
            
            # Validar estructura de respuesta
            embedding = self._validar_respuesta_bedrock(response_body)
            
            logger.debug(f"Embedding generado exitosamente: {len(embedding)} dimensiones")
            return embedding
            
        except ValueError as e:
            raise Exception(f"Error de validación en respuesta Bedrock: {e}")
        except json.JSONDecodeError as e:
            raise Exception(f"Error decodificando JSON de Bedrock: {e}")
        except Exception as e:
            raise Exception(f"Error al generar embedding con Bedrock: {e}")

    def buscar(self, query: str, num_results: int = MAX_RESULTS) -> List[Dict]:
        """Realiza una búsqueda semántica en ChromaDB."""
        try:
            # Generar embedding para la consulta
            query_embedding = self.generar_embedding(query)
            
            # Realizar búsqueda en ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=num_results,
                include=["metadatas", "documents", "distances"]
            )
            
            # Formatear resultados para ser más legibles
            formatted_results = []
            for i in range(len(results["ids"][0])):
                formatted_results.append({
                    "contenido": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "relevancia": 1 - float(results["distances"][0][i])  # Convertir distancia a similitud
                })
            
            return formatted_results
        except Exception as e:
            raise Exception(f"Error al buscar en ChromaDB: {e}")


# Inicializar el buscador semántico
_buscador = None

def obtener_buscador():
    """Obtiene o inicializa la instancia del buscador semántico."""
    global _buscador
    if _buscador is None:
        try:
            _buscador = BuscadorSemantico()
        except Exception as e:
            raise Exception(f"No se pudo inicializar el buscador semántico: {e}")
    return _buscador


@tool
def buscar_codigo(consulta: str) -> str:
    """
    Busca código en el repositorio utilizando una consulta en lenguaje natural.
    Encuentra fragmentos de código, componentes o funcionalidades similares a lo descrito.
    
    Args:
        consulta: Descripción en lenguaje natural de lo que se busca.
        
    Returns:
        String con los resultados más relevantes encontrados.
    """
    logger.info(f"🔍 Iniciando búsqueda semántica: '{consulta}'")
    
    try:
        # Obtener buscador
        logger.debug("📡 Obteniendo instancia del buscador semántico...")
        buscador = obtener_buscador()
        
        # Realizar búsqueda
        logger.debug("🎯 Ejecutando búsqueda en ChromaDB...")
        resultados = buscador.buscar(consulta)
        
        # Log de estadísticas de relevancia
        if resultados:
            relevancias = [r["relevancia"] for r in resultados]
            relevancia_max = max(relevancias)
            relevancia_min = min(relevancias)
            relevancia_promedio = sum(relevancias) / len(relevancias)
            
            logger.debug(f"📊 Estadísticas de relevancia:")
            logger.debug(f"   🔝 Máxima: {relevancia_max:.3f}")
            logger.debug(f"   🔻 Mínima: {relevancia_min:.3f}")
            logger.debug(f"   📈 Promedio: {relevancia_promedio:.3f}")
        
        # Formatear resultados para mostrarlos
        respuesta = f"He encontrado {len(resultados)} resultados para tu consulta:\n\n"
        
        for i, resultado in enumerate(resultados, 1):
            metadata = resultado["metadata"]
            archivo = metadata.get("file_path", "archivo desconocido")
            relevancia = round(resultado["relevancia"] * 100, 2)
            
            logger.debug(f"📄 Resultado {i}: {archivo} (relevancia: {relevancia}%)")
            
            respuesta += f"--- Resultado {i} (Relevancia: {relevancia}%) ---\n"
            respuesta += f"Archivo: {archivo}\n"
            
            # Añadir información adicional útil si está disponible
            if metadata.get("is_component"):
                respuesta += "Tipo: Componente React\n"
            elif metadata.get("is_test"):
                respuesta += "Tipo: Archivo de test\n"
            elif metadata.get("is_config"):
                respuesta += "Tipo: Archivo de configuración\n"
                
            # Añadir fragmento de código
            respuesta += f"\nFragmento:\n```\n{resultado['contenido'][:400]}...\n```\n\n"
        
        logger.info(f"📤 Respuesta generada con {len(respuesta)} caracteres")
        return respuesta
        
    except Exception as e:
        logger.error(f"❌ Error en búsqueda semántica: {str(e)}")
        return f"Error al realizar la búsqueda: {str(e)}" 