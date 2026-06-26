"""
config.py — Central configuration for the Redrob candidate ranker.

All scoring weights, keyword lists, and thresholds live here
so they can be tuned in one place without touching scoring logic.
"""

from datetime import date

# ============================================================================
# Reference date for recency calculations
# ============================================================================
REFERENCE_DATE = date(2026, 6, 18)

# ============================================================================
# Component weight caps (max raw points before behavioral multiplier)
# ============================================================================
MAX_TITLE_CAREER_SCORE = 30.0
MAX_SKILLS_SCORE = 25.0
MAX_EXPERIENCE_SCORE = 15.0
MAX_LOCATION_SCORE = 10.0
MAX_EDUCATION_SCORE = 5.0

# ============================================================================
# Title tier classification
# ============================================================================
# Tier A — direct match to what the JD wants (AI/ML engineering roles)
TITLE_TIER_A = {
    "ml engineer", "machine learning engineer", "senior ml engineer",
    "senior machine learning engineer", "staff ml engineer",
    "ai engineer", "senior ai engineer", "staff ai engineer",
    "applied ml engineer", "applied ai engineer",
    "nlp engineer", "senior nlp engineer",
    "search engineer", "senior search engineer",
    "ranking engineer", "retrieval engineer",
    "ml architect", "ai architect",
    "ml platform engineer", "mlops engineer", "senior mlops engineer",
    "deep learning engineer", "senior deep learning engineer",
    "recommendation engineer", "recommendations engineer",
    "applied scientist", "applied research scientist",
    "ml lead", "ai lead", "machine learning lead",
    "principal ml engineer", "principal ai engineer",
    "lead ml engineer", "lead ai engineer",
    "junior ml engineer",  # still relevant title, just less experience
}

# Tier B — adjacent roles that could be a fit depending on descriptions
TITLE_TIER_B = {
    "data scientist", "senior data scientist", "lead data scientist",
    "staff data scientist", "principal data scientist",
    "software engineer", "senior software engineer", "staff software engineer",
    "backend engineer", "senior backend engineer",
    "platform engineer", "senior platform engineer",
    "data engineer", "senior data engineer",
    "full stack engineer", "senior full stack engineer",
    "research engineer", "senior research engineer",
    "computer vision engineer",  # adjacent but not ideal per JD
    "analytics engineer", "senior analytics engineer",
}

# Tier C — weak match
TITLE_TIER_C = {
    "data analyst", "senior data analyst",
    "research scientist", "scientist",
    "product manager", "technical product manager",
    "tech lead", "engineering manager",
    "solutions architect", "cloud architect",
    "devops engineer", "senior devops engineer",
    "qa engineer", "test engineer",
    "business intelligence analyst",
}

# Anything not in A/B/C is Tier D (near-zero score)

TITLE_TIER_SCORES = {
    "A": 12.0,
    "B": 7.0,
    "C": 3.0,
    "D": 0.5,
}

# ============================================================================
# Career description keywords — evidence of shipping ML/AI systems
# ============================================================================
# High-value: evidence of production ML systems
CAREER_KEYWORDS_HIGH = {
    "ranking system", "recommendation system", "search system",
    "retrieval system", "deployed", "production", "shipped",
    "embeddings", "vector search", "vector database",
    "candidate ranking", "learning to rank", "re-ranking",
    "reranking", "information retrieval", "semantic search",
    "hybrid search", "dense retrieval", "bm25",
    "a/b test", "a/b testing", "online experiment",
    "ndcg", "mrr", "map", "precision@", "recall@",
    "fine-tuning", "fine-tuned", "finetuning", "finetuned",
    "rag", "retrieval augmented", "retrieval-augmented",
    "sentence-transformers", "sentence transformers",
    "faiss", "pinecone", "qdrant", "weaviate", "milvus",
    "opensearch", "elasticsearch",
    "real users", "production deployment", "production system",
    "end-to-end", "end to end",
    "inference", "model serving", "serving infrastructure",
    "embedding drift", "index refresh",
    "llm", "large language model",
}

# Medium-value: general ML/AI work
CAREER_KEYWORDS_MEDIUM = {
    "machine learning", "deep learning", "neural network",
    "natural language processing", "nlp", "text classification",
    "named entity", "sentiment analysis",
    "tensorflow", "pytorch", "keras", "scikit-learn",
    "xgboost", "lightgbm", "catboost",
    "feature engineering", "feature store",
    "model training", "model evaluation",
    "data pipeline", "ml pipeline", "mlops",
    "transformer", "attention mechanism", "bert", "gpt",
    "hugging face", "huggingface",
    "classification", "regression", "clustering",
    "computer vision", "image classification", "object detection",
    "recommendation engine", "recommender",
    "data science", "predictive model",
    "python", "api", "microservice",
}

# ============================================================================
# Consulting firms — JD explicitly warns about consulting-only careers
# ============================================================================
CONSULTING_FIRMS = {
    "tcs", "tata consultancy services", "tata consultancy",
    "infosys",
    "wipro",
    "accenture",
    "cognizant", "cognizant technology solutions",
    "capgemini",
    "hcl", "hcl technologies",
    "tech mahindra",
    "mindtree",  # now part of LTIMindtree
    "ltimindtree", "lti",
    "mphasis",
    "hexaware",
    "persistent systems",
    "l&t infotech", "larsen & toubro infotech",
    "cyient",
    "zensar",
    "birlasoft",
    "coforge", "niit technologies",
}

