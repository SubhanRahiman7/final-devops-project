variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "ap-south-1"
}

variable "project_name" {
  description = "Prefix used in resource names and tags"
  type        = string
  default     = "helpdesk"
}

variable "vpc_cidr" {
  description = "CIDR block of the VPC"
  type        = string
  default     = "10.20.0.0/16"
}

variable "availability_zones" {
  description = "Two availability zones: one public and one private subnet is created in each"
  type        = list(string)
  default     = ["ap-south-1a", "ap-south-1b"]
}

variable "kubernetes_version" {
  description = "EKS control plane version"
  type        = string
  default     = "1.33"
}

variable "node_instance_types" {
  description = "EC2 instance types of the managed node group"
  type        = list(string)
  default     = ["t3.medium"]
}

variable "node_desired_size" {
  type    = number
  default = 2
}

variable "node_min_size" {
  type    = number
  default = 2
}

variable "node_max_size" {
  type    = number
  default = 4
}

variable "cluster_public_access_cidrs" {
  description = "Who may reach the public Kubernetes API endpoint. Restrict this to your own IP (x.x.x.x/32) for real use."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

# ---- local emulator (Moto) so that plan / apply / destroy can be rehearsed without a real AWS account ----
variable "use_local_emulator" {
  description = "true: talk to a local Moto server with dummy credentials; false (default): talk to real AWS"
  type        = bool
  default     = false
}

variable "emulator_endpoint" {
  type    = string
  default = "http://localhost:5001"
}
