resource "random_password" "db" {
  length  = 32
  special = false
}

resource "aws_db_subnet_group" "main" {
  name       = var.project
  subnet_ids = data.aws_subnets.default.ids
}

resource "aws_db_instance" "main" {
  identifier     = var.project
  engine         = "postgres"
  engine_version = "16"
  instance_class = "db.t3.micro"

  db_name  = var.project
  username = var.project
  password = random_password.db.result

  allocated_storage     = 20
  max_allocated_storage = 50
  storage_type          = "gp3"
  storage_encrypted     = true

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false

  backup_retention_period = 7
  skip_final_snapshot     = true # MVP: sin snapshot final al destruir
  apply_immediately       = true
}

# El driver es psycopg v3: SQLAlchemy necesita el prefijo postgresql+psycopg.
resource "aws_secretsmanager_secret" "database_url" {
  name                    = "${var.project}/database-url"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "database_url" {
  secret_id     = aws_secretsmanager_secret.database_url.id
  secret_string = "postgresql+psycopg://${var.project}:${random_password.db.result}@${aws_db_instance.main.address}:5432/${var.project}"
}

# El backend firma los JWT con esta clave. PyJWT avisa por debajo de 32 bytes.
resource "random_password" "jwt_secret" {
  length  = 64
  special = false
}

resource "aws_secretsmanager_secret" "jwt_secret" {
  name                    = "${var.project}/jwt-secret"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "jwt_secret" {
  secret_id     = aws_secretsmanager_secret.jwt_secret.id
  secret_string = random_password.jwt_secret.result
}
