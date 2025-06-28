# api.py (COMPLETO y CORREGIDO con endpoints para Generacion, Config y GESTION DE ARTICULOS/CANVAS)
# Expone endpoints para cargar configuracion, disparar generacion y gestionar articulos generados.
# Genera sugerencias del Copiloto dinámicamente en el endpoint GET /articles/{id}.

import json
# Importar typing List y Optional para type hinting
from typing import (  # Importar Dict y Any para type hinting de diccionarios
    Any, Dict, List, Optional)

# Importar FastAPI y middleware CORS
# Importar el módulo copilot
import copilot  # <-- Importar el módulo copilot
# Importar los módulos de lógica de negocio/herramientas
import database
# Importar mock_publisher para la generación de previsualización HTML
import mock_publisher
import pipeline
# Importar web_tools para verificar API keys (opcional en startup)
import web_tools
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
# Importar los modelos Pydantic necesarios (incluyendo los de articulos generados y config)
from models import (  # Modelos para articulos generados; SourceArticleSummary, SectionListResponse, ChatRequestModel, ChatResponseModel, ConfigDB, ConfigUpdateRequestModel # Estos para otros endpoints futuros
    ConfigBase, GeneratedArticleDB, GeneratedArticleSummary,
    GeneratedArticleUpdate, GenerateRequestModel)
# Importar Field de Pydantic si no está ya importado globalmente
from pydantic import Field  # Si Field no estaba importado al inicio
from starlette.concurrency import run_in_threadpool

# === Configuración de FastAPI ===
app = FastAPI(
    title="SEO-Copilot API",
    description="API del Asistente de Contenido Inteligente (SEO-Copilot).",
    version="0.1.0",
    # Eliminado lifespan = lifespan
)

# === Configuración de CORS (Permisiva para Hackathon) ===
# ¡¡¡ ESTE BLOQUE DEBE ESTAR DESCOMENTADO Y ASÍ !!!
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Permite CUALQUIER origen, incluyendo 'null' para archivos locales
    allow_credentials=True, # Permite credenciales (cookies, auth headers)
    allow_methods=["*"], # Permite todos los métodos (GET, POST, PUT, DELETE)
    allow_headers=["*"], # Permite todos los headers
)


# === Evento de Inicio: Inicializar DB ===
# Esto se ejecuta UNA VEZ cuando el servidor arranca.
@app.on_event("startup")
def startup_event():
    """Inicializa la base de datos al arrancar la aplicación."""
    print("--- API Startup: Inicializando base de datos ---")
    try:
        # Asegurarse de que database.py tiene la función inicializar_db
        database.inicializar_db()
        print("✅ API Startup: Base de datos inicializada.")
    except Exception as e:
        print(f"❌ API Startup: Error al inicializar la base de datos: {str(e)}")
        # Considerar logging o manejo de errores al inicio

    print("--- API Startup: Completo ---")

    # Opcional: Verificar claves de API al inicio si son criticas para el pipeline
    # Asegurarse de que web_tools está importado globalmente si se usa aquí
    if web_tools.UNSPLASH_ACCESS_KEY == "TU_UNSPLASH_ACCESS_KEY":
         print("⚠️ Advertencia: La clave de Unsplash API no está configurada en web_tools.py. La búsqueda de imágenes fallará.")
    # Verificar Gemini key (si llm_client o analyzer tienen una forma de verificarla sin llamar a la API)


# === MODELO DE RESPUESTA ESPECÍFICO PARA GET /articles/{id} ===
# Define este modelo *dentro* de api.py (o en models.py si quieres, pero aquí es más local)
# Este modelo hereda de GeneratedArticleDB y añade el campo 'suggestions'.
class ArticleDetailsResponse(GeneratedArticleDB):
     """Modelo de respuesta para GET /articles/{id} que incluye sugerencias."""
     suggestions: Optional[str] = Field(None, description="Sugerencias de mejora generadas por el Copiloto.")
     # Nota: Al heredar de GeneratedArticleDB, todos sus campos se copian.
     # Asegurarse de que GeneratedArticleDB es compatible con el dict de database.get_generated_article_by_id
     # GeneratedArticleDB ya tiene orm_mode=True, esto se hereda.


