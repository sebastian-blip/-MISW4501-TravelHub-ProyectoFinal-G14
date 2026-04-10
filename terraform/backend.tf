terraform {
  backend "s3" {
    bucket  = "travelhubg14"
    key     = "eks/dev/terraform.tfstate"
    region  = "us-east-2"
    encrypt = true
  }
}
