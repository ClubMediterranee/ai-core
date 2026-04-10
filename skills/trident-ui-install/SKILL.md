---
name: trident-ui-install
description: Install and configure Trident UI component library for Vite and Next.js projects
allowed-tools: Bash, Read, Edit, Write, Glob, Grep, Agent, TaskCreate, TaskUpdate, TaskList, WebFetch
version: 1.0.0
changelog:
  - version: 1.0.0
    date: 2026-04-08
    changes:
      - Initial release
created-at: 2026-04-08
created-by: "Georges Mathieu <georges.mathieu.ext@clubmed.com>"
---

# Trident UI Installation

Streamline the setup of Trident UI component library in your Vite or Next.js project. This skill automates dependency installation, configuration file creation, and design system setup.

## What This Skill Does

Trident UI is a pre-built React component library using Tailwind 4 with CSS-only theming. This skill will:

1. Detect your project type (Vite or Next.js) and package manager
2. Install required dependencies (@clubmed/trident-icons, tailwindcss)
3. Create configuration files (components.json, CSS, Tailwind config)
4. Install the complete design system (157 CSS variables, 25+ animations, component styles)
5. Set up TypeScript path aliases
6. Validate the installation

After setup, you can use Trident UI components by copying them into your project:

- **shadcn CLI**: `npx shadcn@latest add <registry-url>` copies component source code into your project for full customization control

---

## Phase 1: Preflight & Detection

**EXPLAIN**: I need to understand your project structure to provide the right configuration. Let me detect your project type, package manager, and check for any existing installations.

**DO**: Running detection...

```bash
# Check for package.json
if [ ! -f "package.json" ]; then
  echo "❌ Error: No package.json found. Please run this in a project root."
  exit 1
fi

# Detect project type
PROJECT_TYPE="unknown"
if grep -q '"next"' package.json 2>/dev/null || [ -f "next.config.js" ] || [ -f "next.config.ts" ] || [ -f "next.config.mjs" ]; then
  PROJECT_TYPE="nextjs"
elif grep -q '"vite"' package.json 2>/dev/null || [ -f "vite.config.js" ] || [ -f "vite.config.ts" ] || [ -f "vite.config.mjs" ]; then
  PROJECT_TYPE="vite"
fi

# Detect package manager
PKG_MANAGER="npm"
if [ -f "pnpm-lock.yaml" ]; then
  PKG_MANAGER="pnpm"
elif [ -f "yarn.lock" ]; then
  PKG_MANAGER="yarn"
elif [ -f "bun.lockb" ] || [ -f "bun.lock" ]; then
  PKG_MANAGER="bun"
elif [ -f "package-lock.json" ]; then
  PKG_MANAGER="npm"
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
  echo "⚠️  Warning: Node.js >= 18 required. You have $(node -v)"
fi

# Check for existing installation
EXISTING_INSTALL="no"
if grep -q "@clubmed/trident-icons" package.json 2>/dev/null; then
  EXISTING_INSTALL="yes"
fi

# Check for Tailwind 3.x
TAILWIND_VERSION=""
if [ -d "node_modules/tailwindcss" ]; then
  TAILWIND_VERSION=$(node -e "try{console.log(require('./node_modules/tailwindcss/package.json').version)}catch(e){}" 2>/dev/null)
  TAILWIND_MAJOR=$(echo "$TAILWIND_VERSION" | cut -d'.' -f1)
  if [ -n "$TAILWIND_MAJOR" ] && [ "$TAILWIND_MAJOR" -lt 4 ]; then
    echo "⚠️  Tailwind $TAILWIND_VERSION detected (requires 4.x) — see error handling section below"
  fi
fi

# Detect CSS file path
CSS_FILE=""
if [ "$PROJECT_TYPE" = "vite" ]; then
  for file in "src/index.css" "src/main.css" "src/styles.css" "src/global.css"; do
    if [ -f "$file" ]; then
      CSS_FILE="$file"
      break
    fi
  done
  [ -z "$CSS_FILE" ] && CSS_FILE="src/index.css"
elif [ "$PROJECT_TYPE" = "nextjs" ]; then
  for file in "app/globals.css" "src/app/globals.css" "app/global.css" "styles/globals.css"; do
    if [ -f "$file" ]; then
      CSS_FILE="$file"
      break
    fi
  done
  if [ -z "$CSS_FILE" ]; then
    [ -d "src/app" ] && CSS_FILE="src/app/globals.css" || CSS_FILE="app/globals.css"
  fi
fi

# Detect Tailwind config file
TAILWIND_CONFIG=""
if [ "$PROJECT_TYPE" = "vite" ]; then
  for file in "vite.config.ts" "vite.config.js" "vite.config.mjs"; do
    if [ -f "$file" ]; then
      TAILWIND_CONFIG="$file"
      break
    fi
  done
  [ -z "$TAILWIND_CONFIG" ] && TAILWIND_CONFIG="vite.config.ts"
elif [ "$PROJECT_TYPE" = "nextjs" ]; then
  for file in "postcss.config.mjs" "postcss.config.js" "postcss.config.cjs"; do
    if [ -f "$file" ]; then
      TAILWIND_CONFIG="$file"
      break
    fi
  done
  [ -z "$TAILWIND_CONFIG" ] && TAILWIND_CONFIG="postcss.config.mjs"
fi
```

