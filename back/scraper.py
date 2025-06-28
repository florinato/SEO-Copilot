# scraper.py (Corregido - No usa plantilla de prompt para analyzer)

import re
from datetime import \
    datetime  # Importar datetime aquí si se usa para fecha_scraping
from urllib.parse import quote_plus

import analyzer
import database
import requests
import web_tools
from bs4 import BeautifulSoup


def buscar_noticias(
    tema: str,
    num_noticias_a_buscar: int,
    min_score_para_analizar: int,
    num_resultados_a_retornar: int
    # Ya NO recibe analyzer_prompt_template
):
    """
    Busca URLs de fuentes para un tema, resuelve, obtiene contenido, analiza con IA
    y retorna metadata + contenido de las fuentes más relevantes.

    Args:
        tema (str): El tema o consulta de búsqueda principal.
        num_noticias_a_buscar (int): Número máximo de URLs a buscar inicialmente en DDG.
        min_score_para_analizar (int): Score mínimo que una fuente analizada debe tener.
        num_resultados_a_retornar (int): Número máximo de fuentes (metadata + contenido) a retornar.

    Returns:
        list: Lista de diccionarios con metadata de fuente + 'full_content'.
    """
    print(f"\n🔍 Scraper: Buscando noticias sobre: {tema}")
    print(f"   (Config Recibida: Buscar={num_noticias_a_buscar}, Score min={min_score_para_analizar}, Retornar={num_resultados_a_retornar})")

    # ... (fetch_urls_from_ddg - sin cambios) ...
    def fetch_urls_from_ddg():
        """Realiza la búsqueda en DuckDuckGo y retorna una lista de URLs candidatas."""
        query_ddg = f"{tema} site:.es OR site:.com after:2024"
        url = f"https://duckduckgo.com/html/?q={quote_plus(query_ddg)}&kl=es-es"
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            return [
                ("https:" + a['href'] if a['href'].startswith("//") else a['href'])
                for a in soup.select('a.result__url')[:num_noticias_a_buscar]
                if not any(x in a['href'] for x in ["youtube.com", "facebook.com", "twitter.com", "linkedin.com"])
            ]
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Scraper: Error en búsqueda de URLs (RequestException) para '{tema}': {str(e)}")
            return []
        except Exception as e:
            print(f"⚠️ Scraper: Error en búsqueda de URLs (General Exception) para '{tema}': {str(e)}")
            return []


    # --- Lógica principal del scraper ---
    processed_articles = []
    driver = None

    try:
        driver = web_tools.setup_driver()
        if not driver: print("⚠️ Scraper: Continuará sin resolución de redirecciones.")

        for url in fetch_urls_from_ddg():
            try:
                final_url = url
                if driver:
                    resolved = web_tools.get_final_url(url, driver)
                    if resolved: final_url = resolved
                    else: print(f"⚠️ Scraper: Usando URL original por fallo en redirección: {final_url[:60]}...")
                else: final_url = url

                if database.url_existe(final_url):
                    print(f"⏩ Scraper: Saltando duplicado: {final_url[:60]}...")
                    continue

                if any(x in final_url for x in ["/tag/", "/temas/", "?page=", "#", "/category/", ".pdf", ".zip"]):
                    print(f"⏩ Scraper: Saltando URL no-articulo/archivo: {final_url[:60]}...")
                    continue

                text = web_tools.fetch_and_extract_content(final_url)
                if not text:
                    print(f"⏩ Scraper: Saltando URL por contenido no extraído/muy corto: {final_url[:60]}...")
                    continue

                # === Analizar el Contenido con IA (Analyzer) ===
                # analyzer.analyze_with_gemini usa su prompt hardcodeado
                # No le pasamos template aquí
                analysis_result = analyzer.analyze_with_gemini(tema, text) # <-- No pasar template

                if not analysis_result or analysis_result.get('score', 0) is None:
                    print(f"⏩ Scraper: Saltando URL por fallo o score inválido en análisis IA: {final_url[:60]}...")
                    continue

                # === PREPARAR DATOS DE FUENTE PROCESADA ===
                processed_source_data = {
                    'url': final_url,
                    'full_content': text,
                    'score': analysis_result.get('score', 0),
                    'resumen': analysis_result.get('resumen', analysis_result.get('reason', '')),
                    'tags': analysis_result.get('tags', []),
                    'titulo': analysis_result.get('titulo', f"Artículo sobre {tema}"),
                    'fuente': final_url.split('/')[2] if len(final_url.split('/')) > 2 else '',
                    'fecha_publicacion_fuente': None,
                    'fecha_scraping': datetime.now().isoformat(),
                    'usada_para_generar': 0,
                }

                # === Guardar la metadata de la fuente en la tabla `articulos` AQUI ===
                try:
                    source_id_in_db = database.guardar_articulo(processed_source_data)
                    if source_id_in_db:
                        processed_source_data['id'] = source_id_in_db
                        print(f"✅ Scraper: Fuente {final_url[:60]}... analizada y guardada en DB con ID {source_id_in_db}.")
                        processed_articles.append(processed_source_data)
                    else:
                        print(f"⚠️ Scraper: Falló el guardado en DB de fuente {final_url[:60]}... Saltando.")
                except Exception as db_e:
                     print(f"❌ Scraper: Error al intentar guardar fuente {final_url[:60]}... en DB: {db_e}")
                     pass

            except Exception as e:
                print(f"⚠️ Scraper: Error procesando URL {url}: {e}")
                pass

    finally:
        if driver:
            try: driver.quit()
            except Exception as e: print(f"⚠️ Scraper: Error al cerrar el driver de Selenium: {e}")
            print("✅ Scraper: Driver de Selenium cerrado.")


    # === FILTRAR Y ORDENAR ===
    valid_articles = [a for a in processed_articles if a and isinstance(a.get('score'), (int, float)) and a.get('score', 0) >= min_score_para_analizar and a.get('id') is not None]

    if not valid_articles:
        print(f"ℹ️ Scraper: No se encontraron artículos válidos (Score >= {min_score_para_analizar}, guardados en DB).")
        return []

    valid_articles.sort(key=lambda x: x.get('score', 0), reverse=True)

    top_articles = valid_articles[:num_resultados_a_retornar]
    print(f"🏆 Scraper: Retornando TOP {len(top_articles)} artículos de {len(valid_articles)} válidos.")
    return top_articles


