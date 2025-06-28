# analyzer.py

import json
import re

import llm_client  # Para usar el cliente LLM

# Importar aquí el prompt por defecto si está hardcodeado en este archivo
DEFAULT_ANALYZER_PROMPT_TEMPLATE = """
Evalúa este artículo sobre '{tema}' y devuelve SOLO un JSON válido con:
- "score": 1-10 (1=irrelevante, 10=excelente)
- "reason": Explicación concisa
- "resumen": Resumen breve (máx. 100 caracteres)
- "tags": 3-5 palabras clave relevantes

Criterios:
1. Relevancia: ¿Aborda directamente "{tema}"?
2. Autoridad: ¿Fuente confiable/citada?
3. Actualidad: ¿Menciona fechas recientes (2024-2025)?
4. Utilidad: ¿Contiene datos/ejemplos concretos?

Texto del artículo:
{text}
""" # HARDCODEADO AQUI


# analyze_with_gemini ahora solo recibe el tema y el texto
# NO recibe prompt_template
def analyze_with_gemini(tema: str, text: str):
    """
    Analiza el contenido con Gemini usando el cliente LLM y un prompt específico.
    Usa la plantilla de prompt hardcodeada definida en este archivo.
    """
    # === Definición del prompt específico para la tarea de análisis ===
    # Usar la plantilla HARDCODEADA DEFINIDA AQUI
    # Formatear con el tema y el texto recibidos
    prompt = DEFAULT_ANALYZER_PROMPT_TEMPLATE.format(tema=tema, text=text[:8000]) # Limitar texto pasado a la IA


    try:
        # ... (código existente para llamar a llm_client.generate_raw_content) ...
        response_text = llm_client.generate_raw_content(prompt)

        # ... (código existente para extraer y parsear JSON, limpiar) ...
        json_str_match = re.search(r'\{.*\}', response_text, re.DOTALL)

        if json_str_match:
            json_str = json_str_match.group()
            # Limpieza de caracteres de control
            regex_control_chars = r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F\u2028\u2029]'
            cleaned_json_str = re.sub(regex_control_chars, '', json_str)

            # Usar json.loads (o json5 si está configurado como fallback en este archivo)
            try:
                 # Si json5 está configurado como fallback en este archivo, usarlo aquí
                 # from your_module import JSON_PARSER # Si JSON_PARSER se define centralmente
                 # if JSON_PARSER == 'json5':
                 #     import json5
                 #     generated_data = json5.loads(cleaned_json_str)
                 # else:
                 #     generated_data = json.loads(cleaned_json_str)
                 # Para simplificar, usamos json.loads. Si falla, el try/except de abajo lo captura.
                 generated_data = json.loads(cleaned_json_str)

            except json.JSONDecodeError as e:
                 print(f"❌ Analyzer: Error al parsear JSON: {str(e)}")
                 if 'cleaned_json_str' in locals():
                      print(f"Cadena intentando parsear:\n{cleaned_json_str[:500]}...")
                 return None # Fallo crítico de parseo

            # Retornamos el diccionario de análisis
            return generated_data

        else:
            print(f"⚠️ Analyzer: Gemini no retornó estructura JSON esperada para tema '{tema}'. Inicio respuesta: {response_text[:200]}...")
            # Retornar un diccionario de error que el scraper pueda manejar
            return {"score": 1, "reason": "Error de análisis IA", "tags": []}

    except Exception as e:
        # Capturamos cualquier excepción
        print(f"❌ Analyzer: Error general en Gemini: {str(e)}")
        # Retornar un diccionario de error
        return {"score": 1, "reason": "Error general IA", "tags": []}



