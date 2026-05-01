# interfaces/departments/__init__.py
"""
Sprint 55 — Departments package.

Hver department er aðskilinn module með eigin specialist prompt og metadata.
Bæta við nýjum department: búa til ny_skra.py sem erfir BaseDepartment.
"""
from interfaces.departments.base import BaseDepartment
from interfaces.departments.legal import LegalDepartment
from interfaces.departments.finance import FinanceDepartment
from interfaces.departments.writing import WritingDepartment
from interfaces.departments.research import ResearchDepartment
from interfaces.departments.general import GeneralDepartment

# Registry — domain name → department instance
REGISTRY: dict[str, BaseDepartment] = {
    "legal": LegalDepartment(),
    "finance": FinanceDepartment(),
    "writing": WritingDepartment(),
    "research": ResearchDepartment(),
    "general": GeneralDepartment(),
}


def get_department(domain: str) -> BaseDepartment:
    """Skilar department fyrir gefið domain. Fallback á general."""
    return REGISTRY.get(domain, REGISTRY["general"])
