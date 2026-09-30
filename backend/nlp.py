"""Pure-Python NLP pipeline: Naive Bayes category classifier + sentiment + urgency scoring.
No scikit-learn / numpy, so it also works on PCs where Windows blocks compiled DLLs."""
import math
import re
from collections import Counter, defaultdict

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Small seed set so the app works out of the box.
# Replace with your own historical tickets (text, category) for better accuracy.
SEED = [
    ("cannot login password reset not working", "account"),
    ("locked out of my account 2fa code missing", "account"),
    ("forgot password no reset email received", "account"),
    ("unable to sign in account suspended", "account"),
    ("charged twice on my credit card refund", "billing"),
    ("invoice is wrong need updated receipt", "billing"),
    ("payment failed subscription renewal charge", "billing"),
    ("please refund my last payment", "billing"),
    ("app crashes on startup error 500", "bug"),
    ("page shows error when saving data loss", "bug"),
    ("button does not work exception on submit", "bug"),
    ("feature broken after update error message", "bug"),
    ("production api is down all requests failing", "outage"),
    ("service unavailable entire team cannot work", "outage"),
    ("website is down not loading for all users", "outage"),
    ("complete outage servers not responding", "outage"),
    ("how do i export my data to csv", "how_to"),
    ("where can i change notification settings", "how_to"),
    ("how to invite a team member", "how_to"),
    ("question about using the dashboard", "how_to"),
    ("would love a dark mode feature", "feature_request"),
    ("please add integration with slack", "feature_request"),
    ("suggestion to add new report option", "feature_request"),
    ("it would be great to support more languages", "feature_request"),
]

# Extra hints that push obvious tickets to the right category.
HINTS = {
    "outage": ["down", "outage", "unavailable", "offline", "not responding"],
    "bug": ["crash", "crashes", "error", "exception", "broken", "bug"],
    "billing": ["invoice", "refund", "charged", "payment", "billing", "receipt"],
    "account": ["login", "password", "locked", "2fa", "sign", "account"],
    "how_to": ["how", "where", "tutorial", "guide"],
    "feature_request": ["feature", "suggest", "add", "wish", "integration"],
}

STOP = set("the a an is are was were to of and in on for my our it i we you with this that at be have has not".split())


def tokens(text: str) -> list:
    return [w for w in re.findall(r"[a-z0-9']+", text.lower()) if w not in STOP]


class NaiveBayes:
    def __init__(self, data):
        self.cat_docs = Counter()
        self.word_counts = defaultdict(Counter)
        self.vocab = set()
        for text, cat in data:
            self.cat_docs[cat] += 1
            for w in tokens(text):
                self.word_counts[cat][w] += 1
                self.vocab.add(w)
        self.total_docs = sum(self.cat_docs.values())

    def predict(self, text: str) -> str:
        words = tokens(text)
        best, best_score = "how_to", -1e18
        for cat in self.cat_docs:
            total = sum(self.word_counts[cat].values())
            score = math.log(self.cat_docs[cat] / self.total_docs)
            for w in words:
                score += math.log((self.word_counts[cat][w] + 1) / (total + len(self.vocab) + 1))
                if w in HINTS.get(cat, []):
                    score += 2.0
            if score > best_score:
                best, best_score = cat, score
        return best


_clf = NaiveBayes(SEED)
_sia = SentimentIntensityAnalyzer()

URGENT_WORDS = re.compile(
    r"\b(urgent|asap|immediately|down|outage|critical|blocked|production|"
    r"data loss|security|breach|cannot work|deadline)\b", re.I)
LEGAL_WORDS = re.compile(r"\b(lawyer|legal|chargeback|cancel|refund|sue|gdpr)\b", re.I)

CATEGORY_WEIGHT = {"outage": 40, "bug": 22, "billing": 18, "account": 16,
                   "how_to": 5, "feature_request": 2}
PLAN_WEIGHT = {"enterprise": 25, "pro": 12, "free": 0}


def analyze(subject: str, body: str, plan: str, age_hours: float = 0.0) -> dict:
    text = f"{subject}. {body}"
    category = _clf.predict(text)
    sentiment = _sia.polarity_scores(text)["compound"]

    score, reasons = 0.0, []
    w = CATEGORY_WEIGHT.get(category, 5)
    score += w; reasons.append(f"category={category} (+{w})")

    p = PLAN_WEIGHT.get(plan, 0)
    if p: score += p; reasons.append(f"{plan} plan (+{p})")

    if sentiment < -0.3:
        s = round(min(20, abs(sentiment) * 20)); score += s
        reasons.append(f"negative tone (+{s})")

    hits = len(set(m.lower() for m in URGENT_WORDS.findall(text)))
    if hits:
        u = min(20, hits * 7); score += u; reasons.append(f"urgent keywords (+{u})")

    if LEGAL_WORDS.search(text):
        score += 8; reasons.append("legal/churn risk (+8)")

    if age_hours > 0:  # SLA aging: waiting tickets climb the queue
        a = min(10, age_hours / 4); score += a
        reasons.append(f"waiting {age_hours:.0f}h (+{a:.0f})")

    score = min(100.0, score)
    priority = "P1" if score >= 70 else "P2" if score >= 45 else "P3" if score >= 20 else "P4"
    return {"category": category, "sentiment": sentiment, "score": round(score, 1),
            "priority": priority, "reasons": "; ".join(reasons)}
