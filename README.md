# 🤖 DocuBot

Un agente RAG (Retrieval Augmented Generation) inteligente que utiliza **AWS Bedrock**, **ChromaDB** y **Claude 4 Sonnet** para analizar repositorios de código y generar documentación técnica automáticamente.

## 🎯 ¿Qué hace este proyecto?

- **Vectoriza** tu código fuente para búsqueda semántica inteligente
- **Analiza** automáticamente la estructura y funcionalidad del proyecto
- **Genera** documentación técnica profesional en formato Markdown
- **Monitorea** todo el proceso con logs detallados en tiempo real

### 🧠 Potenciado por Claude 4 Sonnet

Este proyecto utiliza **Claude 4 Sonnet**, el modelo más avanzado de Anthropic, que ofrece:
- **Comprensión superior** de código complejo y arquitecturas
- **Análisis contextual profundo** de patrones y dependencias
- **Generación de documentación** más precisa y detallada
- **Razonamiento mejorado** para identificar funcionalidades clave

## 📋 Requisitos Previos

Antes de comenzar, asegúrate de tener:

- **Python 3.8 o superior** instalado
- **Cuenta de AWS** con acceso a Amazon Bedrock
- **Credenciales de AWS** configuradas
- **Git** para clonar repositorios (opcional)

## 🚀 Instalación Paso a Paso

### 1. Clonar o Descargar el Proyecto

```bash
# Si tienes el proyecto en Git
git clone <url-del-repositorio>
cd docubot

# O simplemente descarga y extrae el ZIP
```

### 2. Crear Entorno Virtual

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Windows (PowerShell):
venv\Scripts\Activate.ps1

# En Windows (CMD):
venv\Scripts\activate.bat

# En Linux/Mac:
source venv/bin/activate
```

### 3. Instalar Dependencias

```bash
# Instalar todas las dependencias
pip install -r requirements.txt
```

**Dependencias principales:**
- `chromadb` - Base de datos vectorial
- `boto3` - Cliente AWS para Bedrock
- `langchain-aws` - Integración LangChain con AWS
- `langchain-core` - Núcleo de LangChain
- `langgraph` - Framework para agentes
- `tiktoken` - Tokenización
- `python-dotenv` - Variables de entorno

### 4. Configurar AWS Bedrock

#### Opción A: Variables de Entorno
Crea un archivo `.env` en la raíz del proyecto:

```env
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=tu_access_key_aqui
AWS_SECRET_ACCESS_KEY=tu_secret_key_aqui
```

#### Opción B: AWS CLI (Recomendado)
```bash
# Instalar AWS CLI si no lo tienes
pip install awscli

# Configurar credenciales
aws configure
```

### 5. Verificar Acceso a Bedrock

```bash
# Verificar que tienes acceso a los modelos necesarios
aws bedrock list-foundation-models --region us-east-1
```

**Modelos requeridos:**
- `amazon.titan-embed-text-v1` (para embeddings)
- `us.anthropic.claude-sonnet-4-20250514-v1:0` (para generación con Claude 4)

> **⚠️ Importante**: Claude 4 Sonnet requiere acceso especial en AWS Bedrock. Asegúrate de:
> 1. Solicitar acceso al modelo en la consola de AWS Bedrock
> 2. Verificar que tu cuenta tiene los permisos necesarios
> 3. Confirmar que el modelo está disponible en tu región

## 📁 Preparar tu Repositorio de Código

### Estructura Recomendada

```
docubot/
├── repository/                    # 👈 Coloca aquí tu código
│   └── tu-proyecto/
│       └── src/
│           ├── components/
│           ├── pages/
│           ├── utils/
│           └── ...
├── chroma_db/                     # Se crea automáticamente
├── logs/                          # Se crea automáticamente
├── vectorize_repo.py
├── agent.py
└── requirements.txt
```

### Copiar tu Proyecto

```bash
# Crear directorio repository si no existe
mkdir -p repository

# Copiar tu proyecto (ejemplo)
cp -r /ruta/a/tu/proyecto repository/mi-proyecto

# O clonar desde Git
cd repository
git clone https://github.com/usuario/mi-proyecto.git
```

## 🔄 Uso Completo: De la Vectorización a la Documentación

### PASO 1: Vectorizar el Repositorio

Este paso convierte tu código en vectores para búsqueda semántica.

```bash
# Vectorización básica (usa ./repository/sas-fa-web-frontend/src por defecto)
python vectorize_repo.py

# Vectorización personalizada
python vectorize_repo.py \
    --repo-path "./repository/mi-proyecto/src" \
    --chroma-dir "./chroma_db" \
    --collection-name "mi_proyecto_code" \
    --batch-size 10
