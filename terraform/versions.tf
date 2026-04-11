terraform {
  required_version = ">= 1.3"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.95.0, < 6.0.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = ">= 2.21"
    }
    helm = {
      source  = "hashicorp/helm"
      version = ">= 2.13"
    }
    http = {
      source  = "hashicorp/http"
      version = "~> 3.4"
    }
  }
}