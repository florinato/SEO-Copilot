# database.py
# Contiene las funciones esenciales para el flujo mínimo de generación, guardado,
# configuración y gestión básica de artículos generados.

import json
import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional  # Importar para type hinting

# Define la ruta a tu archivo de esquema SQL
# ASEGÚRATE DE QUE ESTA RUTA ES CORRECTA PARA TU SISTEMA
SCHEMA_FILE_PATH = "C:\\Users\\oscar\\Desktop\\proyectospy\\auto-seo\\schema.sql" # <-- ¡VERIFICA Y AJUSTA ESTA RUTA!
DB_FILE_PATH = "seo_autopilot.db"


def inicializar_db():
    """
    Inicializa la conexión con la base de datos y crea todas las tablas
    ejecutando el script SQL desde SCHEMA_FILE_PATH si no existen.
    """
    print(f"--- Intentando inicializar DB: {DB_FILE_PATH} ---")
    conn = sqlite3.connect(DB_FILE_PATH)
    cursor = conn.cursor()
    sql_script = ""
    try:
        print(f"Verificando si el archivo de esquema existe en: {SCHEMA_FILE_PATH}")
        if not os.path.exists(SCHEMA_FILE_PATH):
             print(f"❌ Error: El archivo de esquema SQL NO FUE ENCONTRADO en {SCHEMA_FILE_PATH}")
        else:
            print(f"Archivo de esquema encontrado. Leyendo contenido desde: {SCHEMA_FILE_PATH}")
            with open(SCHEMA_FILE_PATH, 'r', encoding='utf-8') as f:
                sql_script = f.read()
            print(f"Leído contenido del archivo. Longitud del script: {len(sql_script)} caracteres.")

        if sql_script and sql_script.strip():
            print("Ejecutando script SQL para crear tablas...")
            # Usa executescript para ejecutar múltiples comandos SQL desde el archivo.
            # Esto creará TODAS las tablas definidas en schema.sql (articulos, tags, articulos_fuente_tags,
            # articulos_generados, imagenes_generadas, configuracion, generacion_tareas).
            cursor.executescript(sql_script)
            conn.commit()
            print("✅ Script SQL ejecutado y commit realizado.")
        else:
             print("⏩ Saltando ejecución del script SQL porque estaba vacío o no se encontró el archivo.")

        print(f"✅ Base de datos {DB_FILE_PATH} inicializada/verificada usando {SCHEMA_FILE_PATH}.")

        # Opcional: Verificaciones básicas de tablas clave para confirmar que existen
        try:
            table_checks = ['articulos', 'configuracion', 'articulos_generados', 'imagenes_generadas', 'tags', 'articulos_fuente_tags', 'generacion_tareas']
            for table_name in table_checks:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
                if cursor.fetchone(): print(f"✅ Tabla '{table_name}' verificada. EXISTE.")
                else: print(f"⚠️ Tabla '{table_name}' NO FUE CREADA. Revisa schema.sql")

            # Opcional: Insertar una configuración de ejemplo "Defecto" si la tabla config está vacía
            # Requiere la función save_config más abajo.
            try:
                 # Usa una nueva conexión o asegúrate de que el cursor está listo
                 conn_check = sqlite3.connect(DB_FILE_PATH)
                 cursor_check = conn_check.cursor()
                 cursor_check.execute("SELECT COUNT(*) FROM configuracion")
                 if cursor_check.fetchone()[0] == 0:
                      print("⚠️ Tabla 'configuracion' vacía. Insertando configuración de ejemplo 'Defecto'.")
                      # Definir una config de ejemplo con el tema "Defecto" usando valores típicos/defaults
                      example_default_config = {
                           'tema': 'Defecto',
                           'min_score_fuente': 5, 'num_fuentes_scraper': 10, 'num_resultados_scraper': 5,
                           'min_score_generador': 7, 'num_fuentes_generador': 3,
                           'longitud_texto': 1500, 'tono_texto': 'neutral', 'num_imagenes_buscar': 2,
                           # Prompts no están en la DB por ahora
                           # 'prompt_analyzer_template': None, 'prompt_generator_template': None, 'prompt_copilot_template': None
                      }
                      save_config(example_default_config) # Llama a la función save_config para insertar
                 conn_check.close() # Cierra la conexión de check

            except sqlite3.OperationalError:
                 # Si la tabla config no existe, esta verificación fallará
                 pass
            except Exception as e:
                 print(f"⚠️ Error al intentar insertar config de ejemplo: {str(e)}")


        except Exception as e:
             print(f"⚠️ Error al verificar tablas después de la inicialización: {str(e)}")

    except FileNotFoundError:
        print(f"❌ Error crítico: El archivo de esquema SQL no se encontró.")
        raise
    except Exception as e:
        print(f"❌ Error al ejecutar script SQL de inicialización de DB: {str(e)}")
        conn.rollback() # Rollback si hay un error de ejecución
        raise
    finally:
        conn.close()
        print("--- Fin inicialización DB ---")


