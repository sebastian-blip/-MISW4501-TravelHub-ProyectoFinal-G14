module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  name    = "${var.cluster_name}-vpc"
  cidr    = "10.0.0.0/16"
  azs     = ["${var.region}a", "${var.region}b"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]
  enable_nat_gateway = true
  single_nat_gateway = true
}

module "eks" {
  source          = "terraform-aws-modules/eks/aws"
  cluster_name    = var.cluster_name
  cluster_version = "1.29"
  subnet_ids      = module.vpc.private_subnets
  vpc_id          = module.vpc.vpc_id

  eks_managed_node_groups = {
    default = {
      desired_size = var.node_desired_size
      max_size     = var.node_max_size
      min_size     = var.node_min_size
      instance_types = [var.node_instance_type]
      disk_size      = 20
    }
  }
  enable_irsa = true
}

data "aws_eks_cluster_auth" "cluster" {
  name = module.eks.cluster_name
}

provider "kubernetes" {
  host = module.eks.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
  token = data.aws_eks_cluster_auth.cluster.token
}

provider "helm" {
  kubernetes {
    host = module.eks.cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
    token = data.aws_eks_cluster_auth.cluster.token
  }
}

resource "kubernetes_namespace" "argocd" {
  metadata {
    name = "argocd"
  }
}

resource "helm_release" "argo_cd" {
  name       = "argo-cd"
  repository = "https://argoproj.github.io/argo-helm"
  chart      = "argo-cd"
  namespace  = kubernetes_namespace.argocd.metadata[0].name
  version    = "5.57.2"
  create_namespace = false

  values = [<<EOF
server:
  service:
    type: LoadBalancer
EOF
  ]
}

data "aws_iam_policy_document" "eso_policy" {
  statement {
    actions = [
      "secretsmanager:GetSecretValue",
      "secretsmanager:DescribeSecret",
      "secretsmanager:ListSecrets"
    ]
    resources = ["*"]
  }
}

module "eso_irsa" {
  source                 = "terraform-aws-modules/iam/aws//modules/iam-assumable-role-with-oidc"
  create_role            = true
  role_name              = "external-secrets-irsa"
  provider_url           = module.eks.oidc_provider
  oidc_fully_qualified_subjects = [
    "system:serviceaccount:external-secrets:external-secrets"
  ]
  policy_arns            = [aws_iam_policy.eso_policy.arn]
}

resource "kubernetes_service_account" "eso" {
  metadata {
    name      = "external-secrets"
    namespace = "external-secrets"
    annotations = {
      "eks.amazonaws.com/role-arn" = module.eso_irsa.iam_role_arn
    }
  }
}

resource "helm_release" "external_secrets" {
  name             = "external-secrets"
  repository       = "https://charts.external-secrets.io"
  chart            = "external-secrets"
  namespace        = "external-secrets"
  create_namespace = true
  version          = "0.9.18"
  depends_on       = [module.eks]

  set {
    name  = "serviceAccount.create"
    value = "false"
  }

  set {
    name  = "serviceAccount.name"
    value = kubernetes_service_account.eso.metadata[0].name
  }
}

resource "aws_iam_policy" "eso_policy" {
  name   = "ExternalSecretsSecretsManager"
  policy = data.aws_iam_policy_document.eso_policy.json
}

resource "kubernetes_manifest" "argocd_project" {
  manifest = {
    apiVersion = "argoproj.io/v1alpha1"
    kind       = "AppProject"
    metadata = {
      name      = "demo-project"
      namespace = "argocd"
    }
    spec = {
      description = "Proyecto demo para apps de travelhub"
      sourceRepos = ["*"]
      destinations = [{
        namespace = "*"
        server    = "https://kubernetes.default.svc"
      }]
      clusterResourceWhitelist = [{
        group = "*"
        kind  = "*"
      }]
    }
  }
  depends_on = [helm_release.argo_cd]
}

resource "kubernetes_manifest" "argocd_application" {
  manifest = {
    apiVersion = "argoproj.io/v1alpha1"
    kind       = "Application"
    metadata = {
      name      = "travelhub-dev"
      namespace = "argocd"
    }
    spec = {
      project = "demo-project"
      source = {
        repoURL        = "https://github.com/sebastian-blip/-MISW4501-TravelHub-ProyectoFinal-G14.git"
        targetRevision = "main"
        path           = "k8s/overlays/dev"
      }
      destination = {
        server    = "https://kubernetes.default.svc"
        namespace = "service-soport"
      }
      syncPolicy = {
        automated = {
          prune    = true
          selfHeal = true
        }
        syncOptions = ["CreateNamespace=true"]
      }
    }
  }
  depends_on = [kubernetes_manifest.argocd_project]
}



