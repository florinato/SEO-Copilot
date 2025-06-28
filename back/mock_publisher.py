# mock_publisher.py
# Simula la publicación de un artículo generando un archivo HTML local, incluyendo imágenes.
# Versión con diseño mejorado y HTML corregido.

import os
import re
import webbrowser
from datetime import datetime

import markdown


def convert_markdown_to_html(md_text):
    """Convierte texto en formato Markdown a HTML."""
    if not isinstance(md_text, str):
        return ""
    try:
        html_content = markdown.markdown(md_text, extensions=['fenced_code', 'tables']) # Añadir tablas
        return html_content
    except Exception as e:
        print(f"❌ Error durante la conversión de Markdown a HTML: {str(e)}")
        return f"<p>Error al convertir contenido: {str(e)}</p>"


def publish_to_html(article_data, image_data=None, filename=None):
    """
    Simula la publicación de un artículo generando un archivo HTML local,
    incluyendo la primera imagen si se proporciona metadata.
    """
    if not article_data or not isinstance(article_data, dict):
        print("❌ No se puede generar archivo HTML: Datos del artículo vacíos o inválidos.")
        return

    title = article_data.get('title') or article_data.get('titulo') or 'Artículo Generado Sin Título'
    meta_description = article_data.get('meta_description', 'Sin meta descripción.')
    body_md = article_data.get('body', '')
    tags = article_data.get('tags', [])
    if not isinstance(tags, list):
        tags = []

    body_html = convert_markdown_to_html(body_md)

    image_html = ""
    # Verificar si hay datos de imagen válidos y la URL de la primera imagen existe
    if image_data and isinstance(image_data, list) and len(image_data) > 0 and isinstance(image_data[0], dict) and image_data[0].get('url'):
        first_image = image_data[0]
        img_url = first_image.get('url') # URL de la imagen
        img_alt = first_image.get('alt_text', title) # Alt text, usar título si no hay
        img_author = first_image.get('author', 'Desconocido') # Autor
        img_author_url = first_image.get('author_url') # URL del perfil del autor
        img_source_url = first_image.get('source_page_url') # URL de la página de la imagen en Unsplash
        source_name = first_image.get('licencia', 'Unsplash') # Licencia o fuente


        sanitized_img_alt = img_alt.replace('"', "'") # Sanear comillas para atributo alt
        sanitized_author = img_author.replace('<', '<').replace('>', '>') # Sanear autor
        sanitized_source_name = source_name.replace('<', '<').replace('>', '>') # Sanear fuente

        if img_url: # Asegurarse de que la URL de la imagen no está vacía
            # Construir la etiqueta <img> y la leyenda
            image_html = f'<figure style="margin: 30px auto; text-align: center; max-width: 700px;">\n<img src="{img_url}" alt="{sanitized_img_alt}" style="max-width: 50%; height: auto; display: block; margin: 0 auto; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">\n'

            caption_parts = []
            if img_author and img_author_url:
                 caption_parts.append(f'Foto por <a href="{img_author_url}" target="_blank" rel="noopener noreferrer nofollow" style="color: #555; text-decoration: none;">{sanitized_author}</a>')
            elif img_author:
                 caption_parts.append(f'Foto por {sanitized_author}')

            if img_source_url:
                 caption_parts.append(f'en <a href="{img_source_url}" target="_blank" rel="noopener noreferrer nofollow" style="color: #555; text-decoration: none;">{sanitized_source_name}</a>')
            elif sanitized_source_name and sanitized_source_name != 'Desconocida':
                 caption_parts.append(f'Fuente: {sanitized_source_name}')

            if caption_parts:
                 metadata_caption = first_image.get('caption', '').strip()
                 if metadata_caption:
                      sanitized_metadata_caption = metadata_caption.replace('<', '<').replace('>', '>')
                      image_html += f'<figcaption style="text-align: center; font-size: 0.9em; color: #555; margin-top: 10px; line-height: 1.4;">{sanitized_metadata_caption}'
                      if caption_parts:
                           image_html += ' (' + ' | '.join(caption_parts) + ')'
                      image_html += '</figcaption>\n'
                 elif caption_parts:
                      image_html += f'<figcaption style="text-align: center; font-size: 0.9em; color: #555; margin-top: 10px; line-height: 1.4;">{" | ".join(caption_parts)}</figcaption>\n'


            image_html += '</figure>\n' # Cierre correcto de <figure>

        else:
            print("⚠️ No se pudo incluir imagen en la preview: URL de imagen no encontrada en los datos proporcionados.")

    elif image_data is not None and (not isinstance(image_data, list) or len(image_data) == 0):
         print(f"⚠️ image_data proporcionado pero vacío o inválido para preview.")


    # Generar nombre de archivo si no se proporcionó
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title_for_filename = re.sub(r'[^\w\s\-\._]', '', title).strip().replace(' ', '_')[:60]
        if not safe_title_for_filename:
            safe_title_for_filename = "articulo_generado"
        filename = f"{safe_title_for_filename}_{timestamp}_preview.html"

    # Limpiar y asegurar nombre de archivo final
    safe_filename = "".join([c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')]).rstrip()
    safe_filename = safe_filename.replace(' ', '_')
    if not safe_filename.lower().endswith('.html'):
        safe_filename += '.html'
    if not safe_filename or safe_filename.strip('._- ') == '':
        safe_filename = "generated_article_preview.html"

    full_filepath = os.path.join(os.getcwd(), safe_filename)


    # Construir la estructura HTML completa
    sanitized_title = title.replace('<', '<').replace('>', '>')
    sanitized_meta_description = meta_description.replace('<', '<').replace('>', '>')
    sanitized_tags = ', '.join(tags).replace('<', '<').replace('>', '>')

    html_template = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{sanitized_meta_description}">
    <title>{sanitized_title}</title>
    <link href="https://fonts.googleapis.com/css2?family=Merriweather:wght@400;700&family=Roboto:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary-color: #0056b3;
            --secondary-color: #333;
            --text-color: #444;
            --subtle-text-color: #666;
            --background-color: #f8f8f8;
            --card-background: #fff;
            --border-color: #eee;
            --base-font-size: 15px;
        }}

        body {{
            font-family: 'Roboto', sans-serif;
            font-size: var(--base-font-size);
            line-height: 1.7;
            margin: 0;
            padding: 20px;
            background-color: var(--background-color);
            color: var(--text-color);
            display: flex;
            justify-content: center;
            align-items: flex-start;
            min-height: 100vh;
        }}

        article {{
            max-width: 800px;
            width: 100%;
            margin: 20px 0;
            padding: 30px;
            background-color: var(--card-background);
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
            box-sizing: border-box;
        }}

        h1 {{
            font-family: 'Merriweather', serif;
            color: var(--primary-color);
            text-align: center;
            margin-bottom: 0.5em;
            line-height: 1.3;
            font-size: 2.2em;
        }}

        article > p:first-of-type em {{
            display: block;
            text-align: center;
            color: var(--subtle-text-color);
            font-size: 1em;
            margin-bottom: 2em;
            font-style: normal;
        }}

        h2, h3 {{
            font-family: 'Merriweather', serif;
            color: var(--secondary-color);
            margin-top: 2em;
            margin-bottom: 0.8em;
            padding-bottom: 0.3em;
            border-bottom: 1px solid var(--border-color);
        }}
        h2 {{ font-size: 1.6em; }}
        h3 {{ font-size: 1.2em; border-bottom: none; }}

        figure {{
            margin: 30px auto;
            text-align: center;
            max-width: 700px;
        }}
        article figure img {{
            display: block;
            max-width: 50%;
            height: auto;
            margin: 0 auto;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        figcaption {{ font-size: 0.8em; color: var(--subtle-text-color); margin-top: 10px; line-height: 1.4; }}
        figcaption a {{ color: var(--subtle-text-color); text-decoration: none; }}
        figcaption a:hover {{ text-decoration: underline; }}


        .article-body {{
            margin-top: 20px; /* Espacio arriba del cuerpo */ /* === CORREGIDO: Estaba dentro de figure === */
        }}

        .article-body p {{
            margin-bottom: 1.5em;
            text-align: justify;
            font-size: 1em;
        }}
        .article-body ul, .article-body ol {{ margin-bottom: 1.5em; }}
        .article-body li {{ margin-bottom: 0.5em; }}

        pre {{ background-color: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; margin: 1.5em 0; }}
        code {{ font-family: Consolas, Monaco, 'Andale Mono', 'Ubuntu Mono', monospace; font-size: 0.9em; }}
        pre code {{ display: block; padding: 0; margin: 0; white-space: pre-wrap; word-wrap: break-word; }}

        table {{ width: 100%; border-collapse: collapse; margin: 1.5em 0; }}
        th, td {{ border: 1px solid var(--border-color); padding: 10px; text-align: left; }}
        th {{ background-color: #f0f0f0; font-weight: bold; }}

        .tags {{ margin-top: 40px; font-style: italic; color: var(--subtle-text-color); border-top: 1px solid var(--border-color); padding-top: 15px; font-size: 0.85em; }}
        .tags strong {{ font-weight: normal; }}

        @media (max-width: 600px) {{
            :root {{ --base-font-size: 14px; }}
            body {{ padding: 10px; }}
            article {{ padding: 20px; }}
            h1 {{ font-size: 1.6em; }}
            h2 {{ font-size: 1.3em; }}
            h3 {{ font-size: 1.1em; }}
            figure {{ margin: 20px auto; }}
            article figure img {{ max-width: 70%; }}
            figcaption {{ font-size: 0.75em; }}
            .tags {{ font-size: 0.8em; }}
            code {{ font-size: 0.85em; }}
        }}
    </style>
</head>
<body>
    <article>
        <h1>{sanitized_title}</h1>
        <p><em>{sanitized_meta_description}</em></p>

        {image_html} <!-- La figura de la imagen va aquí -->

        <div class="article-body"> <!-- === CORREGIDO: Este div ahora envuelve solo el cuerpo del artículo === -->
            {body_html}
        </div>

        <div class="tags">
            <strong>Tags:</strong> {sanitized_tags}
        </div>
    </article>
</body>
</html>
"""

    try:
        # Asegurarse de que el nombre del archivo es válido y termina en .html
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title_for_filename = re.sub(r'[^\w\s\-\._]', '', title).strip().replace(' ', '_')[:60]
            if not safe_title_for_filename: safe_title_for_filename = "articulo_generado"
            filename = f"{safe_title_for_filename}_{timestamp}_preview.html"

        safe_filename = "".join([c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')]).rstrip()
        safe_filename = safe_filename.replace(' ', '_')
        if not safe_filename.lower().endswith('.html'): safe_filename += '.html'
        if not safe_filename or safe_filename.strip('._- ') == '': safe_filename = "generated_article_preview.html"

        full_filepath = os.path.join(os.getcwd(), safe_filename)

        with open(full_filepath, "w", encoding="utf-8") as f:
            f.write(html_template)

        print(f"✅ Previsualización HTML generada en: {full_filepath}")

        # Opcional: Abrir automáticamente en el navegador
        try:
            webbrowser.open(f"file://{os.path.abspath(full_filepath)}")
        except Exception as e:
            print(f"⚠️ No se pudo abrir el navegador automáticamente: {str(e)}")
            print(f"Por favor, abre el archivo '{full_filepath}' manualmente en tu navegador.")

    except IOError as e:
        print(f"❌ Error al escribir el archivo HTML '{safe_filename}': {str(e)}")
    except Exception as e:
        print(f"❌ Error inesperado al generar el archivo HTML: {str(e)}")