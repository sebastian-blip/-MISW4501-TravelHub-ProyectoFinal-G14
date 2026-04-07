terraform {
  backend "s3" {
    bucket         = "mi-bucket-tfstate"
    key            = "eks/dev/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
}