# Terraform - AWS VPC + EKS

Creates (24 resources): VPC, 2 public + 2 private subnets in two AZs, Internet gateway, NAT gateway, route tables,
IAM roles for the cluster and the nodes, a KMS key (encrypts Kubernetes Secrets), an EKS cluster and a managed node group.

```bash
cp terraform.tfvars.example terraform.tfvars    # edit; the real file is git-ignored
terraform init
terraform plan
terraform apply
aws eks update-kubeconfig --region ap-south-1 --name helpdesk-eks     # printed as output "configure_kubectl"
terraform destroy                                                      # do not forget: EKS and NAT cost money
```

No credentials are stored here: they come from `aws configure` or the `AWS_*` environment variables.
`local-emulator.tfvars` rehearses the same code against a local Moto server (see the main README for what was run).
