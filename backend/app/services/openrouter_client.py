# app/services/openrouter_client.py

import httpx
from app.config import settings

OPENROUTER_URL = getattr(
    settings, "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
).rstrip("/")

LANG_NAME = {
    "en": "English",
    "te": "Telugu",
    "hi": "Hindi",
    "ta": "Tamil",
    "kn": "Kannada",
    "ml": "Malayalam",
    "mr": "Marathi",
    "bn": "Bengali",
    "gu": "Gujarati",
    "ur": "Urdu",
}

LANG_STRICT_RULE = {
    "en": "Write ONLY in English.",
    "te": "Write ONLY in Telugu language using Telugu script (తెలుగు అక్షరాలు మాత్రమే). Do NOT use English words unless necessary for medicine names.",
    "hi": "Write ONLY in Hindi using Devanagari script (हिंदी में ही). Do NOT use English words unless necessary for medicine names.",
    "ta": "Write ONLY in Tamil using Tamil script.",
    "kn": "Write ONLY in Kannada using Kannada script.",
    "ml": "Write ONLY in Malayalam using Malayalam script.",
    "mr": "Write ONLY in Marathi using Devanagari script.",
    "bn": "Write ONLY in Bengali using Bengali script.",
    "gu": "Write ONLY in Gujarati using Gujarati script.",
    "ur": "Write ONLY in Urdu using Urdu script.",
}


async def _call_openrouter(
    messages: list,
    model: str | None = None,
    temperature: float = 0.2,
) -> str:
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        # "HTTP-Referer": "http://localhost",
        # "X-Title": "HealthBot",
    }

    payload = {
        "model": model or settings.OPENROUTER_MODEL,
        "messages": messages,
        "temperature": temperature,
    }

    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            f"{OPENROUTER_URL}/chat/completions",
            headers=headers,
            json=payload,
        )
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"].strip()


# ----------------------------
# 1) Medical intent classifier
# ----------------------------
async def is_medical_query_openrouter(query: str) -> bool:
    q = (query or "").strip().lower()

    # ✅ quick keyword allow (prevents misclassification)
    medical_keywords = [
        "medicine", "medication", "tablet", "capsule", "syrup", "drug",
        "dose", "dosage", "prescription", "side effect", "contraindication",
        "fever", "cough", "cold", "pain", "headache", "bp", "sugar",
        "infection", "disease", "symptom", "treatment", "diagnosis",
        "antibiotic", "paracetamol", "ibuprofen", "dolo", "azith",
        "rash", "vomit", "diarrhea", "asthma", "diabetes", "hypertension",
        "what is this medicine", "what is this tablet"
    ]
    if any(k in q for k in medical_keywords):
        return True

    prompt = f"""
You are a strict classifier.

Is the following question related to medicine, health, disease,
symptoms, diagnosis, treatment, drugs, prevention, or healthcare?

Question: "{query}"

Reply with ONLY one word:
YES or NO
""".strip()

    out = await _call_openrouter(
        messages=[{"role": "user", "content": prompt}],
        model=settings.OPENROUTER_MODEL,
        temperature=0.0,
    )
    return out.strip().upper() == "YES"



# ----------------------------
# 2) Generate short chat title
# ----------------------------
async def generate_chat_title(query: str) -> str:
    prompt = f"""
Create a short chat title (max 6 words) based on this first user message.
Return ONLY the title text (no quotes, no extra words).

User message: {query}
""".strip()

    title = await _call_openrouter(
        messages=[{"role": "user", "content": prompt}],
        model=settings.OPENROUTER_MODEL,
        temperature=0.2,
    )

    title = (title or "").strip()
    if not title:
        return "Health Chat"
    if len(title) > 60:
        title = title[:60].rstrip()
    return title


# ----------------------------
# 3) Main chat (RAG + fallback)
# ----------------------------
async def openrouter_chat(
    model: str,
    user_message: str,
    chat_history: list,
    rag_context: str,
    language: str,
) -> str:
    lang_code = (language or "en").strip().lower()
    lang_name = LANG_NAME.get(lang_code, "English")
    lang_rule = LANG_STRICT_RULE.get(lang_code, "Write ONLY in English.")

    system = f"""
You are a medical awareness assistant (NOT a doctor).
Safety rules:
- Answer only health/medical awareness queries.
- Do NOT diagnose.
- Do NOT give dosages.
- Give safe general guidance.
- Clearly say when to consult a doctor.
- If emergency signs, advise immediate medical help.

LANGUAGE RULE (VERY IMPORTANT):
- Selected language: {lang_name} ({lang_code})
- {lang_rule}
- If the user writes in a different language, still respond ONLY in {lang_name}.
""".strip()

    # -------- RAG MODE --------
    if rag_context and len(rag_context.strip()) >= 30:
        rag_prompt = f"""
You MUST answer strictly from the context below.

IMPORTANT RULES:
- If medicine name appears → mention it clearly.
- If tablet/drug info present → explain its use.
- Do NOT give generic medicine examples.
- Do NOT guess.
- If answer missing → reply EXACTLY: NO_CONTEXT

Context:
{rag_context}

User question:
{user_message}

Answer:
"""


        messages = [{"role": "system", "content": system}]
        messages.extend(chat_history[-10:])
        messages.append({"role": "user", "content": rag_prompt})

        answer = await _call_openrouter(messages=messages, model=model, temperature=0.2)
        if answer.strip() != "NO_CONTEXT":
            return answer.strip()

    # -------- FALLBACK MODE --------
    emergency_prompt = f"""
The user asked a medical question, but reliable book context was missing.

Give SAFE, GENERAL medical guidance only.

Instructions:
- Suggest 3–5 basic home remedies if applicable
- Mention common OTC medicines (example: paracetamol) — but NO dosage
- Clearly say when to consult a doctor
- Do NOT diagnose
- Be calm and reassuring

User Question:
{user_message}

Answer:
""".strip()

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": emergency_prompt},
    ]
    return await _call_openrouter(messages=messages, model=model, temperature=0.2)
