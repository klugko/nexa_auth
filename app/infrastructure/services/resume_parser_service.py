import httpx
import json
from typing import List, Tuple
from app.config import settings

class ResumeParserService:
    """
    Appelle l'API OpenAI (Chat Completions) avec Structured Outputs (json_schema strict).
    Le modèle retourne une liste de compétences + un score 0..100.
    """
    def __init__(self) -> None:
        self.base_url = settings.openai_base_url.rstrip("/")
        self.api_key = settings.openai_api_key
        self.model = settings.openai_model

    async def extract_skills(self, text: str) -> list[tuple[str, int]]:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY manquant")
        schema = {
            "type": "object",
            "properties": {
                "skills": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "minLength": 1, "maxLength": 120},
                            "score": {"type": "integer", "minimum": 0, "maximum": 100}
                        },
                        "required": ["name", "score"],
                        "additionalProperties": False
                    }
                }
            },
            "required": ["skills"],
            "additionalProperties": False
        }

        max_chars = 18000
        if len(text) > max_chars:
            text = text[:max_chars]

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a recruitment assistant. Extract skills from resumes."},
                {"role": "user", "content": (
                    "From the following resume text, extract a concise list of hard and soft skills.\n"
                    "Return at most 40 skills. Score each skill 0..100 (higher = stronger evidence).\n"
                    "Resume:\n" + text
                )}
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": { "name": "skills_schema", "strict": True, "schema": schema }
            }
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()

        content = data["choices"][0]["message"]["content"]
        try:
            obj = json.loads(content)
        except Exception:
            content = content.strip().strip("`").strip()
            obj = json.loads(content)

        items = []
        for it in obj.get("skills", []):
            name = (it.get("name") or "").strip()
            score = int(it.get("score") or 0)
            if name:
                items.append((name, max(0, min(100, score))))
        return items
