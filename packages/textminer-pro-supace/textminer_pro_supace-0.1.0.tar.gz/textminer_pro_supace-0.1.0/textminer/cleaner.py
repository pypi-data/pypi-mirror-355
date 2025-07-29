from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
import string

# ✅ 간단한 토크나이저 (punkt 없이 작동)
def simple_tokenize(text):
    return text.lower().translate(str.maketrans('', '', string.punctuation)).split()

# ✅ 언어 코드 매핑
LANG_MAP = {
    'en': 'english',
    'fr': 'french',
    'de': 'german',
    'es': 'spanish',
    'it': 'italian',
    'pt': 'portuguese',
    'ru': 'russian',
}

# ✅ 불용어 제거 (punkt 불필요)
def remove_stopwords(text: str, lang='en') -> str:
    lang = LANG_MAP.get(lang, lang)
    try:
        stop_words = set(stopwords.words(lang))
    except:
        return "[지원되지 않는 언어]"

    words = simple_tokenize(text)
    filtered = [w for w in words if w not in stop_words]
    return ' '.join(filtered)

# ✅ 키워드 추출 (TF-IDF 기반)
def extract_keywords(text: str, top_n=5) -> list:
    try:
        vectorizer = TfidfVectorizer(stop_words='english')
        X = vectorizer.fit_transform([text])
        scores = zip(vectorizer.get_feature_names_out(), X.toarray()[0])
        sorted_keywords = sorted(scores, key=lambda x: x[1], reverse=True)
        return [word for word, _ in sorted_keywords[:top_n]]
    except:
        return []