# === Bloque para pruebas independientes (sin cambios) ===
if __name__ == "__main__":
    print("--- Prueba independiente del Scraper ---")
    try:
        database.inicializar_db()
        print("✅ Base de datos inicializada para prueba de scraper.")
    except Exception as e:
        print(f"❌ Error al inicializar la base de datos para la prueba: {e}")
        pass # Continuar si la DB falla

    test_tema = "ultimas noticias inteligencia artificial"
    test_num_buscar = 15
    test_min_score = 6
    test_num_retornar = 5

    processed_sources = buscar_noticias(
        tema=test_tema,
        num_noticias_a_buscar=test_num_buscar,
        min_score_para_analizar=test_min_score,
        num_resultados_a_retornar=test_num_retornar
    )

    print("\n--- Resultados del Scraper (TOP Procesado y Guardado) ---")
    if processed_sources:
        for i, source_data in enumerate(processed_sources):
            print(f"\n{i+1}. ID: {source_data.get('id', 'N/A')}")
            print(f"   URL: {source_data.get('url', 'N/A')}")
            print(f"   Título: {source_data.get('titulo', 'N/A')}")
            print(f"   Score: {source_data.get('score', 'N/A')}")
            print(f"   Resumen: {source_data.get('resumen', 'N/A')}")
            print(f"   Tags: {', '.join(source_data.get('tags', []))}")
            content_preview = source_data.get('full_content', 'Sin contenido').strip()
            print(f"   Contenido (primeros 300 chars): {content_preview[:300]}...")
            print(f"   Longitud contenido: {len(content_preview)} chars")
    else:
        print("❌ El scraper no retornó ninguna fuente procesada y guardada.")
    print("\n--- Fin de la prueba independiente del Scraper ---")