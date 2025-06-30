# SEO-Copilot: Asistente Inteligente para Contenido SEO

![SEO-Copilot Logo](https://via.placeholder.com/150?text=SEO-Copilot)
<!-- Opcional: Añadir un logo después -->

Automatización y Supervisión Asistida por IA para la Creación y Optimización de Contenido Digital.

---

## Resumen

SEO-Copilot es un prototipo de sistema diseñado para revolucionar la creación y gestión de contenido de blog, automatizando tareas clave del pipeline de contenido y ofreciendo asistencia inteligente a través de IA para la revisión y optimización. Va más allá de la simple generación de texto, integrando investigación, análisis de fuentes, generación de borradores optimizados para SEO, búsqueda de imágenes, y herramientas para la edición y mejora colaborativa del contenido.

Construido pensando en la eficiencia y la supervisión humana, SEO-Copilot busca liberar a los creadores de contenido y profesionales del marketing de tareas tediosas, permitiéndoles enfocarse en la estrategia y la creatividad de alto nivel.

---

## Problema que Resuelve

La creación de contenido de calidad para blogs y sitios web es un proceso intensivo en tiempo y recursos. Requiere investigación, redacción, optimización para motores de búsqueda (SEO on-page y de contenido), búsqueda de imágenes, y gestión. Esto es costoso, lento y a menudo un cuello de botella para individuos y empresas que necesitan mantener una presencia digital fresca y relevante.

---

## Solución: SEO-Copilot

SEO-Copilot aborda este problema ofreciendo un pipeline de contenido asistido por IA que:

*   Automatiza la Investigación: Encuentra fuentes relevantes en la web para un tema dado.
*   Genera Borradores Optimizados: Crea artículos completos (título, meta descripción, tags, cuerpo) basados en la investigación y parámetros definidos.
*   Busca Elementos Visuales: Asocia imágenes relevantes al contenido.
*   Ofrece un Espacio de Trabajo (Canvas): Permite revisar y editar el contenido generado.
*   Asiste en la Optimización: Proporciona sugerencias de mejora generadas por IA.
*   Permite Refinar Contenido: Permite aplicar las sugerencias de IA o instrucciones específicas para regenerar el texto.
*   Gestiona Datos: Almacena fuentes, configuraciones y artículos generados.

---

## Funcionalidades Actuales (Prototipo de Hackathon)

El prototipo funcional demuestra las siguientes capacidades:

*   Generación de Contenido Guiada por Parámetros: Inicia un pipeline automatizado (scrpaing, análisis de fuentes, generación de texto por IA, búsqueda de imágenes) para un tema específico, utilizando parámetros como longitud, tono, número mínimo de fuentes y score mínimo, proporcionados a través de la interfaz.
*   Investigación y Análisis de Fuentes: Busca URLs en la web (DuckDuckGo), obtiene su contenido, lo analiza con IA (Google Gemini) asignando un score de relevancia/calidad y extrayendo metadata (resumen, tags). Guarda las fuentes analizadas en una base de datos (SQLite).
*   Generación de Borradores de Artículo: Utiliza las fuentes más relevantes encontradas para un tema y llama a la IA (Google Gemini) para generar un borrador de artículo SEO-optimizado completo (título, meta descripción, tags, cuerpo en Markdown) basándose en los parámetros de longitud y tono. Incluye lógica para manejar respuestas de IA con formato JSON imperfecto.
*   Búsqueda y Asociación de Imágenes: Busca imágenes relevantes utilizando una API (Unsplash) basándose en el título y tags del artículo generado, y asocia las imágenes encontradas al borrador.
*   Persistencia de Datos: Almacena fuentes, artículos generados y metadata de imágenes asociadas en una base de datos SQLite local.
*   Gestión de Configuración por Tema: Permite cargar (y conceptualmente guardar) parámetros de configuración (como longitud, tono, umbrales de score) asociados a un tema/sección específico en la base de datos.
*   API Backend (FastAPI): Un servidor API que expone los puntos de entrada para:
    *   Disparar el pipeline completo de generación (POST /generate).
    *   Cargar la configuración por defecto o guardada para un tema (GET /config/{tema}).
    *   Listar los artículos generados (GET /articles).
    *   Obtener los detalles completos de un artículo generado (incluyendo imágenes) (GET /articles/{id}).
    *   Actualizar un artículo generado (ej. el cuerpo en Markdown desde el Canvas) (PUT /articles/{id}).
    *   Disparar la generación de sugerencias de mejora para un artículo (POST /articles/{id}/generate-suggestions).
    *   Disparar la reescritura del contenido de un artículo basándose en una instrucción/sugerencias (POST /articles/{id}/rewrite).
*   Interfaz Web (HTML/JS): Un panel de control básico basado en HTML y JavaScript que se ejecuta en el navegador y se comunica con la API de FastAPI para:
    *   Permitir ingresar el tema y los parámetros de generación en un formulario.
    *   Disparar el proceso de generación al hacer clic en un botón.
    *   Mostrar una lista de artículos generados.
    *   Navegar a una vista de revisión (el "Canvas") al seleccionar un artículo.
*   Canvas (Vista de Revisión y Edición): En la vista de revisión:
    *   Muestra los datos del artículo (título, meta, imagen, cuerpo) cargados desde el backend.
    *   Presenta el cuerpo del artículo en un área de texto editable (un textarea básico).
    *   Permite guardar los cambios realizados en el Canvas enviándolos al backend (PUT /articles/{id}).
    *   Permite "Publicar" (simulado por ahora, dispara la generación de una previsualización HTML en el backend).
*   Sugerencias del Copiloto (Análisis por IA): Al hacer clic en un botón, llama a la IA (Google Gemini) a través del backend para generar sugerencias de mejora específicas para el artículo que está en el Canvas, basándose en su contenido y elementos SEO.
*   Aplicar Sugerencias (Reescritura Asistida): Las sugerencias se muestran en una lista interactiva. El usuario puede seleccionar sugerencias individuales o aplicar todas. Al aplicar, el JavaScript envía la(s) sugerencia(s) seleccionada(s) (o una combinación de todas) junto con el texto actual del Canvas a un endpoint del backend (POST /articles/{id}/rewrite). El backend llama a la IA para regenerar el cuerpo del artículo basándose en la instrucción/sugerencias y el texto actual del Canvas (y las fuentes originales si están disponibles). El Canvas se actualiza con el texto reescrito.

---

## Cómo Funciona (Flujo Implementado)

*   El usuario abre la interfaz HTML en su navegador.
*   En la sección de generación, ingresa el Tema y ajusta los Parámetros (ej. longitud, tono).
*   Clica "Iniciar Generación".
*   El frontend envía estos datos a la API del backend (POST /generate).
*   El backend ejecuta el Pipeline:
    *   Carga la configuración del tema (si existe).
    *   Llama al Scraper (scraper.py) con los parámetros.
    *   El Scraper busca fuentes, obtiene contenido (web_tools.py), analiza con IA (analyzer.py), guarda la metadata de fuentes en la DB (database.py). Retorna las fuentes procesadas (metadata + contenido).
    *   Llama al Generador (content_generator.py) con las fuentes procesadas y los parámetros.
    *   El Generador construye el prompt y llama a la IA (llm_client.py) para obtener el borrador de artículo (JSON).
    *   Llama a Web Tools para buscar imágenes (web_tools.py).
    *   Guarda el artículo generado y la metadata de imágenes en la DB (database.py).
    *   Marca las fuentes usadas en la DB (database.py).
    *   Genera una previsualización HTML local (mock_publisher.py).
    *   El endpoint POST /generate retorna el ID del artículo generado.
*   El usuario navega a la sección "Artículos Generados".
*   El frontend carga la lista de artículos desde la API (GET /articles) y la muestra.
*   El usuario clica en un artículo de la lista.
*   El frontend navega a la sección de Revisión (Canvas), carga los detalles del artículo desde la API (GET /articles/{id}), y llena el Canvas (el textarea).
*   En la vista de Revisión:
    *   El usuario edita el texto en el Canvas. Clica "Guardar Cambios" (PUT /articles/{id}).
    *   Clica "Generar Sugerencias". El frontend llama a POST /articles/{id}/generate-suggestions. El backend llama a copilot.generate_article_suggestions (IA), que retorna sugerencias como texto plano. El frontend muestra las sugerencias en una lista.
    *   El usuario selecciona sugerencias de la lista.
    *   Clica "Aplicar Sugerencias Seleccionadas". El frontend toma el texto actual del Canvas y las sugerencias seleccionadas, y las envía a POST /articles/{id}/rewrite como una instrucción combinada.
    *   El backend llama a copilot.regenerate_article_content (IA). El Copiloto construye un prompt basado en el texto del Canvas, la instrucción/sugerencias, el contexto del artículo y las fuentes originales (obtenidas de la DB). Llama a content_generator.generate_seo_content (motor de IA) para regenerar el cuerpo.
    *   El backend retorna el cuerpo regenerado. El frontend reemplaza el contenido del Canvas.
*   El usuario puede guardar los cambios reescritos o publicar (simulado).

---

## Stack Tecnológico

*   Backend: Python (FastAPI, Uvicorn, Pydantic, Requests, BeautifulSoup4, Selenium, WebDriver-Manager, Google-generativeai, Markdown, SQLite3)
*   Frontend: HTML, CSS, JavaScript (Fetch API)
*   APIs/Servicios: Google Gemini API, Unsplash API, DuckDuckGo

---

## Potencial y Roadmap Futuro

El prototipo actual es una base sólida para un sistema mucho más potente:

*   Interfaz Conversacional Completa: Integrar un chat directo con el Copiloto (IA) en la UI para controlar todo el flujo de trabajo y obtener asistencia en lenguaje natural ( Road map, usando la tabla de chat).
*   Aplicar Sugerencias Avanzadas: Permitiendo la aplicación de sugerencias o instrucciones a partes específicas del texto (párrafos, secciones), no solo al cuerpo completo.
*   Edición UI Completa: Editor de texto enriquecido (WYSIWYG o Markdown avanzado) en el Canvas, edición de título, meta descripción y tags directamente en la UI.
*   Gestión Completa de Imágenes: Galería de imágenes asociadas, búsqueda de más imágenes desde la UI, subir imágenes propias, insertar imágenes en el texto.
*   Integración con CMS: Conexión directa con APIs de plataformas como WordPress, Shopify, etc., para la publicación automatizada de artículos.
*   Análisis y Estrategia SEO Avanzada: Integración con Google Analytics, detección de "content gaps" comparado con la competencia, análisis de palabras clave, sugerencias de enlazado interno.
*   IA como Agente Autónomo: Modos de operación donde la IA puede generar y publicar contenido automáticamente para temas definidos, bajo objetivos y supervisión configurable.
*   Personalización Avanzada: Configuración detallada por blog/sitio, presets de estilos y tonos, plantillas de prompt editables en la UI.
*   Escalabilidad: Migración a una base de datos en la nube, implementación de colas de tareas para procesos largos, despliegue en servicios cloud (AWS, GCP, Azure, Render, etc.).
*   Soporte para Otros Tipos de Contenido: Generación para redes sociales, emails, descripciones de producto.

---

## Cómo Empezar

*   Clona este repositorio.
*   Crea y activa un entorno virtual de Python.
*   Instala las dependencias necesarias (pip install fastapi uvicorn[standard] pydantic requests beautifulsoup4 google-generativeai markdown selenium webdriver-manager json5).
*   Obtén tus claves de API de Google Gemini y Unsplash. Guárdalas en un archivo de configuración o variables de entorno según se indique en los módulos llm_client.py y web_tools.py.
*   Configura la ruta a tu archivo schema.sql en database.py.
*   Inicia el servidor FastAPI desde la carpeta back/: uvicorn api:app --reload
*   Abre el archivo articles_canvas.html en tu navegador (es recomendable usar una ventana de incógnito para evitar problemas de caché y CORS de archivos locales).

---

## Contribución

Las contribuciones son bienvenidas. Si tienes ideas o quieres ayudar a construir alguna de las funcionalidades del roadmap, no dudes en contactar.

---

## Sobre el Creador

[Tu Nombre/Nombre de Usuario]: Un desarrollador autodidacta apasionado por la IA y la automatización.
