#!/usr/bin/env bash
# Brings the local demo environment up (minikube, HelpDesk, monitoring) and opens the port-forwards.
#   ./scripts/demo-up.sh          start / check everything and print the URLs
#   ./scripts/demo-up.sh stop     stop the port-forwards
set -euo pipefail
PIDFILE=/tmp/helpdesk-demo-portforwards.pid

if [ "${1:-}" = "stop" ]; then
  [ -f "$PIDFILE" ] && xargs kill < "$PIDFILE" 2>/dev/null || true
  rm -f "$PIDFILE"; echo "port-forwards stopped"; exit 0
fi

if ! minikube status >/dev/null 2>&1; then
  echo "starting minikube ..."; minikube start
fi
echo "waiting for the HelpDesk pods ..."
kubectl -n helpdesk wait --for=condition=Ready pod -l app.kubernetes.io/instance=helpdesk \
  --field-selector=status.phase=Running --timeout=300s >/dev/null || true
kubectl -n helpdesk get pods

[ -f "$PIDFILE" ] && xargs kill < "$PIDFILE" 2>/dev/null || true
: > "$PIDFILE"
pf() { kubectl "$@" >/dev/null 2>&1 & echo $! >> "$PIDFILE"; }
pf -n ingress-nginx port-forward svc/ingress-nginx-controller 8088:80
pf -n helpdesk port-forward svc/helpdesk-helpdesk-frontend 3000:80
pf -n monitoring port-forward svc/monitoring-prometheus 9090:9090
pf -n monitoring port-forward svc/monitoring-grafana 3001:80
sleep 2
cat <<MSG

  App (frontend service)   http://localhost:3000
  App via the Ingress      http://helpdesk.local:8088   (needs "127.0.0.1 helpdesk.local" in /etc/hosts)
  Prometheus targets       http://localhost:9090/targets
  Grafana dashboard        http://localhost:3001/d/helpdesk/helpdesk-application-metrics
  Stop the forwards        ./scripts/demo-up.sh stop
MSG
