---
date: 2026-04-03
task: Research CDN options for static asset delivery (images + video)
mode: research
agent: claude-sonnet
session-start: 14:00
---

# Diary — Research: CDN Options for Static Asset Delivery

## Entry — 14:00

### What I did
Started research by listing the current setup: assets are served directly from the app server (Node.js/Express), no CDN in place. Read `src/config/storage.ts` and `src/routes/assets.ts` to understand the upload and serving pipeline.

### Why
The team wants to offload static asset serving before the next peak season. Need to compare at least 3 CDN options against the constraints: EU data residency, video streaming support, existing AWS infrastructure.

### What worked
Reading the existing storage config first gave me the constraint that we're already using S3 (`eu-west-1`). That immediately narrows the CDN candidates — CloudFront is the natural fit; others will require more integration work.

### What didn't work
Assumed there was a media transcoding pipeline — there isn't. Videos are stored as-is. This rules out providers that require proprietary upload APIs (e.g., Cloudinary's video pipeline) unless we add a transcoding step.

### What I learned
Current upload flow: client → Express → `multer` → `aws-sdk` S3 put. No signed URLs in use — assets are public. This is a security concern but out of scope for this research.

### What was tricky
No ADR (Architecture Decision Record) exists for the current storage choice. Had to reconstruct constraints from git history and `package.json`.

### Future work
- Evaluate CloudFront (AWS-native, already in-region)
- Evaluate Cloudflare CDN (simpler pricing, strong EU presence)
- Evaluate Fastly (more complex, but edge compute capabilities)
- Check video streaming support for each

### Technical details
- `src/config/storage.ts` — S3 bucket: `company-assets-prod`, region: `eu-west-1`
- `aws-sdk` version: `2.1450.0` (v2, not v3 — upgrade may be needed)
- Asset types: JPEG/WebP images (avg 200KB), MP4 videos (avg 50MB)
- Traffic estimate: ~2M asset requests/day at peak

---

## Entry — 14:55

### What I did
Evaluated CloudFront and Cloudflare. Skipped Fastly — edge compute is out of scope and pricing is opaque for our traffic level.

**CloudFront**: Native S3 origin support, same AWS account, `eu-west-1` origin shield available. Price: ~$0.0085/GB transfer + $0.0075/10k requests (EU).

**Cloudflare CDN**: Requires pointing DNS to Cloudflare. Free tier covers bandwidth (unlimited on Pro). Strong EU PoPs. R2 integration exists but we'd keep S3 as origin. No per-GB egress charges for CDN → origin pull on Cloudflare plan.

### Why
CloudFront is zero-migration on the infra side but has per-GB costs at scale. Cloudflare is cheaper at our traffic volume but adds DNS dependency and a new vendor.

### What worked
The Cloudflare bandwidth alliance means no egress charges from S3 → Cloudflare — a non-obvious but significant cost saving for our video assets.

### What didn't work
Tried to get CloudFront video streaming pricing for our exact volume — AWS calculator requires an account and I couldn't get a clean number without logging in.

### What I learned
Cloudflare's "bandwidth alliance" with AWS means S3 → Cloudflare egress is free. For 50MB average video files at 2M requests/day, this is ~$0 egress vs. ~$8,500/day on CloudFront at full cache-miss rate (obviously cache hit rate will be much higher, but still a meaningful difference at scale).

### What was tricky
Both options support HTTP/2 and partial content (range requests for video scrubbing). This was my main concern about video support — both handle it natively.

### Future work
- Final recommendation: Cloudflare CDN (cost + simplicity) with S3 origin
- Document migration steps: DNS cutover, cache rules for images vs. video, cache TTLs
- Flag the unsigned S3 assets security concern in the ADR

### Technical details
- CloudFront: `$0.0085/GB` EU transfer, `$0.012/10k` HTTPS requests
- Cloudflare Pro: `$20/month`, unlimited bandwidth, S3 origin pull included
- Both: HTTP range requests supported (video seek works)
- Cloudflare bandwidth alliance partners: AWS, GCP, Azure (no egress charge)
- Migration effort: DNS `CNAME` change + cache rules config (~2h)

---

## Session Close — 15:30

### Summary
Researched CloudFront and Cloudflare CDN as options for static asset delivery. Cloudflare CDN with S3 origin is the recommended choice: zero egress costs via bandwidth alliance, strong EU presence, and minimal migration effort (DNS + cache rules only). CloudFront remains viable if keeping all infra within AWS is a hard requirement.

### What's next
- Write the ADR at `docs/architecture/decisions/CDN-selection.md`
- Get sign-off from infra team on DNS cutover window
- Prototype Cloudflare cache rules for image vs. video TTLs

### Open questions
- Is "everything in AWS" a hard requirement from the security team? If so, CloudFront wins by default.
- What's the acceptable cache-miss rate for video assets? Affects TTL strategy significantly.
