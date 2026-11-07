"""Реестр HTTP MCP-тулов платформы собеседований (сборка по доменам)."""
from __future__ import annotations

from typing import Any

from django.conf import settings

from core.mcp_tools import (
    admin_reports,
    companies,
    debts,
    developers,
    directions,
    employees,
    interviews,
    interns,
    knowledge_base,
    managers,
    offers,
    sad_intern,
)

_MODULES = [
    interviews,
    interns,
    companies,
    directions,
    sad_intern,
    employees,
    managers,
    developers,
    offers,
    debts,
    admin_reports,
    knowledge_base,
]

if 'vector_search' in settings.INSTALLED_APPS:
    from core.mcp_tools import vector_search
    _MODULES.append(vector_search)

TOOLS: dict[str, dict[str, Any]] = {}
for _mod in _MODULES:
    TOOLS.update(_mod.TOOLS)

__all__ = ['TOOLS']
