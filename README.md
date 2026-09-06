# Spendline

**Live: <https://spendline-ots2.vercel.app>**

## Summary

Spendline is a full-stack personal finance tool. You upload a CSV of bank
transactions and get a spending breakdown by category, a month by month trend,
and a savings goal simulation, all behind per user accounts with totals
convertible into other currencies at live rates.

It started as my CIS 1912 final project, a FastAPI and React app deployed on
Kubernetes with Helm, Terraform and GitHub Actions. During Spark application
week I extended it with authentication, per user data scoping, an external API
integration, a redesigned animated frontend, and a public deployment.

I planned and directed the work. I set the scope, made the architecture
decisions, and led the debugging. Claude Code did the implementation under that
direction. I verified it two ways: 38 automated backend tests covering the CSV
parser, analytics, simulation, token verification, the boundary between users,
and the rate cache; plus manual browser testing of every interface change. That
manual testing caught real problems, including a decorative background that
added a horizontal scrollbar, a chart line that rendered in disconnected pieces,
and a colour contrast failure on button labels that predated this week. I also
verified the deployed signed in flow end to end by hand.

## Time

Roughly 6 to 7 hours. Git shows 6.4 hours between the first and last commit,
plus assessment and planning beforehand.

The time went to three things. The requested features: Supabase auth with per
user scoping, the currency API, and the landing page animations. Groundwork the
starting repo needed first, since the results chart was an empty placeholder and
there was no working local development setup. And deployment, which surfaced
three bugs that only appear in production: a build misconfiguration, an API path
being swallowed by a routing rule, and a mismatched allowed origin.

## Features

**Frontend: components, animations, responsiveness**

- React 18 with Vite. Components for upload, charts, simulation, authentication,
  dashboard, empty state and error state.
- Recharts spending breakdown and monthly trend. A separate animated preview on
  the landing page built from real sample output.
- Framer Motion for a staggered entrance, a sliding tab indicator, scroll
  triggered reveals, and smoothly expanding message banners.
- Respects the reduced motion setting. Works down to 390px wide. Colour contrast
  was measured on the rendered page, not assumed.

**Backend: authentication, external API, data**

- FastAPI on Python 3.12. Uploads return immediately with a job id and the
  frontend polls for the result.
- Verifies Supabase tokens, supporting both signing methods Supabase uses.
- Each user's jobs are indexed separately in Redis. Requesting another user's
  data returns "not found" rather than "forbidden", so the response cannot
  confirm the record exists.
- Live exchange rates from the Frankfurter API, fetched server side and cached in
  Redis, falling back to the last known rates if the service is unreachable.
- Redis stores job state and parsed data, so backend instances hold nothing
  themselves and can scale freely.

**Full-stack integration**

- The session token is attached to every request automatically, so refreshed
  tokens are picked up without extra work.
- The client rejects responses that are not valid data, and the interface checks
  the shape of what it receives before using it.
- An error boundary shows what went wrong instead of a blank page.

**Deployment**

- Live at <https://spendline-ots2.vercel.app>. Frontend on Vercel, API and Redis
  on Render built from the repo's own Dockerfile, authentication on Supabase.
- The original Kubernetes setup is still in the repo: Helm chart with autoscaling
  and health checks, Terraform, and GitHub Actions.

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

---

## Running it locally

Needs Docker and Node 20 or later.

First create a free Supabase project. Copy the Project URL and publishable key
from Project Settings, API, into `frontend/.env.local`:

```
VITE_SUPABASE_URL=https://<project>.supabase.co
VITE_SUPABASE_ANON_KEY=<publishable key>
```

Set `SUPABASE_URL` in `docker-compose.yml` to the same project URL, then start
both halves:

```
docker compose up -d
cd frontend && npm install && npm run dev
```

Open http://localhost:5173, create an account, confirm it, and sign in. Then use
Try it with sample data under the upload box.

Tests and linting, from the `backend` directory:

```
python -m pytest
ruff check app/ tests/
```

Settings are read from the environment. See `.env.example` for the full list.

## Deploying it

The frontend is a static build, so it goes to Vercel with its root directory set
to `frontend`. The API and Redis go to Render, which reads `render.yaml` and
builds the backend Dockerfile.

Render needs two values entered by hand, `SUPABASE_URL` and `CORS_ORIGINS`. The
rest come from `render.yaml`. Vercel needs three, all prefixed `VITE_`: the
Supabase URL, the Supabase publishable key, and the Render API URL. Those are
compiled into the bundle, so changing one needs a redeploy rather than a
restart.

Deploy the backend first so its URL exists, then the frontend, then set
`CORS_ORIGINS` on Render to the Vercel URL. Also set the Site URL under
Supabase, Authentication, URL Configuration, or confirmation emails will link
somewhere that does not work.

Vercel gives each deployment its own subdomain, which the exact origin list does
not cover. Use the production URL, or set `CORS_ORIGIN_REGEX` on Render.

## Running it on Kubernetes

The original CIS 1912 deployment. Needs Minikube, kubectl, Helm and Terraform.

```
make up
echo "127.0.0.1 spendline.local" | sudo tee -a /etc/hosts
minikube tunnel
```

Then open http://spendline.local. `make status` shows what is running and
`make down` tears it down. The Helm chart, Terraform config and GitHub Actions
workflow are in `helm/`, `terraform/` and `.github/`.

## Known limitations

Accounts need confirming before they can sign in, and Supabase's built-in mailer
allows only a few sends an hour, so a burst of sign-ups will start failing.
Accounts can be confirmed from the Supabase dashboard.

Background jobs run in the web process, so a restart mid-job loses them. A real
queue would fix it, but it is more machinery than this needs.

Uploaded data expires after 24 hours by design. There is no long-term store.

Amounts are assumed to be dollars. Currency conversion is display only and never
rewrites what is stored.
