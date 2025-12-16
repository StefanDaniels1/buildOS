#!/usr/bin/env python3
"""Direct execution of CO2 calculation"""

import sys
sys.path.insert(0, '/app/workspace')

from calculate_co2_report import main

if __name__ == "__main__":
    # Override sys.argv for direct execution
    sys.argv = [
        'calculate_co2_report.py',
        '/app/workspace/.context/session_session_1765555793733_ebch5w/all_classified_elements.json',
        '/app/.claude/skills/ifc-analysis/reference/durability_database.json',
        '/app/workspace/.context/session_session_1765555793733_ebch5w/co2_report.json'
    ]
    main()
