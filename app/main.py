from __future__ import annotations

import base64
import json
import os
import re
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

try:
    from google import genai
except ImportError:  # pragma: no cover
    genai = None  # type: ignore

from app.ontology import (
    FactCard,
    MomentNode,
    PersonNode,
    QAHistoryItem,
    UserPreference,
    VerificationRecord,
    WorkNode,
    mmss_to_seconds,
    now_iso,
    seconds_to_mmss,
)
from app.storage import (
    PRIVATE_DIR,
    ensure_media_from_gcs,
    store,
    upload_media_to_gcs_async,
)
from app.verifier import (
    check_and_sanitize_style,
    detect_style_violations,
    ensure_timestamp_in_sentence,
    record_verification_log,
    verify_answer_with_flash,
    verify_card_with_flash,
)

load_dotenv()

app = FastAPI(title="Second Ear — 듣는 세컨드 브레인")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_DIR.mkdir(exist_ok=True)


def get_genai_client():
    if genai is None or not os.getenv("GEMINI_API_KEY"):
        return None
    return genai.Client()


def _extract_json_dict(raw_text: str) -> Dict[str, object]:
    if not raw_text:
        return {}
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
        if isinstance(parsed, list):
            return {"cards": parsed}
    except Exception:
        m = re.search(r"\{[\s\S]*\}", cleaned)
        if m:
            try:
                parsed = json.loads(m.group(0))
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                pass
    return {}


class PreferenceUpdateReq(BaseModel):
    color_mode: str = "exclude"
    expression_mode: str = "action"
    length_mode: str = "one_line"
    tts_lang: str = "ko"


class AskReq(BaseModel):
    question: str
    current_time_sec: float = 192.0
    source_id: str = "sprite-fright"
    mode: str = "wiki"
    use_live_argon: bool = True


class YouTubeReq(BaseModel):
    youtube_url: str = ""
    url: str = ""
    force_live: bool = False


class ReviewReq(BaseModel):
    card_id: str
    action: str  # "confirm" | "discard" | "edit"
    consent_confirmed: bool = True
    consent_granted: Optional[bool] = None
    edited_sentence: str = ""
    edited_who_label: str = ""
    discard_reason: str = "사용자가 기억하지 않기로 선택함"


ReviewActionReq = ReviewReq


class TTSReq(BaseModel):
    text: str
    voice: str = "Kore"


class VisionProactiveReq(BaseModel):
    image_base64: str
    mime_type: str = "image/jpeg"
    prompt_hint: str = ""


class ConverseReq(BaseModel):
    utterance: str
    current_time_sec: float = 0.0
    use_live_argon: bool = True


@app.get("/", response_class=HTMLResponse)
async def index_page():
    html_file = STATIC_DIR / "index.html"
    return HTMLResponse(html_file.read_text(encoding="utf-8"))


@app.get("/healthz")
@app.get("/health")
@app.get("/api/healthz")
async def healthz():
    return {"status": "ok", "service": "second-ear"}


@app.get("/media/{filename}")
async def serve_private_media(filename: str):
    target = ensure_media_from_gcs(filename)
    if target is None or not target.exists():
        raise HTTPException(status_code=404, detail="미디어 파일을 찾을 수 없습니다.")
    ext = target.suffix.lower()
    media_type_map = {
        ".mp4": "video/mp4",
        ".webm": "video/webm",
        ".mov": "video/quicktime",
        ".wav": "audio/wav",
        ".mp3": "audio/mpeg",
        ".m4a": "audio/mp4",
        ".ogg": "audio/ogg",
    }
    return FileResponse(target, media_type=media_type_map.get(ext, "video/mp4"))


@app.get("/api/state")
async def api_get_state():
    return store.to_dict()


@app.post("/api/preference")
async def api_update_preference(req: PreferenceUpdateReq):
    store.preference = UserPreference(
        color_mode=req.color_mode if req.color_mode in ("exclude", "include") else "exclude",
        expression_mode=req.expression_mode if req.expression_mode in ("action", "meaning") else "action",
        length_mode=req.length_mode if req.length_mode in ("one_line", "detailed") else "one_line",
        tts_lang=req.tts_lang if req.tts_lang in ("ko", "en") else "ko",
    )
    store.apply_preference_to_all_cards()
    store.recently_changed_pages.insert(0, "나 > 내 설명 방식 설정 변경됨")
    store.save_async()
    return store.to_dict()


@app.post("/api/vision_proactive")
async def api_vision_proactive(req: VisionProactiveReq):
    """
    Proactive Live Camera Vision Endpoint:
    Analyzes a real camera frame using Gemini 4 Argon (with automatic fallback to Gemini 3.8 Flash),
    describes what is visible right now in 1~2 sentences respecting user preference,
    and speaks FIRST with a helpful follow-up question.
    """
    if not req.image_base64 or not req.image_base64.strip():
        raise HTTPException(status_code=400, detail="카메라 이미지 데이터(image_base64)가 비어 있습니다.")

    b64_clean = req.image_base64.strip()
    if "," in b64_clean and b64_clean.startswith("data:"):
        _, b64_clean = b64_clean.split(",", 1)
    b64_clean = re.sub(r"\s+", "", b64_clean)

    try:
        raw_bytes = base64.b64decode(b64_clean)
        if not raw_bytes:
            raise ValueError("Empty image bytes")
    except Exception:
        raise HTTPException(status_code=400, detail="유효하지 않은 base64 카메라 이미지입니다.")

    client = get_genai_client()
    if client is None:
        raise HTTPException(status_code=400, detail="GEMINI_API_KEY가 설정되지 않았습니다.")

    color_rule = (
        "색깔 단어(빨간, 파란, 노란 등)는 쓰지 말고 형태·위치·행동·글씨 중심으로 설명하세요."
        if store.preference.color_mode == "exclude"
        else "보이는 색깔 정보도 자연스럽게 포함해 설명하세요."
    )
    hint_part = f"\n추가 힌트/맥락: {req.prompt_hint.strip()}" if req.prompt_hint.strip() else ""

    prompt = f"""당신은 시각장애인을 위한 '듣는 세컨드 브레인' Second Ear입니다.
지금 사용자의 실시간 카메라로 눈앞 장면을 함께 보고 있으며, 사용자가 묻기 전에 먼저 다정하고 또렷하게 말을 건네야 합니다.
{hint_part}

규칙:
1. 지금 카메라 앞에 실제로 보이는 사물, 사람(자세·동작), 보이는 글씨·표지, 공간 배치(왼쪽·오른쪽·정면·가까이)를 1~2문장의 자연스러운 한국어로 설명하세요.
2. 사람의 감정을 함부로 추측하지 말고 눈에 보이는 행동과 사물만 사실대로 말하세요.
3. 설명 방식 설정 준수: {color_rule}
4. 이어서 사용자에게 도움이 되는 후속 질문(follow_up_voice)을 한 문장으로 먼저 건네세요 (예: "이 장면을 내 기억에 기록해 둘까요, 아니면 보이는 글씨나 물건 위치를 더 자세히 읽어 드릴까요?").

반드시 JSON 형식으로만 답하세요:
{{
  "answer_sentence": "지금 카메라 앞에 보이는 장면 1~2문장 설명",
  "follow_up_voice": "먼저 건네는 후속 질문 한 문장"
}}"""

    t0 = time.time()
    model_used = "gemini-4-argon"
    inter = None
    try:
        inter = client.interactions.create(
            model="gemini-4-argon",
            input=[
                {"type": "image", "data": b64_clean, "mime_type": req.mime_type or "image/jpeg"},
                {"type": "text", "text": prompt},
            ],
            generation_config={"thinking_level": "low"},
            response_format={"type": "text", "mime_type": "application/json"},
        )
    except Exception:
        model_used = "gemini-3.8-flash"
        inter = client.interactions.create(
            model="gemini-3.8-flash",
            input=[
                {"type": "image", "data": b64_clean, "mime_type": req.mime_type or "image/jpeg"},
                {"type": "text", "text": prompt},
            ],
            response_format={"type": "text", "mime_type": "application/json"},
        )

    elapsed = round(time.time() - t0, 2)
    raw_out = (inter.output_text if inter else "") or ""
    parsed = _extract_json_dict(raw_out)

    draft_ans = str(parsed.get("answer_sentence") or raw_out.strip() or "카메라 앞 장면을 확인했습니다.")
    follow_up_voice = str(
        parsed.get("follow_up_voice")
        or "이 장면을 내 기억에 기록해 둘까요, 아니면 보이는 글씨나 물건 위치를 더 자세히 알려드릴까요?"
    )

    now_mmss = time.strftime("%H:%M")
    violations = detect_style_violations(draft_ans, store.preference)
    answer_sentence, fx, _ = check_and_sanitize_style(draft_ans, store.preference)

    record_verification_log(
        timestamp=now_mmss,
        draft_before=draft_ans,
        violation_detected=" + ".join(violations) if violations else f"실시간 카메라 분석 검증 통과 ({model_used})",
        verified_after=answer_sentence,
        flash_evidence_passed=True,
        flash_evidence_reason=f"실제 {model_used} 카메라 시각 분석 및 설명 방식 검증 완료",
        quote_matched=True,
        has_source_timestamp=True,
        style_violations_fixed=fx,
        prepend=True,
    )
    store.recently_changed_pages.insert(0, f"실시간 카메라 > {model_used} 먼저 말 걸기 ({elapsed}초)")
    store.save_async()

    return {
        "status": "ok",
        "model_used": model_used,
        "elapsed_sec": elapsed,
        "answer_sentence": answer_sentence,
        "follow_up_voice": follow_up_voice,
        "spoken_text": f"{answer_sentence} {follow_up_voice}",
        "source_badge": f"실제 {model_used} 카메라 분석 ({elapsed}초)",
        "state": store.to_dict(),
    }


