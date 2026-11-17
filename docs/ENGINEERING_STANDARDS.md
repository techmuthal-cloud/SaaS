# SellerFlow AI — Engineering Standards & Security Baseline

Version 2.0 | November 2026

## 1. Monorepo Structure
```
sellerflow-ai/
├── apps/
│   ├── api/          # FastAPI Python backend (modular domain architecture)
│   └── web/          # Next.js 16 App Router + React 19 + Tailwind CSS frontend
├── packages/
│   └── shared/       # Shared TypeScript contracts and domain models
├── infra/            # Production Dockerfiles, Nginx configs, and compose files
├── docs/             # Financial specifications, architecture, and developer guides
├── tests/            # Automated test suite (unit, integration, security)
└── .github/          # CI workflows and PR review templates
```

---

## 2. Security Controls & Tenant Isolation
1. **Mandatory Tenant Verification**:
   - Every protected route must depend on `verify_tenant_access`.
   - Deny-by-default: If caller is not an active member of `workspace_id`, the API returns `HTTP 403 Forbidden`.
2. **Safe File Uploads**:
   - Files are stored in tenant-isolated paths: `storage/uploads/<workspace_id>/<uuid4>.<ext>`.
   - Never trust client-provided file names; paths must never contain user input (prevents directory traversal).
   - Strict MIME and extension validation: `.csv`, `.tsv`, `.txt`, `.xlsx`.
3. **Formula Injection Sanitization**:
   - Any CSV or Excel export must sanitize all text cells using `sanitize_for_spreadsheet()`.
   - Cells starting with `=`, `+`, `-`, `@`, `\t`, or `\r` are prepended with `'` to neutralize Excel/Calc formula execution.
4. **Secret Management**:
   - All credentials, JWT secret keys, and database passwords must reside in environment variables.
   - Zero hardcoded secrets in version control.

---

## 3. Branch Protection & PR Governance
- **Main Branch Protection**:
  - Direct pushes to `main` are disabled.
  - Require pull request reviews before merging.
  - Require status checks to pass before merging:
    - Backend Unit & Security Tests (`python -m pytest tests/ -v`)
    - Flake8 Python linting
    - Frontend lint (`npm run lint`)
    - Frontend production build (`npm run build`)
    - TruffleHog secret scanning
