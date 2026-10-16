from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Dict, List, Optional

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
    mmss_to_seconds,
    now_iso,
)
from app.seed_data import build_initial_state
from app.verifier import (
    RUNTIME_VERIFICATION_LOGS,
    check_and_sanitize_style,
    detect_style_violations,
    ensure_timestamp_in_sentence,
    record_verification_log,
)

DEFAULT_GCS_BUCKET = "h2gdm-hack26icn-2700-second-ear"
PRIVATE_DIR = Path(__file__).resolve().parent.parent / "private"
PRIVATE_DIR.mkdir(exist_ok=True)
LOCAL_STATE_PATH = PRIVATE_DIR / "wiki_state.json"

FABRICATED_IDS = {
    "person_jihoon",
    "person_soomin",
    "card_real_1",
    "card_pending_1",
    "card_pending_2",
    "mom_real_lunch",
    "sample_lunch_memory",
    "sample_afternoon_memory",
    "sample_korean_memory",
}


def get_gcs_bucket_name() -> str:
    return (
        os.getenv("GCS_BUCKET", DEFAULT_GCS_BUCKET).replace("gs://", "").strip()
        or DEFAULT_GCS_BUCKET
    )


def upload_media_to_gcs_async(local_path: Path, filename: str, content_type: str = "video/mp4") -> None:
    def _upload():
        bucket_name = get_gcs_bucket_name()
        if not bucket_name or not local_path.exists():
            return
        try:
            from google.cloud import storage

            st_client = storage.Client()
            bucket = st_client.bucket(bucket_name)
            blob = bucket.blob(f"media/{filename}")
            blob.upload_from_filename(str(local_path), content_type=content_type)
        except Exception:
            pass

    threading.Thread(target=_upload, daemon=True).start()


