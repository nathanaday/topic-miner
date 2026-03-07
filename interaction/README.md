# Topic Map Visualization

Interactive web app for exploring and studying a topic map produced by the pipeline. Provides a D3 force-directed graph view, topic search, drill-down into subtopics, and mastery tracking.

## Prerequisites

- Python 3.10+
- Node.js 18+

## Backend

The backend is a FastAPI server that manages projects and serves topic map data.

```bash
cd interaction/backend
pip install -r requirements.txt
```

Start the dev server:

```bash
uvicorn main:app --reload
```

The API runs at `http://localhost:8000`. On first startup it creates an `interaction/app-files/` directory for storing project settings and topic map copies.

## Frontend

The frontend is a React + D3 app built with Vite.

```bash
cd interaction/frontend
npm install
npm run dev
```

The dev server runs at `http://localhost:5173` and proxies API requests to the backend.

## Setting Up a Project

Projects let you manage multiple topic maps and link them to their source course material.

1. **Start both servers** (backend and frontend) as described above.
2. On first launch (no projects exist yet) you will see a setup dialog automatically.
3. Fill in the fields:
   - **Project Name** -- a label for this project (e.g. "EE450 Week 1-8").
   - **Topic Map File** -- drag-and-drop or browse for the `topic_map.json` produced by the pipeline. A copy is stored in `app-files/` so the original is never modified.
   - **Source Material Path** (optional) -- the absolute path to the root of the course content repository. The app expects this directory to contain the subdirectories `discussion`, `exam`, `homework`, `lecture`, `student`, and `textbook`. This path is saved for future prompt-generation features and is not read at this time.
4. Click **Create Project**. The graph loads immediately.

## Managing Projects

Open the sidebar using the grid icon in the top-left corner. From there you can:

- **Switch** between projects by clicking a project card.
- **Edit** a project's name or source material path with the pencil icon.
- **Export / Backup** the current topic map (including any mastery progress) with the download icon.
- **Delete** a project with the trash icon (click twice to confirm).
- **Create** a new project with the "+ New Project" button at the bottom of the sidebar.

If all projects are deleted you will be returned to the first-time setup dialog.
