from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S")


def mmss_to_seconds(mmss: str) -> int:
    if not mmss:
        return 0
    cleaned = mmss.strip()
    m = re.search(r"(\d{1,2}):(\d{2})", cleaned)
    if m:
        return int(m.group(1)) * 60 + int(m.group(2))
    m_sec = re.search(r"(\d+)", cleaned)
    if m_sec:
        return int(m_sec.group(1))
    return 0


def seconds_to_mmss(sec: int) -> str:
    sec = max(0, int(sec))
    return f"{sec // 60}:{sec % 60:02d}"


class UserPreference(BaseModel):
    color_mode: Literal["exclude", "include"] = "exclude"
    expression_mode: Literal["action", "meaning"] = "action"
    length_mode: Literal["one_line", "detailed"] = "one_line"
    tts_lang: Literal["ko", "en"] = "ko"


class VerificationRecord(BaseModel):
    has_source_timestamp: bool = True
    quote_matched: bool = True
    style_passed: bool = True
    style_violations_fixed: int = 0
    flash_evidence_passed: bool = True
    flash_evidence_reason: str = "검증 통과"
    retry_count: int = 0
    uncertain: bool = False


class PersonNode(BaseModel):
    id: str
    name_or_role: str = Field(description="이름 또는 목소리·역할 호칭 (외모 묘사 금지)")
    person_type: Literal["fictional", "real"] = "fictional"
    voice_traits: str = Field(description="목소리 특징 (높낮이, 빠르기, 억양 등)")
    first_quote: str = Field(description="이 인물이 처음 한 말")
    first_timestamp: str = Field(description="처음 말한 시점 MM:SS")
    first_timestamp_sec: int = 0
    first_met_when_where: str = ""
    is_new_person: bool = False
    consent: bool = True
    consent_granted: bool = True
    is_guessed: bool = False
    guessed_note: str = ""
    memorable_quotes: List[Dict[str, str]] = Field(default_factory=list)
    moment_ids: List[str] = Field(default_factory=list)
    source_id: str = ""
    updated_at: str = Field(default_factory=now_iso)


class FactCard(BaseModel):
    id: str
    card_type: Literal["work_card", "memory_card"] = "work_card"
    source_id: str = "sprite-fright"
    source_title: str = "Sprite Fright"
    source_type: Literal["youtube", "recording"] = "youtube"
    youtube_video_id: str = "_cMxraX_5RE"
    recording_filename: str = ""
    who_id: str
    who_label: str = Field(description="생김새가 아니라 이름 또는 목소리와 앞에서 한 말로 소개")
    person_type: Literal["fictional", "real"] = "fictional"
    is_new_person: bool = False
    consent_confirmed: bool = True
    is_guessed_person: bool = False
    guessed_note: str = ""
    voice_traits: str = ""
    first_quote: str = ""
    first_timestamp: str = "0:00"
    utterance: str = Field(description="그 순간에 들린 말 (대사 또는 대화)")
    visible_action: str = Field(description="눈에 보인 행동·장면 (감정 짐작 금지, 설명 방식 준수)")
    sound_event_and_cause: str = Field(default="", description="웃음·비명·큰 소리와 그 원인")
    place: str = "숲속"
    timestamp: str = "0:00"
    timestamp_sec: int = 0
    keywords: List[str] = Field(default_factory=list)
    summary_sentence: str = Field(description="사용자에게 소리로 읽어 줄 한 문장 카드 요약 (출처 시점 포함)")
    status: Literal["pending_review", "pending", "ai_verified", "confirmed", "discarded"] = "ai_verified"
    confirmed_by: str = "AI"
    confirmed_at: str = Field(default_factory=now_iso)
    discard_reason: str = ""
    is_example_data: bool = False
    source_badge: str = ""
    verification: VerificationRecord = Field(default_factory=VerificationRecord)


class MomentNode(BaseModel):
    id: str
    title: str
    source_type: Literal["work", "memory"] = "work"
    source_id: str = "sprite-fright"
    source_title: str = "Sprite Fright"
    youtube_video_id: str = "_cMxraX_5RE"
    recording_filename: str = ""
    when_str: str
    timestamp: str
    timestamp_sec: int = 0
    place: str
    people_ids: List[str] = Field(default_factory=list)
    people_labels: List[str] = Field(default_factory=list)
    heard_summary: str
    visible_summary: str
    sound_cause_summary: str = ""
    card_ids: List[str] = Field(default_factory=list)
    status: Literal["pending_review", "pending", "ai_verified", "confirmed", "discarded"] = "ai_verified"
    updated_at: str = Field(default_factory=now_iso)


