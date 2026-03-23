import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


# ─── Keyword Rules ────────────────────────────────────────────────────────────
# Layer 1: fast rule-based matching
# Add as many keywords as you like for each category

CATEGORY_KEYWORDS = {
    "food": [
        "swiggy", "zomato", "restaurant", "cafe", "coffee",
        "pizza", "burger", "dominos", "mcdonalds", "kfc",
        "starbucks", "bakery", "hotel", "dhaba", "food"
    ],
    "groceries": [
        "grocery", "supermarket", "bigbasket", "blinkit", "zepto",
        "dmart", "reliance fresh", "more", "nature basket", "vegetables",
        "fruits", "milk", "provisions"
    ],
    "transport": [
        "uber", "ola", "rapido", "metro", "bus", "petrol", "fuel",
        "parking", "toll", "cab", "auto", "fastag", "irctc", "railway"
    ],
    "shopping": [
        "amazon", "flipkart", "myntra", "ajio", "nykaa", "meesho",
        "snapdeal", "shopping", "mall", "store", "retail"
    ],
    "utilities": [
        "electricity", "water", "gas", "internet", "broadband",
        "airtel", "jio", "vi ", "vodafone", "bsnl", "bill", "recharge"
    ],
    "entertainment": [
        "netflix", "hotstar", "prime", "spotify", "youtube", "gaming",
        "steam", "movie", "cinema", "pvr", "inox", "bookmyshow"
    ],
    "health": [
        "pharmacy", "hospital", "clinic", "doctor", "medicine",
        "apollo", "medplus", "1mg", "practo", "diagnostic", "lab"
    ],
    "subscriptions": [
        "subscription", "membership", "annual", "renewal", "plan"
    ],
    "income": [
        "salary", "credit", "cashback", "refund", "bonus",
        "interest", "dividend", "transfer in", "received"
    ],
    "atm": [
        "atm", "cash withdrawal", "withdrawal"
    ],
    "education": [
        "udemy", "coursera", "college", "university", "school",
        "tuition", "course", "books", "stationery"
    ]
}


# ─── TF-IDF Setup ─────────────────────────────────────────────────────────────
# Layer 2: vectorize category names + keywords for similarity fallback

def _build_tfidf_index():
    """Build a TF-IDF index from category keywords for fallback matching."""
    categories = list(CATEGORY_KEYWORDS.keys())
    # Join all keywords per category into one string
    category_texts = [" ".join(CATEGORY_KEYWORDS[cat]) for cat in categories]

    vectorizer = TfidfVectorizer()
    matrix = vectorizer.fit_transform(category_texts)

    return vectorizer, matrix, categories


_vectorizer, _matrix, _categories = _build_tfidf_index()


# ─── Core Categorization Logic ────────────────────────────────────────────────

def _keyword_match(description: str) -> str | None:
    """Layer 1: Check if description contains any keyword."""
    desc_lower = description.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in desc_lower:
                return category
    return None


def _tfidf_match(description: str) -> str:
    """Layer 2: Find closest category using TF-IDF cosine similarity."""
    desc_vec = _vectorizer.transform([description.lower()])
    similarities = cosine_similarity(desc_vec, _matrix)[0]
    best_index = np.argmax(similarities)

    # If similarity is too low, just call it miscellaneous
    if similarities[best_index] < 0.1:
        return "miscellaneous"

    return _categories[best_index]


def categorize(description: str) -> str:
    """
    Main categorization function.
    Try keyword match first, fall back to TF-IDF.
    """
    if not description or not description.strip():
        return "miscellaneous"

    # Layer 1
    result = _keyword_match(description)
    if result:
        return result

    # Layer 2
    return _tfidf_match(description)


def categorize_batch(descriptions: list[str]) -> list[str]:
    """Categorize a list of descriptions at once."""
    return [categorize(desc) for desc in descriptions]