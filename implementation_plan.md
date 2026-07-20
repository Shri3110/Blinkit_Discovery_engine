# Phase-Wise Implementation Plan (Updated Tech Stack)

This plan outlines the sequential phases to build the AI-Powered Product Discovery Engine using a modern, lightweight Python stack: **Streamlit, ChromaDB, PostgreSQL, and OpenAI/Groq**.

## Phase 1: Foundation & Data Ingestion
**Goal:** Establish database infrastructure and build data collection pipelines.

*   **1.1 Infrastructure Setup:**
    *   Provision PostgreSQL database (via Render or Railway).
*   **1.2 API Connectors Development:**
    *   Build custom Python connectors for Google Play Store, Apple App Store, and Reddit APIs.
*   **1.3 Orchestration:**
    *   Configure simple CRON jobs or lightweight Apache Airflow to fetch incremental data.

## Phase 2: Data Processing & NLP Pipeline
**Goal:** Cleanse, normalize, and store the raw data for AI analysis.

*   **2.1 Text Cleaning Engine:**
    *   Develop a Python service (using spaCy/NLTK) to clean and normalize text.
*   **2.2 Processed Storage:**
    *   Define PostgreSQL schema for storing metadata and clean text.
*   **2.3 Vector Database Setup:**
    *   Initialize and configure ChromaDB (which integrates natively in Python) for semantic search.

## Phase 3: AI & Analytics Engine
**Goal:** Implement the intelligence layer using OpenAI or Groq.

*   **3.1 Embedding Pipeline:**
    *   Integrate OpenAI/Groq to generate vectors for processed text and push them to ChromaDB.
*   **3.2 Topic & Segmentation Engine:**
    *   Develop LLM prompts to extract user segments (e.g., "Family", "Pet Owner") based on text context.
*   **3.3 RAG & Insight Generation:**
    *   Build the RAG pipeline to query ChromaDB for themes and synthesize actionable insights using OpenAI/Groq.

## Phase 4: Presentation & Dashboard UI
**Goal:** Deliver insights to Product Managers through a pure Python frontend.

*   **4.1 Dashboard Frontend:**
    *   Build a Streamlit application (eliminating the need for a separate Node/FastAPI backend).
*   **4.2 Trend Visualizations:**
    *   Implement charts showing sentiment and category exploration trends.
    *   Implement the "Cross-Category Heatmap" matrix.
*   **4.3 Evidence Viewer:**
    *   Build a drill-down UI component linking insights to anonymized raw quotes in PostgreSQL.

## Phase 5: Verification, Refinement & Deployment
**Goal:** Launch the application and optimize model usage.

*   **5.1 Deployment:**
    *   Deploy the application on Streamlit Cloud, Render, or Railway.
*   **5.2 Performance & Cost Optimization:**
    *   Configure logic to toggle between OpenAI (for high reasoning) and Groq (for fast/cheap inference) depending on the task.
*   **5.3 UAT & Handoff:**
    *   Beta testing with the Blinkit Product Management team.
