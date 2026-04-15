terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

locals {
  common_labels = {
    project = var.project_name
    owner   = var.owner
    env     = "production"
  }
}

resource "random_id" "suffix" {
  byte_length = 4
}

# ────────────────────────────────────────────────────────────
# Enable required APIs
# ────────────────────────────────────────────────────────────
resource "google_project_service" "services" {
  for_each = toset([
    "run.googleapis.com",
    "sql-component.googleapis.com",
    "sqladmin.googleapis.com",
    "artifactregistry.googleapis.com",
    "storage.googleapis.com",
  ])

  project            = var.project_id
  service            = each.key
  disable_on_destroy = false
}

# ────────────────────────────────────────────────────────────
# GCS Bucket for raw data
# ────────────────────────────────────────────────────────────
resource "google_storage_bucket" "raw_data" {
  name          = "${var.project_name}-raw-${random_id.suffix.hex}"
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    action { type = "Delete" }
    condition { age = 365 }
  }

  labels = local.common_labels
}

# ────────────────────────────────────────────────────────────
# Cloud SQL PostgreSQL
# ────────────────────────────────────────────────────────────
resource "google_sql_database_instance" "postgres" {
  name             = "${var.project_name}-postgres-${random_id.suffix.hex}"
  database_version = "POSTGRES_16"
  region           = var.region

  settings {
    tier = "db-f1-micro"

    disk_size       = 20
    disk_type       = "PD_SSD"
    disk_autoresize = true

    backup_configuration {
      enabled    = true
      start_time = "03:00"
    }

    ip_configuration {
      ipv4_enabled = false
      require_ssl  = true
    }

    database_flags {
      name  = "max_connections"
      value = "100"
    }
  }

  deletion_protection = false

  depends_on = [google_project_service.services]
}

resource "google_sql_database" "clickstream" {
  name     = var.db_name
  instance = google_sql_database_instance.postgres.name
}

resource "google_sql_user" "clickstream" {
  name     = var.db_user
  instance = google_sql_database_instance.postgres.name
  password = var.db_password
}

# ────────────────────────────────────────────────────────────
# Artifact Registry
# ────────────────────────────────────────────────────────────
resource "google_artifact_registry_repository" "api" {
  repository_id = "${var.project_name}-api"
  format        = "DOCKER"
  location      = var.region
  description   = "Docker images for the clickstream API"

  labels = local.common_labels

  depends_on = [google_project_service.services]
}

# ────────────────────────────────────────────────────────────
# Cloud Run — API service
# ────────────────────────────────────────────────────────────
resource "google_cloud_run_v2_service" "api" {
  name     = "${var.project_name}-api"
  location = var.region

  template {
    containers {
      image = var.api_image

      ports {
        container_port = 8000
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      env {
        name  = "DATABASE_URL"
        value = "postgresql+asyncpg://${var.db_user}:${var.db_password}@/${var.db_name}?host=/cloudsql/${google_sql_database_instance.postgres.connection_name}"
      }

      env {
        name  = "API_HOST"
        value = "0.0.0.0"
      }

      env {
        name  = "API_PORT"
        value = "8000"
      }
    }

    scaling {
      min_instance_count = 0
      max_instance_count = 5
    }
  }

  labels = local.common_labels

  depends_on = [google_project_service.services]
}

resource "google_cloud_run_v2_service_iam_member" "public" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
