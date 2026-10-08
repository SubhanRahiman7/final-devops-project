# Troubleshooting labs

Two deliberately broken manifests. Apply one, investigate with `kubectl`, find the root cause, fix it, verify.

## Lab 1 - broken image (`broken-image.yaml`)

```bash
kubectl apply -f troubleshooting/broken-image.yaml
kubectl get pods -n helpdesk-lab                       # ErrImagePull -> ImagePullBackOff
kubectl describe pod <pod-name> -n helpdesk-lab        # read the Events section
kubectl get events -n helpdesk-lab --sort-by=.lastTimestamp
```

* **Symptom:** the Pod never becomes `Ready`; status `ErrImagePull`, then `ImagePullBackOff`.
* **Investigation:** `describe` shows *Failed to pull image `...:1.27-alpine-does-not-exist`*.
* **Root cause:** the Deployment references an image tag that was never published.
  (On this minikube the registry lookup message was `server misbehaving`, i.e. a flaky DNS answer for the registry host; the
  Deployment is still the cause - the tag does not exist. With a healthy network the message is `manifest unknown / not found`.)
* **Fix:** `kubectl set image deployment/lab-web web=nginxinc/nginx-unprivileged:1.27-alpine -n helpdesk-lab`
* **Verify:** `kubectl get pods -n helpdesk-lab` shows `1/1 Running`.

![lab 1](../docs/screenshots/13-troubleshoot-broken-image.png)

## Lab 2 - broken Service (`broken-service.yaml`)

```bash
kubectl apply -f troubleshooting/broken-service.yaml
kubectl get svc -n helpdesk-lab
kubectl get endpoints -n helpdesk-lab                  # lab-api   <none>
kubectl get pods -n helpdesk-lab --show-labels
```

* **Symptom:** both Pods are `Running 1/1`, but requests to the Service hang; the Service has **no endpoints**.
* **Investigation:** the Service selector is `app=lab-backend`, the Pods carry `app=lab-api`.
* **Root cause:** a Service sends traffic only to Pods whose labels match its selector. No match = no endpoints = no traffic.
* **Fix:** `kubectl patch svc lab-api -n helpdesk-lab -p '{"spec":{"selector":{"app":"lab-api"}}}'`
* **Verify:** `kubectl get endpoints lab-api` lists both Pod IPs and a request returns the nginx page.

![lab 2](../docs/screenshots/14-troubleshoot-broken-service.png)

Clean up: `kubectl delete ns helpdesk-lab`.
