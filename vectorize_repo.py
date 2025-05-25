#!/usr/bin/env python3
"""
Script para vectorizar un repositorio React/TypeScript usando ChromaDB y Amazon Titan Embeddings.
Optimizado para manejar bases de código grandes con uso eficiente de memoria.
"""

import os
import asyncio
import hashlib
import json
import logging
import gc
from pathlib import Path
from typing import List, Dict, Generator, Optional
from dataclasses import dataclass
from datetime import datetime

import boto3
import chromadb
from chromadb.config import Settings
import tiktoken
import argparse

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vectorization.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class FileContent:
    """Clase para representar el contenido de un archivo"""
    path: str
    content: str
    size: int
    hash: str
    metadata: Dict

class RepositoryVectorizer:
    def __init__(
        self,
        repo_path: str,
        chroma_persist_dir: str = "./chroma_db",
        collection_name: str = "react_typescript_code",
        aws_region: str = "us-east-1",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        max_tokens_per_chunk: int = 2000,
        batch_size: int = 10,
        max_workers: int = 4
    ):
        self.repo_path = Path(repo_path)
        self.chroma_persist_dir = chroma_persist_dir
        self.collection_name = collection_name
        self.aws_region = aws_region
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.max_tokens_per_chunk = max_tokens_per_chunk
        self.batch_size = batch_size
        self.max_workers = max_workers
        
        # Inicializar tokenizer para contar tokens
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Configurar clientes AWS y ChromaDB
        self._setup_clients()
        
        # Extensiones de archivos a procesar
        self.supported_extensions = {
            '.ts', '.tsx', '.js', '.jsx', '.json', '.css', '.scss', 
            '.sass', '.less', '.html', '.md', '.mdx', '.yaml', '.yml'
        }
        
        # Directorios a ignorar
        self.ignore_dirs = {
            'node_modules', '.git', '.next', 'build', 'dist', 
            'coverage', '.nyc_output', 'tmp', 'temp'
        }
        
        # Archivos a ignorar
        self.ignore_files = {
            '.env', '.env.local', '.env.production', '.env.development',
            'package-lock.json', 'yarn.lock', '.gitignore', '.eslintrc',
            '.prettierrc', 'tsconfig.json'
        }

    def _setup_clients(self):
        """Configurar clientes de AWS Bedrock y ChromaDB"""
        try:
            # Cliente de AWS Bedrock
            self.bedrock_client = boto3.client(
                'bedrock-runtime',
                region_name=self.aws_region
            )
            
            # Cliente de ChromaDB
            self.chroma_client = chromadb.PersistentClient(
                path=self.chroma_persist_dir,
                settings=Settings(allow_reset=True)
            )
            
            # Crear o obtener colección
            try:
                self.collection = self.chroma_client.get_collection(self.collection_name)
                logger.info(f"Colección existente encontrada: {self.collection_name}")
            except:
                self.collection = self.chroma_client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "React/TypeScript repository vectorization"}
                )
                logger.info(f"Nueva colección creada: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"Error configurando clientes: {e}")
            raise

    def _should_process_file(self, file_path: Path) -> bool:
        """Determinar si un archivo debe ser procesado"""
        # Verificar extensión
        if file_path.suffix not in self.supported_extensions:
            return False
            
        # Verificar si está en directorio ignorado
        for part in file_path.parts:
            if part in self.ignore_dirs:
                return False
                
        # Verificar nombre de archivo
        if file_path.name in self.ignore_files:
            return False
            
        # Verificar tamaño (ignorar archivos muy grandes > 1MB)
        try:
            if file_path.stat().st_size > 1024 * 1024:
                logger.warning(f"Archivo muy grande ignorado: {file_path}")
                return False
        except:
            return False
            
        return True

    def _get_file_metadata(self, file_path: Path) -> Dict:
        """Extraer metadata del archivo"""
        stat = file_path.stat()
        relative_path = file_path.relative_to(self.repo_path)
        
        return {
            "file_path": str(relative_path),
            "file_name": file_path.name,
            "file_extension": file_path.suffix,
            "file_size": stat.st_size,
            "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "directory": str(relative_path.parent),
            "is_component": self._is_react_component(file_path),
            "is_test": self._is_test_file(file_path),
            "is_config": self._is_config_file(file_path)
        }

    def _is_react_component(self, file_path: Path) -> bool:
        """Determinar si es un componente React"""
        return (
            file_path.suffix in {'.tsx', '.jsx'} or
            'components' in str(file_path).lower() or
            file_path.name[0].isupper()
        )

    def _is_test_file(self, file_path: Path) -> bool:
        """Determinar si es un archivo de test"""
        name_lower = file_path.name.lower()
        return (
            '.test.' in name_lower or 
            '.spec.' in name_lower or
            '__tests__' in str(file_path).lower()
        )

    def _is_config_file(self, file_path: Path) -> bool:
        """Determinar si es un archivo de configuración"""
        name_lower = file_path.name.lower()
        return (
            'config' in name_lower or
            name_lower.startswith('.') or
            file_path.suffix in {'.json', '.yaml', '.yml'}
        )

    def _read_file_content(self, file_path: Path) -> Optional[FileContent]:
        """Leer contenido de archivo con manejo de errores"""
        try:
            # Intentar diferentes encodings
            encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
            content = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
                    
            if content is None:
                logger.warning(f"No se pudo decodificar: {file_path}")
                return None
                
            # Calcular hash del contenido usando SHA-256 (más seguro que MD5)
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            
            return FileContent(
                path=str(file_path.relative_to(self.repo_path)),
                content=content,
                size=len(content),
                hash=content_hash,
                metadata=self._get_file_metadata(file_path)
            )
            
        except Exception as e:
            logger.error(f"Error leyendo {file_path}: {e}")
            return None

    def _chunk_content(self, content: str, metadata: Dict) -> List[Dict]:
        """Dividir contenido en chunks optimizados"""
        if not content.strip():
            return []
            
        # Dividir por líneas primero
        lines = content.split('\n')
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for line in lines:
            line_tokens = len(self.tokenizer.encode(line))
            
            # Si la línea sola excede el límite, dividirla por caracteres
            if line_tokens > self.max_tokens_per_chunk:
                if current_chunk:
                    chunk_text = '\n'.join(current_chunk)
                    chunks.append(self._create_chunk_dict(chunk_text, metadata, len(chunks)))
                    current_chunk = []
                    current_tokens = 0
                
                # Dividir línea larga en sub-chunks
                for i in range(0, len(line), self.chunk_size):
                    sub_chunk = line[i:i + self.chunk_size]
                    chunks.append(self._create_chunk_dict(sub_chunk, metadata, len(chunks)))
                continue
            
            # Si agregar esta línea excede el límite, finalizar chunk actual
            if current_tokens + line_tokens > self.max_tokens_per_chunk:
                if current_chunk:
                    chunk_text = '\n'.join(current_chunk)
                    chunks.append(self._create_chunk_dict(chunk_text, metadata, len(chunks)))
                
                # Aplicar overlap manteniendo las últimas líneas
                overlap_lines = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else current_chunk
                current_chunk = overlap_lines + [line]
                current_tokens = sum(len(self.tokenizer.encode(l)) for l in current_chunk)
            else:
                current_chunk.append(line)
                current_tokens += line_tokens
        
        # Procesar chunk final
        if current_chunk:
            chunk_text = '\n'.join(current_chunk)
            chunks.append(self._create_chunk_dict(chunk_text, metadata, len(chunks)))
        
        return chunks

    def _create_chunk_dict(self, text: str, metadata: Dict, chunk_index: int) -> Dict:
        """Crear diccionario de chunk con metadata"""
        return {
            'text': text,
            'metadata': {
                **metadata,
                'chunk_index': chunk_index,
                'chunk_size': len(text),
                'token_count': len(self.tokenizer.encode(text))
            }
        }

    def _validar_respuesta_embedding(self, response_body: dict) -> List[float]:
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

    async def _get_embedding(self, text: str) -> Optional[List[float]]:
        """Obtener embedding usando Amazon Titan"""
        try:
            # Validar entrada
            if not text or not isinstance(text, str):
                logger.error("Texto de entrada inválido para embedding")
                return None
            
            # Preparar request para Bedrock
            body = json.dumps({
                "inputText": text[:8192]  # Titan tiene límite de tokens
            })
            
            # Llamar a Bedrock
            response = self.bedrock_client.invoke_model(
                modelId="amazon.titan-embed-text-v1",
                contentType="application/json",
                accept="application/json",
                body=body
            )
            
            # Procesar respuesta con validación
            response_body = json.loads(response['body'].read())
            
            # Validar estructura de respuesta
            embedding = self._validar_respuesta_embedding(response_body)
            
            logger.debug(f"Embedding obtenido exitosamente: {len(embedding)} dimensiones")
            return embedding
            
        except ValueError as e:
            logger.error(f"Error de validación en respuesta AWS: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error decodificando JSON de AWS: {e}")
            return None
        except Exception as e:
            logger.error(f"Error obteniendo embedding: {e}")
            return None

    async def _process_chunks_batch(self, chunks: List[Dict]) -> List[Dict]:
        """Procesar un batch de chunks para obtener embeddings"""
        tasks = []
        for chunk in chunks:
            task = self._get_embedding(chunk['text'])
            tasks.append(task)
        
        embeddings = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed_chunks = []
        for chunk, embedding in zip(chunks, embeddings):
            if isinstance(embedding, Exception):
                logger.error(f"Error procesando chunk: {embedding}")
                continue
            
            if embedding:
                chunk['embedding'] = embedding
                processed_chunks.append(chunk)
        
        return processed_chunks

    def _store_in_chromadb(self, chunks: List[Dict]) -> None:
        """Almacenar chunks en ChromaDB"""
        if not chunks:
            return
            
        ids = []
        embeddings = []
        metadatas = []
        documents = []
        
        for chunk in chunks:
            # Crear ID único usando SHA-256
            chunk_id = f"{chunk['metadata']['file_path']}_{chunk['metadata']['chunk_index']}"
            chunk_id = hashlib.sha256(chunk_id.encode()).hexdigest()
            
            ids.append(chunk_id)
            embeddings.append(chunk['embedding'])
            metadatas.append(chunk['metadata'])
            documents.append(chunk['text'])
        
        try:
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents
            )
            logger.info(f"Almacenados {len(chunks)} chunks en ChromaDB")
        except Exception as e:
            logger.error(f"Error almacenando en ChromaDB: {e}")

    def _get_all_files(self) -> Generator[Path, None, None]:
        """Generador que yielda todos los archivos a procesar"""
        for file_path in self.repo_path.rglob("*"):
            if file_path.is_file() and self._should_process_file(file_path):
                yield file_path

    async def vectorize_repository(self) -> None:
        """Función principal para vectorizar el repositorio"""
        logger.info(f"Iniciando vectorización de: {self.repo_path}")
        logger.info(f"Guardando en: {self.chroma_persist_dir}")
        
        # Contadores
        total_files = 0
        processed_files = 0
        total_chunks = 0
        
        # Obtener lista de archivos
        files = list(self._get_all_files())
        total_files = len(files)
        logger.info(f"Encontrados {total_files} archivos para procesar")
        
        # Procesar archivos en batches
        for i in range(0, total_files, self.batch_size):
            batch_files = files[i:i + self.batch_size]
            batch_chunks = []
            
            # Leer archivos del batch
            for file_path in batch_files:
                file_content = self._read_file_content(file_path)
                if file_content:
                    chunks = self._chunk_content(file_content.content, file_content.metadata)
                    batch_chunks.extend(chunks)
                    processed_files += 1
                    
                    if processed_files % 10 == 0:
                        logger.info(f"Procesados {processed_files}/{total_files} archivos")
            
            # Obtener embeddings para el batch
            if batch_chunks:
                processed_chunks = await self._process_chunks_batch(batch_chunks)
                total_chunks += len(processed_chunks)
                
                # Almacenar en ChromaDB
                self._store_in_chromadb(processed_chunks)
                
                # Liberar memoria
                del batch_chunks, processed_chunks
                gc.collect()
        
        logger.info(f"Vectorización completada:")
        logger.info(f"- Archivos procesados: {processed_files}/{total_files}")
        logger.info(f"- Total chunks creados: {total_chunks}")
        logger.info(f"- Colección: {self.collection_name}")