# === ENDPOINTS ESENCIALES (Generacion, Config y GESTION DE ARTICULOS/CANVAS) ===

# --- Endpoint para Obtener Configuración por Tema ---
@app.get("/config/{tema}", response_model=ConfigBase) # Retorna ConfigBase
async def get_theme_config(tema: str):
    """
    Obtiene la configuración para un tema (sección).
    Si no existe configuración guardada, retorna los valores por defecto (de Pydantic).
    """
    print(f"➡️ API: Recibida solicitud para obtener configuración del tema '{tema}'")
    # database.get_config retorna un dict con la config guardada o un dict vacio {}
    # La función get_config en database.py no filtra campos, retorna *todos* los de la fila DB.
    config_dict_from_db = database.get_config(tema)

    # Pydantic (response_model=ConfigBase) usará los defaults definidos en el modelo ConfigBase
    # si los campos faltan en config_dict_from_db (cuando es {} o la fila no tiene valor).
    # Asegúrate de que ConfigBase tiene defaults en Field() para los campos no Optional.
    # También, make sure database.get_config returns keys compatible with ConfigBase names.

    if not config_dict_from_db:
        print(f"✅ API: No se encontró configuración guardada para tema '{tema}'. Retornando defaults de modelo.")
        # Al retornar un dict vacío {}. Pydantic usará sus defaults definidos en ConfigBase.
        # Pydantic V2: Usar model_validate para aplicar defaults del modelo si se parte de un dict vacío
        # Create an instance of ConfigBase with the theme, Pydantic will apply its defaults
        config_base_instance = ConfigBase(tema=tema)
        # Return the dictionary representation of the instance. Pydantic will apply defaults.
        # Note: This requires ConfigBase to have defaults in Field()
        return config_base_instance.model_dump() # Pydantic V2
        # return config_base_instance.dict() # Pydantic V1


    else:
        print(f"✅ API: Retornando configuración guardada para tema '{tema}'.")
        # Retornar el dict de la DB. Pydantic (response_model=ConfigBase) lo validará y serializará.
        # Pydantic usará los valores del dict, ignorando sus propios defaults si el campo tiene valor.
        return config_dict_from_db # Retornar el diccionario de la DB


# --- Endpoint de Generación ---
@app.post("/generate", status_code=status.HTTP_202_ACCEPTED) # Usar 202 Accepted si es asíncrono
async def generate_article(generate_request: GenerateRequestModel):
    """
    Dispara el pipeline completo de generación de contenido para un tema.
    Recibe todos los parámetros de configuración desde la UI.
    """
    tema = generate_request.tema
    print(f"➡️ API: Recibida solicitud de generación para tema '{tema}'. Parámetros recibidos:")
    # Pydantic V2: generate_request.model_dump()
    # Pydantic V1: generate_request.dict()
    print(json.dumps(generate_request.model_dump(), indent=2))


    # Validar que las claves de API están configuradas (crítico para el pipeline)
    # Es mejor validar esto en el pipeline mismo o en los módulos que las usan (web_tools, llm_client)
    # Pero un check rápido aquí no está de más.
    # if web_tools.UNSPLASH_ACCESS_KEY == "TU_UNSPLASH_ACCESS_KEY":
    #      print("❌ API: Unsplash API key no configurada.")
    #      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsplash API key no configurada.")
    # ... similar check for Gemini ...


    # --- Ejecutar el pipeline ---
    # Asegurarse de que pipeline está importado globalmente
    article_id = await pipeline.run_full_generation_pipeline(generate_request)

    if article_id is not None:
        print(f"✅ API: Generación completada para tema '{tema}'. Artículo ID: {article_id}")
        return {"message": "Generación completada exitosamente", "article_id": article_id}
    else:
        # Si el pipeline retorna None, indica un fallo interno (ya se imprimieron errores en consola)
        print(f"❌ API: Fallo en el pipeline de generación para tema '{tema}'.")
        # El pipeline debe imprimir los detalles del error.
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Fallo en el pipeline de generación.")


