terraform {
  required_version = ">= 0.13"
  backend "s3" {
    bucket  = "sagemaker-project-template"
    key     = "terraform/state"
    region  = "us-west-2"
    profile = "sagemaker_project_template"
  }
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "3.10.0"
    }
  }
}

provider "aws" {
  profile = "sagemaker_project_template"
  region  = "us-west-2"
}


######## Docker images, Sagemaker algorithm - all what is needed to run train/eval/etc jobs

resource "aws_ecr_repository" "model_environments" {
  name = "model-environments"
}


module "ecr_image" {
  source             = "github.com/faddey-w/terraform-aws-ecr-image?ref=v1.0.2"
  dockerfile_dir     = "docker"
  ecr_repository_url = aws_ecr_repository.model_environments.repository_url
  aws_profile = "sagemaker_project_template"
}
output "worker_image_url" {
  value = module.ecr_image.ecr_image_url
}


######## Network/security settings
# TODO currently we just use some default allow-wildcard security settings
# this has to be adapted to specific project needs!

data "aws_vpc" "default" {
  default = true
}
data "aws_security_group" "default" {
  name = "default"
}
output "security_group_id" {
  value = data.aws_security_group.default.id
}
data "aws_subnet" "default" {
  # for some reason only in this AZ I can create training jobs
  availability_zone = "us-west-2b"
  default_for_az = true
  vpc_id = data.aws_vpc.default.id
}
output "subnet_id_default" {
  value = data.aws_subnet.default.id
}


# in order to connect both S3 and EFS to training jobs,
# the jobs must reside in a subnet that is connected to an internet-enabled subnet via NAT

resource "aws_subnet" "jobs" {
  vpc_id = data.aws_vpc.default.id
  availability_zone = "us-west-2b"
  cidr_block = "172.31.65.0/24"  # TODO this depends on VPC's CIDR block
  # and must not conflict with existing (default) subnets
}
output "subnet_id_jobs" {
  value = aws_subnet.jobs.id
}
resource "aws_eip" "nat" {}

resource "aws_nat_gateway" "jobs" {
  allocation_id = aws_eip.nat.id
  subnet_id     = data.aws_subnet.default.id
}
data "aws_route_table" "default" {
  vpc_id = data.aws_security_group.default.vpc_id
  filter {
    name = "association.main"
    values = ["true"]
  }
}
resource "aws_route_table" "jobs" {
  vpc_id = data.aws_vpc.default.id

  route {
    cidr_block = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.jobs.id
  }
}
resource "aws_route_table_association" "jobs" {
  subnet_id      = aws_subnet.jobs.id
  route_table_id = aws_route_table.jobs.id
}


######## Notebook instances - for interactive work

# create permissions available from within Notebooks:
# (this mimics what AWS console does by default)
resource "aws_iam_policy" "s3_access" {
  policy = <<-EOT
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::*"
      ]
    }
  ]
}
EOT
}
resource "aws_iam_role" "for_sagemaker_instances" {
  name = "for-sagemaker-instances"
  assume_role_policy = <<-EOT
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Action": "sts:AssumeRole",
        "Principal": {
          "Service": "sagemaker.amazonaws.com"
        },
        "Effect": "Allow",
        "Sid": ""
      }
    ]
  }
  EOT
}
output "sagemaker_role_arn" {
  value = aws_iam_role.for_sagemaker_instances.arn
}
resource "aws_iam_role_policy_attachment" "attach_sagemaker_full_access" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
  role = aws_iam_role.for_sagemaker_instances.name
}
resource "aws_iam_role_policy_attachment" "attach_backup_full_access" {
  policy_arn = "arn:aws:iam::aws:policy/AWSBackupFullAccess"
  role = aws_iam_role.for_sagemaker_instances.name
}
resource "aws_iam_role_policy_attachment" "attach_s3_access" {
  policy_arn = aws_iam_policy.s3_access.arn
  role = aws_iam_role.for_sagemaker_instances.name
}

# EFS and S3 are created manually - too important infrastructure to let automated tools work with it
# imagine you issue "terraform destroy" and it'll delete your data...

# mount EFS to Notebooks:
data "aws_efs_file_system" "model_and_data" {
  file_system_id = "fs-0dadd008"
}
output "efs_id" {
  value = data.aws_efs_file_system.model_and_data.file_system_id
}
resource "aws_sagemaker_notebook_instance_lifecycle_configuration" "notebook_config" {
  name = "notebook-config"
  on_create = base64encode(
    <<-EOT
      #! /bin/bash
      # setup a persistent kernel for python3.7
      envName=_my_project
      /home/ec2-user/anaconda3/bin/conda create -y --prefix /home/ec2-user/SageMaker/kernels/$envName python=3.7
    EOT
  )
  on_start = base64encode(
    <<-EOT
      #! /bin/bash

      # mount efs
      mkdir -p /mnt/efs
      sudo mount -t nfs4 -o nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2,noresvport \
          ${data.aws_efs_file_system.model_and_data.dns_name}:/ \
          /mnt/efs
      sudo chmod go+rw /mnt/efs

      # add some inactivity check that would shutdown the instance after an hour
      IDLE_TIME=3600
      wget https://raw.githubusercontent.com/aws-samples/amazon-sagemaker-notebook-instance-lifecycle-config-samples/master/scripts/auto-stop-idle/autostop.py
      (crontab -l 2>/dev/null; echo "*/5 * * * * /usr/bin/python $PWD/autostop.py --time $IDLE_TIME --ignore-connections") | crontab -

      # link all persistent kernels
      if [ -d "/home/ec2-user/SageMaker/kernels" ]; then
        for env in /home/ec2-user/SageMaker/kernels/*; do
          ln -s $env /home/ec2-user/anaconda3/envs/$(basename "$env")
          sudo -u ec2-user python -m ipykernel install --user --name $(basename "$env") --display-name "$(basename "$env")"
        done
      fi
    EOT
  )
}

# notebooks themselves:
resource "aws_sagemaker_notebook_instance" "small" {
  name = "small"
  instance_type = "ml.t3.medium"
  role_arn = aws_iam_role.for_sagemaker_instances.arn
  lifecycle_config_name = "notebook-config"
  subnet_id = data.aws_subnet.default.id
  security_groups = [data.aws_security_group.default.id]
}
resource "aws_sagemaker_notebook_instance" "gpu" {
  name = "gpu"
  instance_type = "ml.p2.xlarge"
  role_arn = aws_iam_role.for_sagemaker_instances.arn
  lifecycle_config_name = "notebook-config"
  subnet_id = data.aws_subnet.default.id
  security_groups = [data.aws_security_group.default.id]
}