import logging
import os

import fitz
from langchain.docstore.document import Document
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

from llm.embedding import E5Embeddings

PDF_DIR = "/app/resources"
INDEX_DIR = "/app/resources/vectorstore"
MODEL_NAME = os.getenv("EMBEDD_MODEL_NAME")

logging.basicConfig(format="%(levelname)s %(name)s %(asctime)s: %(message)s", level=logging.INFO)
logger = logging.getLogger("pdf_indexer")

embeddings = E5Embeddings(OllamaEmbeddings(model=MODEL_NAME, base_url="http://ollama:11434"))


def extract_sections_with_fonts(pdf_path):
    doc = fitz.open(pdf_path)
    sections = []
    current_main = None
    current_sub = None
    buffer = []

    font_sizes = []
    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            lines = block.get("lines", [])
            for line in lines:
                spans = line.get("spans", [])
                for span in spans:
                    if "size" in span:
                        font_sizes.append(span["size"])

    base_font_size = sum(font_sizes) / len(font_sizes) if len(font_sizes) > 0 else 0
    title_threshold = base_font_size * 1.3

    def flush_section():
        nonlocal buffer, current_main, current_sub
        if buffer:
            logger.info(f"{current_main}: {current_sub}")
            sections.append({"chapter": current_main, "subsection": current_sub, "content": "\n".join(buffer)})
            buffer = []

    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        blocks.sort(key=lambda b: b.get("bbox", [0, 0])[1])

        for block in blocks:
            lines = block.get("lines", [])
            for line in lines:
                spans = line.get("spans", [])
                line_text = " ".join([s["text"] for s in spans]).strip()
                if not line_text:
                    continue

                max_font_size = max([s["size"] for s in spans])

                if line_text.startswith("Chapter ") or line_text.startswith("CHAPTER "):
                    flush_section()
                    current_main = line_text
                    current_sub = None

                elif max_font_size > title_threshold or (line_text.isupper() and len(line_text.split()) < 10):
                    flush_section()
                    current_sub = line_text

                else:
                    buffer.append(line_text)

    flush_section()
    return sections


def build_document(pdf_path):
    sections = extract_sections_with_fonts(pdf_path)
    documents = []
    for sec in sections:
        full_title = sec["chapter"] if sec["chapter"] else "UNKNOWN CHAPTER"
        if sec["subsection"]:
            full_title += f" > {sec['subsection']}"
        documents.append(
            Document(
                page_content=f"{full_title}\n{sec['content']}",
                metadata={"chapter": sec["chapter"], "subsection": sec["subsection"]},
            )
        )
    return documents


def process_pdfs():
    logger.info("Processing PDFs")
    documents = []
    logger.info(os.listdir(PDF_DIR))

    for filename in os.listdir(PDF_DIR):
        if filename.lower().endswith(".pdf"):
            filepath = os.path.join(PDF_DIR, filename)
            try:
                documents.extend(build_document(filepath))
            except Exception as e:
                logger.error(f"Erro ao processar {filename}: {e}")

    Chroma.from_documents(documents=documents, embedding=embeddings, persist_directory=INDEX_DIR)

    logger.info(f"Índice atualizado com {len(documents)} chunks de texto")
