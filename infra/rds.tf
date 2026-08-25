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

  # Despliegue efimero (24 h): sin backups automaticos ni snapshot final, para
  # que `terraform destroy` no deje nada cobrando ni bloquee el borrado.
  backup_retention_period = 0
  skip_final_snapshot     = true
  deletion_protection     = false
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

# Administrador inicial. La RDS es privada, asi que no se puede sembrar desde
# fuera de la VPC: el contenedor se autoabastece al arrancar (SEED_DEMO=1).
resource "random_password" "admin" {
  length  = 20
  special = false
}

resource "aws_secretsmanager_secret" "admin_password" {
  name                    = "${var.project}/admin-password"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "admin_password" {
  secret_id     = aws_secretsmanager_secret.admin_password.id
  secret_string = random_password.admin.result
}
