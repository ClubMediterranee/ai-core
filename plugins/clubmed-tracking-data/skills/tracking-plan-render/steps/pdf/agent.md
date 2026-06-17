# PDF renderer agent

Your job: run `render_pdf.py` and report the result.

## Inputs
- `PLAN_FILE`  — path to plan.json
- `OUTPUT_DIR` — output directory
- `SKILL_DIR`  — skill root

## Actions

### 1. Verify reportlab is available

```bash
python3 -c "import reportlab" 2>/dev/null || {
  echo "Installing reportlab..."
  pip3 install reportlab -q
}
```

### 2. Run renderer

```bash
python3 "${SKILL_DIR}/scripts/render_pdf.py" "${PLAN_FILE}" "${OUTPUT_DIR}"
```

### 3. Verify output

```bash
ls -lh "${OUTPUT_DIR}/"*.pdf 2>/dev/null || echo "ERROR: pdf not found"
```

Return the output path on success, error message on failure.
