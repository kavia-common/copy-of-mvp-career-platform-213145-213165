# Role Mapping Service (Node/Express)

This service provides role listing, competency mapping by role, and role adjacency computation based on JSON data files. It serves as a lightweight, stateless service to power UI interactions such as suggesting adjacent roles and inspecting competency overlaps.

- Default port: `4000`
- Default JSON data directory: `data/imports` (relative to the backend project root)
- CORS: enabled for all origins (configure at deploy time as needed)
- Health: `GET /health`

## Endpoints

- `GET /health`
  - Returns `{ "status": "ok" }` when the service is healthy.

- `GET /api/v1/roles`
  - Returns the list of roles from `roles.json`.
  - Response: `[ { "name": "...", "description": "..." }, ... ]`

- `GET /api/v1/competency-map?role=...`
  - Returns a normalized map of required competencies for the specified role.
  - Query params:
    - `role` (required): case-insensitive role name.
  - Response:
    ```
    {
      "role": "Chief Architect",
      "competencies": [
        { "name": "Technical Architecture", "required_level": 5 },
        { "name": "Strategic Thinking", "required_level": 4 }
      ],
      "map": { "Technical Architecture": 5, "Strategic Thinking": 4 }
    }
    ```

- `GET /api/v1/adjacent-roles?role=...&limit=10&minScore=0`
  - Returns suggested adjacent roles with a similarity score using a weighted Jaccard metric over required competency levels.
  - Query params:
    - `role` (required): case-insensitive role name.
    - `limit` (optional, default 10): maximum results.
    - `minScore` (optional, default 0): threshold to filter results.
  - Response:
    ```
    {
      "role": "Chief Architect",
      "total": 3,
      "items": [
        { "role": "CTO", "score": 0.78, "sharedCompetencies": 4, "missingInCurrent": 0, "extraInCurrent": 0 },
        { "role": "VP Engineering", "score": 0.65, "sharedCompetencies": 4, "missingInCurrent": 0, "extraInCurrent": 0 }
      ]
    }
    ```

- `GET /api/v1/mappings/adjacency?currentRole=...&targetRole=...`
  - Returns detailed adjacency between two roles: score, shared competencies, and level deltas.
  - Query params:
    - `currentRole` (required)
    - `targetRole` (required)
  - Response:
    ```
    {
      "currentRole": "Chief Architect",
      "targetRole": "CTO",
      "score": 0.78,
      "shared": [
        { "competency": "Strategic Thinking", "current_level": 4, "target_level": 5, "delta": 1 },
        { "competency": "Team Leadership", "current_level": 4, "target_level": 5, "delta": 1 }
      ],
      "missingInCurrent": [{ "competency": "Stakeholder Management", "target_level": 5 }],
      "extraInCurrent": [],
      "stats": { "sharedCompetencies": 3, "missingInCurrent": 1, "extraInCurrent": 0 }
    }
    ```

Notes:
- If a file `role_adjacency.json` exists in `JSON_DIR`, it will be used to override or supplement similarity scoring. Otherwise, scores are computed from competency mappings using a weighted Jaccard similarity:
  ```
  score = sum_over_union(min(levelA, levelB)) / sum_over_union(max(levelA, levelB))
  ```

## Data Files

By default, the service expects the following JSON files under the configured `JSON_DIR`:

- `roles.json`: array of roles, e.g.
  ```
  [{ "name": "Chief Architect", "description": "..." }, ...]
  ```
- `role_competencies.json`: array of mappings:
  ```
  [{ "role": "Chief Architect", "competency": "Technical Architecture", "required_level": 5 }, ...]
  ```
- `competencies.json`: optional; improves metadata in responses.

Optional:
- `role_adjacency.json`:
  ```
  [{ "currentRole": "Chief Architect", "targetRole": "CTO", "score": 0.85 }, ...]
  ```

## Configuration

Create a `.env` file or set environment variables:
- `PORT` (default `4000`)
- `JSON_DIR` (default `data/imports`)
- `LOG_VERBOSE` (default `false`)

The loader resolves `JSON_DIR` robustly:
- It tries the provided `JSON_DIR` (absolute or relative to `process.cwd()`).
- Falls back to `process.cwd()/data/imports`.
- Falls back to `<service>/../../data/imports` (the backend's default sample path).

## Run

From this directory:

```
npm install
npm start
```

- Server on `http://localhost:4000`

Example:

```
curl -s 'http://localhost:4000/api/v1/adjacent-roles?role=Chief%20Architect'
```

## Minimal Tests

This project uses Node's built-in test runner (Node >= 18):

```
npm test
```

Tests include:
- Adjacency score math
- Loader reading sample JSON from the backend repo's `data/imports`

## CORS

CORS is enabled for all origins by default. For production, restrict `origin` in `src/server.js`.

## Traceability and Matrices

If you have source spreadsheets (e.g., role adjacency or competency matrices), convert or export them into JSON files under `JSON_DIR` following the example structures to ensure the service produces consistent, traceable results.
