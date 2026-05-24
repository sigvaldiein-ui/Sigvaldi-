#!/bin/bash
# DEPRECATED — replaced by supervisord (Sprint 102, 2026-05-24)
echo "❌ Þetta script er deprecated."
echo ""
echo "Alvitur er nú managed af supervisord:"
echo "  supervisorctl status                       # Sjá hvað er running"
echo "  supervisorctl restart alvitur:alvitur-uvicorn"
echo "  supervisorctl tail -f alvitur:alvitur-uvicorn"
echo ""
echo "Skjölun: docs/runbook/supervisord_operations.md"
exit 1
