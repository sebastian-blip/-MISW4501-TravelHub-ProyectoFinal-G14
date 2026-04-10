variable "region" { default = "us-east-2" }
variable "cluster_name" { default = "travelhub-eks" }
variable "node_instance_type" { default = "t3.small" }
variable "node_desired_size" { default = 1 }
variable "node_max_size" { default = 2 }
variable "node_min_size" { default = 1 }