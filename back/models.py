# models.py
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# --- Modelos para Configuración ---

class ConfigBase(BaseModel):
    """Modelo base para la configuración, excluyendo campos gestionados por DB."""
    tema: str = Field(..., description="Nombre de la sección o tema.")
    min_score_fuente: int = Field(5, ge=1, le=10, description="Score mínimo para fuentes en el scraping (Fase 1).")
    num_fuentes_scraper: int = Field(10, ge=1, description="Número de fuentes a intentar buscar en el scraping.")
    num_resultados_scraper: int = Field(5, ge=1, description="Número de fuentes a analizar y considerar guardar en la Fase 1.")
    min_score_generador: int = Field(7, ge=1, le=10, description="Score mínimo para fuentes a usar en la generación (Fase 2).")
    num_fuentes_generador: int = Field(3, ge=1, description="Número de fuentes a usar para la generación.")
    longitud_texto: int = Field(1500, ge=100, description="Longitud estimada del texto en palabras.")
    tono_texto: str = Field("neutral", description="Tono del texto ('neutral', 'formal', 'informal', 'técnico').")
    num_imagenes_buscar: int = Field(2, ge=0, description="Número de imágenes candidatas a buscar.")
    #prompt_analyzer_template: Optional[str] = Field(None, description="Plantilla de prompt personalizada para el Analyzer.")
    #prompt_generator_template: Optional[str] = Field(None, description="Plantilla de prompt personalizada para el Generator.")
    # prompt_copilot_template: Optional[str] = Field(None, description="Plantilla de prompt personalizada para el Copilot.") <-- Eliminado
    # Otros campos de configuración


class ConfigDB(ConfigBase):
    """Modelo para la configuración tal como se lee de la DB."""
    id: int
    fecha_creacion: datetime
    fecha_actualizacion: datetime

    class Config:
        orm_mode = True # Habilita compatibilidad con ORM (útil si usas SQLAlchemy, o con diccionarios de DB)


# --- Modelos para Artículos Fuente (Articulos) ---

class SourceArticleBase(BaseModel):
    """Modelo base para un artículo fuente."""
    titulo: str
    url: str
    score: int = Field(..., ge=1, le=10)
    resumen: Optional[str] = None
    fuente: Optional[str] = None
    fecha_publicacion_fuente: Optional[str] = None # O datetime si parseas la fecha


class SourceArticleDB(SourceArticleBase):
    """Modelo para un artículo fuente tal como se lee de la DB."""
    id: int
    fecha_scraping: datetime
    usada_para_generar: bool = False # Convertir INTEGER a bool

    class Config:
        orm_mode = True


# --- Modelos para Tags ---

class TagBase(BaseModel):
    """Modelo base para un tag."""
    tag: str


class TagDB(TagBase):
    """Modelo para un tag tal como se lee de la DB."""
    id: int

    class Config:
        orm_mode = True


# --- Modelos para Imágenes Generadas ---

class GeneratedImageBase(BaseModel):
    """Modelo base para una imagen generada."""
    url: str
    alt_text: Optional[str] = None
    caption: Optional[str] = None
    licencia: Optional[str] = None
    autor: Optional[str] = None
    author_url: Optional[str] = None # Añadido si web_tools lo obtiene
    source_page_url: Optional[str] = None # Añadido si web_tools lo obtiene


class GeneratedImageDB(GeneratedImageBase):
    """Modelo para una imagen generada tal como se lee de la DB."""
    id: int
    articulo_generado_id: int # FK

    class Config:
        orm_mode = True


# --- Modelos para Artículos Generados (Articulos_Generados) ---

class GeneratedArticleBase(BaseModel):
    """Modelo base para un artículo generado (lo que la IA produce)."""
    tema: str
    titulo: str
    meta_description: Optional[str] = None
    body: str
    tags: List[str] = [] # Esperamos una lista de strings


class GeneratedArticleCreate(GeneratedArticleBase):
    """Modelo para crear un artículo generado (lo que el pipeline guarda inicialmente)."""
    # Puede incluir metadata adicional que no viene directo de la IA JSON
    score_fuentes_promedio: Optional[float] = None
    # fecha_generacion y estado tienen defaults en DB


class GeneratedArticleUpdate(BaseModel):
    """Modelo para actualizar un artículo generado (desde el Canvas)."""
    titulo: Optional[str] = None
    meta_description: Optional[str] = None
    body: Optional[str] = None
    tags: Optional[List[str]] = None # Esperamos una lista de strings
    estado: Optional[str] = None