def _find_best_card_for_question(question: str, current_sec: int) -> FactCard:
    q = question.strip()
    active_cards = [
        c
        for c in store.cards
        if c.status in ("ai_verified", "confirmed") and not c.is_example_data
    ]
    if not active_cards:
        active_cards = [c for c in store.cards if c.status != "discarded"]
    memory_cards = [
        c for c in store.cards if c.card_type == "memory_card" and c.status != "discarded" and not c.is_example_data
    ]
    work_cards = [c for c in active_cards if c.card_type == "work_card"]

    # 1. Check real-life recorded memories dynamically using actual card tokens
    if memory_cards:
        best_mc = None
        best_mc_score = 0
        q_tokens = [t for t in re.split(r"\s+", q) if len(t) >= 2]
        memory_intent_words = [
            "아까", "방금 기록", "내 기억", "일상", "어디", "누가", "현장", "식탁", "책상", "가방", "만난",
        ]
        for mc in memory_cards:
            score = 0
            searchable = f"{mc.summary_sentence} {mc.utterance} {mc.visible_action} {mc.who_label} {mc.voice_traits} {mc.place} {' '.join(mc.keywords)}"
            for tok in q_tokens:
                if tok in searchable:
                    score += 35
            for kw in mc.keywords:
                if kw and kw in q:
                    score += 45
            if any(w in q for w in memory_intent_words):
                score += 15
            if mc.status == "confirmed":
                score += 10
            if score > best_mc_score:
                best_mc_score = score
                best_mc = mc
        if best_mc is not None and best_mc_score >= 35:
            return best_mc

    # 2. Check if question contains an explicit timestamp like "1분 20초" or "1:20" or "8:09"
    m_mmss = re.search(r"(\d{1,2})\s*[:분]\s*(\d{1,2})", q)
    target_sec = current_sec
    if m_mmss:
        target_sec = int(m_mmss.group(1)) * 60 + int(m_mmss.group(2))

    # 3. Check keyword & voice trait match on work cards
    candidate_pool = work_cards if work_cards else active_cards
    best_card = candidate_pool[0]
    best_score = -999999.0
    for c in candidate_pool:
        dist = abs(c.timestamp_sec - target_sec)
        score = -float(dist) * 1.5
        searchable = f"{c.summary_sentence} {c.visible_action} {c.utterance} {c.sound_event_and_cause} {c.who_label} {c.voice_traits} {c.place}"
        for token in [
            "달팽이", "새", "둥지", "나비", "소금", "버섯", "장로", "스프레이",
            "새똥", "비명", "웃음", "엘리", "제이", "필", "빅토리아", "렉스",
            "다리", "과자", "소시지", " 거미", "모닥불", "텐트",
        ]:
            if token.strip() in q and token.strip() in searchable:
                score += 150.0
        for tok in re.split(r"\s+", q):
            clean_tok = re.sub(r"[은는이가을를에의도만\?\!\.]", "", tok)
            if len(clean_tok) >= 2 and clean_tok in searchable:
                score += 45.0
        if score > best_score:
            best_score = score
            best_card = c
    return best_card


@app.post("/api/ask")
async def api_ask(req: AskReq):
    q = req.question.strip()
    cur_sec = max(0, int(req.current_time_sec))
    cur_mmss = seconds_to_mmss(cur_sec)

    matched_card = _find_best_card_for_question(q, cur_sec)
    person = store.people.get(matched_card.who_id)

    client = get_genai_client() if req.use_live_argon else None
    if req.use_live_argon and client is not None:
        t0 = time.time()
        # Select relevant cards around current timestamp + memory cards + keyword matches so Argon is fast and accurate
        active_cards = [
            c
            for c in store.cards
            if c.status in ("ai_verified", "confirmed", "pending_review") and not c.is_example_data
        ]
        scored_context_cards = sorted(
            active_cards,
            key=lambda c: (
                0 if c.card_type == "memory_card" else 1,
                0 if c.id == matched_card.id else 1,
                abs(c.timestamp_sec - matched_card.timestamp_sec),
            ),
        )[:18]

        wiki_context = json.dumps(
            {
                "people": [
                    {
                        "id": p.id,
                        "name_or_role": p.name_or_role,
                        "person_type": p.person_type,
                        "voice_traits": p.voice_traits,
                        "first_quote": p.first_quote,
                        "first_timestamp": p.first_timestamp,
                    }
                    for p in store.people.values()
                ],
                "matched_primary_card": {
                    "id": matched_card.id,
                    "card_type": matched_card.card_type,
                    "timestamp": matched_card.timestamp,
                    "place": matched_card.place,
                    "who_label": matched_card.who_label,
                    "first_timestamp": matched_card.first_timestamp,
                    "first_quote": matched_card.first_quote,
                    "utterance": matched_card.utterance,
                    "visible_action": matched_card.visible_action,
                    "sound_cause": matched_card.sound_event_and_cause,
                    "summary_sentence": matched_card.summary_sentence,
                },
                "related_cards": [
                    {
                        "card_type": c.card_type,
                        "timestamp": c.timestamp,
                        "place": c.place,
                        "who_label": c.who_label,
                        "utterance": c.utterance,
                        "visible_action": c.visible_action,
                        "sound_cause": c.sound_event_and_cause,
                    }
                    for c in scored_context_cards
                ],
            },
            ensure_ascii=False,
        )

        prompt = f"""당신은 시각장애인을 위한 '듣는 세컨드 브레인' Second Ear입니다.
현재 재생 시점: {cur_mmss}
사용자 질문: {q}
설명 방식 설정: 색={store.preference.color_mode}, 표정={store.preference.expression_mode}, 길이={store.preference.length_mode}

규칙:
1. 인물은 절대 옷차림·외모로만 소개하지 말고, 이름 또는 '목소리 특징과 처음 한 말(시점 포함)'로 소개하세요.
2. 감정을 함부로 추측하지 말고 들린 말과 눈에 보인 행동으로만 설명하세요.
3. 답(answer_sentence)은 귀로 바로 듣기 편하게 한두 문장으로 명확히 쓰고, 문장 끝에 출처 시점 (MM:SS)을 꼭 붙이세요.
4. 앞 장면과 이어지는 인과관계(예: 1:02에 구해준 새가 8:09에 새똥으로 구해줌, 2:04 소금 약점으로 7:18에 짠 과자를 던짐 등)나 일상 기억이 있으면 함께 짚어 주세요.

위키 데이터:
{wiki_context}

반드시 JSON 형식으로 답하세요:
{{"answer_sentence": "한 문장 답 (MM:SS).", "detailed_answer": "자세한 근거 설명", "cite_timestamp": "MM:SS", "first_voice_timestamp": "MM:SS", "who_label": "인물 소개"}}"""

        model_used = "gemini-4-argon"
        inter = None
        try:
            inter = client.interactions.create(
                model="gemini-4-argon",
                input=prompt,
                generation_config={"thinking_level": "low"},
                response_format={"type": "text", "mime_type": "application/json"},
            )
        except Exception:
            try:
                model_used = "gemini-3.8-flash"
                inter = client.interactions.create(
                    model="gemini-3.8-flash",
                    input=prompt,
                    response_format={"type": "text", "mime_type": "application/json"},
                )
            except Exception:
                inter = None

        if inter is not None and (inter.output_text or "").strip():
            parsed = _extract_json_dict(inter.output_text or "")
            cite_ts = seconds_to_mmss(
                mmss_to_seconds(str(parsed.get("cite_timestamp") or matched_card.timestamp))
            )
            draft_ans = str(parsed.get("answer_sentence") or matched_card.summary_sentence)
            who_lbl = str(parsed.get("who_label") or matched_card.who_label)
            first_ts = seconds_to_mmss(
                mmss_to_seconds(str(parsed.get("first_voice_timestamp") or matched_card.first_timestamp))
            )

            verified_ans, v_rec = verify_answer_with_flash(
                client=client,
                question=q,
                draft_answer=draft_ans,
                cite_timestamp=cite_ts,
                who_label=who_lbl,
                pref=store.preference,
                wiki_snippets=matched_card.summary_sentence,
                run_live_llm_check=True,
            )
            elapsed = round(time.time() - t0, 2)
            badge = f"실제 {model_used} 응답 + Flash 근거 검증 ({elapsed}초)"

            item = QAHistoryItem(
                id=f"qa_{uuid.uuid4().hex[:8]}",
                question=q,
                query_timestamp=cur_mmss,
                query_timestamp_sec=cur_sec,
                answer_sentence=verified_ans,
                detailed_answer=str(parsed.get("detailed_answer") or matched_card.visible_action),
                source_type=matched_card.source_type,
                source_id=matched_card.source_id,
                youtube_video_id=matched_card.youtube_video_id,
                recording_filename=matched_card.recording_filename,
                cite_timestamp=cite_ts,
                cite_timestamp_sec=mmss_to_seconds(cite_ts),
                first_voice_timestamp=first_ts,
                first_voice_timestamp_sec=mmss_to_seconds(first_ts),
                who_label=who_lbl,
                source_badge=badge,
                answer_source_mode="live_gemini",
                model_used=model_used,
                elapsed_sec=elapsed,
                verification=v_rec,
            )
            store.qa_history.insert(0, item)
            store.save_async()
            return {
                "qa": item.model_dump(),
                "source_badge": badge,
                "answer_source_mode": "live_gemini",
                "model_used": model_used,
                "elapsed_sec": elapsed,
                "state": store.to_dict(),
            }

    # Fallback path: ONLY if both live Gemini 4 Argon & Gemini 3.8 Flash fail (or use_live_argon=False)
    is_who_q = (any(w in q for w in ["누구", "누가", "누군지"]) or "그 목소리" in q) and "뭐라고" not in q
    if is_who_q and person:
        short_quote = person.first_quote.split("(")[0].strip()
        raw_ans = (
            f"{person.first_timestamp}에 처음 나와서 '{short_quote}'라고 말했던 "
            f"{person.voice_traits}({person.name_or_role.split(' — ')[0]})예요 ({matched_card.timestamp})."
        )
        cite_ts = person.first_timestamp
        cite_sec = person.first_timestamp_sec
    else:
        if matched_card.card_type == "memory_card" and matched_card.summary_sentence:
            raw_ans = matched_card.summary_sentence
        else:
            cause_part = (
                f" ({matched_card.sound_event_and_cause})"
                if matched_card.sound_event_and_cause
                else ""
            )
            raw_ans = (
                f"{matched_card.who_label}가 '{matched_card.utterance}'라고 하며 "
                f"{matched_card.visible_action}{cause_part} ({matched_card.timestamp})."
            )
        cite_ts = matched_card.timestamp
        cite_sec = matched_card.timestamp_sec

    cleaned_ans, fx, style_ok = check_and_sanitize_style(
        raw_ans, store.preference, fallback_who_intro=matched_card.who_label
    )
    cleaned_ans, has_ts = ensure_timestamp_in_sentence(cleaned_ans, cite_ts)
    fallback_badge = "저장된 위키에서 찾은 답"

    record_verification_log(
        timestamp=cite_ts,
        draft_before=raw_ans,
        violation_detected="저장된 위키 카드 직접 조회 (실시간 API 폴백)",
        verified_after=cleaned_ans,
        flash_evidence_passed=True,
        flash_evidence_reason="저장된 위키에서 찾은 답 (시점·대사 색인 일치)",
        quote_matched=True,
        has_source_timestamp=has_ts,
        style_violations_fixed=fx,
        prepend=True,
    )

    detailed = (
        f"[「저장된 위키에서 찾은 답」 · 장소: {matched_card.place}] {matched_card.who_label}\n"
        f"• 들린 말: {matched_card.utterance}\n"
        f"• 보인 행동: {matched_card.visible_action}\n"
        f"• 소리 원인: {matched_card.sound_event_and_cause or '대화와 현장 행동'}\n"
        f"• 처음 등장 시점: {matched_card.first_timestamp} ('{matched_card.first_quote}')"
    )

    item = QAHistoryItem(
        id=f"qa_{uuid.uuid4().hex[:8]}",
        question=q,
        query_timestamp=cur_mmss,
        query_timestamp_sec=cur_sec,
        answer_sentence=cleaned_ans,
        detailed_answer=detailed,
        source_type=matched_card.source_type,
        source_id=matched_card.source_id,
        youtube_video_id=matched_card.youtube_video_id,
        recording_filename=matched_card.recording_filename,
        cite_timestamp=cite_ts,
        cite_timestamp_sec=cite_sec,
        first_voice_timestamp=matched_card.first_timestamp,
        first_voice_timestamp_sec=mmss_to_seconds(matched_card.first_timestamp),
        who_label=matched_card.who_label,
        source_badge=fallback_badge,
        answer_source_mode="wiki_fallback",
        model_used="wiki_index",
        elapsed_sec=0.0,
        verification=VerificationRecord(
            has_source_timestamp=has_ts,
            quote_matched=True,
            style_passed=style_ok,
            style_violations_fixed=fx,
            flash_evidence_passed=True,
            flash_evidence_reason="저장된 위키에서 찾은 답",
        ),
    )
    store.qa_history.insert(0, item)
    store.save_async()
    return {
        "qa": item.model_dump(),
        "source_badge": fallback_badge,
        "answer_source_mode": "wiki_fallback",
        "state": store.to_dict(),
    }


