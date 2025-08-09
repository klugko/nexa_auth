from dataclasses import dataclass
from math import exp
from typing import List, Dict, Any, Tuple
from datetime import datetime

from app.infrastructure.services.skill_taxonomy import classify_family

@dataclass(frozen=True)
class WeightConfig:
    tau_recency_years: float = 6.0      # constante de décroissance (plus grand = moins de pénalité)
    min_recency_factor: float = 0.6     # plancher si très ancien
    exp_boost_max_years: float = 5.0    # au-delà, pas plus de boost
    exp_boost_min: float = 0.6          # poids mini d'expérience
    exp_boost_max: float = 1.0          # poids maxi d'expérience
    conf_base: float = 0.75             # base si confidence absent
    k_global_top: int = 10              # nombre de skills à agréger pour score global
    k_family_top: int = 3               # top N par famille pour agrégats

class SkillScoringService:
    def __init__(self, cfg: WeightConfig | None = None) -> None:
        self.cfg = cfg or WeightConfig()

    def _recency_factor(self, last_used_year: int | None) -> float:
        if not last_used_year:
            return 1.0  # pas d'info -> neutre
        now_year = datetime.utcnow().year
        age = max(0, now_year - last_used_year)
        # exponentiel avec plancher
        return max(self.cfg.min_recency_factor, exp(-age / self.cfg.tau_recency_years))

    def _experience_factor(self, years_experience: float | None) -> float:
        if years_experience is None:
            return self.cfg.exp_boost_min
        y = max(0.0, float(years_experience))
        ratio = min(1.0, y / self.cfg.exp_boost_max_years)
        return self.cfg.exp_boost_min + (self.cfg.exp_boost_max - self.cfg.exp_boost_min) * ratio

    def _confidence_factor(self, confidence: int | None) -> float:
        if confidence is None:
            return self.cfg.conf_base
        c = max(0, min(100, int(confidence))) / 100.0
        return 0.5 + 0.5 * c  # 0.5..1.0

    def score_skill(
        self,
        *,
        name: str,
        score: int,
        category: str | None,
        years_experience: float | None,
        confidence: int | None,
        last_used_year: int | None,
    ) -> dict:
        """
        Calcule un 'weighted_score' ∈ [0, 100] combinant:
        - proficiency (score)
        - expérience (boost)
        - récence (exponentiel)
        - confidence (0.5..1.0) 
        Retourne aussi la 'family' calculée.
        """
        prof = max(0, min(100, int(score))) / 100.0
        f_exp = self._experience_factor(years_experience)
        f_rec = self._recency_factor(last_used_year)
        f_conf = self._confidence_factor(confidence)

        weighted = 100.0 * prof * f_exp * f_rec * f_conf
        family = classify_family(name, category)

        return {
            "name": name,
            "family": family,
            "weighted_score": round(min(100.0, weighted), 2),
            "proficiency": int(round(prof * 100)),
            "experience_years": None if years_experience is None else round(years_experience, 1),
            "recency_factor": round(f_rec, 3),
            "confidence": confidence,
        }

    def aggregate(self, scored: List[dict]) -> dict:
        """
        Agrège par famille + calcule un score global:
        - par famille: moyenne des top K weighted_score
        - global: moyenne des top K global + bonus de 'coverage' (nb familles non vides)
        """
        fam_map: Dict[str, List[dict]] = {}
        for it in scored:
            fam_map.setdefault(it["family"], []).append(it)

        families = []
        non_empty_fams = 0
        all_scores = []
        for fam, items in fam_map.items():
            items_sorted = sorted(items, key=lambda x: x["weighted_score"], reverse=True)
            top = items_sorted[: self.cfg.k_family_top]
            if top:
                non_empty_fams += 1
            fam_score = round(sum(x["weighted_score"] for x in top) / max(1, len(top)), 2) if top else 0.0
            families.append({
                "family": fam,
                "score": fam_score,
                "top_skills": top,
            })
            all_scores.extend(x["weighted_score"] for x in items_sorted)

        all_scores.sort(reverse=True)
        top_global = all_scores[: self.cfg.k_global_top]
        base_global = round(sum(top_global) / max(1, len(top_global)), 2) if top_global else 0.0

        coverage = non_empty_fams / 8.0  # 8 familles “tech” typiques
        coverage = max(0.0, min(1.0, coverage))
        global_score = round(min(100.0, base_global * (0.9 + 0.1 * coverage)), 2)

        families.sort(key=lambda x: x["score"], reverse=True)
        return {
            "global_score": global_score,
            "family_count": non_empty_fams,
            "families": families,
        }
