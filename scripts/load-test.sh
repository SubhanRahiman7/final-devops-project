#!/usr/bin/env bash
# Controlled load generator for the HPA demo.
# Starts N busybox pods that call the backend Service in a loop, then prints the HPA every 15 s.
#   ./scripts/load-test.sh start [N] [namespace]   # default: 8 pods, namespace helpdesk
#   ./scripts/load-test.sh watch                   # follow the HPA
#   ./scripts/load-test.sh stop                    # delete the load pods
set -euo pipefail
NS="${3:-helpdesk}"
SVC="${BACKEND_SERVICE:-helpdesk-helpdesk-backend}"
case "${1:-}" in
  start)
    for i in $(seq 1 "${2:-8}"); do
      kubectl -n "$NS" run "load-$i" --image=busybox:1.36 --restart=Never --labels=purpose=loadtest -- \
        /bin/sh -c "while true; do wget -q -O- http://$SVC:8000/api/tickets > /dev/null; done"
    done ;;
  watch) kubectl -n "$NS" get hpa -w ;;
  stop)  kubectl -n "$NS" delete pod -l purpose=loadtest --now ;;
  *) echo "usage: $0 start [N] [namespace] | watch | stop"; exit 1 ;;
esac