```

**Parámetros disponibles:**
- `--repo-path`: Ruta al código fuente
- `--chroma-dir`: Directorio para ChromaDB
- `--collection-name`: Nombre de la colección
- `--batch-size`: Archivos por lote (ajustar según RAM)
- `--aws-region`: Región de AWS

**¿Qué archivos procesa?**
- `.ts`, `.tsx`, `.js`, `.jsx` (React/TypeScript)
- `.json`, `.yaml`, `.yml` (Configuración)
- `.css`, `.scss`, `.sass`, `.less` (Estilos)
- `.html`, `.md`, `.mdx` (Documentación)

**Salida esperada:**
```
2024-01-15 10:30:15 - INFO - Iniciando vectorización de: ./repository/mi-proyecto/src
2024-01-15 10:30:16 - INFO - Encontrados 245 archivos para procesar
2024-01-15 10:30:20 - INFO - Procesados 10/245 archivos
...
2024-01-15 10:35:42 - INFO - Vectorización completada:
2024-01-15 10:35:42 - INFO - - Archivos procesados: 245/245
2024-01-15 10:35:42 - INFO - - Total chunks creados: 1,847
```

### PASO 2: Generar Documentación

Una vez vectorizado, ejecuta el agente documentador:

```bash
# Ejecutar agente documentador
python agent.py
```

**El agente automáticamente:**
1. 🔍 Analiza la estructura del proyecto con **Claude 4**
2. 📊 Genera estadísticas detalladas del repositorio
3. 📝 Crea documentación técnica por módulos
4. 🔗 Genera índices y referencias cruzadas
5. 📋 Identifica áreas sin documentar
6. 🧠 Comprende patrones complejos y arquitecturas avanzadas

### PASO 3: Monitorear el Proceso (Opcional)

Abre una segunda terminal para monitorear en tiempo real:

```bash
# Monitor básico del log más reciente
python monitor_logs.py

# Solo mostrar actividad de herramientas
python monitor_logs.py --herramientas

# Filtrar por nivel de log
python monitor_logs.py --nivel INFO

# Ver estadísticas del proceso
python monitor_logs.py --stats

# Listar todos los logs disponibles
python monitor_logs.py --listar

# Monitorear un log específico
python monitor_logs.py --archivo logs/agente_documentador_20241215_143022.log
```

## 📊 Resultados Generados

Después de ejecutar el agente, encontrarás:

### Documentación Principal
```
📄 00_INDICE_DOCUMENTACION.md      # Índice principal navegable
📄 01_resumen_general.md           # Resumen ejecutivo del proyecto
📄 02_modulo_*.md                  # Documentación detallada por módulos
📄 99_resumen_puntos_sin_documentar.md  # Áreas que necesitan atención
```

### Archivos del Sistema
```
📁 chroma_db/                      # Base de datos vectorial
📁 logs/                          # Logs detallados del proceso
   └── agente_documentador_YYYYMMDD_HHMMSS.log
```

## 🛠️ Herramientas del Agente

El agente utiliza 13 herramientas especializadas:

### 🔍 **Búsqueda y Análisis**
- **buscar_codigo**: Búsqueda semántica inteligente
- **buscar_referencias**: Encuentra uso de funciones/variables
- **analizar_importaciones**: Mapea dependencias

### 🧭 **Navegación del Sistema**
- **obtener_archivo**: Lee contenido completo
- **listar_directorio**: Explora estructura
- **encontrar_archivos**: Busca por patrones
- **obtener_metadatos_archivo**: Información detallada

### 📊 **Estadísticas**
- **estadisticas_repositorio**: Métricas completas del proyecto

### ✍️ **Generación de Documentación**
- **escribir_markdown**: Crea documentos estructurados
- **crear_documentacion_repositorio**: Documentación automática
- **crear_reporte_analisis**: Reportes profesionales
- **agregar_contenido_markdown**: Extiende documentos
- **crear_indice_archivos**: Genera índices navegables

## 🎯 Ejemplos de Uso

### Para Proyecto React/TypeScript
```bash
# 1. Copiar proyecto
cp -r /mi/app/react repository/mi-app

# 2. Vectorizar
python vectorize_repo.py --repo-path "./repository/mi-app/src"

# 3. Documentar
python agent.py
```

### Para Múltiples Proyectos
```bash
# Proyecto 1
python vectorize_repo.py \
    --repo-path "./repository/proyecto1/src" \
    --collection-name "proyecto1_code"

# Proyecto 2
python vectorize_repo.py \
    --repo-path "./repository/proyecto2/src" \
    --collection-name "proyecto2_code"
```

### Para Proyectos Grandes
```bash
# Reducir batch size para proyectos grandes
python vectorize_repo.py \
    --repo-path "./repository/proyecto-grande/src" \
    --batch-size 5 \
    --max-workers 2
