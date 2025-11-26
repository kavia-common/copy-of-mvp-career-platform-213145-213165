from typing import List
import os

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from src.api.deps import get_db
from src.db.database import Base, SessionLocal, engine
# Import model modules to ensure they are registered with SQLAlchemy's Base metadata
from src.models import user as _models_user  # noqa: F401
from src.models import role as _models_role  # noqa: F401
from src.models import template as _models_template  # noqa: F401
from src.models import competency as _models_competency  # noqa: F401
from src.models import role_competency as _models_role_competency  # noqa: F401
from src.models import assessment as _models_assessment  # noqa: F401
from src.models import development_plan as _models_development_plan  # noqa: F401
from src.models import audit as _models_audit  # noqa: F401
from src.models import traceability as _models_traceability  # noqa: F401
from src.models.role import Role
from src.models.template import Template
from src.schemas.role import RoleCreate, RoleRead
from src.schemas.template import TemplateCreate, TemplateOut, TemplateUpdate
from src.seeders.json_seed import seed_from_json_if_enabled

# Tags metadata for OpenAPI documentation
tags_metadata = [
    {"name": "Health", "description": "Service health and readiness checks."},
    {"name": "Auth", "description": "User authentication, profile, and session endpoints."},
    {"name": "Competencies", "description": "Competency catalog and role requirements."},
    {"name": "Assessments", "description": "User competency assessments."},
    {"name": "Gap Analysis", "description": "Compute competency gaps for a target role."},
    {"name": "Development Plans", "description": "Generate and export development plans."},
    {"name": "Admin", "description": "Administrative endpoints (templates, audit logs)."},
    {"name": "Templates", "description": "CRUD operations for templates (demo)."},
    {"name": "Roles", "description": "CRUD operations for roles (SQLite via SQLAlchemy)."},
]

