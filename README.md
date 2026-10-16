Built during Google DeepMind AI Hackathon Seoul, 2026-10-16 11:20–15:20 KST
Idea and design notes (docs/PLAN.md) were prepared before the event; all code was written during the event.

- **Live Cloud Run URL**: https://second-ear-300068085210.asia-northeast3.run.app
- **How to use (1-line)**: Open the link, press **말하기 (Speak)** or type a command in the silent input bar to ask about any scene (`"방금 무슨 일이야?"`), turn on **📷 실시간 카메라 (Live Camera)** for proactive visual guidance, or upload a 30-second video via **🎥 30초 기록 올리기** to extract verified personal memory cards.
- **Shared 3D view (laptop)**: open [`/graph`](https://second-ear-300068085210.asia-northeast3.run.app/graph) (or **함께 보기** on the phone screen) to watch the ontology follow the latest question.

# Second Ear

Second brains are built for eyes. Second Ear is one you can hear: it turns the videos blind people watch and the moments they live into a wiki they can ask by voice, introducing people by their voice and what they said earlier, and saving personal memories only after the user confirms.

See [docs/PLAN.md](docs/PLAN.md) for the problem definition, design, and verification loop.

## Credits

- Demo video: "Sprite Fright" © Blender Studio, licensed under Creative Commons Attribution (CC BY). https://studio.blender.org/films/sprite-fright/
- Open-source libraries and templates used:
  - Google GenAI SDK (`google-genai >= 2.3.0`, Interactions API with `gemini-4-argon`, `gemini-3.8-flash`, and `gemini-3.8-flash-tts`)
  - Google Cloud Storage Python Client (`google-cloud-storage`)
  - FastAPI, Uvicorn, Pydantic (`fastapi`, `uvicorn`, `pydantic`, `python-multipart`)
  - Apple Design System tokens reference: `VoltAgent/awesome-design-md` (`apple/DESIGN.md`)
  - 3D ontology view (`/graph`): `3d-force-graph` 1.73.4 (MIT, https://github.com/vasturiano/3d-force-graph) and `three.js` 0.160.0 (MIT, https://threejs.org), loaded from jsDelivr
  - Font: Pretendard 1.3.9 (SIL Open Font License 1.1, https://github.com/orioncactus/pretendard)

