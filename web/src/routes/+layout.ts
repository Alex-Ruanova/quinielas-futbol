/* Sesión y balance viven en localStorage/el navegador; no hay valor en pre-renderizar
 * en el servidor una app que siempre depende del cliente para saber quién es el usuario. */
export const ssr = false;
