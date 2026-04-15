variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "ecommerce-clickstream"
}

variable "owner" {
  description = "Owner label value"
  type        = string
  default     = "hassan-zaib-hayat"
}

variable "db_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "clickstream"
}

variable "db_user" {
  description = "PostgreSQL user"
  type        = string
  default     = "clickstream"
}

variable "db_password" {
  description = "PostgreSQL password"
  type        = string
  sensitive   = true
}

variable "api_image" {
  description = "Full Docker image path for the API (gcr.io or Artifact Registry)"
  type        = string
  default     = "gcr.io/google-samples/hello-app:1.0"
}
