"""Seed database from JSON files if enabled via environment variables.

Environment variables:
- SEED_FROM_JSON: When truthy, enable seeding during startup.
- INGESTION_JSON_DIR: Directory with roles.json, competencies.json, role_competencies.json.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, Iterable, Optional, Tuple

from sqlalchemy.orm import Session

from src.core.config import get_settings
from src.models.competency import Competency
from src.models.role import Role
from src.models.role_competency import RoleCompetency

logger = logging.getLogger(__name__)


def _read_json(path: str) -> Optional[Any]:
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except Exception as exc:  # defensive: malformed JSON or I/O errors
        logger.warning("Failed to read JSON from %s: %s", path, exc)
        return None


def _normalize_bool(val: Any) -> bool:
    return str(val).strip().lower() in {"1", "true", "yes", "y"}


def _resolve_ingestion_dir(dir_setting: str) -> str:
    """
    Resolve the ingestion directory robustly:
    - Expand '~'
    - If relative, resolve against CWD
    - If not found, also try resolving relative to project root (two levels above this file)
    """
    candidate = os.path.expanduser(dir_setting)
    if not os.path.isabs(candidate):
        candidate_abs = os.path.abspath(candidate)
    else:
        candidate_abs = candidate

    if os.path.exists(candidate_abs):
        return candidate_abs

    # Fallback: relative to project root (assuming this file lives under src/seeders/)
    module_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    fallback = os.path.abspath(os.path.join(module_root, dir_setting))
    if os.path.exists(fallback):
        return fallback

    # Return the absolute candidate anyway (readers will gracefully no-op on missing files)
    return candidate_abs


def upsert_roles(db: Session, items: Iterable[Dict[str, Any]]) -> int:
    """Upsert roles by name."""
    count = 0
    for item in items:
        name = item.get("name") or item.get("role") or item.get("title")
        if not name:
            continue
        description = item.get("description") or item.get("desc")
        existing = db.query(Role).filter(Role.name == name).first()
        if existing:
            if description and existing.description != description:
                existing.description = description
                db.add(existing)
        else:
            db.add(Role(name=name, description=description))
        count += 1
    return count


def upsert_competencies(db: Session, items: Iterable[Dict[str, Any]]) -> int:
    """Upsert competencies by name."""
    count = 0
    for item in items:
        name = item.get("name") or item.get("competency")
        if not name:
            continue
        definition = item.get("definition") or item.get("description")
        category = item.get("category")
        existing = db.query(Competency).filter(Competency.name == name).first()
        if existing:
            changed = False
            if definition and existing.definition != definition:
                existing.definition = definition
                changed = True
            if category and existing.category != category:
                existing.category = category
                changed = True
            if changed:
                db.add(existing)
        else:
            db.add(Competency(name=name, definition=definition, category=category))
        count += 1
    return count


def _resolve_role_and_competency_ids(db: Session, role_ref: Any, comp_ref: Any) -> Tuple[Optional[int], Optional[int]]:
    role_id = None
    comp_id = None
    if isinstance(role_ref, int):
        role_id = role_ref
    else:
        role_name = str(role_ref)
        role = db.query(Role).filter(Role.name == role_name).first()
        role_id = role.id if role else None

    if isinstance(comp_ref, int):
        comp_id = comp_ref
    else:
        comp_name = str(comp_ref)
        comp = db.query(Competency).filter(Competency.name == comp_name).first()
        comp_id = comp.id if comp else None

    return role_id, comp_id


def upsert_role_competencies(db: Session, items: Iterable[Dict[str, Any]]) -> int:
    """Upsert role-competency mappings by role+competency keys."""
    count = 0
    for item in items:
        # Flexible field names
        role_ref = item.get("role_id") or item.get("roleId") or item.get("role") or item.get("role_name")
        comp_ref = item.get("competency_id") or item.get("competencyId") or item.get("competency") or item.get("competency_name")
        level = item.get("required_level") or item.get("level") or item.get("requiredLevel") or 3
        try:
            level = int(level)
        except Exception:
            level = 3

        role_id, comp_id = _resolve_role_and_competency_ids(db, role_ref, comp_ref)
        if not role_id or not comp_id:
            continue

        existing = (
            db.query(RoleCompetency)
            .filter(RoleCompetency.role_id == role_id, RoleCompetency.competency_id == comp_id)
            .first()
        )
        if existing:
            if existing.required_level != level:
                existing.required_level = level
                db.add(existing)
        else:
            db.add(RoleCompetency(role_id=role_id, competency_id=comp_id, required_level=level))
        count += 1
    return count


# PUBLIC_INTERFACE
def seed_from_json_if_enabled(db: Session) -> None:
    """Seed roles, competencies, and role-competency mappings from JSON if configured.

    Notes:
        - Uses a robust path resolver so INGESTION_JSON_DIR works from different working directories.
        - Flushes after role and competency upserts so mapping upserts can resolve newly inserted records
          within the same transaction (SessionLocal has autoflush=False).
    """
    settings = get_settings()
    if not settings.seed_from_json:
        return

    base_dir = _resolve_ingestion_dir(settings.ingestion_json_dir)
    roles_path = os.path.join(base_dir, "roles.json")
    comps_path = os.path.join(base_dir, "competencies.json")
    rc_path = os.path.join(base_dir, "role_competencies.json")

    roles = _read_json(roles_path) or []
    comps = _read_json(comps_path) or []
    mappings = _read_json(rc_path) or []

    total_roles = total_comps = total_maps = 0
    changed = False

    if roles:
        total_roles = upsert_roles(db, roles)
        # Ensure newly added roles are visible to subsequent queries in the same session
        db.flush()
        changed = True

    if comps:
        total_comps = upsert_competencies(db, comps)
        # Ensure newly added competencies are visible before mapping step
        db.flush()
        changed = True

    if mappings:
        total_maps = upsert_role_competencies(db, mappings)
        changed = True

    if changed:
        db.commit()
        logger.info(
            "JSON seed applied from %s (roles=%d, competencies=%d, role_competencies=%d)",
            base_dir, total_roles, total_comps, total_maps
        )
