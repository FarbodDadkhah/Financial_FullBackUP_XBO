# Customer Service Support System

A multi-agent customer service support system for bank representatives, using a 3-agent pipeline (Reformulation, Search, Validation) backed by a RAG knowledge base.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set your Anthropic API key:
   ```bash
   export ANTHROPIC_API_KEY=your-key-here
   ```

3. Run the application:
   ```bash
   python run.py
   ```

4. Open in your browser:
   - **Rep View**: http://localhost:8000/rep
   - **Manager Dashboard**: http://localhost:8000/dashboard

## Architecture

### 3-Agent Pipeline

1. **Reformulation Agent** - Takes raw customer questions and reformulates them into optimized search queries, detecting the primary intent
2. **Search Agent** - Queries the ChromaDB vector database for relevant knowledge base chunks, then synthesizes an answer using Claude
3. **Validation Agent** - Evaluates the answer quality and assigns a confidence score (0-100)

### Tech Stack

- **Backend**: Python + FastAPI
- **RAG / Vector DB**: ChromaDB (embedded)
- **LLM**: Anthropic Claude (claude-sonnet-4-20250514)
- **Stats DB**: SQLite
- **Frontend**: Jinja2 templates + vanilla JS

### Knowledge Base

8 markdown documents covering banking topics: account opening, loans, fees, credit cards, branch info, troubleshooting, wire transfers, and fraud/disputes.
