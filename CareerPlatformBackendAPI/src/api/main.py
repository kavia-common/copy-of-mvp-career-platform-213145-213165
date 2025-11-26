from typing import Generator, List
import os

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.orm import Session

from src.db.database import Base, SessionLocal, engine
from src.models.template import Template
from src.schemas.template import TemplateCreate, TemplateOut, TemplateUpdate

# New imports for Roles
from src.models.role import Role
from src.schemas.role import RoleCreate, RoleRead

# Tags metadata for OpenAPI documentation
tags_metadata = [
    {"name": "Health", "description": "Service health and readiness checks."},
    {
        "name": "Templates",
        "description": "CRUD operations for templates (backed by SQLite via SQLAlchemy).",
    },
    {
        "name": "Roles",
        "description": "CRUD operations for roles (backed by SQLite via SQLAlchemy).",
    },
]

# Configure FastAPI app with metadata and tags
app = FastAPI(
    title="Career Platform Backend API",
    description=(
        "Backend API for the MVP Career Platform. "
        "This instance uses SQLite (via SQLAlchemy) by default for local development and tests."
    ),
    version="0.2.0",
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

    This ensures a clean developer experience without manual migration steps
    while using SQLite in local development and test environments.

    Seeding:
        If the environment variable SEED_SAMPLE_DATA is set to a truthy value
        (e.g., "1", "true", "yes"), and the roles table is empty, a small set
        of sample roles will be inserted.
    """
    # Create all tables for known models
    Base.metadata.create_all(bind=engine)

    # Optional sample data seeding for Roles
    seed_flag = os.getenv("SEED_SAMPLE_DATA", "").strip().lower()
    should_seed = seed_flag in {"1", "true", "yes", "y"}

    if should_seed:
        db = SessionLocal()
        try:
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
def get_db() -> Generator[Session, None, None]:
    """Dependency that provides a transactional SQLAlchemy Session.

    Yields:
        Session: A SQLAlchemy session bound to the configured engine.

    Ensures the session is properly closed after request handling.
    """
    db = SessionLocal()
    try:
        yield db
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
    """List all templates.

    Args:
        db (Session): Database session dependency.

    Returns:
        List[TemplateOut]: All template records.
    """
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
    """Retrieve a template by its ID.

    Args:
        template_id (int): Unique ID of the template.
        db (Session): Database session dependency.

    Returns:
        TemplateOut: The requested template.

    Raises:
        HTTPException: 404 if the template does not exist.
    """
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
    """Update fields on an existing template.

    Args:
        template_id (int): Unique ID of the template to update.
        payload (TemplateUpdate): Fields to update.
        db (Session): Database session dependency.

    Returns:
        TemplateOut: The updated template.

    Raises:
        HTTPException: 404 if the template does not exist.
    """
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
    """Delete a template by its ID.

    Args:
        template_id (int): Unique ID of the template to delete.
        db (Session): Database session dependency.

    Raises:
        HTTPException: 404 if the template does not exist.
    """
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
    """List all roles.

    Args:
        db (Session): Database session dependency.

    Returns:
        List[RoleRead]: All role records.
    """
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
    """Create a new role.

    Args:
        payload (RoleCreate): The role data to create.
        db (Session): Database session dependency.

    Returns:
        RoleRead: The created role record.

    Raises:
        HTTPException: 409 if a role with the same name already exists.
    """
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
    """Retrieve a role by its ID.

    Args:
        role_id (int): Unique ID of the role.
        db (Session): Database session dependency.

    Returns:
        RoleRead: The requested role.

    Raises:
        HTTPException: 404 if the role does not exist.
    """
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return RoleRead.model_validate(role)
