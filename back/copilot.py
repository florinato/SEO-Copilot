# copilot.py (Completo y Corregido - Asegurando Plantilla y Orden)
# Módulo para el Agente Conversacional SEO-Copilot.
# Contiene la lógica para generar sugerencias y regenerar contenido.

from typing import Any, Dict, List, Optional  # Importar List para type hinting

import content_generator
import database
import llm_client

DEFAULT_COPILOT_SUGGESTIONS_PROMPT_TEMPLATE = """
Eres SEO-Copilot, un asistente de IA experto en SEO y creación de contenido. Tu tarea es analizar el artículo proporcionado y listar DIRECTAMENTE SUGERENCIAS de mejora.

Aquí tienes el contexto del artículo que el usuario está revisando:
Título: {titulo}
Meta Descripción: {meta_description}
Tags: {tags}
Tema/Sección: {tema}
Score Promedio de Fuentes: {score_fuentes_promedio:.2f}
Cuerpo del Artículo:
{body_preview} [...] ({body_length} caracteres)

Por favor, **analiza este artículo** y proporciona **sugerencias de mejora concisas y directas** enfocadas en:
1.  **Calidad del Contenido:** ¿Es claro, coherente, interesante? ¿Cubre bien el tema basado en el resumen de fuentes?
2.  **Optimización SEO On-Page:** ¿Qué tal están el título, meta descripción y tags? ¿Hay oportunidades para mejorar la densidad o relevancia de palabras clave? ¿La estructura (H2, H3) es lógica?
3.  **Estilo y Tono:** ¿El tono se ajusta a '{tono}' (si se especifica)? ¿La legibilidad es buena?

**Devuelve ÚNICAMENTE las sugerencias de mejora, listadas directamente. No incluyas introducciones, resúmenes del artículo, ni texto explicativo antes o después de la lista.** Utiliza saltos de línea para separar cada sugerencia.

Sugestiones de mejora:
""" # <-- ESTA ES LA DEFINICIÓN COMPLETA DEL STRING. Asegurarse que no hay errores de sintaxis.


# === Función: Construir Prompt de Modificación para el Generador ===
# DEBE ESTAR DEFINIDA ANTES de regenerate_article_content.
def build_modification_prompt_text(text_to_rewrite: str, instruction: str, article_title: str) -> str:
     """
     Construye el texto del prompt de modificación para añadirlo al placeholder
     {modification_instructions} en el prompt principal del generador.
     """
     modification_prompt = f"""
Basado en el artículo completo (cuerpo en Markdown) que se te proporcionó anteriormente (usando las fuentes originales), reescribe o modifica el texto para cumplir con la siguiente instrucción:

Contexto del Artículo:
Título: {article_title}

Texto actual del artículo (extraído del Canvas para darte contexto):
{text_to_rewrite}

Instrucción para modificar:
{instruction}

Aplica la instrucción a todo el artículo si es necesario, usando el texto actual como referencia de lo que el usuario quiere modificar. **Recuerda que debes devolver el artículo COMPLETO en formato JSON.**

"""
     return modification_prompt


