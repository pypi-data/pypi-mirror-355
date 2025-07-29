{% if data.tf_controller_access.mode == "SSM" %}
provider "aws" {
  region = "{{data.tf_controller_access.region}}"
  alias  = "{{data.tf_controller_access.alias}}"
  {% if data.tf_controller_access.ssm_role %}
  assume_role { role_arn = "arn:aws:iam::${var.aws_ctrl_account}:role/${var.ssm_role}" }
  {% endif %}
}
{% endif %}

provider "aviatrix" {
{% if data.tf_controller_access.mode == "SSM" %}
  username      = "{{data.tf_controller_access.username}}"
  password      = data.aws_ssm_parameter.avx-password.value
{% endif %}
  controller_ip = var.controller_ip
}

{% if not data.spoke_access_key_and_secret %}
locals {
  role_arn = "arn:aws:iam::${var.aws_account}:role/${var.aws_account_role}"
}
{% endif %}

provider "aws" {
  region              = "us-east-1"
  alias               = "spoke_us_east_1"
{% if not data.spoke_access_key_and_secret %}
  allowed_account_ids = [var.aws_account]
  assume_role { role_arn = local.role_arn }
{% endif %}
}

provider "aws" {
  region              = "us-east-2"
  alias               = "spoke_us_east_2"
{% if not data.spoke_access_key_and_secret %}
  allowed_account_ids = [var.aws_account]
  assume_role { role_arn = local.role_arn }
{% endif %}
}

provider "aws" {
  region              = "us-west-1"
  alias               = "spoke_us_west_1"
{% if not data.spoke_access_key_and_secret %}
  allowed_account_ids = [var.aws_account]
  assume_role { role_arn = local.role_arn }
{% endif %}
}

provider "aws" {
  region              = "us-west-2"
  alias               = "spoke_us_west_2"
{% if not data.spoke_access_key_and_secret %}
  allowed_account_ids = [var.aws_account]
  assume_role { role_arn = local.role_arn }
{% endif %}
}

provider "aws" {
  region              = "af-south-1"
  alias               = "spoke_af_south_1"
{% if not data.spoke_access_key_and_secret %}
  allowed_account_ids = [var.aws_account]
  assume_role { role_arn = local.role_arn }
{% endif %}
}

provider "aws" {
  region              = "ap-east-1"
  alias               = "spoke_ap_east_1"
{% if not data.spoke_access_key_and_secret %}
  allowed_account_ids = [var.aws_account]
  assume_role { role_arn = local.role_arn }
{% endif %}
}

provider "aws" {
  region              = "ap-south-1"
  alias               = "spoke_ap_south_1"
{% if not data.spoke_access_key_and_secret %}
  allowed_account_ids = [var.aws_account]
  assume_role { role_arn = local.role_arn }
{% endif %}
}

provider "aws" {
  region              = "ap-northeast-1"
  alias               = "spoke_ap_northeast_1"
{% if not data.spoke_access_key_and_secret %}
  allowed_account_ids = [var.aws_account]
  assume_role { role_arn = local.role_arn }
{% endif %}
}

provider "aws" {
  region              = "ap-northeast-2"
  alias               = "spoke_ap_northeast_2"
{% if not data.spoke_access_key_and_secret %}
  allowed_account_ids = [var.aws_account]
  assume_role { role_arn = local.role_arn }
{% endif %}
}

provider "aws" {
  region              = "ap-northeast-3"
  alias               = "spoke_ap_northeast_3"
{% if not data.spoke_access_key_and_secret %}
  allowed_account_ids = [var.aws_account]
  assume_role { role_arn = local.role_arn }
{% endif %}
}

provider "aws" {
  region              = "ap-southeast-1"
  alias               = "spoke_ap_southeast_1"
{% if not data.spoke_access_key_and_secret %}
  allowed_account_ids = [var.aws_account]
  assume_role { role_arn = local.role_arn }
{% endif %}
}

provider "aws" {
  region              = "ap-southeast-2"
  alias               = "spoke_ap_southeast_2"
{% if not data.spoke_access_key_and_secret %}
  allowed_account_ids = [var.aws_account]
  assume_role { role_arn = local.role_arn }
{% endif %}
}

provider "aws" {
  region              = "ca-central-1"
  alias               = "spoke_ca_central_1"
{% if not data.spoke_access_key_and_secret %}
  allowed_account_ids = [var.aws_account]
  assume_role { role_arn = local.role_arn }
{% endif %}
}

provider "aws" {
  region              = "eu-central-1"
  alias               = "spoke_eu_central_1"
{% if not data.spoke_access_key_and_secret %}
  allowed_account_ids = [var.aws_account]
  assume_role { role_arn = local.role_arn }
{% endif %}
}

provider "aws" {
  region              = "eu-west-1"
  alias               = "spoke_eu_west_1"
{% if not data.spoke_access_key_and_secret %}
  allowed_account_ids = [var.aws_account]
  assume_role { role_arn = local.role_arn }
{% endif %}
}

provider "aws" {
  region              = "eu-west-2"
  alias               = "spoke_eu_west_2"
{% if not data.spoke_access_key_and_secret %}
  allowed_account_ids = [var.aws_account]
  assume_role { role_arn = local.role_arn }
{% endif %}
}

provider "aws" {
  region              = "eu-west-3"
  alias               = "spoke_eu_west_3"
{% if not data.spoke_access_key_and_secret %}
  allowed_account_ids = [var.aws_account]
  assume_role { role_arn = local.role_arn }
{% endif %}
}

provider "aws" {
  region              = "eu-south-1"
  alias               = "spoke_eu_south_1"
{% if not data.spoke_access_key_and_secret %}
  allowed_account_ids = [var.aws_account]
  assume_role { role_arn = local.role_arn }
{% endif %}
}

provider "aws" {
  region              = "eu-north-1"
  alias               = "spoke_eu_north_1"
{% if not data.spoke_access_key_and_secret %}
  allowed_account_ids = [var.aws_account]
  assume_role { role_arn = local.role_arn }
{% endif %}
}

provider "aws" {
  region              = "me-south-1"
  alias               = "spoke_me_south_1"
{% if not data.spoke_access_key_and_secret %}
  allowed_account_ids = [var.aws_account]
  assume_role { role_arn = local.role_arn }
{% endif %}
}

provider "aws" {
  region              = "sa-east-1"
  alias               = "spoke_sa_east_1"
{% if not data.spoke_access_key_and_secret %}
  allowed_account_ids = [var.aws_account]
  assume_role { role_arn = local.role_arn }
{% endif %}
}