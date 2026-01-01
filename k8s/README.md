# Kubernetes Deployment

Helm chart for deploying Synth Mind to Kubernetes.

## Prerequisites

- Kubernetes 1.23+
- Helm 3.8+
- PV provisioner (for persistence)
- Ingress controller (optional)

## Quick Start

```bash
# Add secrets first
kubectl create secret generic synth-mind-secrets \
  --from-literal=ANTHROPIC_API_KEY=your-key-here

# Install the chart
helm install synth-mind ./k8s/synth-mind

# With custom values
helm install synth-mind ./k8s/synth-mind -f my-values.yaml
```

## Configuration

### Essential Values

```yaml
# values-production.yaml
replicaCount: 2

image:
  repository: ghcr.io/synth-mind/synth-mind
  tag: "1.7.0"

envFrom:
  - secretRef:
      name: synth-mind-secrets

persistence:
  enabled: true
  size: 5Gi
  storageClass: "gp3"

ingress:
  enabled: true
  className: "nginx"
  hosts:
    - host: synth.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: synth-tls
      hosts:
        - synth.example.com

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
```

### Secret Configuration

Create a secret with your LLM API key:

```bash
# Using kubectl
kubectl create secret generic synth-mind-secrets \
  --from-literal=ANTHROPIC_API_KEY=sk-ant-xxx

# Or from a file
kubectl create secret generic synth-mind-secrets \
  --from-env-file=.env.production
```

### Available Values

| Parameter | Description | Default |
|-----------|-------------|---------|
| `replicaCount` | Number of replicas | `1` |
| `image.repository` | Container image | `ghcr.io/synth-mind/synth-mind` |
| `image.tag` | Image tag | `latest` |
| `service.type` | Service type | `ClusterIP` |
| `service.port` | Service port | `8080` |
| `ingress.enabled` | Enable ingress | `false` |
| `persistence.enabled` | Enable PVC | `true` |
| `persistence.size` | PVC size | `1Gi` |
| `autoscaling.enabled` | Enable HPA | `false` |
| `resources.limits.memory` | Memory limit | `2Gi` |
| `resources.limits.cpu` | CPU limit | `2000m` |

## Installation Examples

### Development

```bash
helm install synth-dev ./k8s/synth-mind \
  --set image.tag=latest \
  --set persistence.enabled=false \
  --set resources.limits.memory=512Mi
```

### Production (Single Instance)

```bash
helm install synth-prod ./k8s/synth-mind \
  --set image.tag=1.7.0 \
  --set persistence.enabled=true \
  --set persistence.size=10Gi \
  --set envFrom[0].secretRef.name=synth-mind-secrets
```

### Production (HA with Ingress)

```bash
helm install synth-prod ./k8s/synth-mind \
  -f values-production.yaml
```

## Monitoring

### Prometheus ServiceMonitor

```yaml
# Enable ServiceMonitor for Prometheus Operator
serviceMonitor:
  enabled: true
  interval: 15s
  labels:
    release: prometheus
```

### Pod Annotations (Default)

Pods are annotated for Prometheus scraping:

```yaml
prometheus.io/scrape: "true"
prometheus.io/port: "8080"
prometheus.io/path: "/metrics"
```

## Upgrading

```bash
# Update values
helm upgrade synth-mind ./k8s/synth-mind -f values.yaml

# Rollback if needed
helm rollback synth-mind 1
```

## Uninstalling

```bash
helm uninstall synth-mind

# Note: PVC is not deleted automatically
kubectl delete pvc synth-mind-state
```

## Troubleshooting

### Pod Not Starting

```bash
kubectl describe pod -l app.kubernetes.io/name=synth-mind
kubectl logs -l app.kubernetes.io/name=synth-mind
```

### Health Check Failures

```bash
# Check endpoints directly
kubectl port-forward svc/synth-mind 8080:8080
curl http://localhost:8080/health
```

### Persistence Issues

```bash
# Check PVC status
kubectl get pvc
kubectl describe pvc synth-mind-state
```

## Architecture

```
                    ┌──────────────┐
                    │   Ingress    │
                    │  (optional)  │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │   Service    │
                    │  (ClusterIP) │
                    └──────┬───────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
    ┌─────▼─────┐    ┌─────▼─────┐    ┌─────▼─────┐
    │   Pod 1   │    │   Pod 2   │    │   Pod N   │
    │ Synth Mind│    │ Synth Mind│    │ Synth Mind│
    └─────┬─────┘    └─────┬─────┘    └─────┬─────┘
          │                │                │
          └────────────────┼────────────────┘
                           │
                    ┌──────▼───────┐
                    │     PVC      │
                    │ (SharedState)│
                    └──────────────┘
```

**Note:** For multi-replica deployments, consider using a shared database (PostgreSQL) instead of SQLite with shared PVC.