# === ENDPOINTS PARA GESTIÓN DE ARTÍCULOS (PARA EL CANVAS) ===

@app.get("/articles", response_model=List[GeneratedArticleSummary])
async def list_articles(tema: Optional[str] = None, estado: Optional[str] = None):
    """
    Lista artículos generados, opcionalmente filtrados por tema/sección o estado.
    """
    print(f"➡️ API: Recibida solicitud para listar artículos generados (Tema={tema}, Estado={estado}).")
    # Asegurarse de que database.get_all_generated_articles existe en database.py
    articles = database.get_all_generated_articles(tema=tema, estado=estado)
    print(f"✅ API: Retornando {len(articles)} artículos generados.")
    # database.get_all_generated_articles debe retornar list of dicts compatible with GeneratedArticleSummary
    # Pydantic (response_model=List[GeneratedArticleSummary]) lo validará y serializará automáticamente.
    return articles


# --- Endpoint para Obtener Detalles del Artículo (Incluyendo Sugerencias Dinámicas) ---
# Usa el modelo de respuesta ArticleDetailsResponse que incluye 'suggestions'
@app.get("/articles/{article_id}", response_model=GeneratedArticleDB) # NO ESPERA suggestions AHORA
async def get_article_details(article_id: int):
    """
    Obtiene los detalles completos de un artículo generado por su ID, incluyendo imágenes.
    NO genera sugerencias aquí.
    """
    print(f"➡️ API: Recibida solicitud para obtener detalles del artículo ID {article_id}.")
    article_data = database.get_generated_article_by_id(article_id) # Carga el dict de la DB (sin 'suggestions')

    if article_data:
        print(f"✅ API: Artículo ID {article_id} y {len(article_data.get('imagenes', []))} imágenes asociadas cargados.")
        
        return article_data # Retorna el dict tal cual de la DB

    else:
        print(f"❌ API: Artículo ID {article_id} no encontrado.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artículo no encontrado.")


# --- Endpoint para Actualizar Artículo ---
@app.put("/articles/{article_id}", status_code=status.HTTP_200_OK)
async def update_article(article_id: int, updated_data: GeneratedArticleUpdate):
    """
    Actualiza los campos de un artículo generado (desde el Canvas).
    """
    print(f"➡️ API: Recibida solicitud para actualizar artículo ID {article_id}.")
    # updated_data es una instancia validada de GeneratedArticleUpdate
    # Asegurarse de que database.update_generated_article existe en database.py
    updated_data_dict = updated_data.model_dump(exclude_unset=True) # Pydantic V2
    # updated_data_dict = updated_data.dict(exclude_unset=True) # Pydantic V1
    # exclude_unset=True asegura que solo se pasan los campos que fueron enviados en la request (los editados)

    if not updated_data_dict:
         print(f"⚠️ API: Solicitud de actualización para ID {article_id} sin datos para actualizar.")
         # Retornar una respuesta de éxito si no hay datos para actualizar, es una operación válida
         return {"message": "No hay datos para actualizar."} # O status 204 No Content

    success = database.update_generated_article(article_id, updated_data_dict)

    if success:
        print(f"✅ API: Artículo ID {article_id} actualizado exitosamente.")
        return {"message": f"Artículo ID {article_id} actualizado exitosamente."}
    else:
        # database.update_generated_article debe retornar False e imprimir errores o "no encontrado"
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Fallo al actualizar artículo ID {article_id}.")


# --- Endpoint Raíz (Opcional) ---
@app.get("/")
async def read_root():
    return {"message": "SEO-Copilot API está funcionando."}

# --- Endpoint de Salud (Opcional, buena práctica) ---
@app.get("/health")
async def health_check():
    # Podrías añadir aquí checks a la DB u otros servicios
    return {"status": "ok"}