def main():
    parser = argparse.ArgumentParser(description="Vectorizar repositorio React/TypeScript")
    parser.add_argument("--repo-path", default="./repository/sas-fa-web-frontend/src", 
                       help="Ruta al directorio src del repositorio")
    parser.add_argument("--chroma-dir", default="./chroma_db", 
                       help="Directorio para la base de datos ChromaDB")
    parser.add_argument("--collection-name", default="react_typescript_code", 
                       help="Nombre de la colección en ChromaDB")
    parser.add_argument("--aws-region", default="us-east-1", 
                       help="Región de AWS para Bedrock")
    parser.add_argument("--batch-size", type=int, default=10, 
                       help="Tamaño del batch para procesamiento")
    parser.add_argument("--max-workers", type=int, default=4, 
                       help="Número máximo de workers concurrentes")
    
    args = parser.parse_args()
    
    # Verificar que el directorio existe
    if not os.path.exists(args.repo_path):
        logger.error(f"El directorio {args.repo_path} no existe")
        return
    
    # Crear vectorizador
    vectorizer = RepositoryVectorizer(
        repo_path=args.repo_path,
        chroma_persist_dir=args.chroma_dir,
        collection_name=args.collection_name,
        aws_region=args.aws_region,
        batch_size=args.batch_size,
        max_workers=args.max_workers
    )
    
    # Ejecutar vectorización
    try:
        asyncio.run(vectorizer.vectorize_repository())
        logger.info("¡Vectorización completada exitosamente!")
    except Exception as e:
        logger.error(f"Error durante la vectorización: {e}")
        raise

if __name__ == "__main__":
    main()