# === Función: Generar Sugerencias Automáticas (Síncrona) ===
# ESTA FUNCIÓN ES LA QUE FALLA.
def generate_article_suggestions(article_data: dict) -> str:
    """
    Genera sugerencias de mejora para un artículo dado utilizando Gemini (de forma SínCRONA).
    """
    print(f"\n🧠 Copilot: Generando sugerencias para artículo ID {article_data.get('id', 'N/A')} ('{article_data.get('titulo', 'Sin título')[:30]}...')")

    # Construir los valores para el formato
    # Usar .get() con valores por defecto que sean compatibles con el formato esperado
    # Y convertir tipos si es necesario.
    titulo = article_data.get('titulo', 'Sin título')
    meta_description = article_data.get('meta_description', '')
    tags_list = article_data.get('tags', [])
    if not isinstance(tags_list, list): tags_list = []
    tags = ", ".join(tags_list) # Este es el string unido

    tema = article_data.get('tema', 'Desconocido') # Default string

    # Manejar score_fuentes_promedio - Formato {score_fuentes_promedio:.2f} espera un número.
    score_value = article_data.get('score_fuentes_promedio')
    # Si es None, proporcionar 0.0 para el formato flotante :.2f
    score_fuentes_promedio_for_format = score_value if (score_value is not None and isinstance(score_value, (int, float))) else 0.0 # <-- Proporcionar 0.0 si es None


    body_content = article_data.get('body', '')
    body_preview_length = 2000
    body_preview = body_content[:body_preview_length]
    body_length = len(body_content)

    # Obtener el tono del artículo - Es string o None. Placeholder {tono}.
    # Si es None, proporcionar un default STRING.
    tono = article_data.get('tono_texto', 'neutral') # <-- Default string


    # === AÑADIR PRINTS DE DEPURACIÓN PARA LOS VALORES ===
    # Estos prints nos ayudarán a ver si alguno de estos valores es None justo antes de formatear.
    print(f"DEBUG_FORMAT_SUG: titulo: {titulo} ({type(titulo)})")
    print(f"DEBUG_FORMAT_SUG: meta_description: {meta_description} ({type(meta_description)})")
    print(f"DEBUG_FORMAT_SUG: tags: {tags} ({type(tags)})")
    print(f"DEBUG_FORMAT_SUG: tema: {tema} ({type(tema)})")
    print(f"DEBUG_FORMAT_SUG: score_fuentes_promedio_for_format: {score_fuentes_promedio_for_format} ({type(score_fuentes_promedio_for_format)})")
    print(f"DEBUG_FORMAT_SUG: body_preview: {body_preview[:100]}... ({type(body_preview)})")
    print(f"DEBUG_FORMAT_SUG: body_length: {body_length} ({type(body_length)})")
    print(f"DEBUG_FORMAT_SUG: tono: {tono} ({type(tono)})")
    # ==============================================


    try:
        # === VERIFICACIÓN ADICIONAL DE LA PLANTILLA ===
        # Si la variable DEFAULT_COPILOT_SUGGESTIONS_PROMPT_TEMPLATE es None aquí, es un error.
        # Esto no debería pasar si está definida correctamente al principio.
        if DEFAULT_COPILOT_SUGGESTIONS_PROMPT_TEMPLATE is None or not isinstance(DEFAULT_COPILOT_SUGGESTIONS_PROMPT_TEMPLATE, str):
             print(f"❌❌❌ ERROR GRAVE EN COPILOT.PY: Plantilla de sugerencias no es un string válido. Es: {type(DEFAULT_COPILOT_SUGGESTIONS_PROMPT_TEMPLATE)} ❌❌❌")
             return "Error interno: La plantilla de sugerencias no está cargada correctamente."
        # =============================================


        # === Usar .format() con los valores preparados ===
        # Si los prints de depuración muestran valores correctos y la plantilla es string,
        # esta línea DEBERÍA funcionar. Si falla, el diccionario tiene el problema.
        copilot_prompt = DEFAULT_COPILOT_SUGGESTIONS_PROMPT_TEMPLATE.format(
            titulo=titulo,
            meta_description=meta_description,
            tags=tags,
            tema=tema,
            score_fuentes_promedio=score_fuentes_promedio_for_format, # Usar la variable ajustada
            body_preview=body_preview,
            body_length=body_length,
            tono=tono
        )

        # Llamar a Gemini usando llm_client (síncrono)
        ai_response = llm_client.generate_raw_content(copilot_prompt)

        print("✅ Copilot: Sugerencias generadas por Gemini.")
        ai_response = ai_response.replace('```text', '').replace('```', '').strip()
        ai_response = ai_response.replace('```markdown', '').replace('```', '').strip()

        return ai_response # Retornar el string de sugerencias

    except Exception as e:
        print(f"❌ Copilot: Error al generar sugerencias: {str(e)}")
        # Si el error sigue siendo el TypeError, estos prints de depuración nos dirán cuál valor es None o incorrecto
        return f"Error al generar sugerencias de la IA: {str(e)}"


# === Función: Construir Prompt de Modificación para el Generador ===
# DEBE ESTAR DEFINIDA ANTES de regenerate_article_content.
def build_modification_prompt_text(text_to_rewrite: str, instruction: str, article_title: str) -> str:
    """
    Construye el texto del prompt de modificación para añadirlo al placeholder
    {modification_instructions} en el prompt principal del generador.
    """
    # Este es el texto que irá en el placeholder {modification_instructions}
    # dentro de DEFAULT_GENERATOR_PROMPT_TEMPLATE en content_generator.py
    modification_prompt = f"""
Basado en el artículo completo (cuerpo en Markdown) que se te proporcionó anteriormente (usando las fuentes originales), reescribe o modifica el texto para cumplir con la siguiente instrucción:

Contexto del Artículo:
Título: {article_title} # <-- Usamos el título como contexto temático

Texto actual del artículo (extraído del Canvas para darte contexto):
{text_to_rewrite}

Instrucción para modificar:
{instruction}

Aplica la instrucción a todo el artículo si es necesario, usando el texto actual como referencia de lo que el usuario quiere modificar. **Recuerda que debes devolver el artículo COMPLETO en formato JSON.**

"""
    return modification_prompt