**SHOW**: Detection results:

```
🔍 Project Detection Results:

Project Type: [PROJECT_TYPE]
Package Manager: [PKG_MANAGER]
Node.js Version: [VERSION]
Existing Installation: [yes/no]

Files to create/modify:
  - components.json (new)
  - [CSS_FILE] (create or update)
  - [TAILWIND_CONFIG] (create or update)
  - tsconfig.json (update paths only, if exists)

This installation will:
  ✓ Configure Tailwind 4 for your project type
  ✓ Install design system (157 CSS variables + 25+ animations)
  ✓ Set up TypeScript path aliases
  ✓ Enable shadcn CLI for component installation
```

**PAUSE**: Ready to proceed with installation? [Continue]

---

## Phase 2: Install Dependencies

**EXPLAIN**: Installing Trident UI and its required dependencies. This includes the core library, icon package, and Tailwind 4 with the appropriate plugins for your project type.

**DO**: Running package installation...

```bash
# Vite project dependencies
if [ "$PROJECT_TYPE" = "vite" ]; then
  [PKG_MANAGER] install @clubmed/trident-icons tailwindcss
  [PKG_MANAGER] install -D @tailwindcss/vite
fi

# Next.js project dependencies
if [ "$PROJECT_TYPE" = "nextjs" ]; then
  [PKG_MANAGER] install @clubmed/trident-icons tailwindcss
  [PKG_MANAGER] install -D @tailwindcss/postcss postcss
fi
```

**SHOW**: Installation progress and results:

```
📦 Installing packages...

✓ @clubmed/trident-icons@[version]
✓ tailwindcss@[version]
[✓ @tailwindcss/vite@[version] (Vite only)]
[✓ @tailwindcss/postcss@[version] (Next.js only)]
[✓ postcss@[version] (Next.js only)]

Dependencies installed successfully!
```

---

## Phase 3: Create Configuration Files

**EXPLAIN**: Creating configuration files for shadcn CLI compatibility, Tailwind 4 integration, and TypeScript path aliases.

### 3.1 Create components.json

**DO**: Creating `components.json` in project root. Set `"rsc": true` for Next.js (React Server Components), `"rsc": false` for Vite.

```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "default",
  "rsc": false,
  "tsx": true,
  "tailwind": {
    "config": "[TAILWIND_CONFIG]",
    "css": "[CSS_FILE]",
    "baseColor": "slate",
    "cssVariables": true,
    "prefix": ""
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils",
    "ui": "@/components/ui",
    "lib": "@/lib",
    "hooks": "@/hooks"
  },
  "registries": {
    "@tridentui": "https://develop.trident-ui.pro.clubmed/r/{name}.json"
  }
}
```

**SHOW**: `✓ components.json created`

### 3.2 Create/Update CSS File

**DO**: Setting up CSS imports in `[CSS_FILE]`...

