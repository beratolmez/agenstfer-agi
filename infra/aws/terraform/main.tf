# Agentic Growth Intelligence (AGI) - Production AWS Single-Tenant Infrastructure
# Terraform Module for Customer Isolated Environment

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  type    = string
  default = "eu-central-1"
}

variable "customer_id" {
  type    = string
  default = "anka-automation"
}

# 1. Customer Isolated VPC
resource "aws_vpc" "customer_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name        = "agi-vpc-${var.customer_id}"
    Environment = "production"
  }
}

# Subnets
resource "aws_subnet" "public_alb" {
  vpc_id                  = aws_vpc.customer_vpc.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = true
  availability_zone       = "${var.aws_region}a"

  tags = { Name = "agi-subnet-public-alb-${var.customer_id}" }
}

resource "aws_subnet" "private_app" {
  vpc_id            = aws_vpc.customer_vpc.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "${var.aws_region}a"

  tags = { Name = "agi-subnet-private-app-${var.customer_id}" }
}

resource "aws_subnet" "private_db" {
  vpc_id            = aws_vpc.customer_vpc.id
  cidr_block        = "10.0.3.0/24"
  availability_zone = "${var.aws_region}b"

  tags = { Name = "agi-subnet-private-db-${var.customer_id}" }
}

# Internet Gateway
resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.customer_vpc.id

  tags = { Name = "agi-igw-${var.customer_id}" }
}

# Route Tables
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.customer_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }

  tags = { Name = "agi-rt-public-${var.customer_id}" }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public_alb.id
  route_table_id = aws_route_table.public.id
}

# 2. Security Groups
resource "aws_security_group" "alb_sg" {
  name        = "agi-alb-sg-${var.customer_id}"
  description = "Allow inbound HTTPS to ALB"
  vpc_id      = aws_vpc.customer_vpc.id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "app_sg" {
  name        = "agi-app-sg-${var.customer_id}"
  description = "Allow traffic from ALB to App"
  vpc_id      = aws_vpc.customer_vpc.id

  ingress {
    from_port       = 8080
    to_port         = 8080
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "db_sg" {
  name        = "agi-db-sg-${var.customer_id}"
  description = "Allow App to connect to RDS PostgreSQL"
  vpc_id      = aws_vpc.customer_vpc.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# 3. RDS PostgreSQL Instance
resource "aws_db_subnet_group" "db_subnets" {
  name       = "agi-db-subnets-${var.customer_id}"
  subnet_ids = [aws_subnet.private_app.id, aws_subnet.private_db.id]
}

resource "aws_db_instance" "postgres" {
  identifier             = "agi-db-${var.customer_id}"
  allocated_storage      = 20
  max_allocated_storage  = 100
  engine                 = "postgres"
  engine_version         = "16"
  instance_class         = "db.t4g.small"
  db_name                = "agi"
  username               = "agi"
  password               = var.db_password
  db_subnet_group_name   = aws_db_subnet_group.db_subnets.name
  vpc_security_group_ids = [aws_security_group.db_sg.id]
  skip_final_snapshot    = true
  storage_encrypted      = true
}

variable "db_password" {
  type      = string
  sensitive = true
  default   = "production-secure-db-password-change-me"
}

output "alb_dns_name" {
  value       = "https://agi.${var.customer_id}.aws.internal"
  description = "The internal/external URL endpoint for customer deployment"
}
