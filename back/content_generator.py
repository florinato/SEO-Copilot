# content_generator.py
# Módulo principal para la generación (inicial) y ejecución de prompts externos (reescritura).
import json
import re
from typing import Any, Dict, List, Optional  # Importar List para type hinting

import database  # Usado por funciones de Database, aunque no directamente en las funciones principales aquí
import json5
import llm_client  # Para llamar a Gemini
import mock_publisher  # Usado por el pipeline o pruebas, no directamente en las funciones principales aquí
import web_tools  # Usado por scraper, no directamente en las funciones principales aquí

# Importar aquí los prompts por defecto si están hardcodeados en este archivo
DEFAULT_GENERATOR_PROMPT_TEMPLATE = """
Eres un experto redactor de contenido SEO y especialista en [marketing digital]. Tu objetivo es crear un artículo de blog **único, valioso y altamente optimizado para SEO** sobre el tema: **"{topic}"**.

Utilizarás la información proporcionada en las siguientes {loaded_source_count} fuentes para inspirarte y obtener datos. **DEBES sintetizarla, reescribirla completamente en un texto COHESIVO, FLUIDO y bien estructurado que siga una narrativa lógica.** Evita el plagio. **No copies ni parafrasees frases o párrafos directamente de las fuentes; reestructura las ideas por completo.** El artículo debe leerse como una pieza original y pulida.

---
**Fuentes de Información:**
{sources_text}
---

**Instrucciones para el Artículo Generado:**

1.  **Rol:** Actúa como un redactor experto que crea contenido de autoridad para un blog especializado.
2.  **Tarea:** Escribe un artículo completo y bien estructurado sobre "{topic}".
3.  **Originalidad, Síntesis y FLUJO:** El artículo debe ser 100% original y el resultado de una síntesis profunda. **La clave es la fluidez.** Asegura **transiciones suaves y lógicas** entre ideas y secciones. Cada párrafo debe desarrollarse adecuadamente.
4.  **Longitud Estimada:** El **cuerpo** del artículo (todo el texto dentro del 'body' JSON) debe tener aproximadamente **{longitud} palabras**. Asegúrate de cubrir los puntos clave de las fuentes y expande las secciones si es necesario para alcanzar esta longitud.
5.  **Tono:** El tono del artículo debe ser "{tono}".
6.  **Estructura y Formato:**
    *   Presenta la salida **EXCLUSIVAMENTE** como un objeto JSON válido.
    *   El JSON debe tener las siguientes claves:
        *   `title`: **Genera un título atractivo y optimizado para SEO. Este campo NO debe estar vacío.** Debe incluir la palabra clave principal "{topic}".
        *   `meta_description`: Una meta descripción concisa y persuasiva para motores de búsqueda (aprox. 150-160 caracteres), incluyendo la palabra clave principal. **Este campo NO debe estar vacío.**
        *   `tags`: Una lista de 3-4 palabras clave relevantes para el artículo. **Esta lista NO debe estar vacía.**
        *   `body`: El contenido completo del artículo en formato Markdown. **Este campo NO debe estar vacío.**
    *   Dentro del 'body':
        *   Incluye una introducción clara que enganche al lector y presente el tema y el enfoque del artículo.
        *   Utiliza `##` para encabezados H2 y `###` para H3 para dividir el contenido en secciones lógicas.
        *   Asegura que cada sección y subsección fluye naturalmente hacia la siguiente.
        *   Usa párrafos, listas (con `-` o `*` para puntos) y texto en **negrita** (con `**`) para mejorar la legibilidad.
        *   Incluye una conclusión que resuma los puntos principales, ofrezca una reflexión final o perspectiva a futuro, y si es apropiado, un llamado a la acción.
7.  **Optimización SEO:**
    *   Incluye la palabra clave principal "{topic}" de forma natural en el `title`, `meta_description`, al principio del `body` (introducción), y en algunos encabezados (H2/H3) y párrafos del cuerpo.
    *   Incorpora las palabras clave secundarias que incluirás en la lista `tags` de forma natural en el cuerpo del artículo.
    *   Escribe para un público humano: el texto debe ser fácil de leer, interesante y útil.
8.  **Contenido:** Base el contenido *únicamente* en la información de las fuentes proporcionadas. No inventes datos. **Sintetiza y armoniza la información de múltiples fuentes, integrándola de manera natural.**

Produce **SOLO** el objeto JSON. No añadas texto explicativo antes ni después del JSON.

{modification_instructions}
"""


