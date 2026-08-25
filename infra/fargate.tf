resource "aws_ecs_cluster" "main" {
  name = var.project
}

resource "aws_cloudwatch_log_group" "backend" {
  name              = "/ecs/${var.project}-backend"
  retention_in_days = 14
}

data "aws_iam_policy_document" "ecs_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "task_execution" {
  name               = "${var.project}-task-execution"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume.json
}

resource "aws_iam_role_policy_attachment" "task_execution" {
  role       = aws_iam_role.task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "task_execution_secrets" {
  name = "read-secrets"
  role = aws_iam_role.task_execution.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = ["secretsmanager:GetSecretValue"]
      Resource = [
        aws_secretsmanager_secret.database_url.arn,
        aws_secretsmanager_secret.jwt_secret.arn,
        aws_secretsmanager_secret.admin_password.arn,
        aws_secretsmanager_secret.tunnel_token.arn,
      ]
    }]
  })
}

resource "aws_ecs_task_definition" "backend" {
  family                   = "${var.project}-backend"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.task_execution.arn

  container_definitions = jsonencode([{
    name      = "backend"
    image     = "${aws_ecr_repository.backend.repository_url}:latest"
    essential = true

    portMappings = [{ containerPort = var.backend_port, protocol = "tcp" }]

    environment = [
      { name = "PORT", value = tostring(var.backend_port) },
      { name = "CORS_ORIGIN", value = "https://${local.app_hostname}" },
      { name = "SEED_DEMO", value = var.seed_demo ? "1" : "0" },
      { name = "ADMIN_EMAIL", value = var.admin_email },
      { name = "ADMIN_DISPLAY_NAME", value = "Administrador" },
    ]

    secrets = [
      { name = "DATABASE_URL", valueFrom = aws_secretsmanager_secret.database_url.arn },
      { name = "JWT_SECRET", valueFrom = aws_secretsmanager_secret.jwt_secret.arn },
      { name = "ADMIN_PASSWORD", valueFrom = aws_secretsmanager_secret.admin_password.arn },
    ]

    # startPeriod generoso: el entrypoint corre `alembic upgrade head` antes de
    # levantar uvicorn, y la primera migracion sobre una RDS fria no es inmediata.
    healthCheck = {
      command     = ["CMD-SHELL", "wget -q -O /dev/null http://localhost:${var.backend_port}/healthz || exit 1"]
      interval    = 30
      timeout     = 5
      retries     = 3
      startPeriod = 120
    }

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = aws_cloudwatch_log_group.backend.name
        awslogs-region        = var.region
        awslogs-stream-prefix = "backend"
      }
    }
    }, {
    # Sidecar: conecta el tunel HACIA Cloudflare y proxya a localhost:8000
    # (mismo namespace de red del task). Sin puertos de entrada.
    name      = "cloudflared"
    image     = "cloudflare/cloudflared:latest"
    essential = true
    command   = ["tunnel", "--no-autoupdate", "run"]

    secrets = [
      { name = "TUNNEL_TOKEN", valueFrom = aws_secretsmanager_secret.tunnel_token.arn },
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = aws_cloudwatch_log_group.backend.name
        awslogs-region        = var.region
        awslogs-stream-prefix = "cloudflared"
      }
    }
  }])
}

resource "aws_ecs_service" "backend" {
  name            = "backend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = data.aws_subnets.default.ids
    security_groups  = [aws_security_group.backend.id]
    assign_public_ip = true
  }
}