# === NUEVO ENDPOINT: Generar Sugerencias para un Artículo ===
@app.post("/articles/{article_id}/generate-suggestions") # Usar POST para disparar una accion
async def generate_suggestions_for_article(article_id: int):
    """
    Dispara la generación de sugerencias de mejora para un artículo específico.
    """
    print(f"➡️ API: Recibida solicitud para generar sugerencias para artículo ID {article_id}.")

    # Cargar los datos del artículo de la DB
    # Necesitamos el body, titulo, tema, etc. para pasarlos al Copiloto.
    # database.get_generated_article_by_id debe retornar un dict con todos esos campos.
    article_data = database.get_generated_article_by_id(article_id)

    if not article_data:
        print(f"❌ API: Artículo ID {article_id} no encontrado para generar sugerencias.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artículo no encontrado.")

    # --- Ejecutar la función síncrona de generar sugerencias ---
    # La función generate_article_suggestions es SÍNCRONA.
    # Si el endpoint es async def, ejecutar una función síncrona bloquea el loop de eventos.
    # Para evitar bloquear, podemos ejecutar la función síncrona en un threadpool.
    # FastAPI proporciona run_in_threadpool de starlette.concurrency.

    from starlette.concurrency import \
        run_in_threadpool  # Importar run_in_threadpool

    print(f"🧠 API: Ejecutando generación de sugerencias para ID {article_id} en threadpool...")
    # Llamar a la función síncrona copilot.generate_article_suggestions
    article_suggestions = await run_in_threadpool(copilot.generate_article_suggestions, article_data)
    # ==============================================================

    print(f"✅ API: Sugerencias generadas para artículo ID {article_id}.")

    # Retornar las sugerencias como texto plano o envueltas en un objeto
    return {"suggestions": article_suggestions} # Devolver como JSON con una clave 'suggestions'

# api.py (Corregir llamada a mock_publisher.publish_to_html en publish_article)

# ... (otros imports y código) ...

@app.post("/articles/{article_id}/publish", status_code=status.HTTP_200_OK)
async def publish_article(article_id: int):
    """
    "Publica" un artículo generado (genera la previsualización HTML).
    """
    print(f"➡️ API: Recibida solicitud de publicación para artículo ID {article_id}.")

    # 1. Cargar los datos completos del artículo de la DB (incluyendo imágenes)
    # database.get_generated_article_by_id retorna un dict con la clave 'imagenes' (lista de dicts)
    article_data = database.get_generated_article_by_id(article_id)

    if not article_data:
        print(f"❌ API: Artículo ID {article_id} no encontrado para publicar.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artículo no encontrado.")

    # === Generar sugerencias... (opcional) ===
    # ...


    # 2. Generar la previsualización HTML usando mock_publisher
    print(f"🚀 API: Generando previsualización HTML para artículo ID {article_id}...")
    try:
        # Generar un nombre de archivo
        tema_slug = article_data.get('tema', 'articulo').replace(' ', '_')[:30]
        titulo_slug = article_data.get('titulo', 'preview').replace(' ', '_').replace('/', '_')[:50]
        filename_preview = f"{tema_slug}_{titulo_slug}_{article_id}_preview.html"

        # mock_publisher.publish_to_html espera article_data (dict completo) y image_data (LISTA SEPARADA)
        # La lista de imágenes está en article_data['imagenes']
        # === PASAR image_data EXPLÍCITAMENTE ===
        mock_publisher.publish_to_html(
            article_data, # Pasa el diccionario completo (con título, body, etc.)
            image_data=article_data.get('imagenes'), # <--- PASAR LA LISTA DE IMÁGENES COMO image_data
            filename=filename_preview
        )
        # =====================================

        print(f"✅ API: Previsualización HTML generada para artículo ID {article_id}.")

        return {"message": f"Artículo ID {article_id} 'publicado' (previsualización HTML generada). Archivo: {filename_preview}"}

    except Exception as e:
        print(f"❌ API: Falló la publicación/generación HTML para artículo ID {article_id}: {str(e)}")
        # Loggear el error completo del traceback en el terminal de FastAPI
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Fallo al publicar artículo ID {article_id}.")
# === ENDPOINT para Actualizar Artículo ===
@app.put("/articles/{article_id}", status_code=status.HTTP_200_OK) # <--- ESTE ENDPOINT DEBE EXISTIR
async def update_article(article_id: int, updated_data: GeneratedArticleUpdate):
    """
    Actualiza los campos de un artículo generado (desde el Canvas).
    """
    print(f"➡️ API: Recibida solicitud para actualizar artículo ID {article_id}.")
    # updated_data es una instancia validada de GeneratedArticleUpdate
    # Asegurarse de que database.update_generated_article existe en database.py
    updated_data_dict = updated_data.model_dump(exclude_unset=True) # Pydantic V2
    # updated_data_dict = updated_data.dict(exclude_unset=True) # Pydantic V1

    if not updated_data_dict:
         print(f"⚠️ API: Solicitud de actualización para ID {article_id} sin datos para actualizar.")
         return {"message": "No hay datos para actualizar."}

    success = database.update_generated_article(article_id, updated_data_dict) # Asegurarse de que esta funcion existe en database.py

    if success:
        print(f"✅ API: Artículo ID {article_id} actualizado exitosamente.")
        return {"message": f"Artículo ID {article_id} actualizado exitosamente."}
    else:
        # database.update_generated_article debe retornar False e imprimir errores o "no encontrado"
        # Si retorna False, asumimos que el fallo es interno o no se encontro el ID para actualizar.
        # Podrias querer lanzar un 404 aqui si update_generated_article puede indicar que no se encontro el ID.
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Fallo al actualizar artículo ID {article_id}.") # O un 404 si el ID no existia