For **Vite** projects:

```css
@import "tailwindcss";
@source '../src/**/*.{tsx,ts,jsx,js}';

/* Your custom styles below */
```

For **Next.js** projects:

```css
@import "tailwindcss";
@source '../app/**/*.{tsx,ts}';
@source '../components/**/*.{tsx,ts}';

/* Your custom styles below */
```

**SHOW**: `✓ [CSS_FILE] [created/updated]`

### 3.3 Configure Tailwind 4

**DO**: Configuring Tailwind 4 for your project...

For **Vite** projects - updating `[TAILWIND_CONFIG]`:

```typescript
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";
// ... other imports

export default defineConfig({
  // ... other config
  plugins: [
    // ... other plugins
    tailwindcss(),
  ],
});
```

For **Next.js** projects - creating `postcss.config.mjs`:

```javascript
export default {
  plugins: {
    "@tailwindcss/postcss": {},
  },
};
```

**SHOW**: `✓ Tailwind 4 configured for [PROJECT_TYPE]`

### 3.4 Update TypeScript Configuration

**DO**: Adding path aliases to `tsconfig.json` (if exists)...

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"],
      "@/components/*": ["./src/components/*"],
      "@/lib/*": ["./src/lib/*"]
    }
  }
}
```

**SHOW**: `✓ TypeScript paths configured` or `⊘ Skipped (no tsconfig.json)`

### 3.5 Install Design System

**EXPLAIN**: Installing the Trident UI design system foundation. This provides 157 CSS variables (colors, typography, spacing, etc.), 25+ animations, and component base styles. This is installed via the shadcn CLI tool (used on-demand via npx, no separate installation needed).

**DO**: Running shadcn CLI to install design system...

```bash
npx shadcn@latest add https://develop.trident-ui.pro.clubmed/r/tailwind-config.json
```

**SHOW**: Design system installation results:

```
✓ Design system installed successfully!

What was added:
  • 157 CSS variables (colors, typography, spacing, radii, shadows, breakpoints)
  • 25+ animations (bounceEnter, slideDown, zoomIn, loaders, etc.)
  • Component base styles (buttons, forms, tabs, switches, etc.)
  • Custom Tailwind utilities (aspect ratios, line-clamp, grid areas)
  • Custom variants (hocus, hoverable, popover states)

These design tokens are now available in your styles:
  color: var(--color-saffron);
  font-size: var(--text-h2);
  animation: bounceEnter 0.3s ease-out;
```

---

## Phase 4: Validation

**EXPLAIN**: Validating the installation to ensure everything is set up correctly.

**DO**: Running validation checks...

```bash
# Check packages installed
test -d "node_modules/@clubmed/trident-icons" && echo "✓ trident-icons installed" || echo "❌ trident-icons missing"
test -d "node_modules/tailwindcss" && echo "✓ tailwindcss installed" || echo "❌ tailwindcss missing"

# Check config files
test -f "components.json" && echo "✓ components.json created" || echo "❌ components.json missing"
test -f "[CSS_FILE]" && echo "✓ CSS file exists" || echo "❌ CSS file missing"
test -f "[TAILWIND_CONFIG]" && echo "✓ Tailwind config exists" || echo "❌ Tailwind config missing"

# Check design system
if [ -f "components/ui/tailwind-config.tsx" ] || grep -rq --exclude-dir=node_modules "color-saffron" .; then
  echo "✓ Design system installed"
else
  echo "⚠️  Design system may not be installed"
fi
```

**SHOW**: Validation results:

```
✅ Validation Complete!

All checks passed:
  ✓ @clubmed/trident-icons installed
  ✓ tailwindcss installed
  ✓ components.json created
  ✓ [CSS_FILE] configured
  ✓ [TAILWIND_CONFIG] configured
  ✓ Trident UI styles imported
  ✓ Design system installed
```

---

## Phase 5: Next Steps

**EXPLAIN**: Installation complete! Here's how to use Trident UI in your project.

**SHOW**: Usage examples and documentation:

```
✅ Installation Complete!

