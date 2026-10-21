/** Decode locally, honour browser orientation, strip metadata and bound upload pixels. */
export async function prepareImportImage(file: File): Promise<Blob> {
  if (!file.size || file.size > 25 * 1024 * 1024) throw new Error('imageInputError');
  const bytes = new Uint8Array(await file.slice(0, 16).arrayBuffer());
  const text = (start: number, end: number) => String.fromCharCode(...bytes.slice(start, end));
  const supported =
    (bytes[0] === 0xff && bytes[1] === 0xd8 && bytes[2] === 0xff) ||
    (bytes[0] === 0x89 && text(1, 4) === 'PNG') ||
    (text(0, 4) === 'RIFF' && text(8, 12) === 'WEBP') ||
    (text(4, 8) === 'ftyp' &&
      ['heic', 'heix', 'hevc', 'hevx', 'mif1', 'msf1'].includes(text(8, 12)));
  if (!supported) throw new Error('imageInputError');
  let source: ImageBitmap | HTMLImageElement;
  let url: string | undefined;
  try {
    try {
      source = await createImageBitmap(file);
    } catch {
      url = URL.createObjectURL(file);
      const image = new Image();
      image.src = url;
      await image.decode();
      source = image;
    }
    const width = source instanceof HTMLImageElement ? source.naturalWidth : source.width;
    const height = source instanceof HTMLImageElement ? source.naturalHeight : source.height;
    try {
      if (!width || !height || width * height > 32_000_000) throw new Error('imageInputError');
      const ratio = Math.min(1, 2048 / Math.max(width, height));
      const canvas = document.createElement('canvas');
      canvas.width = Math.max(1, Math.round(width * ratio));
      canvas.height = Math.max(1, Math.round(height * ratio));
      const context = canvas.getContext('2d', { alpha: false });
      if (!context) throw new Error('imageInputError');
      context.fillStyle = '#ffffff';
      context.fillRect(0, 0, canvas.width, canvas.height);
      context.drawImage(source, 0, 0, canvas.width, canvas.height);
      const blob = await new Promise<Blob | null>((resolve) =>
        canvas.toBlob(resolve, 'image/jpeg', 0.94),
      );
      if (!blob || blob.size > 8 * 1024 * 1024) throw new Error('imageInputError');
      return blob;
    } finally {
      if ('close' in source) source.close();
    }
  } finally {
    if (url) URL.revokeObjectURL(url);
  }
}
