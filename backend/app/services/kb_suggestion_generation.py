"""Çözülmüş (onaylı yanıtı olan) bir talepten, şirketin SSS'ine eklenebilecek
genelleştirilmiş bir soru-cevap maddesi TASLAĞI üretir.

ÖNEMLİ: Bu fonksiyonun ürettiği öneri hiçbir zaman doğrudan knowledge_base_chunks'a
eklenmez (bkz. CLAUDE.md "İnsan onaylı akış") — bir temsilcinin onay kuyruğuna
(kb_suggestions tablosu, status="pending") düşer; sadece onaylanınca gerçek bir
SSS kaydına dönüşür (bkz. app.routers.kb_suggestions).
"""

from dataclasses import dataclass
from pathlib import Path

from app.services.llm import call_llm

PROMPT_PATH = Path(__file__).parent / "prompts" / "kb_suggestion_prompt.txt"

LABELS = ("SORU:", "CEVAP:", "KOD:")


@dataclass(frozen=True)
class KbSuggestionResult:
    question: str
    answer: str
    intent: str


def _parse_response(raw_response: str, fallback_question: str, fallback_answer: str) -> KbSuggestionResult:
    """`SORU:` / `CEVAP:` / `KOD:` etiketlerini, her biri kendi satırında olacak
    şekilde ayrıştırır — etiketten sonraki tüm satırlar bir sonraki etikete
    kadar o alana ait sayılır (cevap metni birden fazla cümle/satır olabilir).
    Beklenen etiketlerden biri hiç bulunamazsa (model formatı bozarsa), o alan
    için makul bir varsayılana düşülür — sınıflandırmadaki FALLBACK_CATEGORY
    ile aynı "kısmi hata toleransı" prensibi."""
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in raw_response.splitlines():
        stripped = line.strip()
        if stripped.upper() in LABELS:
            current = stripped.upper().rstrip(":")
            sections[current] = []
            continue
        if current is not None:
            sections[current].append(line)

    question = "\n".join(sections.get("SORU", [])).strip() or fallback_question
    answer = "\n".join(sections.get("CEVAP", [])).strip() or fallback_answer
    intent = "\n".join(sections.get("KOD", [])).strip() or "genel"
    return KbSuggestionResult(question=question, answer=answer, intent=intent)


def generate_kb_suggestion(subject: str, body: str, final_answer: str) -> KbSuggestionResult:
    """`subject`/`body`: kaynak talep. `final_answer`: temsilcinin onayladığı/
    düzenlediği nihai yanıt metni (bkz. app.routers.kb_suggestions, ticket'ın
    en yeni onaylı/düzenlenmiş taslağından alınır)."""
    prompt = PROMPT_PATH.read_text(encoding="utf-8")
    context = f"Müşteri talebi:\nKonu: {subject}\n{body}\n\nNihai yanıt:\n{final_answer}"

    raw_response = call_llm(prompt, context)
    return _parse_response(raw_response, fallback_question=subject, fallback_answer=final_answer)
