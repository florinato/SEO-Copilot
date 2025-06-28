# pipeline.py
# Orquesta el pipeline completo de generación de contenido.
# Carga parámetros de configuración por tema desde la DB.
# Usa plantillas de prompt HARDCODEADAS en analyzer.py y content_generator.py.
# Genera la previsualización HTML al finalizar con éxito.

import asyncio
import json  # Importar json para depurar config dicts
import os  # Importar os para manejo de rutas, si mock_publisher lo necesita o para debug
import re  # Importar re si mock_publisher lo necesita (para nombre de archivo)
from datetime import \
    datetime  # Importar datetime si mock_publisher lo necesita para timestamp

import content_generator
# Importar los módulos que contienen las "herramientas"
import database
import scraper
import web_tools
# Importar los modelos Pydantic
from models import (  # Importar GeneratedArticleDB si la función lo retornara (no lo hace ahora)
    GeneratedArticleDB, GenerateRequestModel)


# La función recibe el modelo GenerateRequestModel.
# Esta request model contiene los parámetros (numéricos, estilo)
# que se usarán para esta ejecución. La lógica para cargar la config
# desde la DB y construir este modelo reside en el llamador (ej. endpoint API).
async def run_full_generation_pipeline(generate_request: GenerateRequestModel):
    """
    Ejecuta el pipeline completo de generación de contenido
    basándose en los parámetros numéricos y de estilo proporcionados en la solicitud.
    Usa plantillas de prompt hardcodeadas en analyzer.py y content_generator.py.
    Genera la previsualización HTML al completar con éxito.
    """
    tema = generate_request.tema
    print(f"\n--- PIPELINE: Iniciando para '{tema}' ---")

    # Los parámetros numéricos y de estilo vienen directamente del GenerateRequestModel
    # Las plantillas de prompt NO se usan aquí, los módulos (analyzer, generator)
    # usan sus defaults hardcodeados.

    # Capturar los parámetros relevantes del modelo de request para pasarlos
    # Se asume que GenerateRequestModel tiene todos los campos de ConfigBase y sus defaults
    num_fuentes_scraper = generate_request.num_fuentes_scraper
    min_score_fuente = generate_request.min_score_fuente
    num_resultados_scraper = generate_request.num_resultados_scraper # Este es el límite de fuentes procesadas por scraper
    num_fuentes_generador = generate_request.num_fuentes_generador # Este es el límite de fuentes A USAR por generator
    longitud_texto = generate_request.longitud_texto
    tono_texto = generate_request.tono_texto
    num_imagenes_buscar = generate_request.num_imagenes_buscar


    # Variable para almacenar el ID del artículo generado si tiene éxito
    generated_article_id = None
    # Variable para almacenar los datos completos del artículo generado
    generated_article_data = None
    # Variable para almacenar la metadata de las imágenes encontradas
    found_images_metadata = None
    # Lista de IDs de fuentes usadas
    source_ids_used = []


    try:
        # === PASO 1: Buscar fuentes y obtener su contenido ===
        print("🔍 PIPELINE: Buscando y analizando fuentes...")
        # Pasar SOLO los parámetros numéricos relevantes y el tema a scraper.buscar_noticias
        # scraper.buscar_noticias ahora retorna lista de dicts con metadata Y 'full_content'
        # y guarda la metadata en la DB articulos (y añade el ID).
        sources_with_content = scraper.buscar_noticias(
            tema,
            num_noticias_a_buscar=num_fuentes_scraper,
            min_score_para_analizar=min_score_fuente,
            num_resultados_a_retornar=num_fuentes_generador # Usar este parametro para limitar cuántas fuentes pasar al generator
        )

        if not sources_with_content:
            print("❌ PIPELINE: No se encontraron fuentes útiles.")
            # En una implementación real, podrías registrar un error en la tabla generacion_tareas
            return None # Retornar None si no hay fuentes


        # === PASO 2: Generar el Artículo (texto) ===
        print("✍️ PIPELINE: Generando borrador de artículo...")
        # Pasar la lista de fuentes CON contenido y los parámetros de generación al generator
        # content_generator.generate_seo_content usará su plantilla hardcodeada
        generated_article_data = content_generator.generate_seo_content(
            tema,
            sources_with_content, # Lista de fuentes CON contenido (metadata + 'full_content')
            longitud=longitud_texto, # <-- Pasando args
            tono=tono_texto
        )

        if not generated_article_data:
            print("❌ PIPELINE: Falló la generación del borrador de texto.")
            # Registrar error en generacion_tareas si se usa
            return None

        # === PASO 3: Buscar Imágenes ===
        print("🖼️ PIPELINE: Buscando imágenes...")
        # La búsqueda de imágenes usa datos del artículo generado
        # Construir la query a partir del título y tags generados
        image_search_query = generated_article_data.get('title', tema) + " " + " ".join(generated_article_data.get('tags', []))
        image_search_query = image_search_query[:150].strip()

        # Pasar parámetro num_imagenes_buscar
        found_images_metadata = web_tools.find_free_images(
            image_search_query,
            num_results=num_imagenes_buscar # <-- Pasando arg
        )
        if not found_images_metadata:
             print("⚠️ PIPELINE: No se encontraron imágenes.")


        # === PASO 4: Guardar Artículo Generado y Metadata de Imágenes en DB ===
        print("💾 PIPELINE: Guardando artículo generado y metadata de imágenes...")
        # Asegurarse de que los datos del artículo incluyen el tema antes de guardar
        generated_article_data['tema'] = tema # Añadir el tema para guardar en la DB
        # save_generated_article retorna el ID del artículo generado
        generated_article_id = database.save_generated_article(generated_article_data)

        if generated_article_id:
            # Guardar metadata de imágenes, asociadas al ID del artículo
            if found_images_metadata:
                 for img_meta in found_images_metadata:
                     img_meta['articulo_generado_id'] = generated_article_id
                     database.save_image_metadata(img_meta)
            print(f"✅ PIPELINE: Artículo generado y metadata de imágenes guardadas con ID {generated_article_id}.")

            # === PASO 5: Marcar Fuentes Usadas ===
            print("✅ PIPELINE: Marcando fuentes utilizadas...")
            # Las IDs de las fuentes que se usaron vienen en la lista sources_with_content (ahora incluye ID)
            if sources_with_content: # Solo marcar si realmente se usaron fuentes
                 source_ids_used = [src.get('id') for src in sources_with_content if src.get('id') is not None]
                 for source_id in source_ids_used:
                      database.mark_source_used(source_id)


          


            print(f"--- PIPELINE: Pipeline completado para '{tema}'. Artículo ID: {generated_article_id} ---")
            # Retornar el ID del artículo generado como indicador de éxito
            return generated_article_id

        else:
            print("❌ PIPELINE: Falló al guardar el artículo generado en la base de datos.")
            # Registrar error en generacion_tareas si se usa
            return None # Retornar None en caso de fallo al guardar


    except Exception as e:
        # Manejo de errores general para cualquier fallo en el pipeline
        print(f"❌ PIPELINE: Error CRÍTICO durante el pipeline para '{tema}': {str(e)}")
        # Registrar error en generacion_tareas si se usa
        return None


