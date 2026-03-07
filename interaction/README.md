# Topic Map Visualization

Interactive web app for exploring and studying a topic map produced by the pipeline. Provides a D3 force-directed graph view, topic search, drill-down into subtopics, and mastery tracking.

## Prerequisites

- Python 3.10+
- Node.js 18+

## Backend

The backend is a FastAPI server that reads and serves the `topic_map.json` file.

```bash
cd interaction/backend
pip install -r requirements.txt   # fastapi, uvicorn, python-dotenv
```

Create a `.env` file (see `.env.example`):

```
TOPIC_MAP_PATH="/path/to/your/topic_map.json"
```

Start the dev server:

```bash
uvicorn main:app --reload
```

The API runs at `http://localhost:8000`.

## Frontend

The frontend is a React + D3 app built with Vite.

```bash
cd interaction/frontend
npm install
npm run dev
```

The dev server runs at `http://localhost:5173` and proxies API requests to the backend.
