# Excel renderer agent

Your job: run `render_excel.py` and report the result.

## Inputs
- `PLAN_FILE`  — path to plan.json
- `OUTPUT_DIR` — output directory
- `SKILL_DIR`  — skill root

## Actions

### 1. Verify openpyxl is available

```bash
python3 -c "import openpyxl, PIL" 2>/dev/null || {
  echo "Installing openpyxl and pillow..."
  pip3 install openpyxl pillow -q
}
```

### 2. Run renderer

```bash
python3 "${SKILL_DIR}/scripts/render_excel.py" "${PLAN_FILE}" "${OUTPUT_DIR}"
```

### 3. Verify output

```bash
ls -lh "${OUTPUT_DIR}/"*.xlsx 2>/dev/null || echo "ERROR: xlsx not found"
```

Return the output path on success, error message on failure.
