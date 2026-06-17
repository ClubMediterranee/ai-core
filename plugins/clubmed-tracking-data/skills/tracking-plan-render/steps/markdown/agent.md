# Markdown renderer agent

Your job: run `render_markdown.py` and report the result.

## Inputs
- `PLAN_FILE`  — path to plan.json
- `OUTPUT_DIR` — output directory
- `SKILL_DIR`  — skill root

## Actions

### 1. Run renderer (zero dependencies)

```bash
python3 "${SKILL_DIR}/scripts/render_markdown.py" "${PLAN_FILE}" "${OUTPUT_DIR}"
```

### 2. Verify output

```bash
ls -lh "${OUTPUT_DIR}/"*.md 2>/dev/null || echo "ERROR: md not found"
```

Return the output path on success, error message on failure.