class GeneratedArticleDB(GeneratedArticleBase):
    """Modelo para un artículo generado tal como se lee de la DB."""
    id: int
    fecha_generacion: datetime
    fecha_publicacion_destino: Optional[datetime] = None # O str si no conviertes
    estado: str
    score_fuentes_promedio: Optional[float] = None
    imagenes: List[GeneratedImageDB] = [] # Añadir lista de imágenes asociadas

    class Config:
        orm_mode = True


# --- Modelos para Tareas de Generación (Generacion_Tareas) ---

class GenerationTaskBase(BaseModel):
    """Modelo base para una tarea de generación."""
    tema: str
    estado: str = "pendiente"
    mensaje_error: Optional[str] = None


class GenerationTaskCreate(GenerationTaskBase):
    """Modelo para crear una tarea de generación."""
    configuracion_id: Optional[int] = None # Puede ser None si no se asocia una config especifica
    # fecha_solicitud tiene default en DB


class GenerationTaskDB(GenerationTaskBase):
    """Modelo para una tarea de generación tal como se lee de la DB."""
    id: int
    configuracion_id: Optional[int] = None
    articulo_generado_id: Optional[int] = None
    fecha_solicitud: datetime
    fecha_actualizacion: datetime
    fecha_finalizacion: Optional[datetime] = None

    class Config:
        orm_mode = True


# --- Modelos de Solicitud API ---

# GenerateRequestModel hereda de ConfigBase.
# La UI enviará todos los campos de ConfigBase en la request.
class GenerateRequestModel(ConfigBase):
    """
    Modelo para la solicitud al endpoint POST /generate.
    Incluye todos los parámetros de configuración para el tema específico
    de esta ejecución, enviados desde la UI.
    """
    # Hereda todos los campos de ConfigBase.
    # Tema es requerido. Los demás tienen defaults en ConfigBase.
    pass # No necesitas re-declarar nada si la UI siempre envía todos los campos


# ChatRequestModel ya no necesita 'tema' si el contexto se pasa de otra forma (ej. article_id)
# Opcional: Si quieres permitir chat general sin artículo, puedes dejar 'tema' opcional
class ChatRequestModel(BaseModel):
    """Modelo para la solicitud al endpoint POST /chat."""
    user_message: str
    article_id: Optional[int] = Field(None, description="ID del artículo si el chat es contextual a uno.")
    # tema: Optional[str] = Field(None, description="Tema/sección si el chat es general para una sección.") # Eliminado si el chat es siempre sobre un artículo o tema conocido por el contexto


class ChatResponseModel(BaseModel):
    """Modelo para la respuesta del endpoint POST /chat."""
    ai_response: str
    # Opcional: Indicadores si la IA sugiere una acción que la UI deba manejar (ej. "suggested_action": "show_image_gallery")


class ConfigUpdateRequestModel(ConfigBase):
    """Modelo para la solicitud al endpoint PUT /config. Requiere el tema."""
    # Hereda todos los campos de ConfigBase, incluyendo tema (que es requerido)
    pass


# --- Modelos de Respuesta API (Resumen) ---
# Estos se pueden generar usando los modelos DB definidos arriba

# Lista de Artículos Generados (Resumen)
class GeneratedArticleSummary(BaseModel):
     id: int
     tema: str
     titulo: str
     fecha_generacion: datetime
     estado: str
     score_fuentes_promedio: Optional[float] = None
     # No incluye body ni imágenes

     class Config:
        orm_mode = True


# Lista de Fuentes (Resumen)
class SourceArticleSummary(BaseModel):
     id: int
     titulo: str
     url: str
     score: int
     fuente: Optional[str] = None
     fecha_scraping: datetime
     usada_para_generar: bool

     class Config:
        orm_mode = True


# Lista de Temas/Secciones
class SectionListResponse(BaseModel):
    sections: List[str]
    

class GeneratedArticleSourceLinkBase(BaseModel):
    """Modelo base para la relación entre articulo generado y fuente."""
    articulo_generado_id: int
    articulo_fuente_id: int

class GeneratedArticleSourceLinkDB(GeneratedArticleSourceLinkBase):
    """Modelo DB para la relación (no tiene campos adicionales gestionados por DB en este caso)."""
    # No hay ID propio ni fechas en esta tabla, solo los FKs son la clave primaria
    pass # No necesita campos extra

    class Config:
        orm_mode = True