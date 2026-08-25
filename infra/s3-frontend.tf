# Frontend estatico servido como S3 website detras del proxy de Cloudflare.
# El nombre del bucket DEBE ser igual al hostname (requisito de S3 website
# para rutear CNAMEs). El endpoint website es HTTP-only: Cloudflare termina
# el TLS hacia el browser (modo Flexible hacia este origen).
resource "aws_s3_bucket" "frontend" {
  bucket        = local.app_hostname
  force_destroy = true
}

resource "aws_s3_bucket_website_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  index_document {
    suffix = "index.html"
  }

  # SPA: cualquier ruta desconocida regresa el index. Es lo que hace funcionar
  # /partidos y /admin en un recarga directa del navegador.
  error_document {
    key = "index.html"
  }
}

resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket                  = aws_s3_bucket.frontend.id
  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "frontend" {
  bucket     = aws_s3_bucket.frontend.id
  depends_on = [aws_s3_bucket_public_access_block.frontend]
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "PublicReadWebsite"
      Effect    = "Allow"
      Principal = "*"
      Action    = "s3:GetObject"
      Resource  = "${aws_s3_bucket.frontend.arn}/*"
    }]
  })
}
