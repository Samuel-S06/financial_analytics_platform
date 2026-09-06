# Spendline

Upload a CSV of bank transactions and get a spending breakdown, a month-by-month
trend, and a savings simulation — behind per-user accounts, with totals viewable
in a second currency.

Built for CIS 1912 as a Kubernetes deployment, then extended with authentication,
a live external API, and a motion pass on the landing page.

## What it does

- **Upload a CSV** — bad rows are cleaned and *reported*, not silently dropped
- **See where the money went** — spending by category and by month
- **Simulate a savings goal** — pick a target, a timeframe, and categories to cut
  from; get recommended monthly budgets and a feasibility verdict
- **Switch currency** — totals convert into any of nine other currencies at live rates
- **Accounts** — each user only ever sees their own uploads

## How it's built

| Layer | What runs |
|---|---|
| Frontend | React 18 + Vite, Recharts, Framer Motion |
| Backend | FastAPI (Python 3.12), pandas |
| Job state | Redis — parsed DataFrames as parquet, plus per-user job indexes |
| Auth | Supabase (email/password); the backend verifies JWTs, never sees a password |
| Rates | Frankfurter (ECB reference rates), server-side and Redis-cached |
| Deployment | Docker, Kubernetes (Minikube), Helm, Terraform, GitHub Actions |

### How a request flows

Uploads return `202` with a `job_id` immediately and the work runs in the
background; the frontend polls `GET /job/{id}` until it's terminal. Parsed data
is stored in Redis as parquet, so a simulation can land on a different backend
pod than the upload did and still find its data. That's what keeps the backend
pods stateless and horizontally scalable.

Jobs are indexed under `user:{id}:jobs`, a sorted set scored by creation time.
Reading or simulating against another user's job returns **404, not 403** — a
403 would confirm the id exists.

---

## Running it locally

**Requires:** Docker and Node 20+. (Kubernetes, Helm and Terraform are only
needed for the cluster deployment below.)

### 1. Supabase

Create a free project at [supabase.com](https://supabase.com), then
**Project Settings → API** and copy the **Project URL** and the **publishable
key** (formerly "anon key"). The publishable key is meant to ship in a frontend
bundle. Never put the `service_role` / secret key in this project.

```bash
cat > frontend/.env.local <<'EOF'
VITE_SUPABASE_URL=https://<project>.supabase.co
VITE_SUPABASE_ANON_KEY=<publishable key>
EOF
```

Then set `SUPABASE_URL` in `docker-compose.yml` to the same project URL — the
backend uses it to fetch the public keys it verifies tokens against.

> **Confirming accounts.** This project leaves Supabase's *Confirm email* on, so
> a new signup can't sign in until it's confirmed — either from the emailed link,
> or by an admin in **Authentication → Users**. To skip that entirely, turn off
> *Confirm email* under **Authentication → Sign In / Providers → Email**; it
> needs no SMTP setup.

### 2. Start it

```bash
docker compose up -d        # Redis + the API on :8000, with hot reload
cd frontend && npm install && npm run dev   # UI on :5173
```

Open <http://localhost:5173>, create an account, confirm it, and sign in.

No bank export handy? Hit **Try it with sample data** under the upload zone and
the bundled sample runs straight through. It lives at
[`sample-data/sample_transactions.csv`](sample-data/sample_transactions.csv) and
is served by the app, so you can also drag it in or download it.

Charts appear, then run a simulation (say goal $600 over 12 months, cutting
Dining and Entertainment).

The Vite dev server proxies `/api/*` to the backend, mirroring what nginx does
in the container — so the frontend is same-origin in development and in
production alike.

### Handy commands

```bash
docker compose logs -f backend    # API logs (JSON lines)
docker compose down               # stop
docker compose down -v            # stop and drop Redis data

cd backend && python -m pytest    # 37 tests
cd backend && ruff check app/ tests/
```

> Tests need Python 3.12. If your system `python3` is older:
> `uv venv --python 3.12 .venv && uv pip install -r requirements-dev.txt`

### Configuration

Everything is read from the environment; see `.env.example`. The two that matter
most:

| Variable | Default | Notes |
|---|---|---|
| `AUTH_ENABLED` | `true` | Fails closed on purpose. Setting `false` attributes every request to one shared id and logs a warning at startup — local use only. |
| `CORS_ORIGINS` | `http://localhost:5173` | A no-op while the frontend is same-origin. Required once the two are on different domains. |

---

## Deploying it publicly

Minikube can't give you a public URL, so the hosted split is:

- **Backend + Redis → Render.** It builds `backend/Dockerfile` directly, so the
  container in production is the one that runs locally.
- **Frontend → Vercel.** It's a static bundle; Vercel puts it on a CDN free.
- **Auth → Supabase**, already hosted.

### 1. Backend on Render

Push to GitHub, then **Render → New → Blueprint** and point it at the repo.
`render.yaml` defines the web service and Redis. You'll be asked for two values:

- `SUPABASE_URL` — your project URL
- `CORS_ORIGINS` — your Vercel URL (fill in after step 2, then redeploy)

### 2. Frontend on Vercel

**Vercel → Add New → Project**, import the repo, and set the **Root Directory**
to `frontend`. `frontend/vercel.json` supplies the rest (Vite build, `npm ci`,
and the SPA rewrite so deep links don't 404).

Add three environment variables under **Settings → Environment Variables**:

| Variable | Value |
|---|---|
| `VITE_SUPABASE_URL` | your Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | the publishable key |
| `VITE_API_URL` | your Render URL, e.g. `https://spendline-api.onrender.com` |

`VITE_*` values are baked into the bundle at build time, so changing one needs a
redeploy, not just a restart.

### 3. Close the loop

Set `CORS_ORIGINS` on Render to your Vercel origin (e.g.
`https://your-app.vercel.app`) and redeploy. Without it the browser blocks every
API call.

Vercel also gives every deployment its own preview URL on a different subdomain.
Those are *not* covered by the origin above — add them to `CORS_ORIGINS` as a
comma-separated list if you want previews to reach the API.

> Render's free tier sleeps after inactivity, so the first request after a quiet
> spell takes ~30s to wake. Fine for a demo; worth knowing before you present.

---

## Running it on Kubernetes

The original CIS 1912 deployment. Requires Minikube, kubectl, Helm and Terraform.

```bash
make up
echo "127.0.0.1 financial.local" | sudo tee -a /etc/hosts
minikube tunnel   # leave running in a separate terminal
```

Visit <http://financial.local>. `make status` shows pods, services, ingress and
the autoscaler; `make down` tears it all down.

What's in here:

- **`helm/spendline/`** — deployments, services, ingress, an HPA, and a
  Redis StatefulSet with a PVC. Comments cover probe choices and the ingress
  rewrite rules.
- **`terraform/`** — the namespace and cluster-level resources. Terraform owns
  cluster bootstrap; Helm owns the application.
- **`.github/workflows/ci.yml`** — ruff, pytest, and both image builds on push.
- **`Makefile`** — every workflow: `make up`, `deploy`, `test`, `status`, `down`.

## Known limitations

- **Background jobs aren't durable.** They run in-process via FastAPI
  `BackgroundTasks`, so a pod restart mid-job orphans it. A real queue (Celery,
  RQ, arq) would fix it; it's more machinery than this project needs.
- **Uploaded data expires after 24h**, by design — job records and parsed
  DataFrames both carry a TTL. There is no long-term transaction store.
- **Amounts are assumed to be USD.** Currency conversion is presentational; the
  data is never rewritten.