@app.post("/articles/{article_id}/rewrite", status_code=status.HTTP_200_OK) # Usar POST para disparar una accion, 200 OK si se completa sincrono
async def regenerate_article_content_endpoint(article_id: int, instruction_data: Dict[str, str]):
    """
    Dispara la regeneración de contenido para un artículo específico basada en una instrucción
    (ej. sugerencias aplicadas).
    Recibe un JSON con {'text_to_rewrite': '...', 'instruction': '...'}.
    Retorna {"rewritten_text": "..."}, o un mensaje de error si falla.
    """
    print(f"➡️ API: Recibida solicitud de regeneración para artículo ID {article_id}.")

    # Obtener el texto a reescribir (del Canvas) y la instrucción del payload
    text_to_rewrite = instruction_data.get('text_to_rewrite') # El texto actual del Canvas
    instruction = instruction_data.get('instruction') # La instruccion del usuario

    if not text_to_rewrite or not instruction:
         # Si la instrucción está vacía pero el texto no, podríamos permitirlo como "regenerar sin instrucción"
         # Pero para aplicar sugerencias seleccionadas, la instruction SIEMPRE vendrá.
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Se requieren 'text_to_rewrite' e 'instruction'.")


    # === Ejecutar la función síncrona de regeneración en un threadpool ===
    # Llamar a la función síncrona copilot.regenerate_article_content
    # Pasa el ID del artículo, el texto actual del Canvas y la instrucción.
    # copilot.regenerate_article_content se encarga de obtener el contexto y fuentes.
    print(f"🧠 API: Ejecutando regeneración para ID {article_id} en threadpool...")
    try:
        regenerated_article_result = await run_in_threadpool(
            copilot.regenerate_article_content,
            article_id,
            text_to_rewrite,
            instruction
        )
        # copilot.regenerate_article_content retorna { "rewritten_text": "..." } o None

    except Exception as e:
        print(f"❌ API: Error general durante la ejecución de copilot.regenerate_article_content para ID {article_id}: {str(e)}")
        # Loggear el error completo del traceback en el terminal de FastAPI
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Fallo interno del servidor al regenerar contenido: {str(e)}")


    if not regenerated_article_result:
         # Si copilot.regenerate_article_content retorna None, significa que falló internamente.
         print(f"❌ API: copilot.regenerate_article_content retornó None para ID {article_id}.")
         # El error específico ya debería haber sido impreso dentro de copilot o content_generator.
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"La regeneración de contenido falló para artículo ID {article_id}.")


    print(f"✅ API: Regeneración completada para artículo ID {article_id}.")

    # Retornar el resultado (el diccionario {"rewritten_text": ...})
    # FastAPI serializará automáticamente este diccionario a JSON.
    return regenerated_article_result