"""Admin routes: manage templates and view audit logs."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.api.deps import get_db, require_admin
from src.models.audit import AuditLog
from src.models.template import Template
from src.schemas.audit import AuditLogRead
from src.schemas.template import TemplateCreate, TemplateOut

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


# PUBLIC_INTERFACE
@router.get(
    "/templates",
    response_model=List[TemplateOut],
    summary="List plan templates",
    description="List all plan templates (admin only).",
)
def admin_list_templates(_: object = Depends(require_admin), db: Session = Depends(get_db)) -> List[TemplateOut]:
    """List templates for admin."""
    items = db.query(Template).order_by(Template.id.desc()).all()
    return [TemplateOut.model_validate(t) for t in items]


# PUBLIC_INTERFACE
@router.post(
    "/templates",
    response_model=TemplateOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create plan template",
    description="Create a new plan template (admin only).",
)
def admin_create_template(
    payload: TemplateCreate,
    _: object = Depends(require_admin),
    db: Session = Depends(get_db),
) -> TemplateOut:
    """Create a template for admins."""
    record = Template(name=payload.name, content=payload.content)
    db.add(record)
    db.flush()
    db.add(AuditLog(action="template_create", entity_type="Template", entity_id=str(record.id)))
    db.commit()
    db.refresh(record)
    return TemplateOut.model_validate(record)


# PUBLIC_INTERFACE
@router.get(
    "/audit-logs",
    response_model=List[AuditLogRead],
    summary="View audit logs",
    description="Retrieve audit logs (admin only).",
)
def admin_list_audit_logs(_: object = Depends(require_admin), db: Session = Depends(get_db)) -> List[AuditLogRead]:
    """Return audit log entries."""
    logs = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(500).all()
    return [AuditLogRead.model_validate(x) for x in logs]