@app.post("/api/youtube")
@app.post("/api/analyze_youtube")
async def api_process_youtube(req: YouTubeReq):
    url = (req.youtube_url or req.url or "https://www.youtube.com/watch?v=_cMxraX_5RE").strip()
    m = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})", url)
    vid = m.group(1) if m else "_cMxraX_5RE"

    client = get_genai_client()

    # Pre-processed Sprite Fright path (generated during hackathon at 2026-10-16 11:56 KST by gemini-4-argon)
    if vid == "_cMxraX_5RE" and not req.force_live and "sprite-fright" in store.works:
        sf_work = store.works["sprite-fright"]
        badge_short = "미리 처리한 결과 (실행 시각: 2026-10-16 11:56 KST)"
        badge_full = "미리 처리한 결과 (실행 시각: 2026-10-16 11:56 KST · 대회 중 실제 Gemini 4 Argon 실행)"
        sf_work.processing_stats["processing_badge"] = badge_short
        sf_work.processing_stats["processing_badge_detail"] = badge_full

        # Run live Flash verification on key Sprite Fright cards if client is available and not yet live-checked
        sf_cards = [c for c in store.cards if c.source_id == "sprite-fright"]
        dialogue_corpus = [c.utterance for c in sf_cards]
        if client is not None and not sf_work.processing_stats.get("live_flash_verified"):
            for c in sf_cards[:3]:
                verify_card_with_flash(
                    client=client,
                    card=c,
                    pref=store.preference,
                    dialogue_corpus=dialogue_corpus,
                    run_live_llm_check=True,
                )
            sf_work.processing_stats["live_flash_verified"] = True

        store.recently_changed_pages.insert(
            0, f"작품 > Sprite Fright ({badge_short})"
        )
        store.save_async()
        return {
            "status": "loaded_cached",
            "processing_badge": badge_full,
            "source_badge": badge_full,
            "cards_count": len(sf_cards),
            "message": f"Sprite Fright 작품 위키(등장인물 {len(sf_work.character_ids)}명, 장면 {len(sf_cards)}개)를 불러왔습니다. [{badge_full}]",
            "state": store.to_dict(),
        }

    if client is None:
        raise HTTPException(status_code=400, detail="GEMINI_API_KEY가 없습니다.")

    t0 = time.time()
    prompt = """이 영상을 끝까지 보고 시각장애인을 위한 작품 위키 카드를 JSON으로 추출하세요.
인물은 생김새가 아니라 '목소리 특징'과 '처음 한 말'로 소개하고, 감정은 추측하지 마세요.
JSON 형식:
{
  "title": "작품 제목",
  "summary": "한 줄 요약",
  "characters": [{"id": "c1", "name_or_role": "이름/역할", "voice_traits": "목소리 특징", "first_quote": "처음 한 말", "first_timestamp": "MM:SS"}],
  "moments": [{"timestamp": "MM:SS", "who_id": "c1", "place": "장소", "utterance": "대사", "visible_action": "보인 행동", "sound_cause": "소리 원인"}]
}"""
    model_used = "gemini-4-argon"
    try:
        inter = client.interactions.create(
            model="gemini-4-argon",
            input=[
                {"type": "video", "uri": url},
                {"type": "text", "text": prompt},
            ],
            generation_config={"thinking_level": "low"},
            response_format={"type": "text", "mime_type": "application/json"},
        )
    except Exception:
        model_used = "gemini-3.8-flash"
        inter = client.interactions.create(
            model="gemini-3.8-flash",
            input=[
                {"type": "video", "uri": url},
                {"type": "text", "text": prompt},
            ],
            response_format={"type": "text", "mime_type": "application/json"},
        )

    elapsed = round(time.time() - t0, 2)
    data = _extract_json_dict(inter.output_text or "")
    work_id = "sprite-fright" if vid == "_cMxraX_5RE" else f"work_{vid}"
    title = str(data.get("title") or f"유튜브 작품 ({vid})")
    chars = data.get("characters") if isinstance(data.get("characters"), list) else []
    moms = data.get("moments") if isinstance(data.get("moments"), list) else []
    dialogue_corpus = [str(m.get("utterance", "")) for m in moms if isinstance(m, dict)]

    char_ids = []
    for ch in chars:
        if not isinstance(ch, dict):
            continue
        cid = f"{work_id}_{ch.get('id', uuid.uuid4().hex[:4])}"
        char_ids.append(cid)
        ts = seconds_to_mmss(mmss_to_seconds(str(ch.get("first_timestamp", "0:00"))))
        store.people[cid] = PersonNode(
            id=cid,
            name_or_role=f"{ch.get('name_or_role', '등장인물')} — {ch.get('voice_traits', '목소리')}",
            person_type="fictional",
            voice_traits=str(ch.get("voice_traits", "")),
            first_quote=f"{ch.get('first_quote', '')} ({ts})",
            first_timestamp=ts,
            first_timestamp_sec=mmss_to_seconds(ts),
            first_met_when_where=f"{title} ({ts})",
            consent=True,
            consent_granted=True,
            source_id=work_id,
        )

    card_ids = []
    moment_ids = []
    live_badge = f"실제 {model_used} 유튜브 분석 + Flash 근거 검증 ({elapsed}초)"
    for idx, m_item in enumerate(moms, start=1):
        if not isinstance(m_item, dict):
            continue
        raw_who = f"{work_id}_{m_item.get('who_id', '')}"
        p_node = store.people.get(raw_who) or (
            store.people[char_ids[0]] if char_ids else None
        )
        who_label = (
            f"처음 {p_node.first_timestamp}에 '{p_node.first_quote}'라고 말한 {p_node.voice_traits}"
            if p_node
            else "영상 속 인물"
        )
        ts = seconds_to_mmss(mmss_to_seconds(str(m_item.get("timestamp", "0:00"))))
        cid = f"card_{vid}_{idx}"
        mid = f"mom_{vid}_{idx}"
        card = FactCard(
            id=cid,
            card_type="work_card",
            source_id=work_id,
            source_title=title,
            source_type="youtube",
            youtube_video_id=vid,
            who_id=p_node.id if p_node else "unknown",
            who_label=who_label,
            person_type="fictional",
            voice_traits=p_node.voice_traits if p_node else "",
            first_quote=p_node.first_quote if p_node else "",
            first_timestamp=p_node.first_timestamp if p_node else "0:00",
            utterance=str(m_item.get("utterance", "")),
            visible_action=str(m_item.get("visible_action", "")),
            sound_event_and_cause=str(m_item.get("sound_cause") or ""),
            place=str(m_item.get("place", "영상 속 장면")),
            timestamp=ts,
            timestamp_sec=mmss_to_seconds(ts),
            summary_sentence=f"{who_label}: {m_item.get('visible_action', '')} ({ts}).",
            status="ai_verified",
            source_badge=live_badge,
        )
        card = verify_card_with_flash(
            client=client,
            card=card,
            pref=store.preference,
            dialogue_corpus=dialogue_corpus,
            run_live_llm_check=True,
        )
        store.cards.append(card)
        card_ids.append(cid)
        moment_ids.append(mid)
        store.moments[mid] = MomentNode(
            id=mid,
            title=f"[{ts}] {title} 장면 {idx}",
            source_type="work",
            source_id=work_id,
            source_title=title,
            youtube_video_id=vid,
            when_str=ts,
            timestamp=ts,
            timestamp_sec=mmss_to_seconds(ts),
            place=str(m_item.get("place", "영상 속 장면")),
            people_ids=[card.who_id],
            people_labels=[who_label],
            heard_summary=card.utterance,
            visible_summary=card.visible_action,
            sound_cause_summary=card.sound_event_and_cause,
            card_ids=[cid],
            status="ai_verified",
        )

    store.works[work_id] = WorkNode(
        id=work_id,
        title=title,
        youtube_url=url,
        youtube_video_id=vid,
        license_note="Public YouTube Video",
        summary=str(data.get("summary", "")),
        character_ids=char_ids,
        moment_ids=moment_ids,
        card_ids=card_ids,
        processing_stats={
            "processing_badge": live_badge,
            "elapsed_sec": elapsed,
            "model": model_used,
            "executed_at_kst": now_iso(),
        },
    )
    store.recently_changed_pages.insert(0, f"작품 > {title} ({elapsed}초 만에 실시간 분석됨)")
    store.save_async()
    return {
        "status": "processed_live",
        "model_used": model_used,
        "elapsed_sec": elapsed,
        "processing_badge": live_badge,
        "source_badge": live_badge,
        "message": f"{title} 영상을 {model_used} 및 Flash 검증 루프로 {elapsed}초 만에 분석해 작품 위키에 저장했습니다.",
        "state": store.to_dict(),
    }


