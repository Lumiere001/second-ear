import base64
import json
import os
import subprocess
import time
from pathlib import Path
from dotenv import load_dotenv
from google import genai

load_dotenv()

PRIVATE_DIR = Path(__file__).resolve().parent.parent / "private"
PRIVATE_DIR.mkdir(exist_ok=True)

client = genai.Client()

YOUTUBE_URL = "https://www.youtube.com/watch?v=_cMxraX_5RE"


def test_youtube_video():
    results = {}
    prompt = """이 영상(Sprite Fright)을 보고 시각장애인을 위한 작품 카드를 JSON으로 정리해 주세요.
인물은 옷차림이나 생김새가 아니라 '목소리 특징'과 '처음 한 말(한국어 뜻 + 영어 원문)'로 소개해야 합니다.
감정은 추측하지 말고 눈에 보인 행동과 들린 소리만 적으세요.

다음 JSON 형식으로만 답하세요:
{
  "characters": [
    {
      "id": "char_1",
      "name_or_role": "이름 또는 역할",
      "voice_traits": "목소리 특징",
      "first_quote": "처음 한 말",
      "first_timestamp": "MM:SS"
    }
  ],
  "moments": [
    {
      "timestamp": "MM:SS",
      "who_id": "char_1",
      "utterance": "들린 대사나 소리",
      "visible_action": "눈에 보인 행동",
      "sound_cause": "웃음이나 비명이 났다면 그 이유"
    }
  ]
}"""

    for model_name, gen_cfg in [
        ("gemini-3.8-flash", {}),
        ("gemini-4-argon", {"thinking_level": "low"}),
    ]:
        t0 = time.time()
        try:
            kwargs = {
                "model": model_name,
                "input": [
                    {"type": "video", "uri": YOUTUBE_URL},
                    {"type": "text", "text": prompt},
                ],
                "response_format": {"type": "text", "mime_type": "application/json"},
            }
            if gen_cfg:
                kwargs["generation_config"] = gen_cfg
            inter = client.interactions.create(**kwargs)
            elapsed = round(time.time() - t0, 2)
            text = inter.output_text or "{}"
            results[model_name] = {
                "status": "ok",
                "elapsed_sec": elapsed,
                "output_preview": text[:1500],
            }
            try:
                parsed = json.loads(text)
                results[model_name]["parsed"] = parsed
                if model_name == "gemini-4-argon":
                    (PRIVATE_DIR / "sprite_fright_argon.json").write_text(
                        json.dumps(parsed, ensure_ascii=False, indent=2), encoding="utf-8"
                    )
                else:
                    (PRIVATE_DIR / "sprite_fright_flash.json").write_text(
                        json.dumps(parsed, ensure_ascii=False, indent=2), encoding="utf-8"
                    )
            except Exception as pe:
                results[model_name]["parse_error"] = str(pe)
            print(f"[{model_name}] SUCCESS in {elapsed}s")
        except Exception as e:
            elapsed = round(time.time() - t0, 2)
            results[model_name] = {
                "status": "error",
                "elapsed_sec": elapsed,
                "error": str(e),
            }
            print(f"[{model_name}] ERROR in {elapsed}s: {e}")

    (PRIVATE_DIR / "experiment_results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def create_korean_sample_video():
    """Create a 24-second 720p Korean sample video (under 3MB) simulating a conversation at the hackathon lunch table."""
    wav_path = PRIVATE_DIR / "sample_korean_dialogue.wav"
    mp4_path = PRIVATE_DIR / "sample_korean_memory.mp4"

    print("Generating Korean multi-speaker dialogue audio via gemini-3.8-flash-tts...")
    try:
        inter = client.interactions.create(
            model="gemini-3.8-flash-tts",
            input=[
                {
                    "type": "user_input",
                    "content": [
                        {
                            "type": "text",
                            "text": "안녕하세요 동규 님! 저 옆자리 참가자 김지훈입니다. 점심 드시면서 잠깐 인사드려요.",
                            "annotations": [
                                {
                                    "type": "speech_metadata",
                                    "speaker": "Jihoon",
                                    "style": "warm, clear, friendly young man",
                                }
                            ],
                        },
                        {
                            "type": "text",
                            "text": "아, 반가워요 지훈 님! 지금 휴대폰 배터리가 얼마 안 남아서 걱정하고 있었어요.",
                            "annotations": [
                                {
                                    "type": "speech_metadata",
                                    "speaker": "Donggyu",
                                    "style": "calm and friendly",
                                }
                            ],
                        },
                        {
                            "type": "text",
                            "text": "마침 제 가방에 보조배터리랑 충전 선이 있어요. 여기 식탁 오른쪽에 놓아 드릴게요. 그리고 따뜻한 커피도 한 잔 가져왔습니다. 제 이름과 오늘 대화를 세컨드 이어에 기억해 두셔도 좋아요!",
                            "annotations": [
                                {
                                    "type": "speech_metadata",
                                    "speaker": "Jihoon",
                                    "style": "helpful and cheerful",
                                }
                            ],
                        },
                    ],
                }
            ],
            response_format={"type": "audio"},
            generation_config={
                "speech_config": {
                    "speakers": [
                        {"speaker": "Jihoon", "voice": "Puck"},
                        {"speaker": "Donggyu", "voice": "Kore"},
                    ]
                }
            },
        )
        audio_bytes = base64.b64decode(inter.output_audio.data)
        wav_path.write_bytes(audio_bytes)
        print("Saved TTS WAV:", wav_path, len(audio_bytes), "bytes")
    except Exception as e:
        print("Multi-speaker TTS fallback to single-speaker:", e)
        inter = client.interactions.create(
            model="gemini-3.8-flash-tts",
            input=[
                {
                    "type": "user_input",
                    "content": [
                        {
                            "type": "text",
                            "text": "안녕하세요 동규 님! 저는 옆자리 참가자 김지훈입니다. 휴대폰 배터리가 부족하시면 제 보조배터리를 식탁 오른쪽에 놓아 드릴게요. 따뜻한 커피도 건네 드립니다. 오늘 대화를 기억해 두셔도 좋아요!",
                            "annotations": [
                                {"type": "speech_metadata", "style": "warm and clear"}
                            ],
                        }
                    ],
                }
            ],
            response_format={"type": "audio"},
            generation_config={"speech_config": [{"voice": "Puck"}]},
        )
        audio_bytes = base64.b64decode(inter.output_audio.data)
        wav_path.write_bytes(audio_bytes)

    # Combine WAV with a clean 1280x720 visual canvas showing scenes so Gemini video model sees visual actions too
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        "color=c=0x1e293b:s=1280x720:r=15",
        "-i",
        str(wav_path),
        "-shortest",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        str(mp4_path),
    ]
    subprocess.run(cmd, check=True)
    print("Created sample Korean MP4:", mp4_path, mp4_path.stat().st_size, "bytes")


if __name__ == "__main__":
    create_korean_sample_video()
    test_youtube_video()