# Product companies — evidence of product-company experience is a bonus
PRODUCT_COMPANY_INDICATORS = {
    "product", "saas", "platform", "startup", "series a",
    "series b", "series c", "funded", "venture",
    "consumer", "marketplace", "e-commerce", "ecommerce",
    "fintech", "healthtech", "edtech",
}

# ============================================================================
# Skills categorization for matching
# ============================================================================
SKILLS_CORE_ML = {
    "embeddings", "sentence-transformers", "sentence transformers",
    "bge", "e5", "openai embeddings",
    "faiss", "pinecone", "qdrant", "weaviate", "milvus",
    "opensearch", "elasticsearch", "elastic search",
    "vector database", "vector search", "vector db",
    "hybrid search", "semantic search",
    "information retrieval",
    "ranking", "learning to rank", "re-ranking",
    "recommendation systems", "recommender systems",
    "retrieval", "dense retrieval",
}

SKILLS_PYTHON_INFRA = {
    "python", "docker", "kubernetes", "k8s",
    "ci/cd", "cicd", "jenkins", "github actions",
    "api", "rest api", "fastapi", "flask", "django",
    "aws", "gcp", "azure", "cloud",
    "redis", "postgresql", "mongodb",
    "airflow", "luigi", "prefect",
    "mlflow", "wandb", "weights & biases", "weights and biases",
    "bentoml", "triton", "torchserve",
    "git",
}

SKILLS_LLM = {
    "llm", "large language model", "large language models",
    "lora", "qlora", "peft",
    "fine-tuning", "finetuning", "fine tuning",
    "rag", "retrieval augmented generation",
    "prompt engineering", "prompting",
    "langchain", "llamaindex", "llama index",
    "openai", "anthropic", "claude", "gpt",
    "hugging face", "huggingface", "transformers",
    "bert", "roberta", "distilbert",
    "text generation", "chat model",
    "nlp", "natural language processing",
    "tokenization", "tokenizer",
}

SKILLS_EVAL_RANKING = {
    "ndcg", "mrr", "map", "mean average precision",
    "precision", "recall", "f1",
    "a/b testing", "a/b test", "ab testing",
    "evaluation", "evaluation framework",
    "learning to rank", "xgboost", "lightgbm", "catboost",
    "gradient boosting", "random forest",
    "offline evaluation", "online evaluation",
    "statistical testing", "hypothesis testing",
    "experiment design",
}

SKILL_CATEGORY_MAX_POINTS = {
    "core_ml": 10.0,
    "python_infra": 5.0,
    "llm": 5.0,
    "eval_ranking": 5.0,
}

# ============================================================================
# Experience band scoring
# ============================================================================
EXPERIENCE_BANDS = [
    # (min_years, max_years, score)
    (6.0, 8.0, 15.0),   # sweet spot
    (5.0, 6.0, 12.0),
    (8.0, 9.0, 12.0),
    (4.0, 5.0, 8.0),
    (9.0, 11.0, 8.0),
    (3.0, 4.0, 4.0),
    (11.0, 15.0, 4.0),
    (0.0, 3.0, 1.0),
    (15.0, 50.0, 1.0),
]

# ============================================================================
# Location scoring
# ============================================================================
PREFERRED_CITIES = {"pune", "noida"}
TIER1_INDIAN_CITIES = {
    "hyderabad", "mumbai", "delhi", "new delhi", "gurgaon", "gurugram",
    "bangalore", "bengaluru", "chennai", "kolkata",
    "delhi ncr", "ncr", "greater noida", "ghaziabad", "faridabad",
}

# ============================================================================
# Education — relevant fields
# ============================================================================
RELEVANT_EDUCATION_FIELDS = {
    "computer science", "computer engineering",
    "information technology", "information systems",
    "artificial intelligence", "machine learning",
    "data science", "computational linguistics",
    "mathematics", "applied mathematics", "statistics",
    "electrical engineering", "electronics",
    "software engineering",
}

ADVANCED_DEGREES = {"m.tech", "m.s.", "m.sc", "ms", "mtech", "ph.d", "phd",
                     "m.e.", "me", "master", "masters", "doctorate"}

# ============================================================================
# Behavioral signal thresholds
# ============================================================================
# Recency of last_active_date (days ago)
RECENCY_THRESHOLDS = [
    # (max_days_ago, multiplier)
    (30, 1.0),
    (90, 0.9),
    (180, 0.7),
    (365, 0.5),
    (99999, 0.3),
]

# Recruiter response rate
RESPONSE_RATE_THRESHOLDS = [
    # (min_rate, multiplier)
    (0.6, 1.0),
    (0.3, 0.9),
    (0.0, 0.7),
]

BEHAVIORAL_MULTIPLIER_FLOOR = 0.3
BEHAVIORAL_MULTIPLIER_CEILING = 1.2

# ============================================================================
# Honeypot detection thresholds
# ============================================================================
# If someone claims "expert" in this many skills with 0 endorsements each
HONEYPOT_EXPERT_ZERO_ENDORSEMENT_THRESHOLD = 5
# If skill duration_months is 0 but proficiency is "expert"
HONEYPOT_EXPERT_ZERO_DURATION = True
# Title/description mismatch detection keywords per non-tech title
NON_TECH_TITLES_FOR_MISMATCH = {
    "hr manager", "marketing manager", "accountant", "content writer",
    "graphic designer", "sales executive", "civil engineer",
    "mechanical engineer", "operations manager", "customer support",
    "teacher", "professor", "nurse", "doctor", "lawyer",
    "architect",  # building architect, not software
    "chef", "journalist", "pharmacist",
}
