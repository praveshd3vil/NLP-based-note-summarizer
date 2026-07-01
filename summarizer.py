import re
import logging
from transformers import pipeline, AutoTokenizer

logger = logging.getLogger("summarizer")

MODEL_NAME = "./finalfinetunedModel"

BART_MAX_TOKENS = 1024

MAX_WORDS_PER_CHUNK = 600

_summarizer_pipeline = None


def load_model():
    global _summarizer_pipeline
    if _summarizer_pipeline is None:    
        logger.info(f"Loading summarization model: {MODEL_NAME} ...")

        tokenizer = AutoTokenizer.from_pretrained(
            MODEL_NAME,
            model_max_length=BART_MAX_TOKENS,
        )
        _summarizer_pipeline = pipeline(
            "summarization",
            model=MODEL_NAME,
            tokenizer=tokenizer,
            device=-1,
        )
        logger.info("Model loaded successfully.")
    return _summarizer_pipeline


def is_model_loaded() -> bool:
    return _summarizer_pipeline is not None

def _clean_input_text(text: str) -> str:
    text = re.sub(r"\[\d+\]", "", text)

    text = re.sub(r"[ \t]{2,}", " ", text)

    return text.strip()


def _clean_output_text(summary: str) -> str:
    return re.sub(r"^[#\*\-]\s*", "", summary).strip()


def _split_into_sentences(text: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in sentences if s.strip()]


def _chunk_text(text: str, max_words: int = MAX_WORDS_PER_CHUNK) -> list[str]:
    sentences = _split_into_sentences(text)
    chunks = []
    current_chunk = []
    current_word_count = 0

    for sentence in sentences:
        sentence_word_count = len(sentence.split())
        if current_word_count + sentence_word_count > max_words and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_word_count = 0

        current_chunk.append(sentence)
        current_word_count += sentence_word_count

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def _summarize_chunk(chunk: str) -> str:
    word_count = len(chunk.split())

    max_len = max(30, min(180, int(word_count * 0.4)))
    min_len = max(10, int(max_len * 0.4))

    result = _summarizer_pipeline(
        chunk,
        max_length=max_len,
        min_length=min_len,
        do_sample=False,
        repetition_penalty=2.0, 
        truncation=True,
    )
    summary = result[0]["summary_text"].strip()
    return _clean_output_text(summary)


def summarize_text(text: str) -> str:
    if _summarizer_pipeline is None:
        raise RuntimeError("Summarization model is not loaded yet.")

    text = text.strip()
    if not text:
        raise ValueError("Input text is empty.")

    text = _clean_input_text(text)
    chunks = _chunk_text(text)

    if len(chunks) == 1:
        return _summarize_chunk(chunks[0])
    
    partial_summaries = [_summarize_chunk(c) for c in chunks]
    combined = " ".join(partial_summaries)
    return _summarize_chunk(combined)