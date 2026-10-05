#!/bin/bash
# PreToolUse hook — crée un flag si le skill ab-test-generator est invoqué
# Reçoit JSON sur stdin : {"tool_name":"Skill","tool_input":{"skill":"ab-test-generator",...}}

SKILL=$(python3 -c "
import sys, json
data = json.loads(sys.stdin.read())
print(data.get('tool_input', {}).get('skill', ''))
")

if echo "$SKILL" | grep -qi "ab-test-generator"; then
    touch /tmp/abt_session_active
fi
