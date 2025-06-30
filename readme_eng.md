# SEO-Copilot: Intelligent Assistant for SEO Content

![SEO-Copilot Logo](https://via.placeholder.com/150?text=SEO-Copilot)
<!-- Optional: Add a logo later -->

AI-Assisted Automation and Supervision for Digital Content Creation and Optimization.

---

## Overview

SEO-Copilot is a prototype system designed to radically transform blog content creation and management, automating key content pipeline tasks and offering intelligent AI assistance for review and optimization. It goes beyond simple text generation, integrating research, source analysis, SEO-optimized draft generation, image finding, and tools for collaborative content editing and improvement.

Built with efficiency and human oversight in mind, SEO-Copilot aims to free up content creators and marketing professionals from tedious tasks, allowing them to focus on high-level strategy and creativity.

---

## Problem Solved

Creating quality content for blogs and websites is a time-consuming and resource-intensive process. It requires research, writing, optimization for search engines (on-page and content SEO), image finding, and management. This is costly, slow, and often a bottleneck for individuals and businesses that need to maintain a fresh and relevant digital presence.

---

## Solution: SEO-Copilot

SEO-Copilot addresses this problem by offering an AI-assisted content pipeline that:

*   Automates Research: Finds relevant sources on the web for a given topic.
*   Generates Optimized Drafts: Creates complete articles (title, meta description, tags, body) based on the research and defined parameters.
*   Finds Visual Assets: Associates relevant images with the content.
*   Provides a Workspace (Canvas): Allows for reviewing and editing the generated content.
*   Assists in Optimization: Offers AI-generated suggestions for improvement.
*   Enables Content Refinement: Allows applying AI suggestions or specific instructions to regenerate the text.
*   Manages Data: Stores sources, configurations, and generated articles.

---

## Current Features (Hackathon Prototype)

The functional prototype demonstrates the following capabilities:

*   Parameter-Guided Content Generation: Initiates an automated pipeline (scraping, source analysis, AI text generation, image finding) for a specific topic, using parameters like length, tone, minimum source score, and number of sources, provided through the interface.
*   Source Research and Analysis: Finds URLs on the web (DuckDuckGo), fetches their content, analyzes it with AI (Google Gemini) assigning a relevance/quality score and extracting metadata (summary, tags). Stores the analyzed sources in an SQLite database.
*   Article Draft Generation: Uses the most relevant sources found for a topic and calls the AI (Google Gemini) to generate a complete SEO-optimized article draft (title, meta description, tags, Markdown body) based on length and tone parameters. Includes logic to handle AI responses with imperfect JSON format.
*   Image Finding and Association: Searches for relevant free images (configurable external sources like Unsplash) based on the article's title and tags, and associates the found images with the draft.
*   Data Persistence: Stores sources, generated articles, and associated image metadata in a local SQLite database.
*   Configuration Management per Topic: Allows loading (and conceptually saving) generation configuration parameters (like length, tone, score thresholds) associated with a specific topic/section in the database.
*   Backend API (FastAPI): An API server exposing endpoints to:
    *   Trigger the complete generation pipeline (POST /generate).
    *   Load the default or saved configuration for a topic (GET /config/{tema}).
    *   List generated articles (GET /articles).
    *   Get the full details of a generated article (including images) (GET /articles/{id}).
    *   Update a generated article (e.g., the Markdown body from the Canvas) (PUT /articles/{id}).
    *   Trigger the generation of improvement suggestions for an article (POST /articles/{id}/generate-suggestions).
    *   Trigger the regeneration of an article's content based on an instruction/suggestions (POST /articles/{id}/rewrite).
*   Web Interface (HTML/JS): A basic dashboard built with HTML and JavaScript that runs in the browser and communicates with the FastAPI API to:
    *   Allow entering the topic and generation parameters in a form.
    *   Trigger the generation process with a button click.
    *   Display a list of generated articles.
    *   Navigate to a review view (the "Canvas") when an article is selected.
*   Canvas (Review and Editing View): In the review view:
    *   Displays the article data (title, meta, image, body) loaded from the backend.
    *   Presents the article body in an editable text area (a basic textarea).
    *   Allows saving changes made in the Canvas by sending them to the backend (PUT /articles/{id}).
    *   Allows "Publishing" (simulated for now, triggers local HTML preview generation).
*   Copilot Suggestions (AI Analysis): On a button click, calls the AI (Google Gemini) via the backend to generate specific improvement suggestions for the article in the Canvas, based on its content and SEO elements.
*   Apply Suggestions (Assisted Rewriting): The suggestions are displayed in an interactive list. Users can select individual suggestions or apply all. Upon applying, the JavaScript sends the selected suggestion(s) (or a combination of all) along with the current Canvas text to a backend endpoint (POST /articles/{id}/rewrite). The backend calls the AI to regenerate the article body based on the instruction/suggestions and the current Canvas text (and original sources if available). The Canvas is updated with the rewritten text.

---

## How It Works (Implemented Flow)

*   The user opens the HTML interface in their browser.
*   In the generation section, they enter the Topic and adjust Parameters (e.g., length, tone).
*   They click "Start Generation".
*   The frontend sends this data to the backend API (POST /generate).
*   The backend executes the Pipeline:
    *   Loads the topic's configuration (if it exists).
    *   Calls the Scraper (scraper.py) with parameters.
    *   The Scraper finds sources, fetches content (web_tools.py), analyzes with AI (analyzer.py), saves source metadata to the DB (database.py). Returns the processed sources (metadata + content).
    *   Calls the Generator (content_generator.py) with the processed sources and parameters.
    *   The Generator builds the prompt and calls the AI (llm_client.py) to get the article draft (JSON).
    *   Calls Web Tools to find images (web_tools.py).
    *   Saves the generated article and image metadata to the DB (database.py).
    *   Marks used sources in the DB (database.py).
    *   Generates a local HTML preview (mock_publisher.py).
    *   The POST /generate endpoint returns the ID of the generated article.
*   The user navigates to the "Generated Articles" section (a list).
*   The frontend loads the list of articles from the API (GET /articles) and displays them.
*   The user clicks on an article from the list.
*   The frontend navigates to the Review section (Canvas), loads the article's details from the API (GET /articles/{id}), and populates the Canvas (textarea).
*   In the Review view:
    *   The user edits the text in the Canvas. They click "Save Changes" (PUT /articles/{id}).
    *   They click "Generate Suggestions". The frontend calls POST /articles/{id}/generate-suggestions. The backend calls copilot.generate_article_suggestions (AI), which returns plain text suggestions. The frontend displays the suggestions in a list.
    *   The user selects suggestions from the list.
    *   They click "Apply Selected Suggestions". The frontend takes the current Canvas text and the selected suggestion texts, and sends them as a combined instruction to POST /articles/{id}/rewrite.
    *   The backend calls copilot.regenerate_article_content (AI). The Copilot constructs a prompt based on the Canvas text, the instruction/suggestions, the article's context, and the original sources (retrieved from the DB). It calls content_generator.generate_seo_content (AI engine) to regenerate the body.
    *   The backend returns the regenerated body. The frontend replaces the Canvas content.
*   The user can save the rewritten changes or publish (simulated).

---

## Tech Stack

*   Backend: Python (FastAPI, Uvicorn, Pydantic, Requests, BeautifulSoup4, Selenium, WebDriver-Manager, Google-generativeai, Markdown, SQLite3, Starlette, Fastapi.middleware.cors, Anyio)
*   Frontend: HTML, CSS, JavaScript (Fetch API)
*   APIs/Services: Google Gemini API, Unsplash API, DuckDuckGo (Search/Scraping Source)
*   Database: SQLite

---

## Potential and Future Roadmap

The current prototype is a strong foundation for a much more powerful system:

*   Full Conversational Interface: Integrate a direct chat with the Copilot (AI) in the UI to control the entire workflow and get assistance in natural language.
*   Advanced Suggestion Application: Allowing application of suggestions or instructions to specific parts of the text (paragraphs, sections).
*   Comprehensive UI Editing: Rich text editor (WYSIWYG or advanced Markdown) in the Canvas, editing of title, meta description, and tags directly in the UI.
*   Full Image Management: Gallery of associated images, searching for more images from the UI, uploading own images, inserting images into text.
*   CMS Integration: Direct connection with APIs of platforms like WordPress, Shopify, etc., for automated article publishing.
*   Advanced SEO Analysis & Strategy: Integration with Google Analytics, identifying content gaps, keyword analysis, internal linking suggestions.
*   AI as Autonomous Agent: Operating modes where the AI can generate and publish content automatically for defined topics, under user-defined goals and configurable oversight.
*   Advanced Customization: Detailed configuration per blog/site, style/tone presets, editable prompt templates in the UI.
*   Scalability: Migration to a cloud database, implementation of task queues for long-running processes, deployment on cloud services (AWS, GCP, Azure, Render, etc.).
*   Support for Other Content Types: Generation for social media, emails, product descriptions.

---

## Getting Started

*   Clone this repository.
*   Create and activate a Python virtual environment.
*   Install the necessary dependencies (pip install fastapi uvicorn[standard] pydantic requests beautifulsoup4 google-generativeai markdown selenium webdriver-manager json5 anyio).
*   Obtain your Google Gemini and Unsplash API keys. Store them in a configuration file or environment variables as indicated in llm_client.py and web_tools.py.
*   Configure the path to your schema.sql file in database.py.
*   Start the FastAPI server from the back/ folder: uvicorn api:app --reload
*   Open the articles_canvas.html file directly in your browser (an incognito window is recommended to avoid caching and local file CORS issues).

---

## Contribution

Contributions are welcome. If you have ideas or want to help build any of the roadmap functionalities, feel free to reach out.

---

## About the Creator

[Your Name/Username]: A self-taught developer passionate about AI and automation.
