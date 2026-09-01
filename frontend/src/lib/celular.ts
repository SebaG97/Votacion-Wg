/**
 * Validacion basica de celular en el cliente, antes de llamar a la API.
 * Es intencionalmente permisiva: el backend (`normalizar_celular`) es la
 * fuente de verdad. Solo evita mandar algo obviamente invalido (vacio, todo
 * ceros, o con una cantidad de digitos que no corresponde al formato
 * paraguayo de 9 u 10 digitos con cero inicial).
 */
export function esCelularValido(valor: string): boolean {
  const digitos = valor.replace(/\D/g, "");
  if (!digitos || /^0+$/.test(digitos)) {
    return false;
  }
  return digitos.length === 9 || digitos.length === 10;
}
