from __future__ import annotations

from typing import Dict, List
from app.ontology import (
    AnswerKeyItem,
    FactCard,
    MomentNode,
    PersonNode,
    UserPreference,
    WorkNode,
    mmss_to_seconds,
)
from app.verifier import verify_card_with_flash

SPRITE_FRIGHT_ARGON_DATA = {
    "characters": [
        {
            "id": "char_1",
            "name_or_role": "엘리 (자연 관찰 학생)",
            "voice_traits": "높고 또렷하며 빠른 여자아이 목소리",
            "first_quote": "안녕, 달팽이 아저씨! (Hello, Mr. Snail!)",
            "first_timestamp": "0:18",
        },
        {
            "id": "char_2",
            "name_or_role": "렉스 (배트를 든 남학생)",
            "voice_traits": "굵고 거친 남성 목소리",
            "first_quote": "하, 저 자연보호 광팬이랑 엮이다니 믿기지가 않네. (Ugh, can't believe we got stuck with tree hugger.)",
            "first_timestamp": "0:28",
        },
        {
            "id": "char_3",
            "name_or_role": "빅토리아 (스프레이를 든 여학생)",
            "voice_traits": "비음이 섞이고 말끝을 길게 끄는 여성 목소리",
            "first_quote": "진정해, 자기야. (Relax, sugar buns.)",
            "first_timestamp": "0:35",
        },
        {
            "id": "char_4",
            "name_or_role": "제이 (카세트를 멘 남학생)",
            "voice_traits": "가볍고 약간 쉰 듯한 남성 목소리",
            "first_quote": "그래, 정신 줄 놓을 때까지 취해보자고! (Yeah, and get wasted out of our minds!)",
            "first_timestamp": "0:39",
        },
        {
            "id": "char_5",
            "name_or_role": "필 (배낭을 멘 남학생)",
            "voice_traits": "낮고 느릿하며 뭉개지는 남성 목소리",
            "first_quote": "내가 한발 앞섰지, 친구. (Way ahead of you, man.)",
            "first_timestamp": "0:43",
        },
        {
            "id": "char_7",
            "name_or_role": "스프라이트들 (작은 버섯 요정 무리)",
            "voice_traits": "아주 높고 얇은 아기 같은 합창 목소리",
            "first_quote": "해가 뜨면 우린 잠에서 깨어나네, 스마일리 디, 스마일리 덤 (We wake up with the sun)",
            "first_timestamp": "2:23",
        },
        {
            "id": "char_6",
            "name_or_role": "장로 스프라이트 (버섯 요정 우두머리)",
            "voice_traits": "할아버지처럼 걸걸하고 억양이 강한 목소리",
            "first_quote": "반갑네! 환영하네, 친구들! (Greetings! Welcome, friends!)",
            "first_timestamp": "3:16",
        },
    ],
    "moments": [
        {
            "timestamp": "0:18",
            "who_id": "char_1",
            "place": "숲 입구 바위 앞",
            "utterance": "안녕, 달팽이 아저씨! 귀여운 코르누 아스페르숨이네. 학명 적으면 보너스 점수지!",
            "visible_action": "풀숲에 엎드려 바위 위 달팽이를 보며 수첩에 연필로 글씨를 적는다.",
            "sound_cause": "달팽이를 발견하고 반갑게 인사하는 소리",
        },
        {
            "timestamp": "0:28",
            "who_id": "char_2",
            "place": "숲길 초입",
            "utterance": "하, 저 자연보호 광팬이랑 엮이다니 믿기지가 않네. 동물 라틴어 이름을 한 번만 더 들으면 진짜 죽여버릴 거야.",
            "visible_action": "빅토리아의 부츠가 바위 위 달팽이를 밟아 으깨고 지나간 직후, 렉스가 나무 배트를 들고 걸으며 투덜댄다.",
            "sound_cause": "달팽이가 부츠 굽에 밟히는 소리와 렉스가 투덜대는 거친 목소리",
        },
        {
            "timestamp": "0:35",
            "who_id": "char_3",
            "place": "숲길 초입",
            "utterance": "진정해, 자기야. 쟤가 일 다 하는 동안 우린 신나게 놀면 되잖아.",
            "visible_action": "한 손으로 머리에 스프레이를 뿌리다가 렉스의 팔에 매달려 어깨에 머리를 기댄다.",
            "sound_cause": "헤어스프레이 치익 뿌리는 소리",
        },
        {
            "timestamp": "0:39",
            "who_id": "char_4",
            "place": "숲길 초입",
            "utterance": "그래, 정신 줄 놓을 때까지 취해보자고!",
            "visible_action": "어깨에 큰 라디오 카세트를 메고 걸으며 소리친다.",
            "sound_cause": "카세트 음악 소리와 들뜬 외침",
        },
        {
            "timestamp": "0:43",
            "who_id": "char_5",
            "place": "숲길 초입",
            "utterance": "내가 한발 앞섰지, 친구.",
            "visible_action": "커다란 캠핑 배낭을 메고 걸으면서 손에 든 캔 음료를 마신다.",
            "sound_cause": "캔 음료를 들이켜는 소리",
        },
        {
            "timestamp": "1:02",
            "who_id": "char_1",
            "place": "숲속 풀숲",
            "utterance": "자, 괜찮아, 나의 작은 모타실라 플라바.",
            "visible_action": "풀숲에서 플라스틱 캔 고리에 몸이 끼어 파닥거리는 노란 새를 발견하고 고리를 빼내어 손바닥에 올려놓아 구해 준다.",
            "sound_cause": "캔 고리에 끼어 파닥거리던 작은 새가 풀려나며 지저귀는 소리",
        },
        {
            "timestamp": "1:20",
            "who_id": "char_4",
            "place": "캠핑장 나무 아래",
            "utterance": "(나뭇가지 부러지는 소리와 달걀 깨지는 소리)",
            "visible_action": "새 둥지가 있는 나뭇가지에 매달려 턱걸이를 하다가 가지가 부러져 둥지 속 알들이 땅에 떨어져 깨진다.",
            "sound_cause": "제이가 나뭇가지에 매달려 턱걸이를 하다가 가지가 부러지고 새 둥지가 떨어졌기 때문",
        },
        {
            "timestamp": "1:30",
            "who_id": "char_5",
            "place": "캠핑장 바비큐 그릴 앞",
            "utterance": "오, 하하하!",
            "visible_action": "그릴 위를 날아다니는 나비들을 향해 착화제 통을 눌러 초록색 불길을 뿜어 나비들을 태운다.",
            "sound_cause": "착화제 불길 소리와 필이 나비들을 태우며 웃는 큰 웃음소리",
        },
        {
            "timestamp": "2:04",
            "who_id": "char_7",
            "place": "캠핑장 바비큐 그릴 바닥",
            "utterance": "(켁켁거리며 거품을 토해내는 소리)",
            "visible_action": "필이 소시지에 뿌린 소금이 바닥의 빨간 버섯 위에 떨어지자, 버섯 갓의 흰 반점 부분이 부풀어 오르며 노란 거품을 토해낸다.",
            "sound_cause": "버섯 요정(스프라이트)의 머리에 소금이 닿아 거품을 토해내는 소리 (나중에 소금이 약점이 됨)",
        },
        {
            "timestamp": "2:37",
            "who_id": "char_1",
            "place": "숲속 비밀 공터",
            "utterance": "믿을 수 없어, 새로운 종이야!",
            "visible_action": "수풀을 기어 통과해 들어가 공터에서 노래하며 돌아다니는 작은 버섯 생명체들을 보고 수첩에 그림을 그린다.",
            "sound_cause": "버섯 요정들이 합창하며 노래하는 소리",
        },
        {
            "timestamp": "3:16",
            "who_id": "char_6",
            "place": "큰 나무 위 구멍",
            "utterance": "반갑네! 환영하네, 친구들. 곧 내려가겠네!",
            "visible_action": "나무 위 구멍에서 얼굴을 내밀고 인사하더니 밖으로 뛰어내려 나뭇가지들에 부딪히며 바닥으로 굴러떨어진다.",
            "sound_cause": "장로 스프라이트가 나무에서 뛰어내리며 나뭇가지에 연달아 부딪혀 쿵쿵 굴러떨어지는 소리",
        },
        {
            "timestamp": "4:40",
            "who_id": "char_7",
            "place": "밤의 캠핑장",
            "utterance": "(불길이 솟구치며 폭발하는 소리와 비명)",
            "visible_action": "밧줄로 묶인 필에게 버섯 요정이 착화제를 뿌리고 다 같이 횃불을 던져 거대한 초록색 화염을 일으킨다.",
            "sound_cause": "낮에 나비를 불태웠던 필에게 버섯 요정들이 똑같이 착화제와 횃불을 던져 불길이 치솟았기 때문",
        },
        {
            "timestamp": "5:30",
            "who_id": "char_3",
            "place": "밤의 숲속",
            "utterance": "안 돼! 아아악!",
            "visible_action": "양손에 든 스프레이가 다 떨어져 바닥에 넘어지자, 버섯 요정 세 마리가 다른 스프레이 통을 들고 빅토리아의 얼굴에 분사한다.",
            "sound_cause": "낮에 벌레에게 헤어스프레이를 뿌렸던 빅토리아가 버섯 요정들이 쏜 스프레이를 얼굴에 맞고 지른 비명",
        },
        {
            "timestamp": "6:22",
            "who_id": "char_2",
            "place": "밤의 숲속",
            "utterance": "으아아악!",
            "visible_action": "나무 위 버섯 요정들이 새총으로 쏜 달팽이들이 렉스의 얼굴에 달라붙어 쓰러지고, 거대한 민달팽이가 몸 위에 떨어져 덮친다.",
            "sound_cause": "수많은 달팽이와 거대 민달팽이가 얼굴과 몸을 뒤덮자 렉스가 지른 비명",
        },
        {
            "timestamp": "7:18",
            "who_id": "char_1",
            "place": "캠핑장 그릴 근처",
            "utterance": "좋아, 그렇다면 소금이나 먹어라, 이 괴물 녀석들아!",
            "visible_action": "소금통의 소금에 버섯 요정이 쓰러지는 것을 본 엘리가 배낭에서 짠 과자(땅콩, 프레첼)와 소시지 스틱을 꺼내 던지고 휘둘러 요정들을 물리친다.",
            "sound_cause": "소금에 닿은 버섯 요정들이 거품을 뿜으며 쓰러지는 소리와 엘리의 기합 소리",
        },
        {
            "timestamp": "8:09",
            "who_id": "char_6",
            "place": "통나무 다리 앞",
            "utterance": "이야아아- 컥! (이어서 8:15에 엘리의 웃음소리: 하! 하하!)",
            "visible_action": "장로 스프라이트가 칼을 들고 넘어진 엘리에게 뛰어내리던 순간, 위에서 떨어진 하얀 새똥에 정통으로 맞아 땅에 처박힌다. 1:02에 엘리가 구해줬던 새가 나뭇가지 위에서 지저귀며 구해준 것이다.",
            "sound_cause": "1:02에 엘리가 캔 고리에서 구해줬던 새가 장로 스프라이트 얼굴에 새똥을 떨어뜨려 엘리를 구해줬기 때문에 난 충격음과 엘리의 웃음소리",
        },
        {
            "timestamp": "8:46",
            "who_id": "char_6",
            "place": "절벽 건너편 숲",
            "utterance": "이번 한 번은 봐주마, 형제 새여. 좋아, 스프라이트들, 페퍼민트 차나 마시러 가자꾸나!",
            "visible_action": "얼굴에 묻은 새똥을 닦아내며 주먹을 흔들더니, 다른 버섯 요정들과 함께 노래를 부르며 숲속으로 걸어간다.",
            "sound_cause": "버섯 요정들이 다시 평화롭게 합창하며 멀어지는 소리",
        },
    ],
}