# === Funciones Esenciales para el Flujo de Generación y Guardado ===

def url_existe(url: str) -> bool:
    """Verifica si una URL ya existe en la base de datos (tabla articulos)."""
    conn = sqlite3.connect(DB_FILE_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT 1 FROM articulos WHERE url = ?', (url,))
        return cursor.fetchone() is not None
    except sqlite3.OperationalError as e:
        print(f"⚠️ Error SQL en url_existe: {str(e)}. ¿Existe la tabla 'articulos'?")
        return False
    except Exception as e:
        print(f"Error en url_existe: {str(e)}")
        return False
    finally:
        conn.close()

def guardar_articulo(articulo: Dict[str, Any]) -> Optional[int]:
    """Guarda un artículo fuente en la tabla 'articulos'. Retorna el ID asignado o existente."""
    conn = sqlite3.connect(DB_FILE_PATH)
    cursor = conn.cursor()
    try:
        # Intentar insertar la fuente. IGNORE si ya existe (basado en URL UNIQUE).
        # La base de datos usará los defaults SQL para los campos no proporcionados si no hay conflicto de UNIQUE.
        cursor.execute('''
            INSERT OR IGNORE INTO articulos
            (titulo, url, score, resumen, fuente, fecha_publicacion_fuente, fecha_scraping, usada_para_generar)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
        ''', (
            articulo.get('titulo', ''), # .get() con default string por seguridad
            articulo['url'], # Asumimos que url SIEMPRE viene y es la clave
            articulo.get('score'), # Score puede ser None si el analisis fallo totalmente
            articulo.get('resumen', ''),
            articulo.get('fuente', ''),
            articulo.get('fecha_publicacion_fuente'), # Puede ser None, DB usara default o NULL
            articulo.get('usada_para_generar', 0) # Usar 0 si no viene
        ))
        # Obtener el ID asignado a la fila insertada (si la inserción fue exitosa)
        articulo_id = cursor.lastrowid

        # Si lastrowid es 0, la inserción fue IGNORADA porque la URL ya existía.
        # Necesitamos consultar la DB para obtener el ID del artículo existente.
        if not articulo_id:
             # Buscar el ID del artículo existente por su URL
             cursor.execute('SELECT id FROM articulos WHERE url = ?', (articulo['url'],))
             articulo_id_row = cursor.fetchone()
             if articulo_id_row:
                  articulo_id = articulo_id_row[0] # Obtener el ID de la fila existente
                  # print(f"⚠️ Fuente {articulo['url'][:60]}... ya existía. Usando ID {articulo_id}.") # Debugging opcional
             else:
                  # Esto NO DEBERÍA PASAR si url_existe() funciona o si INSERT OR IGNORE tuvo éxito pero lastrowid fue 0 por alguna razon.
                  print(f"❌ Error: Falló al obtener ID para URL {articulo['url']} después de INSERT OR IGNORE.")
                  conn.rollback() # Asegurarse de que la transacción se revierte si algo salió muy mal
                  return None # Retornar None si no se puede obtener el ID


        # === Lógica de tags (comentada para la versión mínima) ===
        # Si necesitas tags para fuentes, DESCOMENTA esta sección y asegúrate de que
        # las tablas 'tags' y 'articulos_fuente_tags' existen en schema.sql.
        # tag_table_name = 'articulos_fuente_tags'
        # try:
        #     for tag in articulo.get('tags', []):
        #         tag = tag.strip()
        #         if not tag: continue # Skip empty tags
        #         # Insert tag into tags table (ignore if already exists)
        #         cursor.execute('INSERT OR IGNORE INTO tags (tag) VALUES (?)', (tag,))
        #         # Get the ID of the tag (either newly inserted or existing)
        #         cursor.execute('SELECT id FROM tags WHERE tag = ?', (tag,))
        #         tag_id_row = cursor.fetchone()
        #         if tag_id_row:
        #             tag_id = tag_id_row[0]
        #             # Link article and tag in the join table (ignore if link already exists)
        #             cursor.execute(f'INSERT OR IGNORE INTO {tag_table_name} (articulo_fuente_id, tag_id) VALUES (?, ?)', (articulo_id, tag_id))
        #         else:
        #              print(f"⚠️ Could not find ID for tag '{tag}' after insertion attempt in guardar_articulo.")
        # except Exception as e:
        #      print(f"Error in tags/relationships section for article ID {articulo_id}: {str(e)}")
        #      # Do not re-raise, just print warning
        #      pass # Continue processing even if tag linking fails


        conn.commit() # Commit final si todo lo anterior fue bien (o si la inserción/obtención ID fue bien)
        return articulo_id # Retorna el ID del artículo fuente guardado o existente

    except Exception as e:
        print(f"❌ Error general al guardar artículo fuente {articulo.get('url', 'N/A')}: {str(e)}")
        conn.rollback() # Rollback en caso de cualquier otra excepción
        raise # Re-lanzar la excepción para que el llamador (scraper) la maneje
    finally:
        conn.close()


def mark_source_used(source_article_id: int):
    """Marca un artículo fuente como usado para generar contenido."""
    conn = sqlite3.connect(DB_FILE_PATH)
    cursor = conn.cursor() # CORREGIDO: Usar conn.cursor()
    try:
        cursor.execute('''
            UPDATE articulos
            SET usada_para_generar = 1
            WHERE id = ?
        ''', (source_article_id,))
        conn.commit()
        # print(f"✅ Fuente ID {source_article_id} marcada como usada.") # Debugging opcional
    except sqlite3.OperationalError as e:
        print(f"⚠️ Error SQL en mark_source_used: {str(e)}. ¿Existe la tabla 'articulos' y la columna 'usada_para_generar'?")
        conn.rollback()
    except Exception as e:
        print(f"❌ Error en mark_source_used ID {source_article_id}: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

def save_generated_article(article_data: Dict[str, Any]) -> Optional[int]:
    """Guarda un artículo generado en la tabla articulos_generados. Retorna el ID asignado."""
    conn = sqlite3.connect(DB_FILE_PATH)
    cursor = conn.cursor()
    try:
        # Convertir la lista de tags a string JSON para guardarla
        tags_list = article_data.get('tags', [])
        if not isinstance(tags_list, list):
             print(f"⚠️ save_generated_article recibió 'tags' que no es lista: {type(tags_list)}. Guardando como cadena vacía.")
             tags_list = [] # Asegurar que es una lista para json.dumps
        tags_str = json.dumps(tags_list) # json.dumps() convierte lista a string JSON


        tema = article_data.get('tema', 'Desconocido')
        if not tema: # Asegurar que el tema no está vacío
             print("⚠️ save_generated_article: El campo 'tema' está vacío. Usando 'Desconocido'.")
             tema = 'Desconocido'

        # Insertar una nueva fila en articulos_generados.
        # La base de datos usará los defaults SQL para campos no proporcionados si no hay conflicto.
        cursor.execute('''
            INSERT INTO articulos_generados
            (tema, titulo, meta_description, body, tags, fecha_publicacion_destino, estado, score_fuentes_promedio, fecha_generacion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            tema, # Usar el tema (seccion)
            article_data.get('title', 'Sin título'),
            article_data.get('meta_description', ''),
            article_data.get('body', ''),
            tags_str, # Guardar el JSON de tags (string)
            article_data.get('fecha_publicacion_destino'), # Puede ser None, DB usara default o NULL
            article_data.get('estado', 'generado'), # Usar 'generado' si no se especifica
            article_data.get('score_fuentes_promedio') # Score promedio puede ser None
        ))
        article_id = cursor.lastrowid # Obtener el ID asignado a la nueva fila

        conn.commit() # Commit si la inserción fue exitosa
        print(f"✅ Artículo generado '{article_data.get('title', 'N/A')[:50] + '...'}' guardado con ID {article_id}.")
        return article_id # Retornar el ID del artículo generado guardado

    except sqlite3.OperationalError as e:
         print(f"⚠️ Error SQL en save_generated_article: {str(e)}. ¿Existe la tabla 'articulos_generados' y sus columnas?")
         conn.rollback() # Rollback en caso de error SQL
         raise # Re-lanzar
    except Exception as e:
        print(f"❌ Error general al guardar artículo generado '{article_data.get('title', 'N/A')}': {str(e)}")
        conn.rollback() # Rollback en caso de cualquier otra excepción
        raise # Re-lanzar
    finally:
        conn.close() # Cerrar la conexión


def save_image_metadata(image_data: Dict[str, Any]):
    """Guarda la metadata de una imagen asociada a un artículo generado."""
    conn = sqlite3.connect(DB_FILE_PATH)
    cursor = conn.cursor()
    try:
        # Asegurarse de que 'articulo_generado_id' está presente y es un número
        # Pydantic en la API debe validar esto antes de llegar aquí, pero doble check.
        articulo_generado_id = image_data.get('articulo_generado_id')
        if not isinstance(articulo_generado_id, int):
             print(f"⚠️ save_image_metadata: ID de artículo generado inválido o faltante: {articulo_generado_id}. No se guardará la imagen.")
             # Podrías loguear los datos completos de image_data para depurar si es necesario
             # print(f"   Image data: {image_data}")
             return # No guardar si no hay ID válido


        cursor.execute('''
            INSERT INTO imagenes_generadas
            (articulo_generado_id, url, alt_text, caption, licencia, autor)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            articulo_generado_id, # Usar el ID validado
            image_data.get('url', ''),
            image_data.get('alt_text', ''),
            image_data.get('caption', ''),
            image_data.get('licencia', 'Desconocida'),
            image_data.get('autor', 'Desconocido')
        ))
        conn.commit() # Commit si la inserción fue exitosa
        # print(f"✅ Metadata de imagen guardada para articulo generado ID {articulo_generado_id}") # Debugging opcional
    except sqlite3.OperationalError as e:
         print(f"⚠️ Error SQL en save_image_metadata: {str(e)}. ¿Existe la tabla 'imagenes_generadas' y sus columnas?")
         conn.rollback() # Rollback en caso de error SQL
         # No re-lanzar, un fallo al guardar una imagen no debería detener todo
    except Exception as e:
        print(f"❌ Error general al guardar metadata de imagen para articulo generado ID {articulo_generado_id or 'N/A'}: {str(e)}")
        conn.rollback() # Rollback en caso de cualquier otra excepción
        # No re-lanzar
    finally:
        conn.close() # Cerrar la conexión


# === Funciones para la tabla configuracion (para cargar/guardar) ===

def get_config(tema: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene la configuración guardada para un tema.
    Retorna un diccionario con la configuración de la fila encontrada (incluyendo ID y fechas) si existe,
    o un diccionario vacío {} si no.
    Maneja errores de DB retornando también {}.
    """
    conn = sqlite3.connect(DB_FILE_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM configuracion WHERE tema = ?', (tema,))
        row = cursor.fetchone()

        if row:
            col_names = [description[0] for description in cursor.description]
            config_dict = dict(zip(col_names, row))
            print(f"✅ Configuración encontrada para tema '{tema}'.")
            # Retorna el diccionario tal cual lo lee de la DB (incluyendo ID y fechas)
            # La API (Pydantic ConfigBase) se encargará de filtrar los campos que necesita.
            return config_dict
        else:
            print(f"⚠️ No se encontró configuración guardada para tema '{tema}'.")
            return {} # Retornar diccionario vacío si no se encuentra

    except sqlite3.OperationalError as e:
        print(f"⚠️ Error SQL en get_config: {str(e)}. ¿Existe la tabla 'configuracion'?")
        return {} # Retornar diccionario vacío en caso de error

    except Exception as e:
        print(f"❌ Error en get_config para tema '{tema}': {str(e)}")
        return {} # Retornar diccionario vacío en caso de otro error
    finally:
        conn.close()

def save_config(config_dict: Dict[str, Any]) -> bool:
    """
    Guarda o actualiza la configuración para un tema.
    config_dict debe ser un diccionario que contenga al menos 'tema'.
    Los defaults para campos no proporcionados se manejan en SQL.
    """
    if 'tema' not in config_dict or not config_dict['tema']:
        print("❌ Error: config_dict debe incluir un 'tema' para guardar la configuración y no puede estar vacío.")
        return False

    conn = sqlite3.connect(DB_FILE_PATH)
    cursor = conn.cursor()
    try:
        # Usamos INSERT OR REPLACE INTO. SQLite se encarga de los defaults para campos no proporcionados.
        # Construir la query dinámicamente con solo los campos presentes en config_dict + tema
        # No necesitamos una lista hardcodeada de valid_fields aquí, solo asegurarnos que el 'tema' viene.

        # Preparar los campos y valores presentes en el diccionario de entrada
        # Excluir campos que no deben ser insertados/reemplazados por cliente (como id, fechas DB)
        fields_to_process = [k for k in config_dict.keys() if k not in ['id', 'fecha_creacion', 'fecha_actualizacion']]
        values_to_process = [config_dict[k] for k in fields_to_process]

        # El tema es esencial, debe estar en la lista de campos y valores
        if 'tema' not in fields_to_process:
             print("❌ Error: El campo 'tema' no está presente en el diccionario después de excluir campos DB.")
             return False

        # Crear placeholders y nombres de campos para la query
        placeholders = ', '.join(['?'] * len(fields_to_process))
        field_names = ', '.join(fields_to_process)

        # Usamos INSERT OR REPLACE INTO
        # Esto sobrescribirá la fila si ya existe un tema idéntico.
        query = f'''
            INSERT OR REPLACE INTO configuracion ({field_names})
            VALUES ({placeholders})
        '''
        cursor.execute(query, values_to_process)

        conn.commit() # Commit si la operación fue exitosa
        print(f"✅ Configuración guardada para tema '{config_dict['tema']}'.")
        return True

    except sqlite3.OperationalError as e:
         print(f"⚠️ Error SQL en save_config: {str(e)}")
         conn.rollback() # Rollback en caso de error SQL
         return False
    except Exception as e:
        print(f"❌ Error al guardar configuración para tema '{config_dict.get('tema', 'N/A')}': {str(e)}")
        conn.rollback() # Rollback en caso de cualquier otra excepción
        return False
    finally:
        conn.close() # Cerrar la conexión


# === Funciones para obtener datos de artículos generados para la UI (Canvas, Lista) ===

# Implementar estas funciones para que la UI pueda:
# - Listar artículos: get_all_generated_articles(tema=None, estado=None, limit=100) -> list of dicts
# - Ver detalles de 1 artículo: get_generated_article_by_id(article_id) -> dict or None
# - Actualizar 1 artículo: update_generated_article(article_id, updated_data: Dict[str, Any]) -> bool


def get_all_generated_articles(tema: Optional[str] = None, estado: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
    """Obtiene artículos generados, opcionalmente filtrados por tema/sección o estado."""
    conn = sqlite3.connect(DB_FILE_PATH)
    cursor = conn.cursor()
    try:
        # Seleccionar solo los campos necesarios para la lista
        query = 'SELECT id, tema, titulo, fecha_generacion, estado, score_fuentes_promedio FROM articulos_generados WHERE 1=1'
        params = []

        if tema: # Filtrar por tema (seccion)
            query += ' AND tema = ?'
            params.append(tema)
        if estado:
            query += ' AND estado = ?'
            params.append(estado)

        query += ' ORDER BY fecha_generacion DESC LIMIT ?'
        params.append(limit)


        cursor.execute(query, params)
        rows = cursor.fetchall()
        col_names = [description[0] for description in cursor.description]
        results = [dict(zip(col_names, row)) for row in rows] # Crear lista de diccionarios

        print(f"📚 Encontrados {len(results)} artículos generados (Filtros: Tema/Seccion={tema}, Estado={estado}).")
        return results

    except sqlite3.OperationalError as e:
        print(f"⚠️ Error SQL en get_all_generated_articles: {str(e)}. ¿Existe la tabla 'articulos_generados'?")
        return []
    except Exception as e:
        print(f"❌ Error en get_all_generated_articles: {str(e)}")
        return []
    finally:
        conn.close()


def get_generated_article_by_id(article_id: int) -> Optional[Dict[str, Any]]:
    """Obtiene los detalles completos de un artículo generado por su ID, incluyendo metadata de imágenes asociadas."""
    conn = sqlite3.connect(DB_FILE_PATH)
    cursor = conn.cursor()
    try:
        # Obtener datos del artículo principal (seleccionar todos los campos con *)
        cursor.execute('SELECT * FROM articulos_generados WHERE id = ?', (article_id,))
        article_row = cursor.fetchone()

        if not article_row:
            print(f"⚠️ Artículo generado con ID {article_id} no encontrado.")
            return None

        article_col_names = [description[0] for description in cursor.description]
        article_data = dict(zip(article_col_names, article_row))

        # Convertir tags de string JSON a lista
        # Asegúrate de que la columna 'tags' existe en articulos_generados y es TEXT (JSON)
        if 'tags' in article_data and isinstance(article_data['tags'], str): # Verificar que es un string para parsear
             try:
                  article_data['tags'] = json.loads(article_data['tags'])
             except json.JSONDecodeError:
                  print(f"⚠️ Error al parsear tags JSON para artículo ID {article_id}. Tags raw: {article_data['tags']}")
                  article_data['tags'] = [] # Default a lista vacía si falla el parseo
        elif 'tags' not in article_data or article_data['tags'] is None:
             article_data['tags'] = [] # Asegurar que el campo existe y es lista si no viene o es NULL


        # Obtener metadata de imágenes asociadas
        # === CORRECCIÓN: Añadir 'articulo_generado_id' a la lista de columnas seleccionadas ===
        cursor.execute('SELECT id, articulo_generado_id, url, alt_text, caption, licencia, autor FROM imagenes_generadas WHERE articulo_generado_id = ?', (article_id,))
        # =====================================================================================
        image_rows = cursor.fetchall()
        image_col_names = [description[0] for description in cursor.description]
        images_data = [dict(zip(image_col_names, row)) for row in image_rows] # Crear lista de diccionarios

        article_data['imagenes'] = images_data # Añadir la lista de imágenes al diccionario del artículo

        # === Añadir image_url y image_caption directamente al artículo si hay imágenes ===
        if images_data:
            # Tomar la URL y el caption de la primera imagen encontrada
            article_data['image_url'] = images_data[0].get('url')
            article_data['image_caption'] = images_data[0].get('caption')
        else:
            article_data['image_url'] = None
            article_data['image_caption'] = None
        # ===============================================================================

        print(f"✅ Artículo generado ID {article_id} y {len(images_data)} imágenes asociadas cargados.")
        return article_data

    except sqlite3.OperationalError as e:
        print(f"⚠️ Error SQL en get_generated_article_by_id: {str(e)}. ¿Existen las tablas 'articulos_generados' e 'imagenes_generadas' y sus columnas?")
        return None
    except Exception as e:
        print(f"❌ Error en get_generated_article_by_id para ID {article_id}: {str(e)}")
        return None
    finally:
        conn.close()


def update_generated_article(article_id: int, updated_data: Dict[str, Any]) -> bool:
    """Actualiza campos de un artículo generado por su ID."""
    conn = sqlite3.connect(DB_FILE_PATH)
    cursor = conn.cursor()
    try:
        # Define qué campos de `articulos_generados` pueden ser actualizados desde la UI/API
        # Asegúrate de que esta lista coincide con los campos en tu tabla articulos_generados
        allowed_fields = ['titulo', 'meta_description', 'body', 'tags', 'estado', 'fecha_publicacion_destino'] # Añadidos más campos comunes si se quieren editar

        set_clauses = []
        params = []
        filtered_updated_data = {}

        for field, value in updated_data.items():
             if field in allowed_fields:
                  if field == 'tags':
                       # Si el campo es 'tags' y el valor es una lista, convertir a JSON string
                       if isinstance(value, list):
                            filtered_updated_data[field] = json.dumps(value)
                       elif value is None:
                             filtered_updated_data[field] = json.dumps([]) # Guardar lista vacía si es None
                       # Si es string o otro tipo, Pydantic ya validó, guardar tal cual o convertir si necesario
                       # Asumimos que Pydantic (GeneratedArticleUpdate) valida esto.
                  else:
                       filtered_updated_data[field] = value # Otros campos permitidos

        if not filtered_updated_data:
            print(f"⚠️ No hay campos válidos en updated_data para actualizar artículo ID {article_id}.")
            return False # Nada que actualizar

        for field, value in filtered_updated_data.items():
            set_clauses.append(f"{field} = ?")
            params.append(value)

        # Opcional: Actualizar fecha de actualización de la fila si la columna existe
        # set_clauses.append("fecha_actualizacion = CURRENT_TIMESTAMP") # Asumiendo que existe en schema.sql de articulos_generados

        params.append(article_id) # Añadir el ID para la cláusula WHERE

        query = f'''
            UPDATE articulos_generados
            SET {', '.join(set_clauses)}
            WHERE id = ?
        '''

        cursor.execute(query, params)

        # Verificar si se actualizó alguna fila
        if cursor.rowcount == 0:
             print(f"⚠️ Artículo generado con ID {article_id} no encontrado para actualizar.")
             conn.rollback() # Rollback si el UPDATE no afectó ninguna fila
             return False # No se actualizó nada

        conn.commit() # Commit si la operación fue exitosa
        print(f"✅ Artículo generado ID {article_id} actualizado.")
        return True

    except sqlite3.OperationalError as e:
        print(f"⚠️ Error SQL en update_generated_article: {str(e)}. ¿Existe la tabla 'articulos_generados' y sus columnas?")
        conn.rollback() # Rollback en caso de error SQL
        return False # No re-lanzar, retornar False
    except Exception as e:
        print(f"❌ Error general al actualizar artículo generado ID {article_id}: {str(e)}")
        conn.rollback() # Rollback en caso de cualquier otra excepción
        return False # No re-lanzar
    finally:
        conn.close() # Cerrar la conexión


# === Funciones para obtener datos de fuentes para la UI (Admin) ===

# Implementar esta función si se necesita la vista de admin de fuentes
# def get_all_sources(limit: int = 100) -> List[Dict[str, Any]]: ...


# === Funciones para obtener lista de TEMAS/SECCIONES disponibles ===

# Implementar esta función si se necesita listar secciones en la UI
def get_available_temas_secciones() -> List[str]:
    """Obtiene una lista de todos los temas/secciones que tienen configuración guardada."""
    conn = sqlite3.connect(DB_FILE_PATH)
    cursor = conn.cursor()
    try:
        # Seleccionar solo la columna tema
        cursor.execute('SELECT DISTINCT tema FROM configuracion ORDER BY tema')
        rows = cursor.fetchall()
        # Retorna una lista de strings de tema
        return [row[0] for row in rows]
    except sqlite3.OperationalError as e:
        print(f"⚠️ Error SQL en get_available_temas_secciones: {str(e)}. ¿Existe la tabla 'configuracion'?")
        return []
    except Exception as e:
        print(f"❌ Error en get_available_temas_secciones: {str(e)}")
        return []
    finally:
        conn.close()


def save_article_generated_sources(article_generated_id: int, source_article_ids: List[int]) -> bool:
    """
    Guarda los enlaces entre un artículo generado y las fuentes usadas para crearlo.

    Args:
        article_generated_id (int): ID del artículo generado.
        source_article_ids (List[int]): Lista de IDs de fuentes usadas.

    Returns:
        bool: True si tiene éxito, False si falla.
    """
    if not source_article_ids:
        print(f"⚠️ save_article_generated_sources: No hay IDs de fuentes para guardar para artículo generado ID {article_generated_id}.")
        return True # No hay error si no hay nada que guardar

    conn = sqlite3.connect(DB_FILE_PATH)
    cursor = conn.cursor()
    try:
        # Construir la lista de tuplas para la inserción masiva
        relations_to_insert = [(article_generated_id, source_id) for source_id in source_article_ids]

        # Usamos INSERT OR IGNORE INTO en caso de que la relación ya exista (aunque no debería si el ID de generado es nuevo)
        cursor.executemany('''
            INSERT OR IGNORE INTO articulos_generados_fuentes (articulo_generado_id, articulo_fuente_id)
            VALUES (?, ?)
        ''', relations_to_insert)

        conn.commit()
        print(f"✅ Guardadas {cursor.rowcount} relaciones entre artículo generado ID {article_generated_id} y fuentes.")
        return True

    except sqlite3.OperationalError as e:
         print(f"⚠️ Error SQL en save_article_generated_sources: {str(e)}. ¿Existe la tabla 'articulos_generados_fuentes'?")
         conn.rollback()
         return False
    except Exception as e:
        print(f"❌ Error general al guardar relaciones de fuentes para artículo generado ID {article_generated_id}: {str(e)}")
        conn.rollback()
        return False
    finally:
        conn.close()


def get_sources_used_by_article(article_generated_id: int) -> List[Dict[str, Any]]:
    """
    Obtiene los detalles de las fuentes (desde la tabla articulos) usadas para un artículo generado.
    """
    conn = sqlite3.connect(DB_FILE_PATH)
    cursor = conn.cursor()
    try:
        # Unir articulos_generados_fuentes con articulos para obtener los detalles de las fuentes
        query = '''
            SELECT
                a.id, a.titulo, a.url, a.score, a.resumen, a.fuente, a.fecha_publicacion_fuente,
                a.fecha_scraping, a.usada_para_generar
            FROM articulos a
            JOIN articulos_generados_fuentes agf ON a.id = agf.articulo_fuente_id
            WHERE agf.articulo_generado_id = ?
        '''
        cursor.execute(query, (article_generated_id,))
        rows = cursor.fetchall()
        col_names = [description[0] for description in cursor.description]
        results = [dict(zip(col_names, row)) for row in rows] # Crear lista de diccionarios

        print(f"📚 Encontradas {len(results)} fuentes usadas para artículo generado ID {article_generated_id}.")
        return results

    except sqlite3.OperationalError as e:
        print(f"⚠️ Error SQL en get_sources_used_by_article: {str(e)}. ¿Existen las tablas 'articulos' y 'articulos_generados_fuentes'?")
        return []
    except Exception as e:
        print(f"❌ Error en get_sources_used_by_article para artículo generado ID {article_generated_id}: {str(e)}")
        return []
    finally:
        conn.close()