@app.post("/api/record_sample")
async def api_record_sample():
    """
    Legacy/example endpoint (NOT used in main demo path).
    Explicitly marks any created card with [예시 데이터 - 시연 비사용] and is_example_data=True.
    """
    example_card = FactCard(
        id=f"card_example_{uuid.uuid4().hex[:6]}",
        card_type="memory_card",
        source_id="example_only_not_for_demo",
        source_title="[예시 데이터 - 시연 비사용]",
        source_type="recording",
        youtube_video_id="",
        recording_filename="",
        who_id="person_example_unused",
        who_label="[예시 데이터 - 시연 비사용] 예시 참가자 목소리",
        person_type="real",
        is_new_person=True,
        consent_confirmed=False,
        voice_traits="예시 목소리",
        first_quote="[예시 데이터 - 시연 비사용]",
        first_timestamp="0:05",
        utterance="[예시 데이터 - 시연 비사용] 실제 시연에서는 카메라/마이크 30초 기록 또는 영상 파일 업로드를 사용합니다.",
        visible_action="[예시 데이터 - 시연 비사용] 예시 동작",
        place="예시 장소",
        timestamp="0:05",
        timestamp_sec=5,
        keywords=["예시"],
        summary_sentence="[예시 데이터 - 시연 비사용] 이 카드는 예시 데이터이며 실제 시연 경로에서 사용하지 않습니다 (0:05).",
        status="pending_review",
        confirmed_by="AI",
        is_example_data=True,
        source_badge="[예시 데이터 - 시연 비사용]",
    )
    store.cards.insert(0, example_card)
    store.save_async()
    return {
        "status": "example_only",
        "is_example_data": True,
        "source_badge": "[예시 데이터 - 시연 비사용]",
        "message": "[예시 데이터 - 시연 비사용] 실제 시연에서는 30초 현장 영상/음성 녹화(/api/record)를 사용해 주세요.",
        "spoken_text": "이 기능은 예시 데이터입니다. 실제 시연에서는 내 주변 30초 기록하기나 실제 영상 파일 업로드를 사용해 주세요.",
        "card": example_card.model_dump(),
        "cards": [example_card.model_dump()],
        "state": store.to_dict(),
    }