# === FUNCIÓN: Regenerar/Reescribir Contenido del Artículo (Síncrona) ===
# Esta función orquesta la regeneración usando content_generator.generate_seo_content
# DEBE ESTAR DEFINIDA DESPUÉS de build_modification_prompt_text.
def regenerate_article_content(article_id: int, instruction: str, current_body_text: str) -> Optional[Dict[str, Any]]:
    """
    Regenera el contenido de un artículo basándose en una instrucción,
    reutilizando generate_seo_content con un prompt modificado.
    Obtiene el artículo original para el contexto y sus FUENTES USADAS.

    Args:
        article_id (int): El ID del artículo a regenerar.
        instruction (str): La instrucción del usuario para la modificación.
        current_body_text (str): El texto actual del cuerpo del artículo desde el Canvas.

    Returns:
        Optional[Dict[str, Any]]: Diccionario con el cuerpo reescrito { "rewritten_text": "..." }, o None si falla.
    """
    print(f"\n🧠 Copilot: Iniciando regeneración de contenido para artículo ID {article_id}...")

    # 1. Obtener los datos del artículo completo para contexto (titulo, tema, tono)
    article_data_for_context = database.get_generated_article_by_id(article_id)
    if not article_data_for_context:
         print(f"❌ Copilot: Artículo ID {article_id} no encontrado para obtener contexto de regeneración.")
         return None

    # Obtener el título y tema para usar en el prompt y cargar config
    article_title = article_data_for_context.get('titulo', 'Sin título')
    tema_articulo = article_data_for_context.get('tema', 'Desconocido')
    tono_original = article_data_for_context.get('tono_texto', 'neutral') # Asumimos que get_generated_article_by_id lo incluye


    # === 1b. OBTENER LAS FUENTES ORIGINALES USADAS PARA ESTE ARTÍCULO ===
    # ¡Este es el paso clave! Usamos la función de database.py
    # Asumimos que database.get_sources_used_by_article retorna lista de dicts CON 'full_content'.
    print(f"🧠 Copilot: Obteniendo fuentes usadas para artículo ID {article_id}...")
    original_sources_used = database.get_sources_used_by_article(article_id)

    if not original_sources_used:
        print(f"⚠️ Copilot: No se encontraron fuentes usadas registradas para artículo ID {article_id} O no tienen full_content. Regeneración podría ser menos precisa o fallar.")
        # Si no hay fuentes, generate_seo_content fallará (porque espera la lista no vacía).
        # Esto es un fallo crítico para la regeneración contextualizada.
        return None # Fallar si no hay fuentes usadas con contenido
    # =============================================================


    # 2. Cargar la configuración original del tema para obtener los parámetros originales (longitud)
    config_tema_original = database.get_config(tema_articulo)
    longitud_original = config_tema_original.get('longitud_texto', 1500)


    # 3. Construir el texto del prompt de modificación
    modification_prompt_text = build_modification_prompt_text(
        current_body_text,
        instruction,
        article_title
    )


    # 4. Llamar a content_generator.generate_seo_content
    # Pasar las fuentes USADAS, los parámetros ORIGINALES, y el prompt de modificación.
    print(f"🧠 Copilot: Llamando a generate_seo_content para regenerar...")

    # === Llamar a generate_seo_content ===
    # Pasar la lista de fuentes USADAS (original_sources_used)
    regenerated_article_data = content_generator.generate_seo_content(
        tema_articulo, # Tema original del artículo
        original_sources_used, # <-- PASAR LAS FUENTES USADAS AQUÍ
        longitud=longitud_original, # Longitud original
        tono=tono_original, # Tono original
        modification_prompt=modification_prompt_text # Pasar el prompt de modificación
    )
    # ====================================


    if not regenerated_article_data:
         print(f"❌ Copilot: generate_seo_content falló durante la regeneración para ID {article_id}.")
         return None


    print(f"✅ Copilot: Regeneración completada para artículo ID {article_id}. Retornando nuevo body.")

    return {"rewritten_text": regenerated_article_data.get('body', '')}

def build_modification_prompt_text(text_to_rewrite: str, instruction: str, article_title: str) -> str:
    """
    Construye el texto del prompt de modificación para añadirlo al placeholder
    {modification_instructions} en el prompt principal del generador.
    """
    # Este es el texto que irá en el placeholder {modification_instructions}
    # dentro de DEFAULT_GENERATOR_PROMPT_TEMPLATE en content_generator.py
    modification_prompt = f"""

--- INSTRUCCIONES ADICIONALES DE REVISIÓN Y MODIFICACIÓN ---

Ahora, basándote en el artículo completo que generaste previamente (cuerpo en Markdown, usando las fuentes originales listadas arriba) y el contexto actual que te proporciono abajo, reescribe el artículo completo para cumplir con las siguientes instrucciones.

**Importante:** El texto actual del artículo (Canvas) se te proporciona abajo SÓLO para que tengas contexto sobre la estructura y contenido actual y entiendas mejor a qué se refieren las instrucciones del usuario. **La reescritura debe ser una nueva síntesis coherente y fluida a partir de las fuentes originales, incorporando estas modificaciones.**

Contexto del Artículo Original:
Título: {article_title}

Texto actual del artículo (referencia desde el editor del usuario):
---
{text_to_rewrite}
---

**Instrucción específica para modificar/mejorar el artículo:**
{instruction}

Aplica esta instrucción a todo el artículo según corresponda. Asegúrate de que el artículo reescrito sigue cumpliendo todos los requisitos de formato (JSON, encabezados, etc.) y SEO de las instrucciones principales, y que se basa en las fuentes originales.

--- FIN DE INSTRUCCIONES ADICIONALES ---

"""
    return modification_prompt
