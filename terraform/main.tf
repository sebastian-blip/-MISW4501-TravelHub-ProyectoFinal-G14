module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${var.cluster_name}-vpc"
  cidr = "10.0.0.0/16"
  azs  = ["${var.region}a", "${var.region}b"]

  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = true
}

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = var.cluster_name
  cluster_version = "1.30"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  cluster_endpoint_public_access  = true
  cluster_endpoint_private_access = true

  enable_cluster_creator_admin_permissions = true

 eks_managed_node_groups = {
  default = {
    desired_size   = var.node_desired_size
    max_size       = var.node_max_size
    min_size       = var.node_min_size
    instance_types = [var.node_instance_type]
    disk_size      = 20

    ami_type = "AL2023_x86_64_STANDARD"
  }
}

  enable_irsa = true
}


provider "kubernetes" {
  host                   = module.eks.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)

  exec {
    api_version = "client.authentication.k8s.io/v1"
    command     = "aws"
    args        = ["eks", "get-token", "--cluster-name", module.eks.cluster_name, "--region", var.region]
  }
}

provider "helm" {
  kubernetes = {
    host                   = module.eks.cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
    exec = {
      api_version = "client.authentication.k8s.io/v1"
      command     = "aws"
      args        = [
        "eks", "get-token",
        "--cluster-name", module.eks.cluster_name,
        "--region", var.region,
        "--profile", "345340320521_MISWAdmins"
      ]
    }
  }
}

resource "kubernetes_namespace" "argocd" {
  metadata {
    name = "argocd"
  }
}

resource "helm_release" "argo_cd" {
  name             = "argo-cd"
  repository       = "https://argoproj.github.io/argo-helm"
  chart            = "argo-cd"
  namespace        = kubernetes_namespace.argocd.metadata[0].name
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
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "5.39.0"

  role_name = "external-secrets-irsa"

  oidc_providers = {
    main = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["external-secrets:external-secrets-sa"]
    }
  }

  role_policy_arns = {
    eso = aws_iam_policy.eso_policy.arn
  }

}
data "aws_iam_policy_document" "service_soport_s3_read" {
  statement {
    actions   = ["s3:ListBucket"]
    resources = ["arn:aws:s3:::travelhubg14"]
  }

  statement {
    actions = ["s3:GetObject"]
    resources = [
      "arn:aws:s3:::travelhubg14/kafka/ca-cert.pem"
      # o usa arn:aws:s3:::travelhubg14/* si prefieres más amplio
    ]
  }
}

resource "aws_iam_policy" "service_soport_s3_read" {
  name   = "ServiceSoportS3Read"
  policy = data.aws_iam_policy_document.service_soport_s3_read.json
}

module "service_soport_irsa" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "5.39.0"

  role_name = "eks-service-soport-s3-read-role"

  oidc_providers = {
    main = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["apps:service-soport-sa"]
    }
  }

  role_policy_arns = {
    s3 = aws_iam_policy.service_soport_s3_read.arn
  }
}

resource "kubernetes_namespace_v1" "external_secrets" {
  metadata {
    name = "external-secrets"
  }
}



resource "helm_release" "external_secrets" {
  name             = "external-secrets"
  repository       = "https://charts.external-secrets.io"
  chart            = "external-secrets"
  namespace        = "external-secrets"
  create_namespace = true
  version          = "0.9.18"

  wait            = true
  wait_for_jobs   = true
  timeout         = 1800
  atomic          = false
  cleanup_on_fail = false

  set = [
    { name = "serviceAccount.create", value = "true" },
    { name = "serviceAccount.name", value = "external-secrets-sa" },
    { name = "serviceAccount.annotations.eks\\.amazonaws\\.com/role-arn", value = module.eso_irsa.iam_role_arn }
  ]

  depends_on = [module.eks, module.eso_irsa]
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

data "http" "aws_lbc_iam_policy" {
  url = "https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.8.2/docs/install/iam_policy.json"
}

resource "aws_iam_policy" "aws_lbc" {
  name   = "AWSLoadBalancerControllerIAMPolicy"
  policy = data.http.aws_lbc_iam_policy.response_body
}

module "aws_lbc_irsa" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "5.39.0"

  role_name = "eks-aws-load-balancer-controller"

  oidc_providers = {
    main = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["kube-system:aws-load-balancer-controller"]
    }
  }

  role_policy_arns = {
    aws_lbc = aws_iam_policy.aws_lbc.arn
  }
}

resource "helm_release" "aws_load_balancer_controller" {
  name       = "aws-load-balancer-controller"
  repository = "https://aws.github.io/eks-charts"
  chart      = "aws-load-balancer-controller"
  namespace  = "kube-system"

  set = [
    { name = "clusterName", value = module.eks.cluster_name },
    { name = "region", value = var.region },
    { name = "vpcId", value = module.vpc.vpc_id },

    { name = "serviceAccount.create", value = "true" },
    { name = "serviceAccount.name", value = "aws-load-balancer-controller" },
    { name = "serviceAccount.annotations.eks\\.amazonaws\\.com/role-arn", value = module.aws_lbc_irsa.iam_role_arn }
  ]

  depends_on = [module.eks, module.aws_lbc_irsa]
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
        targetRevision = "feat/create_terraform"
        path           = "k8s/overlays/dev"
      }
      destination = {
        server    = "https://kubernetes.default.svc"
        namespace = "apps"
      }
      syncPolicy = {

        syncOptions = ["CreateNamespace=true"]
      }
    }
  }
  depends_on = [kubernetes_manifest.argocd_project]
}
