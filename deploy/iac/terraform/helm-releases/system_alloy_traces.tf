# ========================================================================
# SYSTEM - GRAFANA ALLOY TRACES DEPLOYMENT
# Receives OTLP traces from instrumented applications (gRPC 4317, HTTP
# 4318), batches them, and forwards to Grafana Cloud Tempo.
# ========================================================================

resource "helm_release" "alloy_traces_release" {
  name       = "alloy-traces"
  repository = "https://grafana.github.io/helm-charts"
  chart      = "alloy"
  namespace  = var.observability_config.namespace
  version    = var.observability_config.alloy.chart_version

  create_namespace = true

  values = [<<-EOT
alloy:
  configMap:
    content: |
      // ================================================================
      // OTLP TRACE RECEIVER
      // Apps send traces to this service via OTLP gRPC/HTTP
      // ================================================================

      otelcol.receiver.otlp "default" {
        grpc {
          endpoint = "0.0.0.0:4317"
        }
        http {
          endpoint = "0.0.0.0:4318"
        }
        output {
          traces = [otelcol.processor.batch.default.input]
        }
      }

      // Batch spans before export to reduce network overhead
      otelcol.processor.batch "default" {
        timeout          = "5s"
        send_batch_size  = 1024
        output {
          traces = [otelcol.exporter.otlp.tempo.input]
        }
      }

      // Export to Grafana Cloud Tempo
      otelcol.exporter.otlp "tempo" {
        client {
          endpoint = "${var.observability_config.endpoints.tempo_endpoint}"
          auth     = otelcol.auth.basic.grafana_cloud.handler
        }
      }

      // Grafana Cloud authentication
      otelcol.auth.basic "grafana_cloud" {
        username = "${var.observability_config.grafana_cloud.instance_id}"
        password = "${var.observability_config.grafana_cloud.api_key}"
      }

  extraPorts:
    - name: otlp-grpc
      port: 4317
      targetPort: 4317
      protocol: TCP
    - name: otlp-http
      port: 4318
      targetPort: 4318
      protocol: TCP

controller:
  type: "deployment"
  replicas: 2
  nodeSelector:
    role: "system"

  resources:
    requests:
      cpu: "${var.observability_config.deployment_resources.requests.cpu}"
      memory: "${var.observability_config.deployment_resources.requests.memory}"
    limits:
      cpu: "${var.observability_config.deployment_resources.limits.cpu}"
      memory: "${var.observability_config.deployment_resources.limits.memory}"

serviceAccount:
  create: true

rbac:
  create: true
EOT
  ]

  depends_on = [
    helm_release.alloy_daemonset_release
  ]
}