# === Bloque para pruebas independientes ===
# Este bloque solo se ejecuta si corres pipeline.py directamente.
# Simula la carga de configuración desde la DB para construir un GenerateRequestModel
# y luego ejecuta el pipeline.
if __name__ == "__main__":
    print("--- Prueba independiente del Pipeline Completo ---")

    # Necesitas inicializar la DB para las funciones de database
    try:
        database.inicializar_db()
        print("✅ Base de datos inicializada para prueba de pipeline.")
    except Exception as e:
        print(f"❌ Error al inicializar la base de datos para la prueba: {e}")
        print("Asegúrate de que 'schema.sql' y 'seo_autopilot.db' están accesibles.")
        # Continuar si la DB falla, pero las funciones de database fallarán
        pass # Permite que la prueba continúe aunque el guardado/marcado falle


    # --- Definir el tema de prueba ---
    test_tema = "generacion del 27 en España" # <-- Define tu tema de prueba aquí

    # --- Cargar configuración de DB para el tema de prueba ---
    # Esto simula lo que haría el backend o la UI al cargar la configuración para esta sección.
    # database.get_config retorna un dict{} si no encuentra config, o un dict con la config guardada.
    print(f"\n--- Cargando configuración de DB para tema '{test_tema}' ---")
    config_from_db = database.get_config(test_tema)



    try:
        # Obtener los campos esperados por GenerateRequestModel
        fields_in_generate_request = list(GenerateRequestModel.model_fields.keys()) # Pydantic V2

        # Construir un dict con los campos de la config cargada que coinciden con GenerateRequestModel
        # Si config_from_db no tiene una clave, no se incluirá aquí, y GenerateRequestModel usará su default.
        request_data_dict = {k: config_from_db.get(k) for k in fields_in_generate_request if k in config_from_db}
        # Asegurarse de que el tema siempre está (puede venir de config_from_db, pero doble check)
        request_data_dict['tema'] = test_tema

        # Create the model instance
        test_request_data = GenerateRequestModel(**request_data_dict)

        print(f"✅ GenerateRequestModel creado para prueba: {test_request_data.model_dump()}")


    except Exception as e:
         print(f"❌ Error al crear GenerateRequestModel para la prueba: {str(e)}")
         print("Asegúrate de que database.get_config retorna un diccionario válido y coincide con GenerateRequestModel.")
         # No salir, quizás la siguiente llamada fallará y dará más contexto
         # return # Salir si falla la creación del modelo


    # --- Ejecutar el pipeline completo ---
    print("\n--- Ejecutando pipeline asíncrono... ---")
    # asyncio.run ejecuta una corrutina (función async def)
    generated_article_id = asyncio.run(run_full_generation_pipeline(test_request_data))

    if generated_article_id:
        print(f"\n--- Prueba de Pipeline Completada ---")
        print(f"Artículo generado con éxito. ID: {generated_article_id}")
        # La previsualización HTML ya debería haberse abierto en tu navegador
    else:
        print("\n--- Prueba de Pipeline Fallida ---")
        print("El pipeline no generó un artículo con éxito.")

    print("\n--- Fin de la prueba independiente del Pipeline ---")