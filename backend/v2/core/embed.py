def chunk_and_embed(path: str) -> list[str]:
    # minimal: nur Chunking, Embeddings später (Provider-Call im v1 Orchestrator)
    import pathlib
    text = pathlib.Path(path).read_text(errors="ignore")
    size = 800
    return [text[i:i+size] for i in range(0, len(text), size)]
