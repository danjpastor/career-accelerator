"""Program-neutral Accelerator Academy curriculum engine."""

from .loader import CurriculumError, load_catalog
from .models import ActivityType, CurriculumCatalog, ProgressState
from .schema import ensure_academy_schema
from .service import AcademyService

__all__ = [
    "AcademyService",
    "ActivityType",
    "CurriculumCatalog",
    "CurriculumError",
    "ProgressState",
    "ensure_academy_schema",
    "load_catalog",
]
