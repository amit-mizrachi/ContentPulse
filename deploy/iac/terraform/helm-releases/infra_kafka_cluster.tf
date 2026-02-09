# ========================================================================
# INFRASTRUCTURE - KAFKA CLUSTER
# Strimzi Kafka cluster and topic CRDs
# ========================================================================

resource "kubernetes_manifest" "kafka_cluster" {
  manifest = {
    apiVersion = "kafka.strimzi.io/v1beta2"
    kind       = "Kafka"
    metadata = {
      name      = var.kafka_config.cluster.name
      namespace = kubernetes_namespace.simple_sport_news_namespace.metadata[0].name
    }
    spec = {
      kafka = {
        version  = var.kafka_config.cluster.version
        replicas = var.kafka_config.cluster.replicas
        listeners = [
          {
            name = "plain"
            port = 9092
            type = "internal"
            tls  = false
          }
        ]
        config = {
          "offsets.topic.replication.factor"         = 1
          "transaction.state.log.replication.factor" = 1
          "transaction.state.log.min.isr"            = 1
          "default.replication.factor"               = 1
          "min.insync.replicas"                      = 1
        }
        storage = {
          type        = "persistent-claim"
          size        = var.kafka_config.cluster.storage.size
          class       = var.kafka_config.cluster.storage.storage_class
          deleteClaim = var.kafka_config.cluster.storage.delete_claim
        }
        resources = {
          requests = var.kafka_config.cluster.resources.requests
          limits   = var.kafka_config.cluster.resources.limits
        }
      }
      entityOperator = {
        topicOperator = {}
        userOperator  = {}
      }
    }
  }

  depends_on = [
    helm_release.strimzi_operator_release,
    kubernetes_namespace.simple_sport_news_namespace
  ]
}

resource "kubernetes_manifest" "kafka_topic_content_processing" {
  manifest = {
    apiVersion = "kafka.strimzi.io/v1beta2"
    kind       = "KafkaTopic"
    metadata = {
      name      = var.kafka_config.topics.content_processing.name
      namespace = kubernetes_namespace.simple_sport_news_namespace.metadata[0].name
      labels = {
        "strimzi.io/cluster" = var.kafka_config.cluster.name
      }
    }
    spec = {
      partitions = var.kafka_config.topics.content_processing.partitions
      replicas   = var.kafka_config.topics.content_processing.replicas
      config     = var.kafka_config.topics.content_processing.config
    }
  }

  depends_on = [kubernetes_manifest.kafka_cluster]
}

resource "kubernetes_manifest" "kafka_topic_query_answering" {
  manifest = {
    apiVersion = "kafka.strimzi.io/v1beta2"
    kind       = "KafkaTopic"
    metadata = {
      name      = var.kafka_config.topics.query_answering.name
      namespace = kubernetes_namespace.simple_sport_news_namespace.metadata[0].name
      labels = {
        "strimzi.io/cluster" = var.kafka_config.cluster.name
      }
    }
    spec = {
      partitions = var.kafka_config.topics.query_answering.partitions
      replicas   = var.kafka_config.topics.query_answering.replicas
      config     = var.kafka_config.topics.query_answering.config
    }
  }

  depends_on = [kubernetes_manifest.kafka_cluster]
}
