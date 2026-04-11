# Terraform quickstart (EKS + ArgoCD)

## 1) Requisitos
- Terraform >= 1.5
- AWS CLI v2
- Cuenta AWS con permisos para VPC, EKS, IAM, S3, DynamoDB

---

## 2) Credenciales AWS (local)

### Opción recomendada: AWS Profile
```bash
aws configure --profile travelhub
# AWS Access Key ID
# AWS Secret Access Key
# region (ej: us-east-2)
# output (json)
```

Exporta el profile:
```bash
export AWS_PROFILE=travelhub
export AWS_REGION=us-east-2
```

Verifica identidad:
```bash
aws sts get-caller-identity
```

---


## 5) Flujo de despliegue
```bash
terraform fmt -recursive
terraform validate
terraform plan
terraform apply
```

---

## 6) Si falla por EKS/Kubernetes provider
Usar despliegue en 2 pasos:
```bash
terraform plan -target=module.vpc -target=module.eks -target=helm_release.argo_cd -out=plan-infra.tfplan
terraform apply plan-infra.tfplan
terraform plan -out=plan-full.tfplan 
terraform apply -auto-approve plan-full.tfplan 
```

---

## 7) Destruir infraestructura
```bash
terraform destroy
```

Si hay recursos de k8s/helm bloqueando:
```bash
terraform destroy -target=kubernetes_manifest.argocd_project -target=helm_release.argo_cd -auto-approve
terraform destroy -auto-approve
```