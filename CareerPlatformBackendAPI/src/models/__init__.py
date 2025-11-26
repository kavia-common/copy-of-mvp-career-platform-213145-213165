"""Models package for SQLAlchemy ORM entities.

Import models here to ensure they are registered with SQLAlchemy's Base
before metadata.create_all() is invoked at application startup.
"""

from .user import User  # noqa: F401
from .role import Role  # noqa: F401
from .template import Template  # noqa: F401
from .competency import Competency  # noqa: F401
from .role_competency import RoleCompetency  # noqa: F401
from .assessment import Assessment  # noqa: F401
from .development_plan import DevelopmentPlan  # noqa: F401
from .audit import AuditLog  # noqa: F401
from .traceability import Traceability  # noqa: F401
