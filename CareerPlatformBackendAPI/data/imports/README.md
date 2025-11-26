# JSON Seeding Data

This folder contains example JSON files used to seed the database when `SEED_FROM_JSON=1` is set in the environment (see `.env.example`).

Files:
- `roles.json`: list of roles. Supported fields: `name`, `description`.
- `competencies.json`: list of competencies. Supported fields: `name`, `definition`, `category`.
- `role_competencies.json`: mapping of role requirements. Flexible fields supported:
  - role reference: `role_id` | `roleId` | `role` | `role_name`
  - competency reference: `competency_id` | `competencyId` | `competency` | `competency_name`
  - required level: `required_level` | `level` | `requiredLevel` (defaults to 3)

Notes:
- Role and competency can be referenced by ID or by name.
- Seeding is idempotent: existing rows are updated (upsert-like behavior) where appropriate.
- All files are optional; only present data is applied.

To use:
1. Copy `.env.example` to `.env` and ensure `SEED_FROM_JSON=1` and `INGESTION_JSON_DIR=data/imports`.
2. Start the server. On first run the data will be applied after tables are created.