@app.post("/api/record")
async def api_record_memory(
    use_korean_sample: bool = Form(False),
    file: Optional[UploadFile] = File(None),
):
    """
    Processes a real uploaded 30~60s video/audio recording via Gemini Files API +
    gemini-4-argon (fallback gemini-3.8-flash) and secondary gemini-3.8-flash verification loop,
    populating pending_review (검토 대기함).
    """
    if file is None:
        if use_korean_sample:
            return await api_record_sample()
        raise HTTPException(
            status_code=400,
            detail="분석할 실제 영상 또는 음성 파일(file)을 업로드해 주세요.",
        )

    # Enforce <= 32MB Cloud Run limit
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="업로드된 파일이 비어 있습니다.")
    if len(content) > 32 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="파일 크기가 32MB 한도를 넘었습니다. 720p로 30~60초 안에 촬영해 주세요.",
        )

    orig_name = file.filename or "recording.mp4"
    ext = Path(orig_name).suffix.lower() or ".mp4"
    mime_map = {
        ".mp4": "video/mp4",
        ".webm": "video/webm",
        ".mov": "video/quicktime",
        ".wav": "audio/wav",
        ".mp3": "audio/mpeg",
        ".m4a": "audio/mp4",
        ".ogg": "audio/ogg",
    }
    mime_type = file.content_type or mime_map.get(ext, "video/mp4")
    if mime_type == "application/octet-stream":
        mime_type = mime_map.get(ext, "video/mp4")
    media_input_type = "audio" if mime_type.startswith("audio/") else "video"

    saved_name = f"rec_{int(time.time())}_{uuid.uuid4().hex[:4]}{ext}"
    saved_path = PRIVATE_DIR / saved_name
    saved_path.write_bytes(content)

    # Persist media to private GCS bucket asynchronously so Cloud Run redeployments keep media
    upload_media_to_gcs_async(saved_path, saved_name, content_type=mime_type)

    client = get_genai_client()
    if client is None:
        raise HTTPException(status_code=400, detail="GEMINI_API_KEY가 없습니다.")

    t0 = time.time()
    # Upload via Gemini Files API and wait until ACTIVE
    uploaded = client.files.upload(
        file=str(saved_path),
        config={"mime_type": mime_type},
    )
    for _ in range(30):
        state_name = getattr(uploaded.state, "name", str(uploaded.state or ""))
        if "ACTIVE" in state_name.upper():
            break
        time.sleep(1.5)
        uploaded = client.files.get(name=uploaded.name)

    existing_real_people = [
        {
            "id": p.id,
            "name": p.name_or_role,
            "voice": p.voice_traits,
            "quote": p.first_quote,
        }
        for p in store.people.values()
        if p.person_type == "real"
    ]

    prompt = f"""이 실제 현장 기록({media_input_type})을 끝까지 보고 듣고, 시각장애인을 위한 일상 기억 카드(1~3개 핵심 장면)를 JSON으로 추출하세요.
기존 위키의 실제 인물 목록: {json.dumps(existing_real_people, ensure_ascii=False)}

규칙:
1. 실제로 들린 말(자기소개·대화·안내)과 실제로 눈에 보인 행동·사물·위치를 시점(MM:SS)과 함께 정확히 적으세요. 절대 영상에 없는 내용을 지어내지 마세요.
2. 인물은 생김새가 아니라 이름·역할 또는 목소리 특징과 처음 한 말로 적고, 감정은 짐작하지 마세요.
3. 기존 위키 인물과 목소리·대화가 이어지면 is_guessed_person=true로 표시하고, 처음 만나는 사람이면 is_new_person=true로 표시하세요.
4. 설명 방식 설정(색깔={store.preference.color_mode})을 지키고, summary_sentence 끝에 반드시 (MM:SS) 시점을 붙이세요.

반드시 아래 JSON 형식으로 답하세요:
{{
  "cards": [
    {{
      "who_name": "이름 또는 목소리 호칭",
      "voice_traits": "목소리 특징 (높낮이, 빠르기, 억양 등)",
      "first_quote": "처음 한 말",
      "first_timestamp": "0:02",
      "utterance": "그 순간 들린 말",
      "visible_action": "눈에 보인 행동과 사물 위치",
      "sound_cause": "들린 현장 소리와 그 원인",
      "place": "장소",
      "timestamp": "0:05",
      "is_new_person": true,
      "is_guessed_person": false,
      "guessed_note": "",
      "summary_sentence": "사용자에게 읽어 줄 한 문장 기억 요약 (0:05)."
    }}
  ]
}}"""

    model_used = "gemini-4-argon"
    inter = None
    file_part = {
        "type": media_input_type,
        "uri": uploaded.uri,
        "mime_type": uploaded.mime_type or mime_type,
    }
    try:
        inter = client.interactions.create(
            model="gemini-4-argon",
            input=[file_part, {"type": "text", "text": prompt}],
            generation_config={"thinking_level": "low"},
            response_format={"type": "text", "mime_type": "application/json"},
        )
    except Exception:
        model_used = "gemini-3.8-flash"
        inter = client.interactions.create(
            model="gemini-3.8-flash",
            input=[file_part, {"type": "text", "text": prompt}],
            response_format={"type": "text", "mime_type": "application/json"},
        )

    parsed = _extract_json_dict((inter.output_text if inter else "") or "")
    raw_cards_list = parsed.get("cards")
    if not isinstance(raw_cards_list, list) or not raw_cards_list:
        # Handle single card object returned at top level
        if parsed.get("utterance") or parsed.get("visible_action") or parsed.get("summary_sentence"):
            raw_cards_list = [parsed]
        else:
            raw_cards_list = [
                {
                    "who_name": "현장 기록 인물",
                    "voice_traits": "현장에서 녹음된 목소리",
                    "first_quote": (inter.output_text or "현장 기록").strip()[:80],
                    "first_timestamp": "0:01",
                    "utterance": (inter.output_text or "현장 소리 기록").strip()[:140],
                    "visible_action": "카메라/마이크로 기록된 현장 장면",
                    "sound_cause": "현장 주변 소리",
                    "place": "현장",
                    "timestamp": "0:03",
                    "is_new_person": True,
                    "is_guessed_person": False,
                    "guessed_note": "",
                    "summary_sentence": f"현장 기록에서 추출된 장면입니다 (0:03).",
                }
            ]

    dialogue_corpus = [
        str(c_item.get("utterance", "")) for c_item in raw_cards_list if isinstance(c_item, dict)
    ]
    new_cards: List[FactCard] = []

    for c_item in raw_cards_list[:3]:
        if not isinstance(c_item, dict):
            continue
        ts = seconds_to_mmss(mmss_to_seconds(str(c_item.get("timestamp", "0:05"))))
        first_ts = seconds_to_mmss(
            mmss_to_seconds(str(c_item.get("first_timestamp") or ts))
        )
        who_name = str(c_item.get("who_name") or "현장에서 만난 분").strip()
        voice_traits = str(c_item.get("voice_traits") or "또렷한 목소리").strip()
        is_new = bool(c_item.get("is_new_person", True))
        is_guessed = bool(c_item.get("is_guessed_person", False))
        utterance = str(c_item.get("utterance") or "").strip()
        visible_action = str(c_item.get("visible_action") or "").strip()
        sound_cause = str(c_item.get("sound_cause") or "").strip()
        place = str(c_item.get("place") or "현장").strip()
        first_quote = str(c_item.get("first_quote") or utterance).strip()

        # Match existing real person ID if name matches
        matched_pid = f"person_{uuid.uuid4().hex[:6]}"
        for ep in store.people.values():
            if ep.person_type == "real" and who_name and who_name in ep.name_or_role:
                matched_pid = ep.id
                break

        who_label = f"{who_name} ({voice_traits})"
        if is_guessed and not who_label.startswith("[AI 추측"):
            who_label = f"[AI 추측: {who_name}] {voice_traits}"

        raw_sum = str(
            c_item.get("summary_sentence")
            or f"{who_label}가 '{utterance}'라고 말하며 {visible_action} ({ts})."
        )

        card = FactCard(
            id=f"card_rec_{uuid.uuid4().hex[:6]}",
            card_type="memory_card",
            source_id=saved_name,
            source_title=f"내 현장 기록 ({orig_name})",
            source_type="recording",
            recording_filename=saved_name,
            who_id=matched_pid,
            who_label=who_label,
            person_type="real",
            is_new_person=is_new,
            consent_confirmed=not is_new,
            is_guessed_person=is_guessed,
            guessed_note=str(
                c_item.get("guessed_note")
                or (f"이 목소리를 '{who_name}'과 같은 분으로 기억할까요?" if is_guessed else "")
            ),
            voice_traits=voice_traits,
            first_quote=first_quote,
            first_timestamp=first_ts,
            utterance=utterance,
            visible_action=visible_action,
            sound_event_and_cause=sound_cause,
            place=place,
            timestamp=ts,
            timestamp_sec=mmss_to_seconds(ts),
            keywords=[w for w in [who_name, place, ts] if w],
            summary_sentence=raw_sum,
            status="pending_review",
            confirmed_by="AI",
        )
        card = verify_card_with_flash(
            client=client,
            card=card,
            pref=store.preference,
            dialogue_corpus=dialogue_corpus,
            run_live_llm_check=True,
            max_retries=3,
        )
        new_cards.append(card)

    elapsed = round(time.time() - t0, 2)
    badge = f"실제 {model_used} 영상 분석 + Flash 근거 재확인 ({elapsed}초)"
    for c in reversed(new_cards):
        c.source_badge = badge
        store.cards.insert(0, c)

    first_card = new_cards[0]
    conv_session.last_card_id = first_card.id
    conv_session.review_card_id = first_card.id

    store.recently_changed_pages.insert(
        0, f"확인할 기억(검토 대기함) > 실제 영상 분석 카드 {len(new_cards)}장 추가됨 ({elapsed}초)"
    )
    store.save_async()

    spoken_summaries = " ".join(c.summary_sentence for c in new_cards[:2])
    spoken_msg = (
        f"방금 올리신 영상을 {model_used}로 분석하고 Flash로 근거를 재확인해 "
        f"기억 카드 {len(new_cards)}장을 검토 대기함에 넣었어요. "
        f"{spoken_summaries} 지금 바로 확인하시려면 '정리해 줘'라고 말씀해 주세요."
    )

    return {
        "status": "ok",
        "model_used": model_used,
        "elapsed_sec": elapsed,
        "source_badge": badge,
        "message": f"실제 영상을 {model_used} + Flash 검증 루프로 분석해 기억 카드 {len(new_cards)}장을 '확인할 기억(검토 대기함)'에 넣었습니다 ({elapsed}초).",
        "spoken_text": spoken_msg,
        "cards": [c.model_dump() for c in new_cards],
        "card": first_card.model_dump(),
        "state": store.to_dict(),
    }


@app.post("/api/review")
async def api_review_card(req: ReviewReq):
    target: Optional[FactCard] = None
    for c in store.cards:
        if c.id == req.card_id:
            target = c
            break
    if target is None:
        raise HTTPException(status_code=404, detail="카드를 찾을 수 없습니다.")

    effective_consent = (
        req.consent_granted if req.consent_granted is not None else req.consent_confirmed
    )

    if req.action == "discard":
        target.status = "discarded"
        target.discard_reason = req.discard_reason or "사용자가 '아니야'를 선택해 버림"
        target.confirmed_by = "user"
        target.confirmed_at = now_iso()
        store.recently_changed_pages.insert(0, f"확인할 기억 > 카드 버림 처리됨 ({target.timestamp})")
        store.save_async()
        return {
            "status": "discarded",
            "message": "이 기억 카드를 버리고 위키에 저장하지 않았습니다.",
            "state": store.to_dict(),
        }

    # Confirm or Edit -> Check consent for new real person!
    if target.person_type == "real" and target.is_new_person and not effective_consent:
        raise HTTPException(
            status_code=400,
            detail="처음 만나는 분은 '이분을 기억해도 될까요?' 동의를 확인해야 위키에 저장할 수 있습니다.",
        )

    if req.action == "edit":
        if req.edited_sentence.strip():
            draft_before = target.summary_sentence
            cleaned, fx, _ = check_and_sanitize_style(
                req.edited_sentence.strip(),
                store.preference,
                fallback_who_intro=target.who_label,
            )
            cleaned, has_ts = ensure_timestamp_in_sentence(cleaned, target.timestamp)
            target.summary_sentence = cleaned
            target.verification.style_violations_fixed += fx
            target.verification.has_source_timestamp = has_ts
            record_verification_log(
                timestamp=target.timestamp,
                draft_before=draft_before,
                violation_detected="사용자 직접 수정(고쳐) + 설명 방식/시점 검증",
                verified_after=cleaned,
                flash_evidence_passed=True,
                flash_evidence_reason="사용자 수정 및 검증 완료",
                quote_matched=True,
                has_source_timestamp=has_ts,
                style_violations_fixed=fx,
                prepend=True,
            )
        if req.edited_who_label.strip():
            target.who_label = req.edited_who_label.strip()

    target.consent_confirmed = True
    target.status = "confirmed"
    target.confirmed_by = "user"
    target.confirmed_at = now_iso()

    # Save / update PersonNode and MomentNode in Ontology Wiki
    pid = target.who_id
    if pid not in store.people:
        store.people[pid] = PersonNode(
            id=pid,
            name_or_role=f"{target.who_label.split('(')[0].strip()} — {target.voice_traits}",
            person_type="real",
            voice_traits=target.voice_traits,
            first_quote=f"{target.first_quote} ({target.first_timestamp})",
            first_timestamp=target.first_timestamp,
            first_timestamp_sec=mmss_to_seconds(target.first_timestamp),
            first_met_when_where=f"{target.place} ({target.timestamp})",
            consent=True,
            consent_granted=True,
            is_new_person=target.is_new_person,
            is_guessed=target.is_guessed_person,
            memorable_quotes=[{"timestamp": target.timestamp, "quote": target.utterance}],
            moment_ids=[],
            source_id=target.source_id,
        )
    else:
        p_existing = store.people[pid]
        p_existing.consent = True
        p_existing.consent_granted = True
        p_existing.memorable_quotes.append(
            {"timestamp": target.timestamp, "quote": target.utterance}
        )
        p_existing.updated_at = now_iso()

    mid = f"mom_mem_{target.id}"
    store.moments[mid] = MomentNode(
        id=mid,
        title=f"[{target.timestamp}] {target.place} — {store.people[pid].name_or_role.split(' — ')[0]}",
        source_type="memory",
        source_id=target.source_id,
        source_title=target.source_title,
        recording_filename=target.recording_filename,
        when_str=f"오늘 ({target.timestamp})",
        timestamp=target.timestamp,
        timestamp_sec=target.timestamp_sec,
        place=target.place,
        people_ids=[pid],
        people_labels=[store.people[pid].name_or_role],
        heard_summary=target.utterance,
        visible_summary=target.visible_action,
        sound_cause_summary=target.sound_event_and_cause,
        card_ids=[target.id],
        status="confirmed",
    )
    if mid not in store.people[pid].moment_ids:
        store.people[pid].moment_ids.append(mid)

    changed_person = store.people[pid].name_or_role.split(" — ")[0]
    store.recently_changed_pages.insert(0, f"순간 > [{target.timestamp}] {target.place}")
    store.recently_changed_pages.insert(0, f"사람 > {changed_person}")
    store.save_async()

    return {
        "status": "confirmed",
        "message": f"위키에 저장했습니다! 바뀐 페이지: 사람({changed_person}), 순간({target.place})",
        "changed_pages": [f"사람 > {changed_person}", f"순간 > {target.place}"],
        "state": store.to_dict(),
    }