```

## ⚙️ Configuración Avanzada

### Personalizar Tipos de Archivo

Edita `vectorize_repo.py` línea ~70:

```python
self.supported_extensions = {
    '.ts', '.tsx', '.js', '.jsx',    # React/TypeScript
    '.vue',                          # Vue.js
    '.svelte',                       # Svelte
    '.py',                           # Python
    '.java', '.kt',                  # Java/Kotlin
    '.go', '.rs'                     # Go/Rust
}
```

### Ajustar Parámetros de Chunking

```python
chunk_size=500,              # Líneas por chunk
chunk_overlap=50,            # Overlap entre chunks
max_tokens_per_chunk=2000    # Límite de tokens por chunk
```

### Directorios a Ignorar

```python
self.ignore_dirs = {
    'node_modules', '.git', '.next', 'build', 'dist',
    'coverage', '.nyc_output', 'tmp', 'temp',
    'vendor', '__pycache__'  # Añadir más según necesidad
}
```

## 🚨 Solución de Problemas

### Error: "No module named 'chromadb'"
```bash
# Verificar que el entorno virtual está activo
pip list | grep chromadb

# Reinstalar si es necesario
pip install --upgrade chromadb
```

### Error: "Unable to locate credentials"
```bash
# Verificar configuración AWS
aws configure list

# Configurar credenciales
aws configure

# O verificar variables de entorno
echo $AWS_ACCESS_KEY_ID
```

### Error: "Access denied to model"
```bash
# Verificar acceso a Bedrock en la consola AWS
# Ir a: AWS Console > Bedrock > Model access
# Solicitar acceso a los modelos necesarios
```

**Para Claude 4 específicamente:**
1. Ve a AWS Console > Bedrock > Model access
2. Busca "Claude 4 Sonnet" en la lista
3. Solicita acceso si no está habilitado
4. Espera la aprobación (puede tomar unos minutos)
5. Verifica que el modelo ID sea exactamente: `us.anthropic.claude-sonnet-4-20250514-v1:0`

### ChromaDB Corrupta
```bash
# Eliminar base de datos y recrear
rm -rf chroma_db/
python vectorize_repo.py
```

### Memoria Insuficiente
```bash
# Reducir batch size
python vectorize_repo.py --batch-size 3 --max-workers 1
```

### Archivos No Procesados
```bash
# Verificar logs de vectorización
tail -f vectorization.log

# Verificar extensiones soportadas
grep "supported_extensions" vectorize_repo.py
```

## 📈 Optimización del Rendimiento

### Para Proyectos Pequeños (< 100 archivos)
```bash
python vectorize_repo.py --batch-size 20 --max-workers 8
```

### Para Proyectos Medianos (100-500 archivos)
```bash
python vectorize_repo.py --batch-size 10 --max-workers 4
```

### Para Proyectos Grandes (> 500 archivos)
```bash
python vectorize_repo.py --batch-size 5 --max-workers 2
```

### Monitoreo de Recursos
```bash
# En otra terminal, monitorear uso de memoria
watch -n 2 'ps aux | grep python'

# Monitorear logs en tiempo real
python monitor_logs.py --herramientas
```

## 🔒 Consideraciones de Seguridad

- ✅ **Datos locales**: Todo se procesa localmente
- ✅ **AWS Bedrock**: Solo se envían chunks de código (no archivos completos)
- ✅ **Sin almacenamiento externo**: ChromaDB es local
- ⚠️ **Credenciales AWS**: Mantén seguras tus credenciales
- ⚠️ **Código sensible**: Revisa que no haya secretos en el código

## 📝 Logs y Monitoreo

### Tipos de Logs
- **vectorization.log**: Proceso de vectorización
- **agente_documentador_*.log**: Actividad del agente
- **Logs en tiempo real**: Via monitor_logs.py

### Niveles de Log
- **INFO**: Eventos importantes
- **DEBUG**: Detalles técnicos
- **WARNING**: Situaciones de atención
- **ERROR**: Errores y excepciones

## 🤝 Contribuir

Para contribuir al proyecto:

1. Fork el repositorio
2. Crea una rama para tu feature
3. Implementa mejoras
4. Añade tests si es necesario
5. Envía un Pull Request

## 📄 Licencia

Este proyecto está licenciado bajo la [Licencia MIT](LICENSE) - ver el archivo LICENSE para más detalles.

## 🆘 Soporte

Si encuentras problemas:

1. **Revisa los logs**: `python monitor_logs.py --stats`
2. **Verifica configuración**: AWS credentials, Python version
3. **Consulta troubleshooting**: Sección de solución de problemas
4. **Abre un issue**: Con logs y detalles del error

---

## 🎉 ¡Listo para Usar!

Ahora tienes todo lo necesario para:
- ✅ Vectorizar cualquier repositorio de código
- ✅ Generar documentación técnica automática
- ✅ Monitorear el proceso en tiempo real
- ✅ Personalizar según tus necesidades

**¡Comienza documentando tu primer proyecto!** 🚀 