def ensure_media_from_gcs(filename: str) -> Optional[Path]:
    safe_name = Path(filename).name
    target = PRIVATE_DIR / safe_name
    if target.exists():
        return target
    bucket_name = get_gcs_bucket_name()
    if not bucket_name:
        return None
    try:
        from google.cloud import storage

        st_client = storage.Client()
        bucket = st_client.bucket(bucket_name)
        blob = bucket.blob(f"media/{safe_name}")
        if blob.exists():
            blob.download_to_filename(str(target))
            return target
    except Exception:
        pass
    return None


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
        self.verification_logs: List[Dict[str, object]] = RUNTIME_VERIFICATION_LOGS
        self.tts_cache: Dict[str, str] = {}

        # Restore persisted user memories, people, moments, QA history from GCS or local file
        self._restore_persisted_state()
        self.evaluate_answer_key()

    def _load_persisted_json(self) -> Optional[Dict[str, object]]:
        bucket_name = get_gcs_bucket_name()
        if bucket_name:
            try:
                from google.cloud import storage

                st_client = storage.Client()
                bucket = st_client.bucket(bucket_name)
                blob = bucket.blob("state/wiki_state.json")
                if blob.exists():
                    raw_text = blob.download_as_text(encoding="utf-8")
                    return json.loads(raw_text)
            except Exception:
                pass
        if LOCAL_STATE_PATH.exists():
            try:
                return json.loads(LOCAL_STATE_PATH.read_text(encoding="utf-8"))
            except Exception:
                pass
        return None

    def _is_fabricated_entry(self, obj_dict: Dict[str, object]) -> bool:
        for key in ("id", "who_id", "source_id", "recording_filename"):
            val = str(obj_dict.get(key, ""))
            if val in FABRICATED_IDS or val.startswith("card_sample_"):
                return True
        who_label = str(obj_dict.get("who_label", "")) + str(obj_dict.get("name_or_role", ""))
        if "김지훈" in who_label or "박수민" in who_label:
            return True
        return False

    def _restore_persisted_state(self) -> None:
        saved = self._load_persisted_json()
        if not saved or not isinstance(saved, dict):
            return

        # 1. Preference
        pref_data = saved.get("preference")
        if isinstance(pref_data, dict):
            try:
                self.preference = UserPreference(**pref_data)
            except Exception:
                pass

        # 2. Additional Works (beyond sprite-fright)
        works_data = saved.get("works")
        if isinstance(works_data, dict):
            for wid, wdict in works_data.items():
                if wid != "sprite-fright" and isinstance(wdict, dict):
                    try:
                        self.works[wid] = WorkNode(**wdict)
                    except Exception:
                        pass

        # 3. Real People & Extra Work Characters (filtering out fabricated sample people)
        people_data = saved.get("people")
        if isinstance(people_data, dict):
            for pid, pdict in people_data.items():
                if not isinstance(pdict, dict) or self._is_fabricated_entry(pdict):
                    continue
                if pid not in self.people:
                    try:
                        self.people[pid] = PersonNode(**pdict)
                    except Exception:
                        pass

        # 4. Real-life Moments & Extra Work Moments
        moments_data = saved.get("moments")
        if isinstance(moments_data, dict):
            for mid, mdict in moments_data.items():
                if not isinstance(mdict, dict) or self._is_fabricated_entry(mdict):
                    continue
                pids = mdict.get("people_ids") or []
                if any(p in FABRICATED_IDS for p in pids):
                    continue
                if mid not in self.moments:
                    try:
                        self.moments[mid] = MomentNode(**mdict)
                    except Exception:
                        pass

        # 5. Memory Cards & Extra Work Cards
        existing_card_ids = {c.id for c in self.cards}
        cards_data = saved.get("cards")
        if isinstance(cards_data, list):
            restored_cards: List[FactCard] = []
            for cdict in cards_data:
                if not isinstance(cdict, dict) or self._is_fabricated_entry(cdict):
                    continue
                cid = str(cdict.get("id", ""))
                if not cid or cid in existing_card_ids or cid.startswith("card_sf_"):
                    continue
                try:
                    fc = FactCard(**cdict)
                    if fc.status == "pending":
                        fc.status = "pending_review"
                    restored_cards.append(fc)
                    existing_card_ids.add(cid)
                except Exception:
                    pass
            if restored_cards:
                self.cards = restored_cards + self.cards

        # 6. QA History
        qa_data = saved.get("qa_history")
        if isinstance(qa_data, list):
            for qdict in qa_data:
                if not isinstance(qdict, dict) or self._is_fabricated_entry(qdict):
                    continue
                if "김지훈" in str(qdict.get("answer_sentence", "")) or "박수민" in str(qdict.get("answer_sentence", "")):
                    continue
                try:
                    self.qa_history.append(QAHistoryItem(**qdict))
                except Exception:
                    pass

        # 7. Verification logs
        v_logs = saved.get("verification_logs") or saved.get("verification_loop_examples")
        if isinstance(v_logs, list):
            existing_sigs = {
                f"{x.get('timestamp')}:{x.get('verified_after')}"
                for x in self.verification_logs
            }
            for v in v_logs:
                if not isinstance(v, dict) or not (v.get("logged_at") or v.get("checked_at")):
                    continue
                draft_str = str(v.get("draft_before", ""))
                if (
                    "박수민" in draft_str
                    or "김지훈" in draft_str
                    or "안경 쓴 소녀가 풀숲에서" in draft_str
                    or "장로 버섯이 화난 듯이" in draft_str
                ):
                    continue
                sig = f"{v.get('timestamp')}:{v.get('verified_after')}"
                if sig not in existing_sigs:
                    self.verification_logs.insert(0, v)
                    existing_sigs.add(sig)

    def apply_preference_to_all_cards(self) -> None:
        for card in self.cards:
            if card.status == "pending":
                card.status = "pending_review"
            draft_before = card.summary_sentence
            violations = detect_style_violations(
                card.summary_sentence, self.preference, card.who_label
            ) + detect_style_violations(
                card.visible_action, self.preference, card.who_label
            )
            cleaned_act, fx1, _ = check_and_sanitize_style(
                card.visible_action, self.preference, fallback_who_intro=card.who_label
            )
            cleaned_sum, fx2, _ = check_and_sanitize_style(
                card.summary_sentence, self.preference, fallback_who_intro=card.who_label
            )
            cleaned_sum, has_ts = ensure_timestamp_in_sentence(cleaned_sum, card.timestamp)
            card.visible_action = cleaned_act
            card.summary_sentence = cleaned_sum
            card.verification.style_violations_fixed += fx1 + fx2
            card.verification.has_source_timestamp = has_ts
            if fx1 + fx2 > 0:
                record_verification_log(
                    timestamp=card.timestamp,
                    draft_before=draft_before,
                    violation_detected=" + ".join(violations) if violations else "설명 방식 변경 적용",
                    verified_after=card.summary_sentence,
                    flash_evidence_passed=card.verification.flash_evidence_passed,
                    flash_evidence_reason=card.verification.flash_evidence_reason,
                    quote_matched=card.verification.quote_matched,
                    has_source_timestamp=has_ts,
                    style_violations_fixed=fx1 + fx2,
                    prepend=True,
                )

    def evaluate_answer_key(self) -> None:
        active_cards = [
            c for c in self.cards if c.status in ("ai_verified", "confirmed")
        ]
        for item in self.answer_key:
            target_sec = mmss_to_seconds(item.query_timestamp)
            best_card = None
            best_score = -999999.0
            for c in active_cards:
                dist = abs(c.timestamp_sec - target_sec)
                score = -float(dist) * 2.0
                searchable = f"{c.summary_sentence} {c.visible_action} {c.utterance} {c.sound_event_and_cause} {c.who_label} {c.voice_traits}"
                for kw in item.expected_keywords:
                    if kw in searchable:
                        score += 80.0
                if score > best_score:
                    best_score = score
                    best_card = c

            if best_card is None:
                item.model_answer = ""
                item.model_timestamp = ""
                item.passed = False
                item.checked_at = now_iso()
                continue

            item.model_answer = best_card.summary_sentence
            item.model_timestamp = best_card.timestamp
            searchable_best = (
                f"{best_card.summary_sentence} {best_card.visible_action} "
                f"{best_card.utterance} {best_card.sound_event_and_cause} "
                f"{best_card.who_label} {best_card.first_timestamp}"
            )
            kw_hits = sum(1 for kw in item.expected_keywords if kw in searchable_best)
            kw_pass = (
                (kw_hits / len(item.expected_keywords)) >= 0.5
                if item.expected_keywords
                else True
            )
            ts_range = item.expected_timestamp_range
            ts_pass = (
                (ts_range[0] <= best_card.timestamp_sec <= ts_range[1])
                if len(ts_range) == 2
                else True
            )
            item.passed = bool(kw_pass and ts_pass)
            item.checked_at = now_iso()

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
            if p.person_type == "real" and not (p.consent and p.consent_granted)
        )

        unconfirmed_writes = sum(
            1
            for c in self.cards
            if c.card_type == "memory_card"
            and c.status == "confirmed"
            and c.confirmed_by != "user"
        )

        style_remaining = sum(
            len(detect_style_violations(c.summary_sentence, self.preference, c.who_label))
            for c in active_cards
        ) + sum(
            len(detect_style_violations(q.answer_sentence, self.preference, q.who_label))
            for q in self.qa_history
        )

        style_rewrites = sum(
            c.verification.style_violations_fixed for c in self.cards
        ) + sum(q.verification.style_violations_fixed for q in self.qa_history)

        ak_total = len(self.answer_key)
        ak_passed = sum(1 for a in self.answer_key if a.passed is True)
        ak_accuracy = round(100.0 * ak_passed / ak_total, 1) if ak_total > 0 else 0.0

        memory_cards = [
            c for c in self.cards if c.card_type == "memory_card" and not c.is_example_data
        ]
        reviewed_cards = [
            c for c in memory_cards if c.status in ("confirmed", "discarded")
        ]
        confirmed_cards = [c for c in memory_cards if c.status == "confirmed"]
        discarded_cards = [c for c in memory_cards if c.status == "discarded"]

        ev_rate = (
            round(100.0 * evidence_passed / total_checked, 1)
            if total_checked > 0
            else 0.0
        )
        q_rate = (
            round(100.0 * quote_matched / quote_checked, 1)
            if quote_checked > 0
            else 0.0
        )
        cit_rate = (
            round(100.0 * (total_checked - unsourced) / total_checked, 1)
            if total_checked > 0
            else 0.0
        )
        human_conf_rate = (
            round(100.0 * len(confirmed_cards) / len(reviewed_cards), 1)
            if reviewed_cards
            else 0.0
        )

        return DashboardMetrics(
            evidence_checked_total=total_checked,
            evidence_passed_total=evidence_passed,
            evidence_pass_rate=ev_rate,
            quote_checked_total=quote_checked,
            quote_matched_total=quote_matched,
            quote_match_rate=q_rate,
            quote_accuracy=q_rate,
            citation_rate=cit_rate,
            unsourced_sentences=unsourced,
            unconsented_people_saved=unconsented,
            unconsented_new_people=unconsented,
            unconfirmed_wiki_writes=unconfirmed_writes,
            style_violations_remaining=style_remaining,
            style_auto_rewrites=style_rewrites,
            answer_key_total=ak_total,
            answer_key_passed=ak_passed,
            answer_key_accuracy=ak_accuracy,
            human_reviewed_total=len(reviewed_cards),
            human_confirmed_total=len(confirmed_cards),
            human_discarded_total=len(discarded_cards),
            human_confirmation_rate=human_conf_rate,
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

        for c in active_cards:
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

        raw_bucket = get_gcs_bucket_name()

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
            "verification_loop_examples": list(self.verification_logs[:25]),
            "verification_logs": list(self.verification_logs[:25]),
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
            bucket_name = get_gcs_bucket_name()
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