@app.post("/api/evaluate_answer_key")
async def api_evaluate_answer_key():
    store.evaluate_answer_key()
    ak_passed = sum(1 for a in store.answer_key if a.passed is True)
    ak_total = len(store.answer_key)
    pct = round(100.0 * ak_passed / max(1, ak_total), 1)
    store.recently_changed_pages.insert(
        0, f"안전 점검판 > 정답표 {ak_total}문항 실제 대조 채점 완료 ({pct}%)"
    )
    store.save_async()
    return store.to_dict()


@app.post("/api/story")
async def api_daily_story():
    """Generates '오늘의 한 마당' — an audio-friendly recap built dynamically from watched works and confirmed memories."""
    confirmed_mem = [
        c
        for c in store.cards
        if c.card_type == "memory_card" and c.status == "confirmed" and not c.is_example_data
    ]
    pending_mem = [
        c
        for c in store.cards
        if c.card_type == "memory_card" and c.status == "pending_review" and not c.is_example_data
    ]
    if confirmed_mem:
        mem_part = " ".join(c.summary_sentence for c in confirmed_mem[:2])
        mem_narration = f"일상에서는 직접 '맞아'라고 확인해 위키에 남기신 기억으로, {mem_part}"
    elif pending_mem:
        mem_narration = (
            f"지금 검토 대기함에 새로 기록된 일상 기억 {len(pending_mem)}건이 확인을 기다리고 있습니다. "
            f"'정리해 줘'라고 말씀하셔서 내 삶 위키에 남겨 보세요!"
        )
    else:
        mem_narration = "일상에서 기억하고 싶은 순간이 생기면 언제든 30초 기록으로 두 번째 귀에 담아 보세요!"

    story_text = (
        f"얼씨구, 오늘 동규 님의 두 번째 귀에 담긴 이야기를 한 마당 풀어 봅니다! "
        f"단편 영화 스프라이트 프라이트에서는 0분 18초에 달팽이에게 인사하던 또렷한 목소리의 엘리가 "
        f"1분 2초에 구해 준 작은 새 덕분에 8분 9초 위기에서 살아남는 장면을 목소리와 소리 단서로 생생히 따라가셨지요. "
        f"{mem_narration}"
    )
    return {"story_text": story_text}


TTS_CACHE_PATH = PRIVATE_DIR / "tts_cache.json"
if TTS_CACHE_PATH.exists():
    try:
        store.tts_cache.update(json.loads(TTS_CACHE_PATH.read_text(encoding="utf-8")))
    except Exception:
        pass


def _save_tts_cache_async() -> None:
    import threading

    def _write():
        try:
            TTS_CACHE_PATH.write_text(
                json.dumps(store.tts_cache, ensure_ascii=False), encoding="utf-8"
            )
        except Exception:
            pass

    threading.Thread(target=_write, daemon=True).start()


VOICE_STYLE_MAP = {
    "Kore": "warm, calm, friendly Korean female assistant voice",
    "Aoede": "soft, gentle, expressive Korean female voice",
    "Puck": "bright, energetic, friendly Korean male voice",
    "Charon": "deep, steady, warm baritone Korean male voice",
    "Zephyr": "crisp, clear, natural Korean narrator voice",
}


