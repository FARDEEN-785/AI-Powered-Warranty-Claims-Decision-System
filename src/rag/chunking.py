def chunk_warranty_text(text: str, chunk_size: int = 500, overlap: int = 100) -> list:

    chunks = []
    start = 0

    while start < len(text):

        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlap

    return chunks

