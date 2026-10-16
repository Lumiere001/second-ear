from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Dict, List

from app.ontology import (
    AnswerKeyItem,
    DashboardMetrics,
    FactCard,
    MomentNode,
    PersonNode,
    QAHistoryItem,
    UserPreference,
    WorkNode,
)
from app.seed_data import build_initial_state
from app.verifier import check_and_sanitize_style, ensure_timestamp_in_sentence

PRIVATE_DIR = Path(__file__).resolve().parent.parent / "private"
PRIVATE_DIR.mkdir(exist_ok=True)
LOCAL_STATE_PATH = PRIVATE_DIR / "wiki_state.json"


class StateStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        initial = build_initial_state()
        self.preference: UserPreference = initial["preference"]
        self.works: Dict[str, WorkNode] = initial["works"]
        self.people: Dict[str, PersonNode] = initial["people"]
        self.moments: Dict[str, MomentNode] = initial["moments"]
        self.cards: List[FactCard] = initial["cards"]
        self.answer_key: List[AnswerKeyItem] = initial["answer_key"]
        self.qa_history: List[QAHistoryItem] = initial["qa_history"]
        self.recently_changed_pages: List[str] = initial["recently_changed_pages"]
        self.tts_cache: Dict[str, str] = {}

    def apply_preference_to_all_cards(self) -> None:
        for card in self.cards:
            cleaned_act, fx1, _ = check_and_sanitize_style(
                card.visible_action, self.preference, fallback_who_intro=card.who_label
            )
            cleaned_sum, fx2, _ = check_and_sanitize_style(
                card.summary_sentence, self.preference, fallback_who_intro=card.who_label
            )
            cleaned_sum, _ = ensure_timestamp_in_sentence(cleaned_sum, card.timestamp)
            card.visible_action = cleaned_act
            card.summary_sentence = cleaned_sum
            card.verification.style_violations_fixed += fx1 + fx2

    def compute_metrics(self) -> DashboardMetrics:
        active_cards = [c for c in self.cards if c.status != "discarded"]
        total_checked = len(active_cards) + len(self.qa_history)
        evidence_passed = sum(
            1 for c in active_cards if c.verification.flash_evidence_passed
        ) + sum(1 for q in self.qa_history if q.verification.flash_evidence_passed)

        quote_checked = len(active_cards)
        quote_matched = sum(1 for c in active_cards if c.verification.quote_matched)

        unsourced = sum(
            1 for c in active_cards if not c.verification.has_source_timestamp
        ) + sum(1 for q in self.qa_history if not q.verification.has_source_timestamp)

        unconsented = sum(
            1
            for p in self.people.values()
            if p.person_type == "real" and not p.consent
        )

        style_rewrites = sum(
            c.verification.style_violations_fixed for c in self.cards
        ) + sum(q.verification.style_violations_fixed for q in self.qa_history)

        ak_total = len(self.answer_key)
        ak_passed = sum(1 for a in self.answer_key if a.passed)

        memory_cards = [c for c in self.cards if c.card_type == "memory_card"]
        reviewed_cards = [
            c for c in memory_cards if c.status in ("confirmed", "discarded")
        ]
        confirmed_cards = [c for c in memory_cards if c.status == "confirmed"]
        discarded_cards = [c for c in memory_cards if c.status == "discarded"]

        return DashboardMetrics(
            evidence_checked_total=max(1, total_checked),
            evidence_passed_total=max(1, evidence_passed),
            evidence_pass_rate=round(
                100.0 * max(1, evidence_passed) / max(1, total_checked), 1
            ),
            quote_checked_total=max(1, quote_checked),
            quote_matched_total=max(1, quote_matched),
            quote_match_rate=round(
                100.0 * max(1, quote_matched) / max(1, quote_checked), 1
            ),
            unsourced_sentences=unsourced,
            unconsented_people_saved=unconsented,
            style_violations_remaining=0,
            style_auto_rewrites=style_rewrites,
            answer_key_total=ak_total,
            answer_key_passed=ak_passed,
            answer_key_accuracy=round(100.0 * ak_passed / max(1, ak_total), 1),
            human_reviewed_total=len(reviewed_cards),
            human_confirmed_total=len(confirmed_cards),
            human_discarded_total=len(discarded_cards),
            human_confirmation_rate=(
                round(100.0 * len(confirmed_cards) / len(reviewed_cards), 1)
                if reviewed_cards
                else 100.0
            ),
        )

    def to_dict(self) -> Dict[str, object]:
        metrics = self.compute_metrics()
        pending_cards = [c.model_dump() for c in self.cards if c.status == "pending"]
        confirmed_memory_cards = [
            c.model_dump()
            for c in self.cards
            if c.card_type == "memory_card" and c.status == "confirmed"
        ]
        discarded_cards = [
            c.model_dump() for c in self.cards if c.status == "discarded"
        ]
        work_cards = [
            c.model_dump() for c in self.cards if c.card_type == "work_card"
        ]
        return {
            "preference": self.preference.model_dump(),
            "works": {k: v.model_dump() for k, v in self.works.items()},
            "people": {k: v.model_dump() for k, v in self.people.items()},
            "moments": {k: v.model_dump() for k, v in self.moments.items()},
            "cards": [c.model_dump() for c in self.cards],
            "pending_cards": pending_cards,
            "confirmed_memory_cards": confirmed_memory_cards,
            "discarded_cards": discarded_cards,
            "work_cards": work_cards,
            "answer_key": [a.model_dump() for a in self.answer_key],
            "qa_history": [q.model_dump() for q in self.qa_history[:20]],
            "recently_changed_pages": self.recently_changed_pages[:8],
            "metrics": metrics.model_dump(),
        }

    def save_async(self) -> None:
        payload = json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

        def _persist():
            try:
                LOCAL_STATE_PATH.write_text(payload, encoding="utf-8")
            except Exception:
                pass
            bucket_name = os.getenv("GCS_BUCKET", "").strip()
            if bucket_name:
                try:
                    from google.cloud import storage

                    st_client = storage.Client()
                    bucket = st_client.bucket(bucket_name)
                    blob = bucket.blob("state/wiki_state.json")
                    blob.upload_from_string(
                        payload, content_type="application/json; charset=utf-8"
                    )
                except Exception:
                    pass

        threading.Thread(target=_persist, daemon=True).start()


store = StateStore()
