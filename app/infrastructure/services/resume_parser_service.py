import httpx, json
from typing import List, Tuple
from app.config import settings


_ALLOWED_CATEGORIES = {
    "language", "framework", "library", "tool", "database",
    "cloud", "devops", "ml", "data", "soft", "domain",
    "api", "testing", "security", "other"
}
_ALLOWED_SENIORITY = {
    "intern", "junior", "mid", "senior", "staff",
    "principal", "lead", "expert"
}


def _norm_category(s: str) -> str:
    s = (s or "").strip().lower()
    return s if s in _ALLOWED_CATEGORIES else "other"


def _norm_seniority(s: str):
    s = (s or "").strip().lower()
    return s if s in _ALLOWED_SENIORITY else None


def _years_to_months(years) -> int | None:
    try:
        y = float(years)
        if y < 0:
            return None
        m = int(round(y * 12))
        return max(0, min(600, m))  # borne 50 ans
    except Exception:
        return None


class ResumeParserService:
    def __init__(self) -> None:
        self.base_url = settings.openai_base_url.rstrip("/")
        self.api_key = settings.openai_api_key
        self.model = settings.openai_model

    async def extract_skills(self, text: str) -> list[dict]:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY manquant")

        max_chars = 18000
        if len(text) > max_chars:
            text = text[:max_chars]

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a recruitment assistant. Extract concise, normalized skills from resumes. "
                        "Prefer canonical names (e.g., 'PostgreSQL', 'FastAPI', 'Azure'), avoid duplicates. "
                        "Return a JSON object with a 'skills' array containing skill objects with these fields: "
                        "name (string), category (string), proficiency (0-100), years_experience (number), "
                        "seniority (string), confidence (0-100), last_used_year (integer)."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Extract skills from this resume text:\n\n{text}"
                    )
                }
            ],
            "response_format": {"type": "json_object"}  # Correct format for OpenAI API
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=90) as client:
            r = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            try:
                r.raise_for_status()
            except httpx.HTTPStatusError as e:
                error_detail = r.text
                print(f"OpenAI API error: {error_detail}")
                raise

        data = r.json()
        content = data["choices"][0]["message"]["content"]
        obj = json.loads(content)

        out: list[dict] = []
        for it in obj.get("skills", []):
            name = (it.get("name") or "").strip()
            if not name:
                continue
                
            score = int(it.get("proficiency") or 0)
            category = _norm_category(it.get("category"))
            months = _years_to_months(it.get("years_experience"))
            seniority = _norm_seniority(it.get("seniority"))
            confidence = it.get("confidence")
            confidence = None if confidence is None else int(confidence)
            last_used_year = it.get("last_used_year")
            last_used_year = None if last_used_year is None else int(last_used_year)

            out.append({
                "name": name[:120],
                "score": max(0, min(100, score)),
                "category": category,
                "years_experience_months": months,
                "seniority": seniority,
                "confidence": None if confidence is None else max(0, min(100, confidence)),
                "last_used_year": last_used_year,
            })
        return out