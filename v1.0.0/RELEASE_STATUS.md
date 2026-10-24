# Release status

C01–C21 baseline complete. Remaining work is being implemented continuously.

External requirements confirmed absent:
- Hugging Face and GitHub API return proxy 403. Added domains to environment draft;
  user must review/save and Publish. Draft save does not update runtime.
- Supabase/Cloudflare/R2 bindings absent. Need project URL, account/project/bucket,
  explicit deployment visibility and securely supplied credentials before real deployment.
- Intel Mac is unavailable here; actual CPU/model latency and Mac install remain unverified.

No paid infrastructure or cloud LLM API will be created. Model files stay out of Git.
