from dataclasses import dataclass
from typing import Dict, List, Tuple

from rapidfuzz import process, fuzz

from app.schemas.schemas import GemmaMedicine


DRUG_DICTIONARY = {
    "paracetamol": ["pcm", "parac", "crocin"],
    "amoxicillin": ["amox", "amoxil"],
}

FREQUENCY_MAP: Dict[str, int] = {
    "od": 1,
    "bd": 2,
    "tds": 3,
    "qid": 4,
}


@dataclass
class ValidatedMedicine:
    original_name: str
    normalized_name: str
    dose: str
    frequency: str
    frequency_per_day: int
    duration_days: int
    instructions: str
    confidence: float
    drug_match_success: float


def normalize_drug_name(name: str) -> Tuple[str, float]:
    name_lower = name.lower().strip()

    for canonical, aliases in DRUG_DICTIONARY.items():
        if name_lower == canonical:
            return canonical.title(), 1.0
        if name_lower in aliases:
            return canonical.title(), 0.9

    all_names = list(DRUG_DICTIONARY.keys()) + [a for aliases in DRUG_DICTIONARY.values() for a in aliases]
    best, score, _ = process.extractOne(name_lower, all_names, scorer=fuzz.WRatio)
    if score >= 80:
        for canonical, aliases in DRUG_DICTIONARY.items():
            if best == canonical or best in aliases:
                return canonical.title(), score / 100.0

    return name, 0.5


def parse_duration(duration: str) -> int:
    if not duration:
        return 0
    tokens = duration.lower().split()
    for token in tokens:
        if token.isdigit():
            return int(token)
    return 0


def map_frequency(freq: str) -> Tuple[str, int]:
    if not freq:
        return "", 0
    key = freq.lower().strip()
    per_day = FREQUENCY_MAP.get(key, 0)
    return freq.upper(), per_day


def validate_medicines(gemma_medicines: List[GemmaMedicine], ocr_reliability: float, json_parse_success: float) -> Tuple[List[ValidatedMedicine], float]:
    validated: List[ValidatedMedicine] = []
    total_drug_match = 0.0

    for item in gemma_medicines:
        normalized_name, drug_score = normalize_drug_name(item.medicine)
        freq_str, per_day = map_frequency(item.frequency)
        duration_days = parse_duration(item.duration)

        medicine_confidence = (
            ocr_reliability * 0.4 +
            json_parse_success * 0.3 +
            drug_score * 0.3
        ) * 100.0

        validated.append(
            ValidatedMedicine(
                original_name=item.medicine,
                normalized_name=normalized_name,
                dose=item.dose,
                frequency=freq_str,
                frequency_per_day=per_day,
                duration_days=duration_days,
                instructions=item.instructions,
                confidence=medicine_confidence,
                drug_match_success=drug_score * 100.0,
            )
        )
        total_drug_match += drug_score

    if gemma_medicines:
        avg_drug_match = total_drug_match / len(gemma_medicines)
    else:
        avg_drug_match = 0.0

    final_confidence = (
        ocr_reliability * 0.4 +
        json_parse_success * 0.3 +
        avg_drug_match * 0.3
    ) * 100.0

    return validated, final_confidence