def generate_seo_content(
    topic: str,
    sources_with_content: list, # Lista de diccionarios con 'full_content', 'score', etc.
    longitud: int,
    tono: str,
    modification_prompt: Optional[str] = None # Prompt de modificación opcional
):
    """
    Genera un artículo de blog optimizado para SEO (generación inicial),
    O regenera/reescribe un artículo (si modification_prompt es dado).
    Siempre espera una respuesta JSON.
    """
    print(f"\n✍️ Generator: Generando/Regenerando contenido para '{topic}'")
    print(f"   (Modo: {'Regeneración' if modification_prompt else 'Generación Inicial'})")
    print(f"   (Config Recibida: Longitud={longitud} palabras, Tono='{tono}')")


    # === PASO 1: Construir el Prompt Base (Usando la plantilla hardcodeada y fuentes/parámetros) ===
    if not sources_with_content:
        print(f"❌ Generator: No se proporcionaron fuentes con contenido para generar/regenerar contenido sobre '{topic}'.")
        return None

    source_contents = []
    loaded_source_count = 0

    for i, source_data in enumerate(sources_with_content):
        content = source_data.get('full_content')
        if content:
            source_contents.append(f"### Fuente {i+1}: {source_data.get('titulo', source_data.get('url', 'N/A'))}\n\n{content}\n\n---\n\n")
            loaded_source_count += 1

    if not source_contents:
         print(f"❌ Generator: No se pudo usar el contenido de ninguna fuente proporcionada para generar/regenerar.")
         return None

    sources_text = "".join(source_contents)

    # Construir el prompt final usando la plantilla HARDCODEADA
    # Formatear con los parámetros recibidos Y el prompt de modificación (o "")
    try:
        generation_prompt = DEFAULT_GENERATOR_PROMPT_TEMPLATE.format(
            topic=topic,
            sources_text=sources_text,
            loaded_source_count=loaded_source_count,
            longitud=longitud,
            tono=tono,
            # === LLENAR EL PLACEHOLDER AQUI ===
            modification_instructions=f"\n\nInstrucciones de Modificación:\n{modification_prompt}" if modification_prompt else ""
            # ===============================
        )
    except KeyError as e:
         print(f"❌ Generator: Error al formatear plantilla: {e}. Asegúrate de que la plantilla tiene todos los placeholders correctos incluyendo modification_instructions.")
         return None


    # === PASO 4: Llamar a la IA y Parsear la Respuesta (Siempre JSON esperado) ===
    try:
        print("🧠 Generator: Solicitando respuesta a Gemini...")
        raw_response_text = llm_client.generate_raw_content(generation_prompt) # Síncrona, NO usar await aquí

        # === Lógica de parseo JSON ===
        json_match = re.search(r'\{.*\}', raw_response_text, re.DOTALL)

        if json_match:
            json_str = json_match.group(0)
            json_str = json_str.replace('```json', '').replace('```', '').strip()
            regex_control_chars = r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F\u2028\u2029]'
            cleaned_json_str = re.sub(regex_control_chars, '', json_str)

            try:
                 generated_data = json.loads(cleaned_json_str)
            except json.JSONDecodeError as e:
                 print(f"❌ Generator: Error al parsear JSON: {str(e)}")
                 if 'cleaned_json_str' in locals(): print(f"Cadena intentando parsear:\n{cleaned_json_str[:500]}...")
                 return None # Fallo crítico de parseo

            required_keys = ['title', 'meta_description', 'tags', 'body']
            if not all(key in generated_data for key in required_keys):
                 print(f"❌ Generator: Estructura JSON incompleta. Faltan claves.")
                 print(f"Datos parseados:\n{generated_data}")
                 return None

            print("✅ Generator: Contenido generado/regenerado y parseado JSON.")
            # Añadir metadata adicional (tema)
            generated_data['tema'] = topic
            # score_fuentes_promedio no se calcula aquí.

            return generated_data # Retorna el diccionario validado (si es JSON completo)

        else:
            print(f"❌ Generator: La respuesta de la IA NO contenía un objeto JSON válido.")
            print(f"Respuesta cruda recibida:\n{raw_response_text[:500]}...")
            return None

    except Exception as e:
        print(f"❌ Generator: Error general al generar/regenerar contenido: {str(e)}")
        if raw_response_text: print(f"Respuesta cruda (parcial):\n{raw_response_text[:500]}...")
        return None

# === FUNCIÓN: Ejecutar un Prompt Externo (para tareas que no necesitan JSON) ===
# Esta función SE MANTIENE SEPARADA. La usará copilot para tareas que NO necesitan generar JSON completo.
# Por ejemplo: generar solo sugerencias (texto plano), o reescribir solo un fragmento si no quieres regenerar todo el JSON.
def execute_external_prompt(prompt: str) -> str:
    """
    Ejecuta un prompt pre-construido con el cliente LLM principal.
    Ideal para tareas de texto plano (reescritura de fragmentos, resumen, etc.).

    Args:
        prompt (str): El prompt completo para enviar al LLM.

    Returns:
        str: La respuesta cruda (limpiada) del LLM.
    """
    print(f"\n🧠 Generator: Ejecutando prompt externo (Texto Plano)...")
    print(f"   Prompt (inicio): '{prompt[:200]}...'")

    try:
        # Llamar a Gemini usando llm_client (síncrono)
        ai_response = llm_client.generate_raw_content(prompt) # Síncrona, NO usar await aquí

        print("✅ Generator: Prompt externo ejecutado. Respuesta recibida.")
        # Limpiar la respuesta si es necesario (ej. quitar bloques de código markdown)
        ai_response = ai_response.replace('```text', '').replace('```', '').strip()
        ai_response = ai_response.replace('```markdown', '').replace('```', '').strip() # También para markdown


        return ai_response # Retornar respuesta limpia

    except Exception as e:
        print(f"❌ Generator: Error al ejecutar prompt externo (Texto Plano): {str(e)}")
        return f"Error al ejecutar prompt: {str(e)}"


# === Bloque para pruebas independientes (si lo mantienes) ===
# ...