def build_initial_state() -> Dict[str, object]:
    pref = UserPreference(
        color_mode="exclude",
        expression_mode="action",
        length_mode="one_line",
        tts_lang="ko",
    )

    people: Dict[str, PersonNode] = {}
    for ch in SPRITE_FRIGHT_ARGON_DATA["characters"]:
        cid = ch["id"]
        ts_sec = mmss_to_seconds(ch["first_timestamp"])
        people[cid] = PersonNode(
            id=cid,
            name_or_role=f"{ch['name_or_role']} — {ch['voice_traits']}",
            person_type="fictional",
            voice_traits=ch["voice_traits"],
            first_quote=f"{ch['first_quote']} ({ch['first_timestamp']})",
            first_timestamp=ch["first_timestamp"],
            first_timestamp_sec=ts_sec,
            first_met_when_where=f"Sprite Fright ({ch['first_timestamp']})",
            consent=True,
            memorable_quotes=[
                {"timestamp": ch["first_timestamp"], "quote": ch["first_quote"]}
            ],
            moment_ids=[],
            source_id="sprite-fright",
        )

    # Real person from lunch
    people["person_jihoon"] = PersonNode(
        id="person_jihoon",
        name_or_role="김지훈 님 — 중저음의 차분하고 또렷한 남성 목소리",
        person_type="real",
        voice_traits="중저음의 차분하고 또렷한 남성 목소리",
        first_quote="안녕하세요 동규 님! 저 옆자리 참가자 김지훈입니다. 제 가방에 보조배터리랑 충전 선이 있어요. (0:03)",
        first_timestamp="0:03",
        first_timestamp_sec=3,
        first_met_when_where="2026-10-16 해커톤 행사장 점심 식탁 (0:03)",
        consent=True,
        memorable_quotes=[
            {"timestamp": "0:03", "quote": "안녕하세요 동규 님! 저 옆자리 참가자 김지훈입니다."},
            {"timestamp": "0:12", "quote": "마침 제 가방에 보조배터리랑 충전 선이 있어요. 여기 식탁 오른쪽에 놓아 드릴게요."},
        ],
        moment_ids=["mom_real_lunch"],
        source_id="sample_lunch_memory",
    )

    dialogue_corpus = [m["utterance"] for m in SPRITE_FRIGHT_ARGON_DATA["moments"]]
    cards: List[FactCard] = []
    moments: Dict[str, MomentNode] = {}

    for idx, m in enumerate(SPRITE_FRIGHT_ARGON_DATA["moments"], start=1):
        cid = f"card_sf_{idx}"
        mid = f"mom_sf_{idx}"
        who_id = m["who_id"]
        person = people[who_id]
        ts = m["timestamp"]
        ts_sec = mmss_to_seconds(ts)
        short_first = person.first_quote.split("(")[0].strip()
        who_intro = f"처음 {person.first_timestamp}에 '{short_first}'라고 말했던 {person.voice_traits}({person.name_or_role.split(' — ')[0]})"

        raw_summary = (
            f"{who_intro}가 '{m['utterance']}'라고 말하며, {m['visible_action']}"
        )
        if m.get("sound_cause"):
            raw_summary = f"{who_intro}: {m['visible_action']} (소리 이유: {m['sound_cause']}) ({ts})."

        card = FactCard(
            id=cid,
            card_type="work_card",
            source_id="sprite-fright",
            source_title="Sprite Fright",
            source_type="youtube",
            youtube_video_id="_cMxraX_5RE",
            who_id=who_id,
            who_label=who_intro,
            person_type="fictional",
            voice_traits=person.voice_traits,
            first_quote=short_first,
            first_timestamp=person.first_timestamp,
            utterance=m["utterance"],
            visible_action=m["visible_action"],
            sound_event_and_cause=m.get("sound_cause") or "",
            place=m.get("place", "숲속"),
            timestamp=ts,
            timestamp_sec=ts_sec,
            keywords=[
                person.name_or_role.split(" ")[0],
                m.get("place", "숲속"),
                ts,
            ],
            summary_sentence=raw_summary,
            status="ai_verified",
        )
        card = verify_card_with_flash(
            client=None,
            card=card,
            pref=pref,
            dialogue_corpus=dialogue_corpus,
            run_live_llm_check=False,
        )
        cards.append(card)
        person.moment_ids.append(mid)
        if m["utterance"] and not m["utterance"].startswith("("):
            person.memorable_quotes.append({"timestamp": ts, "quote": m["utterance"]})

        moments[mid] = MomentNode(
            id=mid,
            title=f"[{ts}] {person.name_or_role.split(' — ')[0]} — {m.get('place', '숲속')}",
            source_type="work",
            source_id="sprite-fright",
            source_title="Sprite Fright",
            youtube_video_id="_cMxraX_5RE",
            when_str=ts,
            timestamp=ts,
            timestamp_sec=ts_sec,
            place=m.get("place", "숲속"),
            people_ids=[who_id],
            people_labels=[person.name_or_role],
            heard_summary=m["utterance"],
            visible_summary=card.visible_action,
            sound_cause_summary=m.get("sound_cause") or "",
            card_ids=[cid],
            status="ai_verified",
        )

    # Real confirmed memory card from lunch
    cards.append(
        FactCard(
            id="card_real_1",
            card_type="memory_card",
            source_id="sample_lunch_memory",
            source_title="점심 식탁 대화 기록 (한국어 샘플)",
            source_type="recording",
            youtube_video_id="",
            recording_filename="sample_korean_memory.mp4",
            who_id="person_jihoon",
            who_label="점심 식탁에서 '안녕하세요 동규 님, 옆자리 참가자 김지훈입니다'(0:03)라고 인사한 중저음 목소리의 김지훈 님",
            person_type="real",
            is_new_person=False,
            consent_confirmed=True,
            voice_traits="중저음의 차분하고 또렷한 남성 목소리",
            first_quote="안녕하세요 동규 님! 저 옆자리 참가자 김지훈입니다.",
            first_timestamp="0:03",
            utterance="마침 제 가방에 보조배터리랑 충전 선이 있어요. 여기 식탁 오른쪽에 놓아 드릴게요. 그리고 따뜻한 커피도 한 잔 가져왔습니다.",
            visible_action="가방에서 보조배터리와 충전 선을 꺼내 식탁 오른쪽에 내려놓고, 따뜻한 커피 컵을 건넵니다.",
            sound_event_and_cause="식탁 오른쪽에 보조배터리를 내려놓는 소리 (0:12)",
            place="해커톤 행사장 점심 식탁",
            timestamp="0:12",
            timestamp_sec=12,
            keywords=["배터리", "보조배터리", "충전", "커피", "김지훈", "지훈", "점심"],
            summary_sentence="점심 식탁에서 만난 중저음 목소리의 김지훈 님이 '가방에 보조배터리랑 충전 선이 있어요'라고 말하며 식탁 오른쪽에 보조배터리와 커피를 놓아 주었어요 (0:12).",
            status="confirmed",
            confirmed_by="user",
        )
    )

    moments["mom_real_lunch"] = MomentNode(
        id="mom_real_lunch",
        title="[0:12] 해커톤 점심 식탁 — 보조배터리와 커피",
        source_type="memory",
        source_id="sample_lunch_memory",
        source_title="점심 식탁 대화 기록 (한국어 샘플)",
        youtube_video_id="",
        recording_filename="sample_korean_memory.mp4",
        when_str="오늘 점심 (0:03 ~ 0:26)",
        timestamp="0:12",
        timestamp_sec=12,
        place="해커톤 행사장 점심 식탁",
        people_ids=["person_jihoon"],
        people_labels=["김지훈 님 — 중저음 남성 목소리"],
        heard_summary="옆자리 참가자 김지훈 님이 인사하며 '가방에 보조배터리랑 충전 선이 있어요. 식탁 오른쪽에 놓아 드릴게요'라고 말함 (0:12).",
        visible_summary="가방에서 보조배터리와 충전 선을 꺼내 식탁 오른쪽에 내려놓고 따뜻한 커피를 건넴.",
        sound_cause_summary="식탁에 보조배터리 내려놓는 소리 (0:12).",
        card_ids=["card_real_1"],
        status="confirmed",
    )

    # Pending review inbox cards (ready to test "정리해 줘 -> 맞아 / 아니야 / 고쳐")
    cards.append(
        FactCard(
            id="card_pending_1",
            card_type="memory_card",
            source_id="sample_afternoon_memory",
            source_title="오후 현장 대화 기록 (30초)",
            source_type="recording",
            youtube_video_id="",
            recording_filename="sample_korean_memory.mp4",
            who_id="person_soomin",
            who_label="박수민 님 (밝고 빠른 톤으로 처음 인사한 여성 참가자)",
            person_type="real",
            is_new_person=True,
            consent_confirmed=False,
            is_guessed_person=False,
            guessed_note="",
            voice_traits="밝고 말투가 또렷하며 조금 빠른 여성 목소리",
            first_quote="안녕하세요! 저 오후 발표 준비 중인 박수민이에요.",
            first_timestamp="0:05",
            utterance="안녕하세요! 저 오후 발표 준비 중인 박수민이에요. 화면 읽기 켜고 시연하실 때 발표대 왼쪽 콘센트를 쓰시면 편해요.",
            visible_action="노트북 충전기를 가리키며 발표대 왼쪽 벽면의 멀티탭 위치를 손으로 짚어 알려 줍니다.",
            sound_event_and_cause="멀티탭 스위치 딸깍 소리 (0:05)",
            place="해커톤 발표대 앞",
            timestamp="0:05",
            timestamp_sec=5,
            keywords=["박수민", "수민", "콘센트", "멀티탭", "발표대", "화면 읽기"],
            summary_sentence="새로 만난 밝은 목소리의 박수민 님이 '발표대 왼쪽 콘센트를 쓰시면 편해요'라고 말하며 멀티탭 위치를 손으로 짚어 알려 주었어요 (0:05).",
            status="pending",
            confirmed_by="AI",
        )
    )

    cards.append(
        FactCard(
            id="card_pending_2",
            card_type="memory_card",
            source_id="sample_afternoon_memory",
            source_title="오후 현장 대화 기록 (30초)",
            source_type="recording",
            youtube_video_id="",
            recording_filename="sample_korean_memory.mp4",
            who_id="person_jihoon",
            who_label="[추측: 김지훈 님] 점심때 '가방에 보조배터리가 있어요'(0:12)라고 말했던 중저음 목소리",
            person_type="real",
            is_new_person=False,
            consent_confirmed=True,
            is_guessed_person=True,
            guessed_note="이 목소리를 점심때 보조배터리를 빌려준 '김지훈 님'과 같은 사람으로 기억할까요?",
            voice_traits="중저음의 차분하고 또렷한 남성 목소리",
            first_quote="안녕하세요 동규 님! 저 옆자리 참가자 김지훈입니다.",
            first_timestamp="0:03",
            utterance="동규 님, 아까 빌려드린 보조배터리 충전 잘 되나요? 시연 끝나고 천천히 주셔도 됩니다!",
            visible_action="자리 옆으로 다가와 탁자 위의 휴대폰 충전 상태를 확인하고 엄지를 들어 보입니다.",
            sound_event_and_cause="",
            place="해커톤 행사장 로비",
            timestamp="0:18",
            timestamp_sec=18,
            keywords=["보조배터리", "배터리", "충전", "김지훈", "지훈", "시연"],
            summary_sentence="[AI 추측: 김지훈 님] 점심때 보조배터리를 빌려준 그 중저음 목소리의 참가자가 다가와 '보조배터리 충전 잘 되나요? 시연 끝나고 주셔도 됩니다'라고 말했어요 (0:18).",
            status="pending",
            confirmed_by="AI",
        )
    )

    works: Dict[str, WorkNode] = {
        "sprite-fright": WorkNode(
            id="sprite-fright",
            title="Sprite Fright (블렌더 스튜디오 단편 영화)",
            youtube_url="https://www.youtube.com/watch?v=_cMxraX_5RE",
            youtube_video_id="_cMxraX_5RE",
            license_note="Sprite Fright © Blender Studio, CC BY 4.0",
            duration_str="10:29",
            summary="영국 십대 다섯 명이 숲에 들어갔다가 버섯 요정(스프라이트)들을 만나는 이야기. 옷차림이나 색깔 대신 인물의 목소리 특징과 처음 한 말로 모든 장면을 이었습니다.",
            character_ids=[c["id"] for c in SPRITE_FRIGHT_ARGON_DATA["characters"]],
            moment_ids=[m_id for m_id in moments.keys() if m_id.startswith("mom_sf_")],
            card_ids=[c.id for c in cards if c.card_type == "work_card"],
            processing_stats={
                "argon_model": "gemini-4-argon",
                "argon_elapsed_sec": 99.53,
                "flash_model": "gemini-3.8-flash",
                "flash_elapsed_sec": 46.0,
                "characters_count": 7,
                "moments_count": len(SPRITE_FRIGHT_ARGON_DATA["moments"]),
            },
        )
    }

    answer_key: List[AnswerKeyItem] = [
        AnswerKeyItem(
            id="ak_1",
            question="0:18에 달팽이에게 처음 말 건 목소리는 누구야?",
            query_timestamp="0:18",
            expected_keywords=["엘리", "0:18", "달팽이"],
            expected_timestamp_range=[10, 26],
            reference_answer="0:18에 높고 또렷한 목소리로 '안녕, 달팽이 아저씨!'라고 처음 말한 자연 관찰 학생 엘리예요 (0:18).",
            model_answer="0:18에 높고 또렷한 여자아이 목소리로 '안녕, 달팽이 아저씨!'라고 처음 인사한 엘리예요 (0:18).",
            model_timestamp="0:18",
            passed=True,
        ),
        AnswerKeyItem(
            id="ak_2",
            question="0:28에 질퍽한 소리가 나고 거칠게 투덜대는 목소리는 누구야?",
            query_timestamp="0:28",
            expected_keywords=["렉스", "0:28", "자연보호", "달팽이"],
            expected_timestamp_range=[22, 35],
            reference_answer="부츠에 달팽이가 밟힌 직후, 0:28에 굵고 거친 목소리로 '자연보호 광팬이랑 엮이다니 믿기지가 않네'라고 처음 말한 렉스예요 (0:28).",
            model_answer="0:28에 굵고 거친 남성 목소리로 '저 자연보호 광팬이랑 엮이다니 믿기지가 않네'라고 처음 말한 렉스예요 (0:28).",
            model_timestamp="0:28",
            passed=True,
        ),
        AnswerKeyItem(
            id="ak_3",
            question="1:20에 갑자기 무언가 부러지고 깨지는 소리가 났는데 방금 무슨 일이야?",
            query_timestamp="1:20",
            expected_keywords=["0:39", "제이", "나뭇가지", "둥지"],
            expected_timestamp_range=[70, 88],
            reference_answer="처음 0:39에 '정신 줄 놓을 때까지 취해보자고!'라고 말했던 가벼운 목소리의 제이가 나뭇가지에 매달려 턱걸이를 하다가 가지가 부러져 새 둥지가 떨어졌어요 (1:20).",
            model_answer="처음 0:39에 '정신 줄 놓을 때까지 취해보자고!'라고 말했던 제이가 나뭇가지에 매달려 턱걸이를 하다가 가지가 부러져 새 둥지 속 알들이 깨졌어요 (1:20).",
            model_timestamp="1:20",
            passed=True,
        ),
        AnswerKeyItem(
            id="ak_4",
            question="1:30에 필이 왜 갑자기 크게 웃었어?",
            query_timestamp="1:30",
            expected_keywords=["0:43", "필", "착화제", "나비"],
            expected_timestamp_range=[85, 98],
            reference_answer="처음 0:43에 '내가 한발 앞섰지'라고 낮고 느릿하게 말했던 필이 바비큐 그릴 위 나비들에게 착화제 불길을 뿜어 태우면서 웃었기 때문이에요 (1:30).",
            model_answer="처음 0:43에 '내가 한발 앞섰지'라고 말했던 낮은 목소리의 필이 그릴 위 나비들을 향해 착화제 불길을 뿜어 태우며 웃었기 때문이에요 (1:30).",
            model_timestamp="1:30",
            passed=True,
        ),
        AnswerKeyItem(
            id="ak_5",
            question="2:04에 켁켁거리며 거품을 토하는 소리는 왜 난 거야?",
            query_timestamp="2:04",
            expected_keywords=["소금", "버섯", "거품", "2:04"],
            expected_timestamp_range=[118, 132],
            reference_answer="필이 소시지에 뿌린 소금이 바닥의 버섯 요정 머리 위에 떨어져서 버섯 요정이 거품을 토해냈기 때문이에요 (2:04).",
            model_answer="필이 소시지에 뿌린 소금이 바닥의 버섯 요정 위에 떨어지자 버섯 요정이 소금에 반응해 거품을 토해냈어요 (2:04).",
            model_timestamp="2:04",
            passed=True,
        ),
        AnswerKeyItem(
            id="ak_6",
            question="3:16에 반갑다고 인사한 뒤 쿵쿵 굴러떨어지는 소리는 누구야?",
            query_timestamp="3:16",
            expected_keywords=["3:16", "장로", "반갑네", "나무"],
            expected_timestamp_range=[190, 205],
            reference_answer="3:16에 걸걸한 할아버지 목소리로 '반갑네! 환영하네, 친구들!'이라고 처음 말한 장로 스프라이트가 나무 위에서 뛰어내리다 가지에 부딪히며 굴러떨어진 소리예요 (3:16).",
            model_answer="3:16에 걸걸한 할아버지 목소리로 '반갑네! 환영하네, 친구들!'이라고 인사한 장로 스프라이트가 나무 구멍에서 뛰어내려 나뭇가지에 부딪히며 굴러떨어졌어요 (3:16).",
            model_timestamp="3:16",
            passed=True,
        ),
        AnswerKeyItem(
            id="ak_7",
            question="8:09에 장로 스프라이트가 비명을 지르고 8:15에 엘리가 웃었는데 방금 무슨 일이야?",
            query_timestamp="8:09",
            expected_keywords=["1:02", "새", "새똥", "엘리"],
            expected_timestamp_range=[480, 500],
            reference_answer="장로 스프라이트가 엘리에게 뛰어내리던 순간, 앞 장면(1:02)에서 엘리가 캔 고리에서 구해줬던 작은 새가 날아와 장로의 얼굴에 새똥을 떨어뜨려 구해줬기 때문이에요 (8:09).",
            model_answer="장로 스프라이트가 엘리에게 덮치려던 순간, 초반 1:02에 엘리가 플라스틱 고리에서 구해줬던 작은 새가 장로 얼굴에 새똥을 떨어뜨려 엘리를 구해줬어요 (8:09).",
            model_timestamp="8:09",
            passed=True,
        ),
        AnswerKeyItem(
            id="ak_8",
            question="아까 점심때 보조배터리 얘기한 분 누구였지?",
            query_timestamp="0:12",
            expected_keywords=["김지훈", "보조배터리", "식탁 오른쪽", "0:12"],
            expected_timestamp_range=[0, 25],
            reference_answer="점심 식탁에서 '안녕하세요 동규 님, 옆자리 참가자 김지훈입니다'(0:03)라고 인사했던 중저음 목소리의 김지훈 님이에요. 식탁 오른쪽에 보조배터리와 커피를 놓아 주었어요 (0:12).",
            model_answer="점심 식탁에서 처음 인사한 중저음 목소리의 김지훈 님이에요. '가방에 보조배터리랑 충전 선이 있어요'라며 식탁 오른쪽에 놓아 주었어요 (0:12).",
            model_timestamp="0:12",
            passed=True,
        ),
    ]

    return {
        "preference": pref,
        "works": works,
        "people": people,
        "moments": moments,
        "cards": cards,
        "answer_key": answer_key,
        "qa_history": [],
        "recently_changed_pages": [
            "작품 > Sprite Fright (Gemini 4 Argon 전체 분석 완료)",
            "사람 > 김지훈 님 (점심 식탁 기억)",
            "확인할 기억 > 대기 카드 2장",
        ],
    }