📦 Installed:
  - @clubmed/trident-icons@[version]
  - tailwindcss@[version]
  - Design system (157 CSS variables, 25+ animations, component styles)

🚀 Usage:

1. shadcn CLI (copy component to project):
   npx shadcn@latest add https://develop.trident-ui.pro.clubmed/r/button.json

   This copies the component source into your project for full customization.
   After copying, import and use it like any local component.

2. Use design tokens in your styles:
   .my-element {
     color: var(--color-saffron);
     font-size: var(--text-h2);
     border-radius: var(--radius-lg);
     animation: bounceEnter 0.3s ease-out;
   }

3. Browse available components:
   Visit the registry: https://develop.trident-ui.pro.clubmed/r
   Or check documentation: https://trident-ui.pro.clubmed

📚 Next Steps:
  • Add a component via shadcn CLI and test in your app
  • Explore the design system CSS variables
  • Browse the component registry for available components
  • Read the documentation for component props and usage

🎨 Design Tokens Available:
  Colors: --color-black, --color-ultramarine, --color-saffron, --color-wave, etc.
  Typography: --text-b6 through --text-h0 (body and heading scales)
  Spacing: --spacing (base unit)
  Radii: --radius-sm, --radius-md, --radius-lg, --radius-pill, --radius-full
  Animations: bounceEnter, slideDown, zoomIn, pulse, spin, and 20+ more

💡 Tips:
  • Use TypeScript for autocomplete on component props
  • Check Storybook examples for component usage patterns
  • The library uses Tailwind 4's CSS-only theming
  • All components are marked with 'use client' for Next.js compatibility
```

---

## Error Handling

### Partial Installation Detected

If existing Trident UI installation found:

- Offer to update existing files or skip
- Show diff of changes to be made
- Provide option to force reinstall

### Unknown Project Type

If neither Vite nor Next.js detected:

```
⚠️  Unknown project type detected.

I couldn't automatically detect if this is a Vite or Next.js project.
Please specify your project type:
  1. Vite
  2. Next.js
  3. Other (show manual instructions)

[User selects option]
```

### Tailwind 3.x Detected

If Tailwind 3.x is installed:

```
⚠️  Tailwind 3.x detected!

Trident UI requires Tailwind 4.x. This is a major version upgrade with breaking changes.

Options:
  1. Upgrade to Tailwind 4 (recommended)
  2. Show migration guide
  3. Cancel installation

[User selects option]
```

### Node.js Version Too Low

If Node.js < 18:

```
❌ Node.js version too low

Trident UI requires Node.js >= 18. You have [current version].

Please upgrade Node.js and try again:
  https://nodejs.org/
```

### Permission Errors

If file write fails:

```
❌ Permission denied writing to [file]

Please ensure you have write permissions to the project directory.
You may need to run with appropriate permissions.
```

---

## Guardrails

- **Never overwrite files without asking**: Always check if files exist and ask before overwriting
- **Validate before proceeding**: Check all preflight conditions before making changes
- **Preserve existing content**: When updating CSS or config files, preserve user's existing content
- **Clear error messages**: Provide actionable error messages with recovery steps
- **Graceful degradation**: If optional steps fail (like TypeScript config), continue but warn the user
- **Version compatibility**: Check for conflicting versions and warn appropriately
- **Rollback guidance**: If installation fails midway, provide steps to clean up

---

## Troubleshooting

### Components not styled correctly

Check that:

1. CSS import is present in your main CSS file
2. Tailwind 4 is configured correctly for your project type
3. Design system was installed via shadcn CLI
4. Build/dev server was restarted after installation

### TypeScript errors on imports

Check that:

1. `tsconfig.json` has correct path aliases
2. TypeScript version is compatible (>= 4.9)

### Tailwind classes not working

Check that:

1. `@source` directive includes your component paths
2. Tailwind 4 postcss plugin is configured
3. CSS file is imported in your app entry point

### Design tokens not available

Check that:

1. `npx shadcn add tailwind-config.json` completed successfully
2. Generated files are in your project
3. Build/dev server was restarted

For more help, visit: https://trident-ui.pro.clubmed/troubleshooting
 