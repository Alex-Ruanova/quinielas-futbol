/* Sesión y balance viven en localStorage/el navegador; no hay valor en pre-renderizar
 * en el servidor una app que siempre depende del cliente para saber quién es el usuario. */
export const ssr = false;

/* Con ssr=false esto no genera HTML con datos: emite el shell de cada ruta como
 * un archivo propio. Sin él, S3 sirve el index de fallback con estado 404 en
 * /partidos, /admin y demás, y Cloudflare puede cachear ese 404. */
export const prerender = true;

/* S3 website no añade `.html` a una ruta, pero sí sirve el documento índice
 * cuando la clave parece un directorio. Con esto el build emite
 * `partidos/index.html` en vez de `partidos.html`, y la ruta responde 200
 * en lugar de caer en el error_document con un 404 enganoso. */
export const trailingSlash = 'always';