# Configure FastAPI app with metadata and tags
app = FastAPI(
    title="Career Platform Backend API",
    description=(
        "Backend API for the MVP Career Platform. "
        "This instance uses SQLite (via SQLAlchemy) by default for local development and tests."
    ),
    version="0.3.0",
    openapi_tags=tags_metadata,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, set to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    """Create database tables and optionally seed data at application startup.

    Flow:
    1. Create all tables for known models.
    2. If SEED_FROM_JSON=1, upsert roles/competencies/mappings from JSON files.
    3. Else if SEED_SAMPLE_DATA=1 AND roles empty, seed a few roles as demo.
    """
    # Create tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Seed from JSON if enabled
        seed_from_json_if_enabled(db)

        # Optional sample data seeding for Roles (fallback/demo)
        seed_flag = os.getenv("SEED_SAMPLE_DATA", "").strip().lower()
        should_seed = seed_flag in {"1", "true", "yes", "y"}
        if should_seed:
            count = db.query(Role).count()
            if count == 0:
                samples = [
                    Role(
                        name="Chief Architect",
                        description="Leads architecture strategy across the organization.",
                    ),
                    Role(
                        name="CTO",
                        description="Executive responsible for overall technology strategy and execution.",
                    ),
                    Role(
                        name="VP Engineering",
                        description="Leads engineering teams and delivery of product initiatives.",
                    ),
                    Role(
                        name="Enterprise Architect",
                        description="Designs and governs enterprise-level systems and integrations.",
                    ),
                ]
                db.add_all(samples)
                db.commit()
    finally:
        db.close()


# PUBLIC_INTERFACE
@app.get(
    "/",
    summary="Health Check",
    tags=["Health"],
    responses={200: {"description": "Service is healthy"}},
)
def health_check() -> dict:
    """Health check endpoint.

    Returns:
        dict: A simple message indicating the API is healthy.
    """
    return {"message": "Healthy"}


# ---------------------------
# Templates CRUD (SQLite demo)
# ---------------------------

# PUBLIC_INTERFACE
@app.post(
    "/templates",
    response_model=TemplateOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create template",
    tags=["Templates"],
    responses={
        201: {"description": "Template created successfully"},
        400: {"description": "Invalid input"},
    },
)
def create_template(payload: TemplateCreate, db: Session = Depends(get_db)) -> TemplateOut:
    """Create a new template.

    Args:
        payload (TemplateCreate): The template data to create.
        db (Session): Database session dependency.

    Returns:
        TemplateOut: The created template record.
    """
    template = Template(name=payload.name, content=payload.content)
    db.add(template)
    db.commit()
    db.refresh(template)
    return TemplateOut.model_validate(template)


# PUBLIC_INTERFACE
@app.get(
    "/templates",
    response_model=List[TemplateOut],
    summary="List templates",
    tags=["Templates"],
    responses={200: {"description": "List of templates"}},
)
def list_templates(db: Session = Depends(get_db)) -> List[TemplateOut]:
    """List all templates."""
    templates = db.query(Template).order_by(Template.id.desc()).all()
    return [TemplateOut.model_validate(t) for t in templates]


# PUBLIC_INTERFACE
@app.get(
    "/templates/{template_id}",
    response_model=TemplateOut,
    summary="Get template",
    tags=["Templates"],
    responses={
        200: {"description": "Template found"},
        404: {"description": "Template not found"},
    },
)
def get_template(template_id: int, db: Session = Depends(get_db)) -> TemplateOut:
    """Retrieve a template by its ID."""
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return TemplateOut.model_validate(template)


# PUBLIC_INTERFACE
@app.put(
    "/templates/{template_id}",
    response_model=TemplateOut,
    summary="Update template",
    tags=["Templates"],
    responses={
        200: {"description": "Template updated"},
        404: {"description": "Template not found"},
    },
)
def update_template(
    template_id: int, payload: TemplateUpdate, db: Session = Depends(get_db)
) -> TemplateOut:
    """Update fields on an existing template."""
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    if payload.name is not None:
        template.name = payload.name
    if payload.content is not None:
        template.content = payload.content

    db.add(template)
    db.commit()
    db.refresh(template)
    return TemplateOut.model_validate(template)


# PUBLIC_INTERFACE
@app.delete(
    "/templates/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete template",
    tags=["Templates"],
    responses={
        204: {"description": "Template deleted"},
        404: {"description": "Template not found"},
    },
)
def delete_template(template_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a template by its ID."""
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    db.delete(template)
    db.commit()
    return None


# ---------------------------
# Roles CRUD (SQLite-backed)
# ---------------------------

# PUBLIC_INTERFACE
@app.get(
    "/api/v1/roles",
    response_model=List[RoleRead],
    summary="List roles",
    description="List all roles currently stored in the database.",
    tags=["Roles"],
    responses={200: {"description": "List of roles"}},
)
def list_roles(db: Session = Depends(get_db)) -> List[RoleRead]:
    """List all roles."""
    roles = db.query(Role).order_by(Role.id.asc()).all()
    return [RoleRead.model_validate(r) for r in roles]


# PUBLIC_INTERFACE
@app.post(
    "/api/v1/roles",
    response_model=RoleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create role",
    description="Create a new role. Role names must be unique.",
    tags=["Roles"],
    responses={
        201: {"description": "Role created successfully"},
        400: {"description": "Invalid input"},
        409: {"description": "Role already exists"},
    },
)
def create_role(payload: RoleCreate, db: Session = Depends(get_db)) -> RoleRead:
    """Create a new role."""
    existing = db.query(Role).filter(Role.name == payload.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Role name already exists"
        )

    role = Role(name=payload.name, description=payload.description)
    db.add(role)
    db.commit()
    db.refresh(role)
    return RoleRead.model_validate(role)


# PUBLIC_INTERFACE
@app.get(
    "/api/v1/roles/{role_id}",
    response_model=RoleRead,
    summary="Get role by ID",
    description="Retrieve a role by its numeric ID.",
    tags=["Roles"],
    responses={
        200: {"description": "Role found"},
        404: {"description": "Role not found"},
    },
)
def get_role(role_id: int, db: Session = Depends(get_db)) -> RoleRead:
    """Retrieve a role by its ID."""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return RoleRead.model_validate(role)


# Include sub-routers for versioned API
from src.api.routers.auth import router as auth_router  # noqa: E402
from src.api.routers.competencies import router as competencies_router  # noqa: E402
from src.api.routers.assessment import router as assessment_router  # noqa: E402
from src.api.routers.gap_analysis import router as gap_router  # noqa: E402
from src.api.routers.development_plan import router as plan_router  # noqa: E402
from src.api.routers.admin import router as admin_router  # noqa: E402

app.include_router(auth_router)
app.include_router(competencies_router)
app.include_router(assessment_router)
app.include_router(gap_router)
app.include_router(plan_router)
app.include_router(admin_router)
