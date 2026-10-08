# Rehearse plan / apply / destroy against a local Moto server (no AWS account needed):
#   docker run -d --name moto -p 5001:5000 -e MOTO_IAM_LOAD_MANAGED_POLICIES=true motoserver/moto
#   terraform apply -var-file=local-emulator.tfvars
use_local_emulator = true
