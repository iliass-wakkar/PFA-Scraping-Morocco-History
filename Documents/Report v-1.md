## Project Report: Automated Historical Data Processing and Knowledge Synthesis System

**Date:** May 25, 2025

**Prepared For:** [Recipient's Name/Organization, if applicable]

**Prepared By:** [Your Name/Team Name]

---

### 1. Executive Summary

This report details the development and implementation of an advanced, multi-stage data processing pipeline designed to acquire, filter, synthesize, and present historical information. The system leverages large language models (LLMs) for intelligent content analysis and article generation, culminating in a structured, searchable knowledge base accessible via a modern web application. The core objective is to transform disparate raw historical sources into coherent, well-cited articles, providing a robust foundation for historical research and interactive knowledge exploration.

### 2. Project Overview and Architecture

The project is structured as a robust, modular pipeline comprising three distinct processing phases (Stage 1, Stage 2, Stage 3) followed by a deployment phase. This phased approach ensures data integrity, facilitates debugging, and optimizes the utilization of LLM capabilities for specific tasks.

**Overall Pipeline Flow:**

1. **Data Acquisition (Phase 1 - Initial Scraping):** Collects raw historical texts and metadata.
2. **Data Filtering & Initial Summarization (Phase 2 - Stage 1):** Processes raw data for relevance and extracts key facts per source.
3. **Article Synthesis (Phase 2 - Stage 2):** Synthesizes relevant source information into a comprehensive article with simple citations.
4. **Final Article Structuring & Citation Linking (Phase 2 - Stage 3):** Transforms the synthesized article into a detailed, database-ready JSON format with precise paragraph-level source attribution.
5. **Deployment (Phase 3):** Ingests final JSONs into a MongoDB database, exposes data via a Flask backend API, and presents it through a React frontend.

### 3. Detailed Phase Breakdown

#### 3.1. Phase 1: Data Acquisition (Initial Scraping)

**Objective:** To systematically collect raw textual content from various online historical sources (e.g., academic journals, historical archives, digital libraries) and associate it with essential metadata.

**Process:**
This phase involves a dedicated scraping mechanism (presumably a Python script utilizing libraries like `requests` for HTTP and `BeautifulSoup` for HTML parsing, though not explicitly provided in our discussions).

* It navigates specified URLs or performs searches.
* Extracts the full textual content of articles, PDFs, or web pages.
* Captures crucial metadata such as the original URL, source type (e.g., `main_url`, `linked_pdf`), and potentially the original language section.
* Saves each scraped source as a structured entry, often within a larger JSON file grouped by the historical event it pertains to.

**Output Format:**
Raw JSON files, typically one per historical event, containing a list of source entries. Each source entry includes the `scraped_text` and `original_source_metadata` (e.g., `original_item_url`, `source_url`, `source_type`, `link_text`, `original_language_section`).

#### 3.2. Phase 2: Data Filtering & Initial Summarization (Stage 1)

**Objective:** To intelligently filter vast amounts of raw scraped data for direct relevance to a specific historical event and to extract concise summaries and key facts from each relevant source using LLMs.

**Process:**
This stage is managed by the `Phase1_Article_Summurise.py` script.

* **Input:** Raw JSON files from Phase 1.
* **LLM Interaction:** The script iterates through each source, constructs a detailed prompt for a Gemini LLM (e.g., `gemini-1.5-flash`, `gemini-2.0-flash`), and sends the source text for analysis.
* **Prompt Engineering:** The LLM prompt is meticulously designed to:
  * Instruct the LLM to act as an "expert historian and data analyst."
  * Clearly define the target historical event (`event_name`).
  * Demand a strict JSON output format based on relevance:
    * **Relevant Sources:** Requires `relevance_status: "relevant"`, a `source_summary` (comprehensive summary of historical content), and `extracted_key_facts` (specific historical data points like dates, people, events). The prompt emphasizes prioritizing comprehensive extraction over brevity.
    * **Irrelevant Sources:** Requires `relevance_status: "irrelevant"` and a `relevance_reason` (brief explanation of irrelevance).
* **Robust Error Handling & Key Management:** This script features advanced mechanisms to ensure continuous processing despite API challenges:
  * **API Key Pool:** Utilizes a configurable list of multiple API keys and models (`API_KEYS_MODELS`) to leverage different free tier quotas and increase processing throughput.
  * **Dynamic Key Rotation:** Automatically switches to the next available API key/model upon encountering rate limits (HTTP 429, `RESOURCE_EXHAUSTED` status) or invalid API keys (HTTP 400 specific).
  * **Intelligent Retries:** Implements retry logic for transient errors (e.g., API overload (HTTP 503), connection timeouts, JSON validation failures), attempting multiple times with the *same* key before rotating.
  * **Input Token Limit Handling:** Specifically detects `Input Token Limit Exceeded` errors (HTTP 400 with specific message) and marks the source as failed, without retrying or rotating, as this indicates a fundamental input size mismatch for the model.
  * **Progress State Saving:** Continuously saves processing progress (`stage1_progress.json`), including processed source UIDs and the current active API key index, enabling seamless resumption after interruptions (e.g., `KeyboardInterrupt`).
* **Text Truncation:** Dynamically truncates large input texts to fit within the LLM's context window, ensuring API calls are within limits.

**Output Format:**
JSON files (e.g., `[event_name].json`) saved in a `stage1_output` directory. Each file contains a list of processed source entries, including `source_uid`, `original_source_metadata`, `processing_metadata`, and the `llm_processed_output` (either relevant with summary/facts or irrelevant with reason).

#### 3.3. Phase 2: Article Synthesis (Stage 2)

**Objective:** To synthesize information from multiple relevant Stage 1 sources into a single, coherent historical article, incorporating simple citation markers for later detailed linking.

**Process:**
This stage is managed by the `Phase2_merge_Summarys.py` script.

* **Input:** Filters the Stage 1 output JSON files, collecting `source_summary` and `extracted_key_facts` only from sources marked as "relevant" for a given event.
* **Prompt Engineering:** The LLM prompt for this stage is designed to:
  * Instruct the LLM to act as an "expert historical author and synthesist."
  * Provide the `event_name` and a consolidated text block of all relevant source summaries and key facts, with each source numbered (e.g., `1`, `2`, `3`...).
  * Crucially, it instructs the LLM to generate the article text with **simple numerical citation markers** (e.g., `[1]`, `[2, 5]`) directly embedded in the text where information is drawn from a specific source.
  * The prompt specifically asks the LLM to return **only the article text** (formatted with Markdown headings for title and sections), without any surrounding JSON structure or source mapping, to avoid hitting LLM output token limits.
* **Script-Managed Source Mapping:** The script itself, not the LLM, maintains and outputs the mapping between the simple citation numbers used in the prompt and the actual source URLs (or UIDs) from Stage 1. This ensures reliability and avoids LLM output size constraints.
* **Robust Error Handling:** Similar to Stage 1, this script includes the intelligent retry and key rotation logic to handle API timeouts, rate limits, and other errors during the synthesis process.

**Output Format:**
JSON files (e.g., `[event_name]_stage2_output.json`) saved in a `stage2_output` directory. Each file contains:

* `event_name`: The name of the event.
* `article_title`: The title extracted from the LLM's raw text output.
* `article_text_raw`: The raw string output from the LLM (including Markdown headings and `[#]` markers).
* `source_references_ordered`: A list, generated by the script, containing the actual URLs (or UIDs) of the relevant sources in the exact order they were numbered and presented to the LLM.

#### 3.4. Phase 2: Final Article Structuring & Citation Linking (Stage 3)

**Objective:** To transform the raw synthesized article text into a highly structured JSON format, complete with unique paragraph IDs and precise paragraph-level source attribution, ready for database ingestion.

**Process:**
This stage is managed by the `Phase3_structure_article.py` script. This is primarily a  **scripting and data processing task** , not an LLM task.

* **Input:**
  * JSON files from the modified Stage 2 output.
  * The original Stage 1 output directory (to look up full source metadata).
* **Text Parsing & Structuring:**
  * The script reads the `article_text_raw` from Stage 2 output.
  * It parses the Markdown headings (`#` for main title, `##` for subtitles) to identify the article title and logically divide the text into sections.
  * Each section is further split into individual paragraphs (using newline delimiters).
  * Unique `paragraph_id`s (e.g., `s1_p1`, `s2_p3`) are assigned to each paragraph.
* **Citation Linking:**
  * For each paragraph, the script uses regular expressions to find all `[#]` citation markers.
  * For each number `n` extracted from a marker, it uses `n-1` as an index to retrieve the corresponding URL (or UID) from the `source_references_ordered` list (from Stage 2 output).
  * These retrieved URLs/UIDs are then added to the `source_uids` list for that specific paragraph.
* **Source List Compilation:**
  * The script gathers all unique URLs/UIDs that were cited anywhere in the article.
  * For each unique URL/UID, it performs a lookup in the **original Stage 1 output data** to retrieve the full `original_source_metadata` (including `source_url`, `original_item_url`, `source_type`, `original_language_section`, etc.).
  * This comprehensive metadata is then compiled into the `source_list` array in the final JSON.

**Output Format:**
A single, highly structured JSON file for each event (e.g., `[event_name]_stage3_final.json`), ready for database ingestion. This file contains:

* `event_name`
* `article_title`
* `sections`: An array of section objects, each with a `subtitle` and an array of `paragraphs`.
* `paragraphs`: Each paragraph object includes `paragraph_id`, `text` (plain text, markers removed), and `source_uids` (list of actual URLs/UIDs).
* `source_list`: A comprehensive array of all unique sources cited, each with its `source_uid`, `source_url`, and other original metadata.

### 4. Deployment and Application Layer

The meticulously processed and structured historical articles are designed for seamless integration into a modern web application, providing an interactive and searchable knowledge base.

#### 4.1. MongoDB Integration

**Purpose:** To provide robust, scalable, and flexible persistent storage for the final structured historical articles. MongoDB's document-oriented nature is ideally suited for the nested JSON structure of the Stage 3 output.

**Process:**

* A dedicated script (or an extension of the Stage 3 script) is responsible for ingesting the `_stage3_final.json` files into a MongoDB database.
* Each `_stage3_final.json` file typically maps to a single document within a designated MongoDB collection (e.g., `historical_articles`).
* The nested `sections`, `paragraphs`, and `source_list` arrays within the JSON are naturally stored as embedded documents and arrays in MongoDB, preserving the hierarchical structure.
* Indexing strategies are applied to fields like `event_name` and `article_title` to optimize search and retrieval performance.

#### 4.2. Flask Backend (API Layer)

**Purpose:** To serve as an intermediary API layer, exposing the historical article data from MongoDB to the frontend application and potentially handling advanced functionalities like interactive AI queries.

**Technology:** Developed using Python with the Flask micro-framework and `PyMongo` for MongoDB interaction.

**Functionality:**

* **Article Retrieval Endpoints:**
  * `GET /articles`: Retrieves a list of all available articles (e.g., by title and event name).
  * `GET /articles/<event_name>`: Fetches a specific article by its event name, returning the full structured JSON.
* **Search Functionality:** Endpoints to search articles based on keywords, potentially across `article_title`, `subtitle`, or `paragraph.text`.
* **Interactive AI Integration:** This is a key advanced feature.
  * When a user asks a question on an article page, the Flask backend can identify the most relevant paragraphs from that article.
  * These relevant paragraphs, along with the user's query, are then sent to a smaller, more efficient LLM (e.g., `gemini-2.0-flash-lite` or a fine-tuned model) via the Gemini API.
  * The LLM generates a concise answer based *only* on the provided article context.
  * The backend returns this LLM-generated answer to the frontend. This ensures answers are grounded in the processed historical data.

#### 4.3. React Frontend (User Interface)

**Purpose:** To provide a dynamic, responsive, and intuitive user interface for exploring the historical articles and interacting with the AI knowledge system.

**Technology:** Developed using React.js (JavaScript library) for building user interfaces, complemented by modern CSS frameworks like Tailwind CSS for aesthetic and responsive design.

**Functionality:**

* **Article Display:** Renders the structured JSON articles from the Flask API.
  * Presents the main `article_title` and `sections` with `subtitles`.
  * Displays each `paragraph.text`.
  * Crucially, it dynamically renders citations: When a paragraph is displayed, it identifies the `source_uids` associated with it. These UIDs are then used to look up the corresponding `source_url` from the `source_list` array, allowing users to click directly to the original source.
* **Navigation & Search:** Provides navigation to browse articles by event and a search bar to find specific content.
* **Interactive AI Chat:** Integrates a chat interface where users can ask questions about the currently viewed article.
  * Sends user queries to the Flask backend.
  * Displays the LLM-generated answers.
  * Potentially highlights the paragraphs that were used to generate the answer, further reinforcing source transparency.
* **Responsive Design:** Ensures optimal viewing and usability across various devices (desktops, tablets, mobile phones) and screen orientations, leveraging Tailwind CSS's responsive utilities.

### 5. Conclusion

This project successfully establishes a robust and intelligent pipeline for historical data processing. By meticulously breaking down the complex task into manageable stages, leveraging LLMs for intelligent content analysis and synthesis, and implementing comprehensive error handling, the system efficiently transforms raw, unstructured historical data into a highly organized and accessible knowledge base. The integration with MongoDB, Flask, and React provides a powerful platform for researchers, students, and enthusiasts to explore historical events with unprecedented detail and interactive capabilities, setting the foundation for future advancements in digital humanities and AI-powered knowledge retrieval.
