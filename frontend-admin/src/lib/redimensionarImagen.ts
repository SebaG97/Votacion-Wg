const LADO_MAXIMO = 800;
const CALIDAD_JPEG = 0.85;

/**
 * Achica la foto en el navegador antes de subirla (DEC-037): las fotos de
 * celular pesan varios MB y el backend acepta hasta 1 MB. Devuelve un JPEG
 * de como maximo 800 px de lado; si la imagen ya es chica, solo la
 * recomprime.
 */
export async function redimensionarImagen(archivo: File): Promise<Blob> {
  const bitmap = await createImageBitmap(archivo);
  const escala = Math.min(1, LADO_MAXIMO / Math.max(bitmap.width, bitmap.height));
  const ancho = Math.round(bitmap.width * escala);
  const alto = Math.round(bitmap.height * escala);

  const canvas = document.createElement("canvas");
  canvas.width = ancho;
  canvas.height = alto;
  const contexto = canvas.getContext("2d");
  if (!contexto) {
    throw new Error("El navegador no permite procesar la imagen.");
  }
  contexto.drawImage(bitmap, 0, 0, ancho, alto);
  bitmap.close();

  return new Promise((resolve, reject) => {
    canvas.toBlob(
      (blob) => (blob ? resolve(blob) : reject(new Error("No se pudo procesar la imagen."))),
      "image/jpeg",
      CALIDAD_JPEG,
    );
  });
}
