# Spendline

**Live: <https://spendline-ots2.vercel.app>**

Upload a CSV of bank transactions and get a spending breakdown, a month-by-month
trend, and a savings simulation — behind per-user accounts, with totals viewable
in a second currency.

Built for CIS 1912 as a Kubernetes deployment, then extended with
authentication, a live external API, and a motion pass on the landing page.

| Piece | Where it runs |
|---|---|
| Frontend | Vercel — <https://spendline-ots2.vercel.app> |
| API + Redis | Render — <https://spendline-api.onrender.com> |
| Auth | Supabase |

> Render's free tier sleeps after inactivity, so the first request after a quiet
> spell takes ~30s to wake. If the page seems to hang on first load, that's why.

## How to try it

1. Open <https://spendline-ots2.vercel.app>, create an account, confirm it using
   the emailed link, and sign in.
2. Click **Try it with sample data** under the upload box. This uses
   [`sample-data/sample_transactions.csv`](sample-data/sample_transactions.csv)
   from this repo. You can also drag that file in yourself.
3. Change the currency in the top right.
4. Run a simulation, then sign out.

The API sleeps when idle on the free plan, so the first action after signing in
can take about 30 seconds.

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

## Features included

Mapped to the assessment's suggested criteria.

**Frontend**
- Components: upload, charts, simulation, authentication, dashboard, empty state, error state
- Animations: staggered entrance, sliding tab indicator, scroll-triggered reveals, expanding message banners, all respecting the reduced motion setting
- Mobile responsiveness: works down to 390px wide, with no sideways scrolling

**Backend**
- Registration, login and logout through Supabase; the backend verifies tokens and never handles a password
- API calls: live exchange rates from the Frankfurter API, fetched server-side and cached
- Data layer: Redis holds job state, parsed transaction data, and a per-user index, so each account only ever sees its own uploads
- Classes and objects: a job store interface with Redis and in-memory implementations, so tests run without a server

**Full-stack**
- React frontend against a FastAPI backend, with tokens attached to every request automatically
- Asynchronous job handling: uploads return straight away and the frontend polls for the result

**Deployment**
- Live on Vercel and Render, with authentication on Supabase
- Also deployable to Kubernetes with the Helm chart and Terraform in this repo
- 38 backend tests and linting run in GitHub Actions on every push

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

Minikube can't hand out a public URL, so the hosted split is:

- **Backend + Redis → Render.** It builds `backend/Dockerfile` directly, so the
  container in production is the one that runs locally.
- **Frontend → Vercel.** A static bundle on a CDN, free.
- **Auth → Supabase**, already hosted.

### Environment variables

**Render — backend.** Everything below maps to a field on `Settings` in
`backend/app/config.py`; pydantic-settings reads each one from the uppercased
field name.

| Variable | Required | Value / where it comes from | Entry |
|---|---|---|---|
| `SUPABASE_URL` | **Yes** | Supabase → Project Settings → API → **Project URL** | **Manual** (`sync: false`) |
| `CORS_ORIGINS` | **Yes** | Your Vercel origin, e.g. `https://spendline-ots2.vercel.app`. Comma-separated for more than one | **Manual** (`sync: false`) |
| `CORS_ORIGIN_REGEX` | No | Covers every Vercel URL for the project at once, including the per-deployment subdomains an exact list misses: `https://spendline-ots2(-[a-z0-9-]+)?\.vercel\.app`. Keep it anchored | **Manual** |
| `AUTH_ENABLED` | **Yes** | `true` | Auto — set in `render.yaml` |
| `USE_REDIS` | **Yes** | `true` | Auto — set in `render.yaml` |
| `REDIS_HOST` | **Yes** | The Redis instance's host | Auto — `fromService` |
| `REDIS_PORT` | **Yes** | The Redis instance's port | Auto — `fromService` |
| `SUPABASE_JWT_SECRET` | **No — leave unset** | Only for legacy HS256 projects. This project's Supabase signs **ES256** and publishes a JWKS, which needs no secret. Setting it forces the wrong verification path and breaks every login | — |
| `SERVICE_NAME` | No | Defaults to `spendline-backend` | — |
| `JOB_TTL_SECONDS` | No | Defaults to `86400` (24h) | — |
| `DEV_USER_ID` | No | Only read when `AUTH_ENABLED=false` | — |

So on Render you type in **two values**: `SUPABASE_URL` and `CORS_ORIGINS`.

**Vercel — frontend.** These are every `import.meta.env` reference in `src/`;
there are no others.

| Variable | Value / where it comes from |
|---|---|
| `VITE_SUPABASE_URL` | Supabase → Project Settings → API → **Project URL** |
| `VITE_SUPABASE_ANON_KEY` | Supabase → Project Settings → API → **publishable key** (`sb_publishable_…`). Safe to expose; it ships in the bundle. Never the `service_role` / secret key |
| `VITE_API_URL` | Your Render URL, e.g. `https://spendline-api.onrender.com` |

