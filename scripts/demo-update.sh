#!/usr/bin/env bash
# "See the deployment update": roll the cluster to the images CI built and pushed for a commit.
#   ./scripts/demo-update.sh                 # the commit you are on (git rev-parse HEAD)
#   ./scripts/demo-update.sh <full-sha>      # any commit whose pipeline pushed images
# The GitHub pipeline already deploys to a throw-away kind cluster; this is the same Helm upgrade
# against the local minikube cluster, using the SHA-tagged images from GHCR.
set -euo pipefail
SHA="${1:-$(git rev-parse HEAD)}"
OWNER="${GHCR_OWNER:-subhanrahiman7}"
NS=helpdesk
BE="ghcr.io/$OWNER/helpdesk-backend"; FE="ghcr.io/$OWNER/helpdesk-frontend"

echo "== images for $SHA"
for img in "$BE" "$FE"; do
  docker pull -q "$img:$SHA" >/dev/null || { echo "image $img:$SHA is not in GHCR yet - wait for the pipeline's build job"; exit 1; }
  minikube image load "$img:$SHA"
done

echo "== helm upgrade"
helm upgrade --install helpdesk helm/helpdesk -n "$NS" -f helm/helpdesk/values-dev.yaml \
  --set backend.image.repository="$BE"  --set backend.image.tag="$SHA" \
  --set frontend.image.repository="$FE" --set frontend.image.tag="$SHA" \
  --wait --timeout 5m
kubectl -n "$NS" rollout status deploy/helpdesk-helpdesk-backend
kubectl -n "$NS" rollout status deploy/helpdesk-helpdesk-frontend

echo "== running now"
helm list -n "$NS"
kubectl -n "$NS" get deploy -o custom-columns=NAME:.metadata.name,READY:.status.readyReplicas,IMAGE:.spec.template.spec.containers[0].image
# the rollout replaced the pods that the port-forwards were attached to: open them again
"$(dirname "$0")/demo-up.sh" > /dev/null 2>&1 || true
echo "Reload the browser: http://localhost:3000"
