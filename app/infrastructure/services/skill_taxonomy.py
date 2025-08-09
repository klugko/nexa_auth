import re
from typing import Dict, List, Tuple, Optional

_FAMILIES = [
    "programming_languages",
    "web_frameworks",
    "databases",
    "cloud",
    "devops",
    "data_ml",
    "mobile",
    "testing",
    "tools",
    "soft_skills",
    "domain",
    "other",
]

# Patterns (précompilés) — ajoute ce que tu veux selon ton contexte
_PATTERNS: Dict[str, List[re.Pattern]] = {
    "programming_languages": [
        re.compile(r"\b(python|java|kotlin|go|golang|rust|typescript|javascript|node\.?js|c\+\+|c#|php|ruby|scala|swift|dart)\b", re.I),
    ],
    "web_frameworks": [
        re.compile(r"\b(fastapi|django|flask|spring|spring boot|laravel|symfony|rails|express|nest\.?js|next\.?js|nuxt\.?js|angular|react|vue)\b", re.I),
    ],
    "databases": [
        re.compile(r"\b(postgres(?:ql)?|mysql|mariadb|sqlite|oracle|sql server|mssql|mongodb|redis|elasticsearch|dynamodb|cassandra|neo4j)\b", re.I),
    ],
    "cloud": [
        re.compile(r"\b(aws|gcp|google cloud|azure|cloud run|lambda|ecs|eks|gke|aks|cloudfront|s3|cloudformation|terraform|pulumi)\b", re.I),
    ],
    "devops": [
        re.compile(r"\b(docker|kubernetes|k8s|github actions|gitlab ci|jenkins|argo|istio|helm|prometheus|grafana|ansible)\b", re.I),
    ],
    "data_ml": [
        re.compile(r"\b(pandas|numpy|pyspark|spark|airflow|dbt|sklearn|tensorflow|pytorch|mlflow|huggingface)\b", re.I),
    ],
    "mobile": [
        re.compile(r"\b(android|ios|swiftui|kotlin multiplatform|react native|flutter)\b", re.I),
    ],
    "testing": [
        re.compile(r"\b(pytest|unittest|jest|cypress|playwright|junit|selenium|cucumber)\b", re.I),
    ],
    "tools": [
        re.compile(r"\b(git|linux|bash|zsh|make|vim|vscode|postman|swagger|openapi|grpc)\b", re.I),
    ],
    "soft_skills": [
        re.compile(r"\b(communication|leadership|mentoring|agile|scrum|kanban|ownership|collaboration)\b", re.I),
    ],
    "domain": [
        re.compile(r"\b(fintech|healthcare|e-?commerce|iot|telecom|banking|insurtech|adtech|edtech|gaming)\b", re.I),
    ],
}

# Mapping depuis category normalisée -> famille
_CATEGORY_TO_FAMILY = {
    "language": "programming_languages",
    "framework": "web_frameworks",
    "library": "web_frameworks",
    "database": "databases",
    "cloud": "cloud",
    "devops": "devops",
    "ml": "data_ml",
    "data": "data_ml",
    "mobile": "mobile",
    "testing": "testing",
    "tool": "tools",
    "soft": "soft_skills",
    "domain": "domain",
    "other": "other",
}

def classify_family(skill_name: str, category: Optional[str]) -> str:
    """
    Retourne la famille pour un skill. On privilégie une category existante (enrichie),
    sinon on match avec la taxonomie regex. Fallback 'other'.
    """
    if category:
        fam = _CATEGORY_TO_FAMILY.get(category.lower())
        if fam:
            return fam

    name = skill_name.lower().strip()
    for fam, patterns in _PATTERNS.items():
        if any(p.search(name) for p in patterns):
            return fam
    return "other"