`VITE_*` values are baked in at build time, so changing one needs a **redeploy**,
not a restart.

### Build settings

**Render** needs none. `render.yaml` declares `runtime: docker`, so Render builds
`backend/Dockerfile` with `./backend` as context and runs the image's own `CMD`:

```
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Health checks hit `/health`. Don't set a build or start command in the
dashboard — a Docker service takes both from the image.

**Vercel** reads `frontend/vercel.json`, but set the **Root Directory** to
`frontend` when importing, or the build runs at the repo root and finds no app.
If auto-detection misfires, these are the values:

| Setting | Value |
|---|---|
| Framework Preset | Vite |
| Root Directory | `frontend` |
| Install Command | `npm ci` |
| Build Command | `npm run build` |
| Output Directory | `dist` |

### Deployment order

There's a circular dependency — the frontend needs the backend's URL, and the
backend needs the frontend's origin for CORS — but it isn't a deadlock, because
both platforms give predictable URLs (`https://<name>.onrender.com`,
`https://<project>.vercel.app`). Backend first, then frontend, then one CORS
touch-up.

1. **Push to GitHub.** Both platforms deploy from git.
2. **Supabase → Authentication → URL Configuration → Site URL.** Set it to your
   Vercel URL, and add it under **Redirect URLs**. Confirmation and recovery
   emails link to the Site URL — leave it at `localhost` and every emailed link
   in production points at a machine the recipient doesn't have.
3. **Render → New → Blueprint**, point at the repo. It reads `render.yaml` and
   creates the web service plus Redis. Enter `SUPABASE_URL`, and
   `CORS_ORIGINS` set to the Vercel URL you expect in step 5.
4. **Wait for the first deploy**, then confirm the real Render URL and that
   `https://<render-url>/health` returns `{"status":"ok",…}`.
5. **Vercel → Add New → Project**, import the repo, **Root Directory =
   `frontend`**. Add the three `VITE_*` variables using the real Render URL from
   step 4. Deploy.
6. **Confirm the real Vercel URL.** If it differs from what you guessed in step
   3, update `CORS_ORIGINS` on Render and redeploy the backend.
7. **Smoke test:** sign up, confirm the account, upload the sample CSV, toggle
   the currency, sign out.

### Manual dashboard settings not captured in any config file

- **Supabase → Authentication → URL Configuration → Site URL** — step 2 above.
  The single most common reason a deployed Supabase app "works but nobody can
  log in".
- **Supabase → Authentication → Sign In / Providers → Email → Confirm email.**
  Left on, the built-in mailer allows only a few sends per hour and bounces
  count against the project, so a handful of sign-ups in one session will start
  failing with `over_email_send_rate_limit`. Turning it off needs no SMTP.
  Leaving it on means confirming each account by hand under **Authentication →
  Users**.
- **Vercel gives every deployment its own subdomain**, which the production
  origin in `CORS_ORIGINS` does not cover — opening a build from Vercel's
  dashboard rather than the production alias fails CORS on every request. Set
  `CORS_ORIGIN_REGEX` to cover them all, or stick to the production URL.
- **Render's free tier sleeps** after inactivity; the first request afterwards
  takes ~30s. Worth warming before a demo.

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

## How this was built

I planned and directed the work: I set the scope, made the architecture
decisions, and led the debugging. Claude Code did the implementation under that
direction.

It was verified two ways. There are 38 automated backend tests covering the CSV
parser, analytics, simulation, token verification, the boundary between users,
and the rate cache. Every interface change was also tested by hand in a browser,
which is what caught the problems that tests would not: a decorative background
that added a horizontal scrollbar, a chart line that rendered in disconnected
pieces, and a colour contrast failure on button labels that predated this work.
The deployed signed-in flow was verified end to end by hand.

## Time

Roughly 6 to 7 hours. Git shows 6.4 hours between the first and last commit,
plus assessment and planning beforehand.

The time went to three things. The requested features: Supabase auth with
per-user scoping, the currency API, and the landing page animations. Groundwork
the starting repo needed first, since the results chart was an empty placeholder
and there was no working local development setup. And deployment, which
surfaced three bugs that only appear in production: a build misconfiguration, an
API path being swallowed by a routing rule, and a mismatched allowed origin.

## Known limitations

- **Accounts must be confirmed before they can sign in.** Supabase's email
  confirmation is left on, and the built-in mailer allows only a few sends an
  hour, so a burst of sign-ups will start failing. For a walkthrough with more
  than a couple of people, confirm accounts under Supabase → Authentication →
  Users, or turn confirmation off there.
- **Background jobs aren't durable.** They run in-process via FastAPI
  `BackgroundTasks`, so a pod restart mid-job orphans it. A real queue (Celery,
  RQ, arq) would fix it; it's more machinery than this project needs.
- **Uploaded data expires after 24h**, by design — job records and parsed
  DataFrames both carry a TTL. There is no long-term transaction store.
- **Amounts are assumed to be USD.** Currency conversion is presentational; the
  stored data is never rewritten.
