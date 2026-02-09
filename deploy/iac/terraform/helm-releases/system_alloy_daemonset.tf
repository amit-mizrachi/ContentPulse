# ========================================================================
# SYSTEM - GRAFANA ALLOY DAEMONSET
# Collects container logs (all namespaces) and K8s metrics (kubelet,
# cadvisor, kube-state-metrics). Ships to Grafana Cloud.
# ========================================================================

resource "helm_release" "alloy_daemonset_release" {
  name       = "alloy-logs-metrics"
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
      // LOG COLLECTION (all namespaces)
      // ================================================================

      // Discover pods on this node only
      discovery.kubernetes "pods" {
        role = "pod"
        selectors {
          role  = "pod"
          field = "spec.nodeName=" + env("HOSTNAME")
        }
      }

      // Extract K8s metadata labels
      discovery.relabel "pod_logs" {
        targets = discovery.kubernetes.pods.targets

        rule {
          source_labels = ["__meta_kubernetes_namespace"]
          target_label  = "namespace"
        }
        rule {
          source_labels = ["__meta_kubernetes_pod_name"]
          target_label  = "pod"
        }
        rule {
          source_labels = ["__meta_kubernetes_pod_container_name"]
          target_label  = "container"
        }
        rule {
          source_labels = ["__meta_kubernetes_pod_label_app"]
          target_label  = "app"
        }
        rule {
          source_labels = ["__meta_kubernetes_pod_node_name"]
          target_label  = "node"
        }

        // Construct log file path on the node host
        rule {
          source_labels = ["__meta_kubernetes_pod_uid", "__meta_kubernetes_pod_container_name"]
          target_label  = "__path__"
          separator     = "/"
          replacement   = "/var/log/pods/*$1/*.log"
        }
      }

      // Tail log files from the node filesystem (performant, no API overhead)
      loki.source.file "pod_logs" {
        targets    = discovery.relabel.pod_logs.output
        forward_to = [loki.process.pod_logs.receiver]
      }

      // Parse CRI format, then extract structured fields from JSON logs
      loki.process "pod_logs" {
        forward_to = [loki.write.grafana_cloud.receiver]

        // Parse CRI log wrapper (containerd/CRI-O format)
        stage.cri {}

        // Parse JSON structured logs (simple_sport_news services emit JSON to stdout)
        stage.json {
          expressions = {
            level        = "level",
            trace_id     = "trace_id",
            span_id      = "span_id",
            service_name = "service_name",
            log_type     = "log_type",
          }
        }

        // Promote key fields to Loki labels for efficient filtering
        stage.labels {
          values = {
            level        = "",
            service_name = "",
            log_type     = "",
          }
        }

        // Store trace correlation IDs as structured metadata (Loki 3.x+)
        stage.structured_metadata {
          values = {
            trace_id = "",
            span_id  = "",
          }
        }
      }

      // Ship logs to Grafana Cloud Loki
      loki.write "grafana_cloud" {
        endpoint {
          url = "${var.observability_config.endpoints.loki_url}"
          basic_auth {
            username = "${var.observability_config.grafana_cloud.instance_id}"
            password = "${var.observability_config.grafana_cloud.api_key}"
          }
        }
      }

      // ================================================================
      // KUBERNETES NODE METRICS (kubelet + cadvisor)
      // ================================================================

      discovery.kubernetes "nodes" {
        role = "node"
      }

      // Kubelet metrics
      discovery.relabel "kubelet" {
        targets = discovery.kubernetes.nodes.targets
        rule {
          target_label = "__address__"
          replacement  = "kubernetes.default.svc:443"
        }
        rule {
          source_labels = ["__meta_kubernetes_node_name"]
          regex         = "(.+)"
          target_label  = "__metrics_path__"
          replacement   = "/api/v1/nodes/$1/proxy/metrics"
        }
      }

      prometheus.scrape "kubelet" {
        targets = discovery.relabel.kubelet.output
        scheme  = "https"
        tls_config {
          ca_file              = "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"
          insecure_skip_verify = true
        }
        bearer_token_file = "/var/run/secrets/kubernetes.io/serviceaccount/token"
        forward_to        = [prometheus.remote_write.grafana_cloud.receiver]
      }

      // cadvisor metrics (container resource usage)
      discovery.relabel "cadvisor" {
        targets = discovery.kubernetes.nodes.targets
        rule {
          target_label = "__address__"
          replacement  = "kubernetes.default.svc:443"
        }
        rule {
          source_labels = ["__meta_kubernetes_node_name"]
          regex         = "(.+)"
          target_label  = "__metrics_path__"
          replacement   = "/api/v1/nodes/$1/proxy/metrics/cadvisor"
        }
      }

      prometheus.scrape "cadvisor" {
        targets = discovery.relabel.cadvisor.output
        scheme  = "https"
        tls_config {
          ca_file              = "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"
          insecure_skip_verify = true
        }
        bearer_token_file = "/var/run/secrets/kubernetes.io/serviceaccount/token"
        forward_to        = [prometheus.remote_write.grafana_cloud.receiver]
      }

      // ================================================================
      // KUBE-STATE-METRICS (cluster-level object metrics)
      // ================================================================

      discovery.kubernetes "kube_state_metrics" {
        role = "service"
        selectors {
          role  = "service"
          label = "app.kubernetes.io/name=kube-state-metrics"
        }
      }

      prometheus.scrape "kube_state_metrics" {
        targets    = discovery.kubernetes.kube_state_metrics.targets
        job_name   = "kube-state-metrics"
        forward_to = [prometheus.remote_write.grafana_cloud.receiver]
      }

      // Ship metrics to Grafana Cloud Prometheus (Mimir)
      prometheus.remote_write "grafana_cloud" {
        endpoint {
          url = "${var.observability_config.endpoints.prometheus_remote_write_url}"
          basic_auth {
            username = "${var.observability_config.grafana_cloud.instance_id}"
            password = "${var.observability_config.grafana_cloud.api_key}"
          }
        }
      }

controller:
  type: "daemonset"

  tolerations:
    - operator: "Exists"

  volumes:
    extra:
      - name: varlogpods
        hostPath:
          path: /var/log/pods

  volumeMounts:
    extra:
      - name: varlogpods
        mountPath: /var/log/pods
        readOnly: true

  resources:
    requests:
      cpu: "${var.observability_config.daemonset_resources.requests.cpu}"
      memory: "${var.observability_config.daemonset_resources.requests.memory}"
    limits:
      cpu: "${var.observability_config.daemonset_resources.limits.cpu}"
      memory: "${var.observability_config.daemonset_resources.limits.memory}"

serviceAccount:
  create: true

rbac:
  create: true
EOT
  ]

  depends_on = [
    helm_release.metrics_server_release,
    helm_release.kube_state_metrics_release
  ]
}
