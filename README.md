
# Global News Sentiment Data Pipeline

An asynchronous Data Engineering pipeline that automatically scrapes global RSS news feeds, extracts mentioned countries using NLP (SpaCy), and analyzes news tone using a local LLM via an OpenAI-compatible API.

---

## What it Does & Why it's Useful

This project is a complete automated pipeline designed to convert messy text from news feeds into structured analytical data:

1. **Ingest:** Asynchronously fetches and parses global news feeds (like BBC World) without blocking the application.
2. **Filter:** Uses SpaCy
3. to find countries mentioned in the text and automatically filters out articles with no geographical data.
4. **Analyze (LLM Scoring):** Groups articles into batches and asks a Language Model to score the news tone for each country on a scale from -1.0 (very negative) to +1.0 (very positive).
5. **Store:** Saves everything into a PostgreSQL database using an async database manager.

Instead of paying for expensive cloud APIs, this project shows how to build a reliable analytics pipeline that runs completely locally using open-source LLMs.

---

##  Tech Stack

* **Language:** Python 3.12 (Async architecture via `asyncio` and `httpx`)
* **Database:** PostgreSQL + SQLAlchemy 2.0 (Async mode via `asyncpg`)
* **NLP:** SpaCy (Targeted country extraction)
* **LLM API:** OpenAI-compatible client integration
* **Resilience:** `Pydantic Settings` for configuration and `Tenacity` for automatic API retries with exponential backoff.

---

##  Performance Benchmarks & Core Metrics

### Real Pipeline Metrics from Logs

* **Scraping & Database Ingestion:** ~1.5 seconds to fetch, parse, and write 54 raw articles into PostgreSQL.
* **LLM Inference Speed:** ~8.68 seconds average processing time per news item. *Note: This includes full text analysis and multi-entity score generation per batch on local hardware.*
* **Data Integrity:** Built-in `ON CONFLICT DO NOTHING` handling ensures that the pipeline is completely idempotent. It won't duplicate rows or waste LLM tokens if you run it multiple times on the same data.

> ** How to make it faster:** While the current setup uses batching to process 3 articles at once sequentially (to avoid overloading the local GPU memory), the pipeline architecture is fully asynchronous. By shifting from a local model to high-throughput cloud APIs (like Groq, Together AI, or OpenAI), you can process multiple batches concurrently via `asyncio.gather`. This will scale the throughput heavily and cut down the per-article processing time to fractions of a second.

##  How to Run Locally

### 1. LLM Server Setup

Make sure you have an operational OpenAI-compatible API endpoint. This can be:

* A local server like **LM Studio**, **vLLM**, or **Ollama** running on your machine.
* A cloud API key (Groq, OpenAI, Mistral, etc.).

### 2. Environment Configuration

Create a `.env` file in the root directory:

```env
POSTGRES_URL=postgresql+asyncpg://postgres:your_password@localhost:5432/postgres
AI_URL=http://localhost:1234/v1 # Change to your LLM provider URL
API_KEY=your_api_token_here 
BATCH_SIZE=3 #or 1 if multithreading is not supported
NEWS_URLS=RSS_URL1,RSS_URL2,RSS_URL3 #etc
ENABLE_SCHEDULER=True #If you want the script to run on a schedule
INTERVAL_MINUTES=30
```


### 3. Execution via Docker Compose (Recommended)

You don't need to manually configure the database or Python environments. Docker Compose handles everything, linking the script and PostgreSQL into a single network:

```bash
docker compose up --build -d
```

* `-d` runs the entire setup in detached (background) mode.

> 💡 **Note on Scheduler:** If `ENABLE_SCHEDULER=True`, the pipeline container will stay alive permanently. It wakes up every `X` minutes (defined in `.env`) to process new articles, logs the results, and safely goes back to sleep without resource drainage.

---

### 4. Direct Host Execution (Manual Debugging)

If you want to run the project outside Docker for quick testing, follow these steps:

1. **Create a virtual environment:**

   ```bash
   python -m venv .venv
   ```
2. **Activate the virtual environment:**

   * **Linux / macOS:**
     ```bash
     source .venv/bin/activate
     ```
   * **Windows:**
     ```cmd
     .venv\Scripts\activate
     ```
3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```
4. **Run the application:**

   ```bash
   python main.py
   ```