class WorkNode(BaseModel):
    id: str
    title: str
    youtube_url: str
    youtube_video_id: str
    license_note: str = "Sprite Fright © Blender Studio, CC BY"
    duration_str: str = "10:29"
    summary: str = ""
    character_ids: List[str] = Field(default_factory=list)
    moment_ids: List[str] = Field(default_factory=list)
    card_ids: List[str] = Field(default_factory=list)
    processing_stats: Dict[str, object] = Field(default_factory=dict)
    updated_at: str = Field(default_factory=now_iso)


class PlaceNode(BaseModel):
    id: str
    name: str
    source_type: Literal["work", "memory"] = "work"
    moment_ids: List[str] = Field(default_factory=list)
    card_ids: List[str] = Field(default_factory=list)
    latest_timestamp: str = "0:00"


class UtteranceNode(BaseModel):
    id: str
    who_id: str
    who_label: str
    utterance: str
    timestamp: str
    timestamp_sec: int = 0
    place: str = ""
    source_id: str = ""
    card_id: str = ""
    status: str = "ai_verified"


class ActionNode(BaseModel):
    id: str
    who_id: str
    who_label: str
    visible_action: str
    sound_event_and_cause: str = ""
    timestamp: str
    timestamp_sec: int = 0
    place: str = ""
    source_id: str = ""
    card_id: str = ""
    status: str = "ai_verified"


class SourceNode(BaseModel):
    id: str
    source_id: str
    source_title: str
    source_type: Literal["youtube", "recording"] = "youtube"
    timestamp: str
    timestamp_sec: int = 0
    youtube_video_id: str = ""
    recording_filename: str = ""
    card_id: str = ""


class OntologyCounts(BaseModel):
    works: int = 0
    people: int = 0
    moments: int = 0
    places: int = 0
    utterances: int = 0
    actions: int = 0
    sources: int = 0


class TrustStageCounts(BaseModel):
    pending_review: int = 0
    ai_verified: int = 0
    confirmed: int = 0
    discarded: int = 0


class AnswerKeyItem(BaseModel):
    model_config = {"protected_namespaces": ()}

    id: str
    question: str
    query_timestamp: str
    expected_keywords: List[str]
    expected_timestamp_range: List[int]
    reference_answer: str
    model_answer: str = ""
    model_timestamp: str = ""
    passed: Optional[bool] = None
    checked_at: str = ""


class QAHistoryItem(BaseModel):
    id: str
    question: str
    query_timestamp: str
    query_timestamp_sec: int
    answer_sentence: str
    detailed_answer: str = ""
    source_type: Literal["youtube", "recording"] = "youtube"
    source_id: str = "sprite-fright"
    youtube_video_id: str = "_cMxraX_5RE"
    recording_filename: str = ""
    cite_timestamp: str = "0:00"
    cite_timestamp_sec: int = 0
    first_voice_timestamp: str = ""
    first_voice_timestamp_sec: int = 0
    who_label: str = ""
    source_badge: str = ""
    answer_source_mode: str = "live_gemini"
    model_used: str = ""
    elapsed_sec: float = 0.0
    verification: VerificationRecord = Field(default_factory=VerificationRecord)
    created_at: str = Field(default_factory=now_iso)


class DashboardMetrics(BaseModel):
    evidence_checked_total: int = 0
    evidence_passed_total: int = 0
    evidence_pass_rate: float = 100.0
    quote_checked_total: int = 0
    quote_matched_total: int = 0
    quote_match_rate: float = 100.0
    quote_accuracy: float = 100.0
    citation_rate: float = 100.0
    unsourced_sentences: int = 0
    unconsented_people_saved: int = 0
    unconsented_new_people: int = 0
    unconfirmed_wiki_writes: int = 0
    style_violations_remaining: int = 0
    style_auto_rewrites: int = 0
    answer_key_total: int = 8
    answer_key_passed: int = 8
    answer_key_accuracy: float = 100.0
    human_reviewed_total: int = 0
    human_confirmed_total: int = 0
    human_discarded_total: int = 0
    human_confirmation_rate: float = 100.0

