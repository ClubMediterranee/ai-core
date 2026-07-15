---
applies-to: [ground, write, review, harden]
enforcement: judgment
---

# Rule: No repo pollution

Temporary exploration and DOM-inspection scripts must be created in a system temp directory
(e.g. `/tmp/`), never inside the project repository. The repo holds only the committed suite:
specs, utils, fixtures, config. Throwaway probes, scratch selectors, and one-off scripts do not
belong in version control and must never be committed.

The one sanctioned in-repo artifact directory is `.e2e-artifacts/` (flow-map, test-plan), which
should be gitignored by the target repo.

**Review action:** a scratch/debug script committed inside the repo is a finding.
