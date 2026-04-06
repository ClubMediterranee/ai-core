---
name: trident-icons
description: 'Find and use icons from the @clubmed/trident-icons library. Use when a user asks which icon to use for a given concept, writes <Icon name= without knowing the right name, mentions "@clubmed/trident-icons", asks "quelle icône pour X", "which icon for Y", "find me an icon", "what icon represents Z", "liste les icônes de transport", or needs import code for Trident icons. Also triggers when writing or reviewing a component that should display an icon from the Club Med design system.'
allowed-tools: WebFetch
version: 1.2.0
changelog:
  - version: 1.2.0
    date: 2026-04-06
    changes:
      - Switch from Bash/curl to WebFetch — curl blocked by CDN, WebFetch works
  - version: 1.1.0
    date: 2026-04-06
    changes:
      - Removed MCP reference — no server available yet
      - Simplified to fetch script only
  - version: 1.0.0
    date: 2026-04-06
    changes:
      - Initial release — semantic search via live catalog fetch with 1h file cache, import code generation
created-at: 2026-04-06
created-by: "Jeremy Wallez <jeremy.wallez@clubmed.com>"
---

# Trident Icons — Find & Use

Help users find the right icon and generate correct import code for `@clubmed/trident-icons`.

---

## Step 1 — Get the Catalog

```
WebFetch: https://latest.trident-icons.pro.clubmed/icons-metadata.json
```

The JSON structure: `categories[{ category, icons[{ name, withOrientation?, variants? }] }]`

---

## Step 2 — Find the Right Icon

Search the catalog by matching the user's description against icon names (PascalCase English).

Key patterns to recognize:
- **Fill / Outline / Default** — style variants of the same icon (`HeartFilled`, `HeartOutlined`)
- **Orientation** (`withOrientation: true`) — use the `Left/Right/Up/Down` suffixed variant, never the bare name (`ArrowDefaultLeft`, not `ArrowDefault`)
- **Category hint** — when context is clear (dining → Food, sport → Activities, room amenity → Room, social network → Socials, transport → Transports), narrow the search there first
- **Ambiguous concepts** — some concepts map to multiple icons depending on context: `wifi/internet` → `Internet` (Utilities, general connectivity) vs `WIFI` (Room, in-room amenity). Ask for context when unclear.

If no exact match exists, suggest the closest alternative and mention the Storybook: `https://latest.trident-icons.pro.clubmed/`

---

## Step 3 — Generate Import Code

Always import by **category** — never import all icons at once (bundle size).

Use `svg-use` for optimal performance, `svg` only when lazy loading is explicitly needed.

**Single icon:**
```tsx
import { Icon, IconsProvider } from '@clubmed/trident-icons';
import Actions from '@clubmed/trident-icons/svg-use/Actions';

<IconsProvider icons={[Actions]}>
  <Icon name="Search" />
</IconsProvider>
```

**Multiple icons — group imports by category:**
```tsx
import { Icon, IconsProvider } from '@clubmed/trident-icons';
import Actions from '@clubmed/trident-icons/svg-use/Actions';
import Utilities from '@clubmed/trident-icons/svg-use/Utilities';

<IconsProvider icons={[Actions, Utilities]}>
  <Icon name="CrossDefault" />
  <Icon name="CalendarDefault" />
</IconsProvider>
```

**Category names with hyphens** (e.g. `ResortFill-EC`) use their exact segment in the path:
```tsx
import ResortFillEC from '@clubmed/trident-icons/svg-use/ResortFill-EC';
```

**Icon props:**
```tsx
<Icon
  name="Search"
  size="24px"           // custom size
  color="currentColor"  // inherits from parent by default
  className="my-icon"   // additional CSS classes
/>
```

---

## Resources

- **Live catalog**: https://latest.trident-icons.pro.clubmed/icons-metadata.json
- **Storybook**: https://latest.trident-icons.pro.clubmed/
- **Package**: `@clubmed/trident-icons`
