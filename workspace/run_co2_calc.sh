#!/bin/bash
cd /app/workspace
python3 calculate_co2_report.py \
  /app/workspace/.context/session_session_1765555793733_ebch5w/all_classified_elements.json \
  /app/.claude/skills/ifc-analysis/reference/durability_database.json \
  /app/workspace/.context/session_session_1765555793733_ebch5w/co2_report.json
