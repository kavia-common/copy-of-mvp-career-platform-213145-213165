from typing import Generator, List

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.orm import Session

from src.db.database import Base, SessionLocal, engine
from src.models.template import Template
from src.schemas.template import TemplateCreate, TemplateOut, TemplateUpdate

# Tags metadata for OpenAPI documentation
tags_metadata = [
    {"name": "Health", "description": "Service health and readiness checks."},
    {
        "name": "Templates",
        "description": "CRUD operations for templates (backed by SQLite via SQLAlchemy).",
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
    """Create database tables at application startup.

    This ensures a clean developer experience without manual migration steps
    while using SQLite in local development and test environments.
    """
    Base.metadata.create_all(bind=engine)


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