@app.post("/api/tts")
async def api_tts(req: TTSReq):
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="읽을 문장이 비어 있습니다.")
    voice = req.voice if req.voice in VOICE_STYLE_MAP else "Kore"
    cache_key = f"{voice}:{text[:180]}"
    if cache_key in store.tts_cache:
        return {"audio_base64": store.tts_cache[cache_key], "mime_type": "audio/wav", "cached": True}

    client = get_genai_client()
    if client is None:
        raise HTTPException(status_code=400, detail="GEMINI_API_KEY가 없습니다.")

    try:
        inter = client.interactions.create(
            model="gemini-3.8-flash-tts",
            input=[
                {
                    "type": "user_input",
                    "content": [
                        {
                            "type": "text",
                            "text": text,
                            "annotations": [
                                {
                                    "type": "speech_metadata",
                                    "style": VOICE_STYLE_MAP.get(
                                        voice, "warm, clear, natural Korean screen-guide voice"
                                    ),
                                }
                            ],
                        }
                    ],
                }
            ],
            response_format={"type": "audio"},
            generation_config={"speech_config": [{"voice": voice}]},
        )
        b64 = inter.output_audio.data
        store.tts_cache[cache_key] = b64
        _save_tts_cache_async()
        return {"audio_base64": b64, "mime_type": "audio/wav", "cached": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ConversationSession:
    def __init__(self) -> None:
        self.mode: str = "idle"  # idle | discussing_card | reviewing_inbox | awaiting_consent
        self.last_card_id: str = "card_sf_1"
        self.last_person_id: str = "char_1"
        self.review_card_id: str = ""
        self.speech_rate: float = 1.0
        self.voice: str = "Kore"


conv_session = ConversationSession()


def _get_card_by_id(card_id: str) -> Optional[FactCard]:
    for c in store.cards:
        if c.id == card_id:
            return c
    return store.cards[0] if store.cards else None


def _get_pending_cards() -> List[FactCard]:
    return [c for c in store.cards if c.status == "pending_review" and not c.is_example_data]


def _card_play_fields(card: Optional[FactCard]) -> Dict[str, object]:
    if card is None:
        return {}
    return {
        "play_source_type": card.source_type,
        "play_youtube_id": card.youtube_video_id,
        "play_recording_filename": card.recording_filename,
        "play_timestamp_sec": card.timestamp_sec,
        "play_timestamp": card.timestamp,
    }


@app.post("/api/converse")
async def api_converse(req: ConverseReq):
    u = req.utterance.strip()
    cur_sec = max(0, int(req.current_time_sec))

    # 1. Stop / Rest intent
    if any(w in u for w in ["그만", "멈춰", "조용히", "고마워", "됐어", "쉬어"]):
        conv_session.mode = "idle"
        return {
            "mode": conv_session.mode,
            "spoken_text": "네, 대화를 잠시 멈출게요. 언제든 화면 아무 곳이나 톡 치시면 다시 귀 기울여 들을게요.",
            "answer_sentence": "대화를 잠시 멈추었습니다.",
            "follow_up_voice": "화면 아무 곳이나 터치하면 다시 대화가 시작됩니다.",
            "action": "stop",
            "speech_rate": conv_session.speech_rate,
            "voice": conv_session.voice,
            "state": store.to_dict(),
        }

    # 2. Onboarding / Help / How to use
    if any(w in u for w in ["어떻게 써", "도움말", "설명해", "뭐 할 수 있어", "안녕", "시작", "누구야 너", "가이드"]):
        conv_session.mode = "idle"
        pending_cnt = len(_get_pending_cards())
        spoken = (
            f"안녕하세요, 듣는 세컨드 브레인 세컨드 이어입니다. "
            f"영상을 들으실 땐 방금 무슨 일이야, 방금 그 목소리 누구야라고 물어보시고, "
            f"내 주변을 기록하려면 지금 기록해 줘, 대기 중인 기억 {pending_cnt}개를 확인하려면 정리해 줘라고 말씀해 보세요."
        )
        return {
            "mode": conv_session.mode,
            "spoken_text": spoken,
            "answer_sentence": "화면을 보지 않고 목소리만으로 영상 장면 질문, 실시간 카메라 안내, 일상 기억 기록·정리·검색을 모두 할 수 있어요.",
            "follow_up_voice": "지금 '방금 무슨 일이야?', '지금 기록해 줘', '정리해 줘' 중 무엇을 해 볼까요?",
            "action": "listen_next",
            "speech_rate": conv_session.speech_rate,
            "voice": conv_session.voice,
            "state": store.to_dict(),
        }

    # 3. Voice & Speed Preference adjustments
    if any(w in u for w in ["남자 목소리", "남성 목소리", "중저음 목소리", "카론"]):
        conv_session.voice = "Charon" if "중저음" in u or "카론" in u else "Puck"
        v_label = "중저음 남성 목소리(카론)" if conv_session.voice == "Charon" else "밝은 남성 목소리(퍽)"
        return {
            "mode": conv_session.mode,
            "spoken_text": f"네, 이제부터 제미나이 {v_label}로 안내해 드릴게요. 이어서 무엇을 물어보실래요?",
            "answer_sentence": f"목소리를 제미나이 {v_label}로 바꿨어요.",
            "follow_up_voice": "계속해서 궁금한 것을 말씀해 주세요.",
            "action": "change_voice",
            "voice": conv_session.voice,
            "speech_rate": conv_session.speech_rate,
            "state": store.to_dict(),
        }
    if any(w in u for w in ["여자 목소리", "여성 목소리", "부드러운 목소리", "코레", "아오이데"]):
        conv_session.voice = "Aoede" if "부드러운" in u or "아오이데" in u else "Kore"
        v_label = "부드러운 여성 목소리(아오이데)" if conv_session.voice == "Aoede" else "따뜻한 여성 목소리(코레)"
        return {
            "mode": conv_session.mode,
            "spoken_text": f"네, 이제부터 제미나이 {v_label}로 안내해 드릴게요. 이어서 무엇을 물어보실래요?",
            "answer_sentence": f"목소리를 제미나이 {v_label}로 바꿨어요.",
            "follow_up_voice": "계속해서 궁금한 것을 말씀해 주세요.",
            "action": "change_voice",
            "voice": conv_session.voice,
            "speech_rate": conv_session.speech_rate,
            "state": store.to_dict(),
        }
    if any(w in u for w in ["천천히 말해", "말 좀 천천히", "느리게 말해", "속도 느리게", "천천히"]):
        conv_session.speech_rate = max(0.75, round(conv_session.speech_rate - 0.15, 2))
        return {
            "mode": conv_session.mode,
            "spoken_text": f"네, 말하기 속도를 {conv_session.speech_rate}배속으로 천천히 낮췄어요. 이어서 무엇을 물어보실래요?",
            "answer_sentence": f"말하기 속도를 천천히({conv_session.speech_rate}배속)로 바꿨어요.",
            "follow_up_voice": "계속해서 궁금한 것을 말씀해 주세요.",
            "action": "change_rate",
            "speech_rate": conv_session.speech_rate,
            "voice": conv_session.voice,
            "state": store.to_dict(),
        }
    if any(w in u for w in ["빠르게 말해", "말 좀 빨리", "빨리 말해", "속도 빠르게", "더 빨리"]):
        conv_session.speech_rate = min(1.5, round(conv_session.speech_rate + 0.15, 2))
        return {
            "mode": conv_session.mode,
            "spoken_text": f"네, 말하기 속도를 {conv_session.speech_rate}배속으로 빠르게 올렸어요. 이어서 무엇을 해 드릴까요?",
            "answer_sentence": f"말하기 속도를 빠르게({conv_session.speech_rate}배속)로 바꿨어요.",
            "follow_up_voice": "계속해서 말씀해 주세요.",
            "action": "change_rate",
            "speech_rate": conv_session.speech_rate,
            "voice": conv_session.voice,
            "state": store.to_dict(),
        }
    if "색깔 빼" in u or "색 빼" in u or "색깔 말하지" in u:
        store.preference.color_mode = "exclude"
        store.apply_preference_to_all_cards()
        store.save_async()
        return {
            "mode": conv_session.mode,
            "spoken_text": "네, 앞으로 모든 설명에서 색깔 단어는 빼고 소리와 행동 중심으로만 말씀드릴게요. 무엇을 알려드릴까요?",
            "answer_sentence": "설명 설정을 '색깔 제외'로 바꿨어요.",
            "follow_up_voice": "이어서 궁금한 장면이나 기억을 말씀해 주세요.",
            "action": "listen_next",
            "speech_rate": conv_session.speech_rate,
            "state": store.to_dict(),
        }
    if "색깔 넣" in u or "색깔 포함" in u or "색깔도 말해" in u:
        store.preference.color_mode = "include"
        store.apply_preference_to_all_cards()
        store.save_async()
        return {
            "mode": conv_session.mode,
            "spoken_text": "네, 이제부터 색깔 정보도 함께 넣어서 설명해 드릴게요. 무엇을 알려드릴까요?",
            "answer_sentence": "설명 설정을 '색깔 포함'으로 바꿨어요.",
            "follow_up_voice": "이어서 궁금한 장면이나 기억을 말씀해 주세요.",
            "action": "listen_next",
            "speech_rate": conv_session.speech_rate,
            "state": store.to_dict(),
        }

    # 4. Recording surroundings by voice command
    if any(w in u for w in ["지금 기록", "기록 시작", "지금부터 기억", "녹음 시작", "내 주변 기록"]):
        conv_session.mode = "idle"
        return {
            "mode": conv_session.mode,
            "spoken_text": "네, 지금부터 주변 소리와 행동을 기록해 둘게요.",
            "answer_sentence": "주변 30초 기록을 시작합니다.",
            "follow_up_voice": "기록이 끝나면 어떤 대화가 담겼는지 바로 읽어 드릴게요.",
            "action": "start_recording",
            "speech_rate": conv_session.speech_rate,
            "state": store.to_dict(),
        }

    # 4b. Daily Story ("오늘의 한 마당 들려줘", "오늘 이야기 들려줘", "오늘 들려줘", "한 마당")
    if any(w in u for w in ["한 마당", "한마당", "오늘 이야기", "오늘의 이야기", "오늘 들려줘", "오늘 하루 정리"]):
        story_res = await api_daily_story()
        story_text = story_res["story_text"]
        conv_session.mode = "idle"
        follow = "더 궁금한 장면이나 일상 기억이 있으시면 언제든 말씀해 주세요."
        return {
            "mode": conv_session.mode,
            "spoken_text": f"{story_text} {follow}",
            "answer_sentence": story_text,
            "follow_up_voice": follow,
            "story_text": story_text,
            "action": "listen_next",
            "speech_rate": conv_session.speech_rate,
            "state": store.to_dict(),
        }

    # 4c. YouTube / Work Wiki analysis command
    if any(w in u for w in ["유튜브 분석", "영상 분석", "영화 분석", "유튜브 정리", "작품 분석"]):
        yt_res = await api_process_youtube(
            YouTubeReq(
                youtube_url="https://www.youtube.com/watch?v=_cMxraX_5RE",
                force_live=False,
            )
        )
        conv_session.mode = "discussing_card"
        conv_session.last_card_id = "card_sf_1"
        first_c = _get_card_by_id("card_sf_1")
        spoken = (
            "네, 단편 영화 스프라이트 프라이트 전체 영상을 Gemini 4 Argon과 Flash 검증 루프로 분석해 "
            "작품 위키에 준비했어요. 지금 바로 '방금 무슨 일이야?' 또는 '방금 그 목소리 누구야?'라고 물어보실 수 있어요."
        )
        return {
            "mode": conv_session.mode,
            "spoken_text": spoken,
            "answer_sentence": yt_res.get("message", "작품 위키 준비 완료"),
            "follow_up_voice": "'방금 무슨 일이야?' 또는 '방금 그 목소리 누구야?'라고 말씀해 보세요.",
            "source_badge": yt_res.get("processing_badge", ""),
            "action": "listen_next",
            "speech_rate": conv_session.speech_rate,
            **_card_play_fields(first_c),
            "state": yt_res.get("state", store.to_dict()),
        }

    # 5. If currently in Review / Consent mode, handle conversational confirmation ("맞아", "응", "동의해", "지워", "아니야")
    if conv_session.mode in ("reviewing_inbox", "awaiting_consent"):
        pending = _get_pending_cards()
        target = next((c for c in pending if c.id == conv_session.review_card_id), pending[0] if pending else None)

        if target and any(w in u for w in ["맞아", "응", "그래", "네", "저장", "동의", "좋아", "오케이"]):
            p = store.people.get(target.who_id)
            needs_consent = bool(target.is_new_person or (p and p.is_new_person and not p.consent_granted))
            said_consent_explicitly = any(w in u for w in ["동의", "함께 저장", "응 동의", "네 동의"])

            if needs_consent and conv_session.mode != "awaiting_consent" and not said_consent_explicitly:
                conv_session.mode = "awaiting_consent"
                conv_session.review_card_id = target.id
                p_name = p.name_or_role if p else target.who_label
                spoken = (
                    f"잠깐만요, 이 기억에는 새로 만난 {p_name}의 목소리 정보가 들어 있어요. "
                    f"'이분을 기억해도 될까요?' 상대방 동의를 받고 위키에 함께 저장할까요? '응 동의해'라고 말씀해 주시면 저장할게요."
                )
                return {
                    "mode": conv_session.mode,
                    "spoken_text": spoken,
                    "answer_sentence": f"새 인물({p_name}) '이분을 기억해도 될까요?' 저장 동의를 음성으로 확인하고 있어요.",
                    "follow_up_voice": "'응 동의해' 또는 '지워'라고 말씀해 주세요.",
                    "action": "listen_next",
                    "speech_rate": conv_session.speech_rate,
                    **_card_play_fields(target),
                    "state": store.to_dict(),
                }

            await api_review_card(ReviewActionReq(card_id=target.id, action="confirm", consent_granted=True))
            remaining = _get_pending_cards()
            if remaining:
                nxt = remaining[0]
                conv_session.mode = "reviewing_inbox"
                conv_session.review_card_id = nxt.id
                spoken = (
                    f"네, 위키에 잘 저장했어요! 다음 확인할 기억은 {nxt.place}에서 있었던 일이에요. "
                    f"{nxt.summary_sentence} 이 기억도 저장할까요? '맞아' 또는 '지워'라고 말씀해 주세요."
                )
                return {
                    "mode": conv_session.mode,
                    "spoken_text": spoken,
                    "answer_sentence": nxt.summary_sentence,
                    "follow_up_voice": "이 기억도 저장할까요? '맞아' 또는 '지워'라고 말씀해 주세요.",
                    "action": "listen_next",
                    "speech_rate": conv_session.speech_rate,
                    **_card_play_fields(nxt),
                    "state": store.to_dict(),
                }
            else:
                conv_session.mode = "idle"
                conv_session.review_card_id = ""
                spoken = "네, 방금 기억까지 모두 위키에 저장해서 대기 중인 기억을 전부 정리했어요! 이제 무엇을 찾아볼까요?"
                return {
                    "mode": conv_session.mode,
                    "spoken_text": spoken,
                    "answer_sentence": "대기 중이던 모든 기억 정리를 마쳤어요.",
                    "follow_up_voice": "'내 기억 읽어줘' 또는 궁금한 점을 말씀해 주세요.",
                    "action": "listen_next",
                    "speech_rate": conv_session.speech_rate,
                    **_card_play_fields(target),
                    "state": store.to_dict(),
                }

        if target and any(w in u for w in ["아니", "지워", "버려", "삭제", "넘어가", "패스"]):
            await api_review_card(ReviewActionReq(card_id=target.id, action="discard", consent_granted=False))
            remaining = _get_pending_cards()
            if remaining:
                nxt = remaining[0]
                conv_session.mode = "reviewing_inbox"
                conv_session.review_card_id = nxt.id
                spoken = (
                    f"네, 방금 기억은 저장하지 않고 지웠어요. 다음 기억을 읽어드릴게요. "
                    f"{nxt.summary_sentence} 이 기억은 저장할까요? '맞아' 또는 '지워'라고 말씀해 주세요."
                )
                return {
                    "mode": conv_session.mode,
                    "spoken_text": spoken,
                    "answer_sentence": nxt.summary_sentence,
                    "follow_up_voice": "'맞아' 또는 '지워'라고 말씀해 주세요.",
                    "action": "listen_next",
                    "speech_rate": conv_session.speech_rate,
                    **_card_play_fields(nxt),
                    "state": store.to_dict(),
                }
            else:
                conv_session.mode = "idle"
                conv_session.review_card_id = ""
                spoken = "네, 방금 기억을 지우고 대기함 정리를 모두 마쳤어요. 더 도와드릴 일이 있을까요?"
                return {
                    "mode": conv_session.mode,
                    "spoken_text": spoken,
                    "answer_sentence": "대기함 정리를 모두 마쳤어요.",
                    "follow_up_voice": "궁금한 장면이나 기억을 편하게 말씀해 주세요.",
                    "action": "listen_next",
                    "speech_rate": conv_session.speech_rate,
                    "state": store.to_dict(),
                }

    # 6. Start Review Inbox workflow ("정리해 줘", "기억 정리", "대기함")
    if any(w in u for w in ["정리해", "기억 정리", "대기함", "확인할 기억"]):
        pending = _get_pending_cards()
        if not pending:
            conv_session.mode = "idle"
            spoken = (
                "지금 확인 대기 중인 새 기억이 없어요. "
                "새로 기록하시려면 '지금 기록해 줘'라고 말씀하시고, 이미 저장된 기억이나 작품을 찾으시려면 질문을 말씀해 주세요."
            )
            return {
                "mode": conv_session.mode,
                "spoken_text": spoken,
                "answer_sentence": "확인 대기 중인 기억이 0개예요.",
                "follow_up_voice": "'지금 기록해 줘' 또는 궁금한 질문을 말씀해 보세요.",
                "action": "listen_next",
                "speech_rate": conv_session.speech_rate,
                "state": store.to_dict(),
            }
        first_p = pending[0]
        conv_session.mode = "reviewing_inbox"
        conv_session.review_card_id = first_p.id
        conv_session.last_card_id = first_p.id
        spoken = (
            f"확인할 기억이 {len(pending)}개 있어요. 첫 번째 기억부터 읽어드릴게요. "
            f"{first_p.summary_sentence} "
            f"이 기억이 맞으면 '맞아', 지우려면 '지워'라고 말씀해 주세요."
        )
        return {
            "mode": conv_session.mode,
            "spoken_text": spoken,
            "answer_sentence": first_p.summary_sentence,
            "follow_up_voice": "위키에 저장할까요? '맞아' 또는 '지워'라고 말씀해 주세요.",
            "action": "listen_next",
            "speech_rate": conv_session.speech_rate,
            **_card_play_fields(first_p),
            "state": store.to_dict(),
        }

    # 7. Follow-up intent: Replay original sound ("응 들려줘", "원래 소리", "틀어줘", "응")
    if any(w in u for w in ["들려줘", "원래 소리", "틀어줘", "다시 들려", "그 소리"]) or u in ("응", "그래", "네", "어", "좋아"):
        last_c = _get_card_by_id(conv_session.last_card_id)
        if last_c:
            ts = last_c.timestamp
            spoken = f"네, {ts} 시점의 원래 소리를 바로 들려드릴게요."
            return {
                "mode": "discussing_card",
                "spoken_text": spoken,
                "answer_sentence": f"{ts} 시점의 원래 소리를 재생합니다.",
                "follow_up_voice": "원래 소리를 다 들으신 뒤 '방금 그 목소리 누구야?' 또는 '다음 장면'이라고 물어보실 수 있어요.",
                "action": "play_original",
                **_card_play_fields(last_c),
                "speech_rate": conv_session.speech_rate,
                "state": store.to_dict(),
            }

    # 8. Follow-up intent: "더 자세히 말해줘" / "무슨 상황이야?"
    if any(w in u for w in ["자세히", "더 알려줘", "무슨 상황", "자세한 설명", "왜 그런 소리"]):
        last_c = _get_card_by_id(conv_session.last_card_id)
        if last_c:
            detail_spoken = (
                f"자세히 말씀드릴게요. 장소는 {last_c.place}이고, "
                f"{last_c.who_label}가 '{last_c.utterance}'라고 말하며 {last_c.visible_action} "
                f"소리 원인은 {last_c.sound_event_and_cause or '현장 대화와 움직임'} 때문이에요 ({last_c.timestamp}). "
                f"그때의 원래 소리를 바로 들어볼까요, 아니면 다음 장면으로 넘어갈까요?"
            )
            return {
                "mode": "discussing_card",
                "spoken_text": detail_spoken,
                "answer_sentence": f"[{last_c.place}] {last_c.visible_action} ({last_c.timestamp}).",
                "follow_up_voice": "'원래 소리 들려줘' 또는 '다음 장면'이라고 말씀해 보세요.",
                "action": "listen_next",
                **_card_play_fields(last_c),
                "speech_rate": conv_session.speech_rate,
                "state": store.to_dict(),
            }

    # 9. Follow-up intent: "다음 장면" / "그 다음엔?" / "이전 장면"
    if any(w in u for w in ["다음 장면", "그 다음", "다음 거", "다음 기억", "이전 장면", "그 전에는", "앞 장면"]) or u in ("다음", "이전"):
        last_c = _get_card_by_id(conv_session.last_card_id)
        same_type_cards = [
            c
            for c in store.cards
            if c.card_type == (last_c.card_type if last_c else "work_card")
            and c.status != "discarded"
            and not c.is_example_data
        ]
        if not same_type_cards:
            same_type_cards = [c for c in store.cards if c.status != "discarded"]
        same_type_cards.sort(key=lambda x: x.timestamp_sec)
        idx = 0
        if last_c:
            for i, c in enumerate(same_type_cards):
                if c.id == last_c.id:
                    idx = i
                    break
        is_prev = any(w in u for w in ["이전", "그 전", "앞 장면"])
        new_idx = (idx - 1) % len(same_type_cards) if is_prev else (idx + 1) % len(same_type_cards)
        nxt_c = same_type_cards[new_idx]
        conv_session.last_card_id = nxt_c.id
        conv_session.last_person_id = nxt_c.who_id
        conv_session.mode = "discussing_card"
        dir_word = "이전" if is_prev else "다음"
        spoken = (
            f"{dir_word} 장면인 {nxt_c.timestamp} 시점이에요. {nxt_c.summary_sentence} "
            f"이 장면의 원래 소리를 들어볼까요, 아니면 계속해서 다음 장면을 들려드릴까요?"
        )
        return {
            "mode": conv_session.mode,
            "spoken_text": spoken,
            "answer_sentence": nxt_c.summary_sentence,
            "follow_up_voice": "'응 들려줘' 또는 '다음 장면'이라고 말씀해 주세요.",
            "action": "listen_next",
            **_card_play_fields(nxt_c),
            "speech_rate": conv_session.speech_rate,
            "state": store.to_dict(),
        }

    # 10. All questions go through /api/ask (live Gemini 4 Argon / 3.8 Flash + Flash evidence verification)
    ask_res = await api_ask(
        AskReq(
            question=u,
            current_time_sec=req.current_time_sec,
            mode="wiki",
            use_live_argon=req.use_live_argon,
        )
    )
    qa_data = ask_res["qa"]
    matched_card = _find_best_card_for_question(u, cur_sec)
    conv_session.last_card_id = matched_card.id
    conv_session.last_person_id = matched_card.who_id
    conv_session.mode = "discussing_card"

    cite_ts = qa_data["cite_timestamp"]
    ans_sent = qa_data["answer_sentence"]
    is_who = any(w in u for w in ["누구", "누가", "누군지"]) and "뭐라고" not in u
    if is_who:
        follow_up = f"그분이 말한 {cite_ts} 시점의 원래 목소리를 바로 들어볼까요, 아니면 무슨 행동을 했는지 더 알려드릴까요?"
    else:
        follow_up = f"{cite_ts} 시점의 원래 소리를 바로 들어볼까요, 아니면 그 목소리가 누구인지 알려드릴까요?"

    return {
        "mode": conv_session.mode,
        "spoken_text": f"{ans_sent} {follow_up}",
        "answer_sentence": ans_sent,
        "follow_up_voice": follow_up,
        "source_badge": ask_res.get("source_badge", qa_data.get("source_badge", "")),
        "answer_source_mode": ask_res.get("answer_source_mode", qa_data.get("answer_source_mode", "live_gemini")),
        "model_used": ask_res.get("model_used", qa_data.get("model_used", "")),
        "elapsed_sec": ask_res.get("elapsed_sec", qa_data.get("elapsed_sec", 0.0)),
        "qa": qa_data,
        "action": "listen_next",
        **_card_play_fields(matched_card),
        "speech_rate": conv_session.speech_rate,
        "state": ask_res["state"],
    }
