# HelpDesk - DevOps final capstone

[![CI/CD](https://github.com/SubhanRahiman7/final-devops-project/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/SubhanRahiman7/final-devops-project/actions/workflows/ci-cd.yml)

**Author:** Subhan Rahiman (24BCS10095) - Session 21 final project.

HelpDesk is a small support-ticket system (a SaaS-style dashboard for customer-support teams). Customers raise tickets,
agents prioritise, assign and resolve them, and managers watch the numbers. The application is deliberately modest; the
point of the project is the path it travels - from a laptop to a monitored Kubernetes environment:

```
Developer -> Git/GitHub -> GitHub Actions (pytest, frontend build, Trivy, GHCR) -> Terraform (AWS VPC + EKS)
          -> Helm -> Kubernetes (Ingress, HPA) -> Prometheus + Grafana -> troubleshooting
```

> **Honest notes (please read)**
> * **Terraform** (VPC + EKS) was validated, planned, applied and destroyed against the **Moto AWS emulator**, not real AWS:
>   the AWS account available to me is blocked by an organisation policy. The code is identical for real AWS
>   (`use_local_emulator = false`), but there is **no AWS Console screenshot** and no EKS cluster was ever created in AWS.
> * **Kubernetes, Helm, Ingress, HPA, Prometheus and Grafana** ran on a local **minikube** cluster, not on EKS.
>   The CI pipeline additionally deploys the chart to a throw-away **kind** cluster on every push to `main`.
> * Terminal screenshots are rendered from the real output of the commands; browser screenshots are real captures.

## Contents

[Application](#1-application) | [Run locally](#2-run-it-locally) | [Tests](#3-tests) | [Docker](#4-docker) |
[CI/CD](#5-cicd-pipeline) | [Security](#6-security-scanning-trivy) | [Terraform](#7-terraform-aws-vpc--eks) |
[Kubernetes and Helm](#8-kubernetes-and-helm) | [Ingress and HPA](#9-ingress-and-autoscaling) |
[Monitoring](#10-monitoring) | [Troubleshooting](#11-troubleshooting-labs) | [Repository layout](#12-repository-layout) |
[Demo script](#13-final-demo-script) | [Lessons learned](#14-lessons-learned)

## 1. Application

| Layer | Technology |
|-------|------------|
| Frontend | React 19 + Vite, responsive CSS: dark sidebar, KPI cards, ticket table, status filters, priority badges, activity feed, pipeline panel, create-ticket modal, loading and error states |
| Backend | FastAPI (Python 3.12), SQLAlchemy 2 ORM, Pydantic validation |
| Database | PostgreSQL 16, schema managed by **Alembic** migrations |
| Metrics | `prometheus-fastapi-instrumentator` on `/metrics` |

REST API (Swagger UI at `/docs`):

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | service info |
| GET | `/health` | **liveness** - the process is alive (does not touch the database) |
| GET | `/ready` | **readiness** - answers `READY` only if the database responds (else 503) |
| GET | `/metrics` | Prometheus metrics |
| GET | `/api/tickets` | list tickets (`?status=` and `?priority=` filters) |
| GET | `/api/tickets/{id}` | one ticket |
| POST | `/api/tickets` | create a ticket |
| PUT | `/api/tickets/{id}` | update a ticket |
| DELETE | `/api/tickets/{id}` | delete a ticket |
| GET | `/api/tickets/stats` | totals by status / priority / category, resolution rate, open urgent tickets |

The browser only calls relative URLs (`/api/...`). nginx (Compose) and the Ingress (Kubernetes) route them to the backend,
so the frontend never needs to know an internal hostname.

![dashboard](docs/screenshots/03-app-dashboard.png)
![swagger](docs/screenshots/04-swagger-docs.png)

## 2. Run it locally

**Fastest - Docker Compose** (needs only Docker):

```bash
docker compose up --build        # http://localhost:3000   (API docs: http://localhost:8000/docs)
docker compose down              # add -v to delete the database volume
```

**Backend directly** (Python 3.12+, PostgreSQL):

```bash
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
export DATABASE_URL='postgresql+psycopg://helpdesk:helpdesk@localhost:5432/helpdesk'
alembic upgrade head
SEED_DEMO_DATA=true uvicorn app.main:app --reload --port 8000
```

**Frontend directly:** `cd frontend && npm install && npm run dev` (http://localhost:5173, `/api` is proxied to port 8000).

## 3. Tests

```bash
cd backend && pytest -v          # ruff + 10 tests, coverage gate 85 % (currently 96 %)
```

Tests run on an in-memory SQLite database (the FastAPI `get_db` dependency is overridden in `tests/conftest.py`), never on
the real database. They cover health, readiness (including the 503 path), full CRUD, 404s, validation errors, filters,
statistics, metrics and the seed routine. This is the first quality gate: if a test fails the pipeline stops and no image
is built or pushed.

![pytest](docs/screenshots/01-pytest.png)

## 4. Docker

* [`backend/Dockerfile`](backend/Dockerfile) - Python 3.12-slim, dependencies, Alembic + app code, **non-root user (uid 10001)**,
  `HEALTHCHECK`, runs `alembic upgrade head` and then uvicorn.
* [`frontend/Dockerfile`](frontend/Dockerfile) - **multi-stage**: Node builds `dist/`, a tiny `nginx-unprivileged` image serves it
  (**non-root uid 101**, port 8080). nginx also proxies `/api/` to the backend and exposes `/healthz`.
* [`docker-compose.yml`](docker-compose.yml) - postgres (with healthcheck) -> backend -> frontend on one network.

![compose](docs/screenshots/02-compose-stack.png)

## 5. CI/CD pipeline

[`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml) runs on every push and pull request to `main`:

```
backend-test (ruff + pytest) --+
frontend-build (npm build) ----+--> build-scan-push (matrix: backend, frontend) --> deploy (kind + Helm + smoke test)
validate-infra (terraform, helm,|        build -> Trivy scan -> push to GHCR           only on push to main
  Trivy config scan)            |
secret-scan (Gitleaks) ---------+
```

* Images are tagged with the **full Git commit SHA** (never `latest`): commit A -> image A, which gives traceability from the
  running pod back to the source code.
* Pull requests build and scan but never push or deploy.
* The deploy job pulls the SHA-tagged images from GHCR into a kind cluster, runs `helm upgrade --install`, `helm test` and a
  curl smoke test through the frontend.
* Dependabot (`.github/dependabot.yml`) keeps pip, npm, Docker and Actions dependencies current.

Latest run on `main` - all jobs green: [run #9](https://github.com/SubhanRahiman7/final-devops-project/actions/runs/37806628991)

![run](docs/screenshots/19-github-actions-run.png)

Images in GitHub Container Registry, tagged with commit SHAs
([backend](https://github.com/SubhanRahiman7/final-devops-project/pkgs/container/helpdesk-backend),
[frontend](https://github.com/SubhanRahiman7/final-devops-project/pkgs/container/helpdesk-frontend)):

![ghcr backend](docs/screenshots/22-ghcr-backend-sha-tags.png)
![ghcr frontend](docs/screenshots/23-ghcr-frontend-sha-tags.png)

## 6. Security scanning (Trivy)

| Layer | Control | Where |
|-------|---------|-------|
| Container images | **Trivy** - HIGH/CRITICAL with a fix available fail the build | `build-scan-push`, both images, before the push |
| Infrastructure as code | Trivy config scan of Terraform, Helm templates, manifests, Dockerfiles | `validate-infra` |
| Secrets | Gitleaks over the whole Git history | `secret-scan` |
| Runtime hardening | non-root, read-only root filesystem, dropped capabilities, seccomp `RuntimeDefault`, resource limits | Dockerfiles + Helm chart |

**What Trivy found and what it means.** Scanning the unpatched `nginx-unprivileged:1.27-alpine` base image that the frontend is built on reported **42 HIGH/CRITICAL
vulnerabilities with an available fix**, all in operating-system packages - for example
CVE-2026-31789 (CRITICAL) in `libcrypto3` 3.3.3-r0, fixed in 3.3.7-r0. They were not in the application code: the Alpine base had been published before those fixes. The fix is one line in the Dockerfile (`apk upgrade --no-cache`); the rescanned image has
**0** findings, and so does the backend image. The IaC scan found two real Terraform issues - EKS secrets were not encrypted
(AWS-0039) and the API endpoint defaulted to `0.0.0.0/0` (AWS-0041) - fixed with a KMS key and a variable that has no
default and rejects `0.0.0.0/0`. A clean scan only means *no known fixable* HIGH/CRITICAL CVEs at scan time; it is one
control, not a guarantee. (`--ignore-unfixed` is used so that findings nobody can fix yet do not block releases.)

![trivy](docs/screenshots/24-trivy-scan.png)

## 7. Terraform (AWS VPC + EKS)

[`terraform/`](terraform/) creates 24 resources in `ap-south-1`: a VPC with **two public and two private subnets** in two AZs,
Internet gateway, NAT gateway, route tables, IAM roles for the control plane and the nodes, a KMS key that encrypts Kubernetes
Secrets, the **EKS cluster** and a **managed node group** (2-4 x t3.medium). `terraform.tfvars.example` is provided; the real
`terraform.tfvars` is git-ignored and no credentials are stored anywhere.

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars      # set cluster_public_access_cidrs to your own IP/32
terraform init && terraform plan && terraform apply
aws eks update-kubeconfig --region ap-south-1 --name helpdesk-eks
terraform destroy                                  # EKS + NAT cost money
```

Rehearsal without an AWS account (what the screenshots show): `docker run -d -p 5001:5000 -e MOTO_IAM_LOAD_MANAGED_POLICIES=true motoserver/moto`
and `terraform apply -var-file=local-emulator.tfvars` - the same code against a local AWS emulator. After apply the AWS
API (emulator) was queried to confirm 1 VPC, 4 subnets, 1 NAT and 1 internet gateway, the cluster and the node group; `destroy`
removed all 24 resources and the state was empty.

![validate](docs/screenshots/15-terraform-init-validate.png)
![plan](docs/screenshots/16-terraform-plan.png)
![apply](docs/screenshots/17-terraform-apply-verify.png)
![destroy](docs/screenshots/18-terraform-destroy.png)

## 8. Kubernetes and Helm

[`k8s/namespace.yaml`](k8s/namespace.yaml) creates namespace `helpdesk`. The Helm chart [`helm/helpdesk`](helm/helpdesk) deploys:

| Object | Details |
|--------|---------|
| backend Deployment + ClusterIP Service | 2+ replicas, `startup`/`readiness (/ready)`/`liveness (/health)` probes, requests/limits, non-root, read-only root fs, init container that waits for PostgreSQL |
| frontend Deployment + ClusterIP Service | 2 replicas, probes on `/healthz`, non-root, read-only root fs |
| PostgreSQL StatefulSet + Service + PVC | `pg_isready` probes, runs as the `postgres` user (70), data on a PersistentVolumeClaim |
| Secret | database password: generated on first install and kept stable across upgrades, or an `existingSecret` (used by `values-prod.yaml`) |
| Ingress, HPA, PodDisruptionBudget | see next section |
| ServiceMonitor | tells the Prometheus Operator what to scrape (enabled in dev/prod values) |
| `helm test` | a pod that calls `/ready`, the stats API, the frontend page and the API through nginx |

`values.yaml` holds the defaults; `values-dev.yaml` (local images, `helpdesk.local`) and `values-prod.yaml` (3 replicas,
bigger limits, external Secret, `helpdesk.example.com`) override them.

```bash
kubectl apply -f k8s/namespace.yaml
docker build -t helpdesk-backend:dev ./backend && docker build -t helpdesk-frontend:dev ./frontend
minikube image load helpdesk-backend:dev helpdesk-frontend:dev
helm upgrade --install helpdesk ./helm/helpdesk -n helpdesk -f helm/helpdesk/values-dev.yaml --wait
helm list -n helpdesk && kubectl get pods,svc,ingress,hpa -n helpdesk && helm test helpdesk -n helpdesk
```

![kubernetes and helm](docs/screenshots/05-kubernetes-helm.png)

Two real bugs found on the way, both fixed and committed:
* **Duplicate demo data:** two backend replicas starting together both saw an empty table and both seeded it (14 rows instead of 7).
  Fixed with PostgreSQL advisory locks around the seed and the Alembic migration, so replicas serialise.
* **PostgreSQL crash loop:** with all capabilities dropped the official image could not `chown` its data directory. Fixed by
  running the pod as the `postgres` user (uid 70, `fsGroup` 70) instead of root.

## 9. Ingress and autoscaling

The Ingress (`ingressClassName: nginx`, host `helpdesk.local`) routes **`/api` -> backend** and **`/` -> frontend**. An Ingress is
only configuration; the ingress-nginx controller (minikube addon) implements it.

![app via ingress](docs/screenshots/06-app-via-ingress.png)

**HPA:** the backend scales between 2 and 5 pods at 60 % CPU (`scripts/load-test.sh start 8` starts eight busybox pods that call
the API in a loop). CPU rose to 339 % of the requested value, the replicas went 2 -> 4 -> 5 (the maximum) and the extra pods
became Ready. (The very first reading, 63 %, is the tail of an earlier traffic test I had just run through the Ingress.)

![hpa](docs/screenshots/11-hpa-scale-out.png)

## 10. Monitoring

[`monitoring/prometheus-values.yaml`](monitoring/prometheus-values.yaml) configures **kube-prometheus-stack** (Prometheus,
Grafana, kube-state-metrics, node-exporter). Prometheus scrapes the backend through the chart's **ServiceMonitor**; the Grafana
dashboard ([`monitoring/dashboards/helpdesk.json`](monitoring/dashboards/helpdesk.json)) is loaded from a labelled ConfigMap;
[`monitoring/alert-rules.yaml`](monitoring/alert-rules.yaml) defines three alerts (backend down, 5xx error rate > 5 %, p95 latency > 1 s).

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack -n monitoring --create-namespace \
  -f monitoring/prometheus-values.yaml
kubectl apply -f monitoring/dashboard-configmap.yaml -f monitoring/alert-rules.yaml
kubectl -n monitoring port-forward svc/monitoring-prometheus 9090:9090      # Prometheus
kubectl -n monitoring port-forward svc/monitoring-grafana 3001:80           # Grafana
```

The Grafana values enable anonymous access **for this local demo only**; never do that on a shared cluster.

![metrics](docs/screenshots/07-metrics-endpoint.png)
![targets](docs/screenshots/08-prometheus-targets.png)
![promql](docs/screenshots/09-prometheus-query.png)
![grafana](docs/screenshots/10-grafana-dashboard.png)
![grafana under load](docs/screenshots/12-grafana-under-load.png)

## 11. Troubleshooting labs

Full write-up: [troubleshooting/README.md](troubleshooting/README.md).

| Lab | Symptom | Investigation | Root cause | Fix |
|-----|---------|---------------|-----------|-----|
| [broken-image.yaml](troubleshooting/broken-image.yaml) | `ErrImagePull` -> `ImagePullBackOff` | `get pods`, `describe pod` (Events), `get events` | the image tag does not exist | `kubectl set image ...` with a real tag |
| [broken-service.yaml](troubleshooting/broken-service.yaml) | pods Running, Service unreachable | `get svc`, `get endpoints` (`<none>`), `get pods --show-labels` | Service selector `app=lab-backend`, pods are `app=lab-api` | fix the selector |

(In lab 1 the minikube DNS was flaky, so the pull error text reads `lookup ... server misbehaving` rather than `not found`; the tag
is nevertheless the cause, as the fix proves.)

![lab1](docs/screenshots/13-troubleshoot-broken-image.png)
![lab2](docs/screenshots/14-troubleshoot-broken-service.png)

## 12. Repository layout

```
backend/          FastAPI app (app/), tests/, alembic/ migrations, Dockerfile
frontend/         React + Vite source, nginx template, multi-stage Dockerfile
docker-compose.yml  full local stack
terraform/        AWS VPC + EKS (+ KMS), tfvars example
helm/helpdesk/    chart: templates, values, values-dev, values-prod
k8s/              namespace manifest
monitoring/       Prometheus/Grafana values, dashboard, alert rules
troubleshooting/  deliberately broken manifests + write-up
scripts/          load-test.sh (HPA demo)
.github/          CI/CD workflow, Dependabot
docs/screenshots/ evidence
```

## 13. Final demo script

1. `docker compose up --build` -> open http://localhost:3000, create a ticket; open `/docs` and call the API.
2. `docker compose exec postgres psql -U helpdesk -c 'select * from tickets'`.
3. Change something small, `git commit`, `git push` -> watch the Actions run (tests, Trivy, GHCR, kind deploy).
4. Show the SHA-tagged images in GHCR and the Trivy step.
5. Show `terraform/` and the plan/apply/destroy evidence.
6. `kubectl get pods,svc,ingress,hpa -n helpdesk`, `helm list -n helpdesk`, open http://helpdesk.local.
7. `./scripts/load-test.sh start 8` -> watch `kubectl get hpa -n helpdesk -w`; show Grafana.
8. Break a Service or image with the troubleshooting labs and fix it live.

## 14. Lessons learned

* **Gates find real problems.** Trivy caught 42 fixable CVEs in a base image I trusted and two Terraform misconfigurations
  I would not have noticed by reading the code.
* **Replicas race.** Anything that runs on start-up (migrations, seeding) must be safe when several replicas start together.
* **Hardening has consequences.** Dropping all capabilities broke the PostgreSQL image's start-up until it ran as the right user.
* **Readiness is not liveness.** `/health` must not depend on the database, `/ready` must - otherwise a database outage restarts
  every pod instead of just removing them from the Service.
* **Autoscaling needs requests and a metrics source**, and a load generator strong enough to move the numbers.
* **Reproduce CI locally first** (`ruff`, `pytest`, `helm lint`, `trivy`, `terraform validate`) - most failures were found in seconds.
* **Be explicit about what was and was not run in real AWS.**
