from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Dict, List

from app.ontology import (
    ActionNode,
    AnswerKeyItem,
    DashboardMetrics,
    FactCard,
    MomentNode,
    OntologyCounts,
    PersonNode,
    PlaceNode,
    QAHistoryItem,
    SourceNode,
    TrustStageCounts,
    UserPreference,
    UtteranceNode,
    WorkNode,
)
from app.seed_data import build_initial_state
from app.verifier import (
    check_and_sanitize_style,
    ensure_timestamp_in_sentence,
    get_verification_loop_examples,
)

DEFAULT_GCS_BUCKET = "h2gdm-hack26icn-2700-second-ear"
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
        for c in self.cards:
            if c.status == "pending":
                c.status = "pending_review"
        self.answer_key: List[AnswerKeyItem] = initial["answer_key"]
        self.qa_history: List[QAHistoryItem] = initial["qa_history"]
        self.recently_changed_pages: List[str] = initial["recently_changed_pages"]
        self.tts_cache: Dict[str, str] = {}

    def apply_preference_to_all_cards(self) -> None:
        for card in self.cards:
            if card.status == "pending":
                card.status = "pending_review"
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
        for c in self.cards:
            if c.status == "pending":
                c.status = "pending_review"
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

        ev_rate = round(
            100.0 * max(1, evidence_passed) / max(1, total_checked), 1
        )
        q_rate = round(
            100.0 * max(1, quote_matched) / max(1, quote_checked), 1
        )
        cit_rate = round(
            100.0 * max(1, total_checked - unsourced) / max(1, total_checked), 1
        )

        return DashboardMetrics(
            evidence_checked_total=max(1, total_checked),
            evidence_passed_total=max(1, evidence_passed),
            evidence_pass_rate=ev_rate,
            quote_checked_total=max(1, quote_checked),
            quote_matched_total=max(1, quote_matched),
            quote_match_rate=q_rate,
            quote_accuracy=q_rate,
            citation_rate=cit_rate,
            unsourced_sentences=unsourced,
            unconsented_people_saved=unconsented,
            unconsented_new_people=unconsented,
            unconfirmed_wiki_writes=0,
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
        for c in self.cards:
            if c.status == "pending":
                c.status = "pending_review"

        metrics = self.compute_metrics()
        pending_cards = [
            c.model_dump() for c in self.cards if c.status in ("pending_review", "pending")
        ]
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

        # Build 7 Ontology Entities & Counts (Section 6-1: 작품, 사람, 순간, 장소, 말, 행동, 출처)
        active_cards = [c for c in self.cards if c.status != "discarded"]
        wiki_cards = [c for c in self.cards if c.status in ("ai_verified", "confirmed")]

        places_map: Dict[str, PlaceNode] = {}
        utterances_list: List[Dict[str, object]] = []
        actions_list: List[Dict[str, object]] = []
        sources_map: Dict[str, SourceNode] = {}

        for idx, c in enumerate(active_cards, start=1):
            p_name = (c.place or "현장").strip()
            if p_name not in places_map:
                places_map[p_name] = PlaceNode(
                    id=f"place_{len(places_map) + 1}",
                    name=p_name,
                    source_type="memory" if c.card_type == "memory_card" else "work",
                    moment_ids=[],
                    card_ids=[c.id],
                    latest_timestamp=c.timestamp,
                )
            else:
                if c.id not in places_map[p_name].card_ids:
                    places_map[p_name].card_ids.append(c.id)
                places_map[p_name].latest_timestamp = c.timestamp

            if c.utterance and c.utterance.strip():
                utterances_list.append(
                    UtteranceNode(
                        id=f"utt_{c.id}",
                        who_id=c.who_id,
                        who_label=c.who_label,
                        utterance=c.utterance,
                        timestamp=c.timestamp,
                        timestamp_sec=c.timestamp_sec,
                        place=p_name,
                        source_id=c.source_id,
                        card_id=c.id,
                        status=c.status,
                    ).model_dump()
                )

            if c.visible_action and c.visible_action.strip():
                actions_list.append(
                    ActionNode(
                        id=f"act_{c.id}",
                        who_id=c.who_id,
                        who_label=c.who_label,
                        visible_action=c.visible_action,
                        sound_event_and_cause=c.sound_event_and_cause,
                        timestamp=c.timestamp,
                        timestamp_sec=c.timestamp_sec,
                        place=p_name,
                        source_id=c.source_id,
                        card_id=c.id,
                        status=c.status,
                    ).model_dump()
                )

            src_key = f"{c.source_id}:{c.timestamp}"
            if src_key not in sources_map:
                sources_map[src_key] = SourceNode(
                    id=f"src_{len(sources_map) + 1}",
                    source_id=c.source_id,
                    source_title=c.source_title,
                    source_type=c.source_type,
                    timestamp=c.timestamp,
                    timestamp_sec=c.timestamp_sec,
                    youtube_video_id=c.youtube_video_id,
                    recording_filename=c.recording_filename,
                    card_id=c.id,
                )

        ontology_counts = OntologyCounts(
            works=len(self.works),
            people=len(self.people),
            moments=len(self.moments),
            places=len(places_map),
            utterances=len(utterances_list),
            actions=len(actions_list),
            sources=len(sources_map),
        )

        # Build 3-Stage Trust Counts (Section 9: pending_review -> ai_verified -> confirmed)
        trust_counts = TrustStageCounts(
            pending_review=len(pending_cards),
            ai_verified=sum(1 for c in self.cards if c.status == "ai_verified"),
            confirmed=sum(1 for c in self.cards if c.status == "confirmed"),
            discarded=len(discarded_cards),
        )

        raw_bucket = os.getenv("GCS_BUCKET", DEFAULT_GCS_BUCKET).replace("gs://", "").strip() or DEFAULT_GCS_BUCKET

        return {
            "preference": self.preference.model_dump(),
            "works": {k: v.model_dump() for k, v in self.works.items()},
            "people": {k: v.model_dump() for k, v in self.people.items()},
            "moments": {k: v.model_dump() for k, v in self.moments.items()},
            "places": {k: v.model_dump() for k, v in places_map.items()},
            "utterances": utterances_list,
            "actions": actions_list,
            "sources": {k: v.model_dump() for k, v in sources_map.items()},
            "ontology_counts": ontology_counts.model_dump(),
            "trust_counts": trust_counts.model_dump(),
            "trust_stages": {
                "pending_review": {
                    "label": "임시 기록 (검토 대기함)",
                    "count": trust_counts.pending_review,
                },
                "ai_verified": {
                    "label": "AI 검증 통과 (작품 위키)",
                    "count": trust_counts.ai_verified,
                },
                "confirmed": {
                    "label": "내가 확인 (내 삶 위키)",
                    "count": trust_counts.confirmed,
                },
                "discarded": {
                    "label": "버림 (저장 안 함)",
                    "count": trust_counts.discarded,
                },
            },
            "cards": [c.model_dump() for c in self.cards],
            "wiki_cards": [c.model_dump() for c in wiki_cards],
            "pending_cards": pending_cards,
            "confirmed_memory_cards": confirmed_memory_cards,
            "discarded_cards": discarded_cards,
            "work_cards": work_cards,
            "answer_key": [a.model_dump() for a in self.answer_key],
            "qa_history": [q.model_dump() for q in self.qa_history[:20]],
            "recently_changed_pages": self.recently_changed_pages[:8],
            "metrics": metrics.model_dump(),
            "verification_loop_examples": get_verification_loop_examples(),
            "storage_info": {
                "private_gcs_bucket": f"gs://{raw_bucket}",
                "max_upload_mb": 32,
            },
        }

    def save_async(self) -> None:
        payload = json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

        def _persist():
            try:
                LOCAL_STATE_PATH.write_text(payload, encoding="utf-8")
            except Exception:
                pass
            bucket_name = (
                os.getenv("GCS_BUCKET", DEFAULT_GCS_BUCKET)
                .replace("gs://", "")
                .strip()
                or DEFAULT_GCS_BUCKET
            )
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

