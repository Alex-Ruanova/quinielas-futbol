output "app_url" {
  value = "https://${local.app_hostname}"
}

output "api_url" {
  value = "https://${local.api_hostname}"
}

output "frontend_bucket" {
  value = aws_s3_bucket.frontend.bucket
}

output "ecr_repository" {
  value = aws_ecr_repository.backend.repository_url
}

output "rds_endpoint" {
  value = aws_db_instance.main.address
}

output "ecs_cluster" {
  value = aws_ecs_cluster.main.name
}

# Para correr `alembic upgrade head` o `seed_demo.py` a mano contra produccion,
# via el secreto (nunca se imprime la contrasena en claro).
output "database_url_secret" {
  description = "Nombre del secreto con la DATABASE_URL de produccion"
  value       = aws_secretsmanager_secret.database_url.name
}

output "admin_email" {
  value = var.admin_email
}

output "admin_password_secret" {
  description = "Lee la contrasena con: aws secretsmanager get-secret-value --secret-id <esto>"
  value       = aws_secretsmanager_secret.admin_password.name
}
