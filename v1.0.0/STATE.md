# MW-NV v1.0.0 STATE
Current task: D01 NIM HQ and private Cloudflare/Supabase deployment
Status: code ready; external deployment and NIM validation BLOCKED
NIM: --hq nim, meta/llama-3.1-8b-instruct, candidate validation/algorithm fallback
Supabase: private mw-nv-replays bucket; initial-private-demo uploaded/checksum PASS
Storage: manifest index read-back PASS; anon read denied; SQL table not required
Pages: config/build/private password session prepared; no deployment URL
Blocker: Cloudflare create403 Authentication error; token verify401 Invalid API Token
Blocker: integrate.api.nvidia.com CONNECT403; actual NIM latency/cost UNKNOWN
Required: replace Cloudflare token; allow NIM domain; actual Pages secrets per NIM_DEPLOY.md
Tests: Python HQ11+live/tactics12 PASS; JS13/build/Pages Functions PASS
Next: cd viewer && npx wrangler pages deploy dist --project-name mw-nv --branch dev/v1.0.0
Docs: cloud/NIM_DEPLOY.md; existing traffic/side bias findings remain
Branch: dev/v1.0.0; Mac/NIM live unverified; no paid resources enabled
Usage: UNKNOWN
