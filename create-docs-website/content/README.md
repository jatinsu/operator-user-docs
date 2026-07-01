# Cluster Logging Operator Documentation

## Overview

The Cluster Logging Operator (CLO) is a Kubernetes operator for OpenShift that manages log collection, transformation, and forwarding. It deploys Vector as the log collector and supports complex log routing through inputs, outputs, filters, and pipelines defined via the ClusterLogForwarder CRD.

Current version: **6.5.1**

## Key Features

- Collect logs from multiple sources: application containers, infrastructure (journald, system pods), and audit logs (Kubernetes API, OpenShift API, auditd, OVN)
- Forward logs to 13+ destinations: LokiStack, Elasticsearch, Splunk, AWS CloudWatch, Google Cloud Logging, Azure Logs Ingestion, Kafka, Syslog, HTTP, OTLP, S3, Loki, and more
- Filter and transform logs with drop filters, prune filters, multiline exception detection, parse filters, audit policy filters, and custom labels
- Composable pipelines connecting any combination of inputs, filters, and outputs
- Production features: TLS, multiple authentication methods, rate limiting, delivery guarantees (AtLeastOnce/AtMostOnce), compression
- Network policy support for collector pods
- Multi-architecture: amd64, arm64, ppc64le, s390x

## Documentation Index

| Page | Description |
|------|-------------|
| [Getting Started](getting-started.md) | Prerequisites, installation, and first ClusterLogForwarder |
| [Deployment Guide](deployment.md) | How to deploy, upgrade, and remove the operator |
| [Configuration Reference](configuration-reference.md) | Complete reference for all ClusterLogForwarder fields |
| [API Reference](api-reference.md) | CRD spec and status field reference with examples |
| [Troubleshooting](troubleshooting.md) | Common issues, diagnostic commands, and solutions |
| [Examples](examples/) | Example ClusterLogForwarder configurations |

## Architecture Overview

The data flow through the Cluster Logging Operator follows these steps:

1. User creates a ClusterLogForwarder CR defining inputs, outputs, filters, and pipelines.
2. The operator validates the configuration and checks RBAC permissions.
3. The operator generates Vector collector configuration (TOML).
4. Vector is deployed as a DaemonSet (for node/container logs) or Deployment (for network receivers).
5. Vector collects, transforms, and forwards logs to configured destinations.
6. Status conditions report the health of each component.

## Key Concepts

| Concept | Description |
|---------|-------------|
| **ClusterLogForwarder** | The primary CRD for configuring log collection and forwarding |
| **Inputs** | Define what logs to collect (application, infrastructure, audit, receiver) |
| **Outputs** | Define where to send logs (13+ destination types) |
| **Filters** | Transform or filter log records (drop, prune, parse, multiline, audit, labels) |
| **Pipelines** | Connect inputs to outputs through optional filters |
| **ServiceAccount** | Required for collector pod authentication and RBAC |
| **Vector** | The log collector/forwarder engine deployed by the operator |

## Quick Example

A minimal ClusterLogForwarder that forwards application logs to a LokiStack:

```yaml
apiVersion: observability.openshift.io/v1
kind: ClusterLogForwarder
metadata:
  name: collector
  namespace: openshift-logging
spec:
  serviceAccount:
    name: logcollector
  outputs:
    - name: lokistack-out
      type: lokiStack
      lokiStack:
        authentication:
          token:
            from: serviceAccount
        target:
          name: logging-loki
          namespace: openshift-logging
  pipelines:
    - name: app-logs
      inputRefs:
        - application
      outputRefs:
        - lokistack-out
```

## Related Resources

- [OpenShift Logging Documentation](https://docs.openshift.com/container-platform/latest/logging/cluster-logging.html)
- [Vector Documentation](https://vector.dev/docs/)
