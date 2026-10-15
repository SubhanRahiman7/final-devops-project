# Final demo - run sheet

The rubric's live demo: **commit a change, watch the pipeline run, see the deployment update.** About 10 minutes.

## Before you start (5 minutes, once)

```bash
./scripts/demo-up.sh                 # starts minikube, waits for the pods, opens the port-forwards
kubectl get pods -n helpdesk         # all Running
kubectl get pods -n monitoring       # all Running
```

Open in the browser: the app (http://localhost:3000), the Actions page of the repository, Prometheus targets
(http://localhost:9090/targets), Grafana (http://localhost:3001/d/helpdesk/helpdesk-application-metrics).
Optional, for the Ingress hostname: add `127.0.0.1  helpdesk.local` to `/etc/hosts`, then http://helpdesk.local:8088.

## The demo, step by step

| # | Show | Say |
|---|------|-----|
| 1 | The app at http://localhost:3000; create a ticket; open http://localhost:8000/docs after `docker compose up` or the same API via Swagger | React frontend, FastAPI backend, PostgreSQL; the browser only calls `/api`, nginx / the Ingress route it |
| 2 | `docker compose exec postgres psql -U helpdesk -c 'select id, subject, status from tickets'` (compose) | the data is really in PostgreSQL, schema created by Alembic |
| 3 | **Change:** edit `frontend/src/App.jsx`, line `Track, prioritise and resolve customer tickets.` -> e.g. `Live demo: this text came from a commit.` | a small, visible change |
| 4 | `git add -A && git commit -m "demo: change the dashboard subtitle" && git push` | Git is the trigger for everything |
| 5 | GitHub -> Actions: the run starts. Walk the jobs: pytest, frontend build, Terraform/Helm checks, Gitleaks, **Trivy**, image build, push, kind deploy | the first quality gate is the tests; a failing test stops the pipeline before any image exists |
| 6 | When `Image - frontend` is green: Packages -> `helpdesk-frontend` -> the new tag equals the commit SHA | tags are commit SHAs, never `latest`: production traces back to source |
| 7 | `./scripts/demo-update.sh` (uses `git rev-parse HEAD`) | the same Helm upgrade the pipeline does on kind, against my cluster, with the SHA-tagged images |
| 8 | `kubectl get pods -n helpdesk -w` (rolling update, old pods replaced one at a time), `helm list -n helpdesk`, `kubectl get deploy -n helpdesk -o wide` | rolling update with `maxUnavailable: 0`: no downtime; the image tag is the SHA |
| 9 | Reload http://localhost:3000: **the new subtitle is on the page** | deployment updated |
| 10 | `kubectl get svc,ingress,hpa -n helpdesk`; `./scripts/load-test.sh start 8`; `kubectl get hpa -n helpdesk -w` (2 -> 5 pods); Grafana; `./scripts/load-test.sh stop` | Ingress routes `/` and `/api`; HPA scales on CPU; Prometheus scrapes `/metrics`, Grafana shows it |
| 11 | `kubectl apply -f troubleshooting/broken-service.yaml`, then `get endpoints`, `get pods --show-labels`, patch the selector | a Service selects pods by label; no match = no endpoints = no traffic |

Cleanup after the demo: `kubectl delete ns helpdesk-lab`, `./scripts/demo-up.sh stop`.

## If something is slow or fails

* **The pipeline takes about 4 minutes.** Talk through the Trivy step meanwhile, or show the last green run:
  https://github.com/SubhanRahiman7/final-devops-project/actions
* **A pod is `Unknown` after the laptop slept:** `kubectl -n helpdesk delete pod <name>`; the Deployment replaces it.
* **`demo-update.sh` says the image is not in GHCR yet:** the build job is still running; wait for the green `Image - frontend` job.
* **No network:** `./scripts/demo-update.sh <older-sha>` with a SHA whose images are already pulled still works; or show the
  recorded evidence in `docs/screenshots/`.

## Questions you should be ready for

* **What did Trivy find?** 42 fixable HIGH/CRITICAL vulnerabilities in the old nginx base image (OS packages such as
  libcrypto3), none in my code. Fixed by moving to a current base image and `apk upgrade`; scan is now clean. The pipeline went
  red on three commits before that, so nothing was published - the gate worked. (README, section 6.)
* **Is the Terraform real?** It is complete and valid (VPC, subnets, NAT, EKS + node group, KMS) and was planned, applied and
  destroyed against the Moto AWS emulator because my AWS account is blocked. No real EKS cluster was created; the cluster demo
  runs on minikube and, in CI, on kind.
* **Liveness vs readiness?** `/health` does not touch the database (a DB outage must not restart every pod); `/ready` does (so
  pods leave the Service instead).
* **Why did two replicas seed the database twice?** They started together and both saw an empty table; fixed with PostgreSQL
  advisory locks. (README, section 8.)
* **Why is Grafana open without a login?** Local demo only; stated in the values file and the README.
