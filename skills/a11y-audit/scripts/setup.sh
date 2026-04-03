#!/usr/bin/env bash
# a11y-audit — dependency setup script
# Run: bash skills/a11y-audit/scripts/setup.sh

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}a11y-audit — checking dependencies${NC}\n"

# ── 1. Node.js ──────────────────────────────────────────────────────────────
if ! command -v node &> /dev/null; then
  echo -e "${RED}✗ Node.js not found. Install from https://nodejs.org (LTS recommended)${NC}"
  exit 1
fi
NODE_VERSION=$(node -v)
echo -e "${GREEN}✓ Node.js ${NODE_VERSION}${NC}"

# ── 2. npm / package.json ───────────────────────────────────────────────────
if [ ! -f "package.json" ]; then
  echo -e "${YELLOW}  No package.json found — creating minimal one${NC}"
  echo '{"name":"a11y-audit-deps","private":true}' > package.json
fi

# ── 3. Playwright ────────────────────────────────────────────────────────────
echo -e "\n${BLUE}Checking Playwright...${NC}"
if npx playwright --version &> /dev/null 2>&1; then
  PW_VERSION=$(npx playwright --version)
  echo -e "${GREEN}✓ Playwright ${PW_VERSION}${NC}"
else
  echo -e "${YELLOW}  Installing @playwright/test...${NC}"
  npm install --save-dev @playwright/test
  echo -e "${YELLOW}  Installing Chromium browser...${NC}"
  npx playwright install chromium
  echo -e "${GREEN}✓ Playwright installed${NC}"
fi

# Check Chromium is available
if ! npx playwright install --dry-run chromium 2>&1 | grep -q "chromium.*is already installed"; then
  echo -e "${YELLOW}  Installing Chromium browser...${NC}"
  npx playwright install chromium
fi

# ── 4. axe-core ──────────────────────────────────────────────────────────────
echo -e "\n${BLUE}Checking axe-core...${NC}"
if [ -d "node_modules/axe-core" ]; then
  AXE_VERSION=$(node -e "console.log(require('axe-core/package.json').version)" 2>/dev/null)
  echo -e "${GREEN}✓ axe-core ${AXE_VERSION} (local)${NC}"
else
  echo -e "${YELLOW}  Installing axe-core (local fallback for offline use)...${NC}"
  npm install --save-dev axe-core
  AXE_VERSION=$(node -e "console.log(require('axe-core/package.json').version)")
  echo -e "${GREEN}✓ axe-core ${AXE_VERSION}${NC}"
fi

# ── 5. Summary ───────────────────────────────────────────────────────────────
echo -e "\n${GREEN}All dependencies ready. You can now run a11y-audit.${NC}"
echo -e "  axe-core CDN (primary):  https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.10.2/axe.min.js"
echo -e "  axe-core local fallback: node_modules/axe-core/axe.min.js"
echo -e "  Playwright browser:      chromium\n"
