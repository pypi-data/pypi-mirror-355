import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

def remove_stopwords(text: str, lang='english'):
    tokens = word_tokenize(text)
    stop_words = set(stopwords.words(lang))
    return ' '.join([w for w in tokens if w.lower() not in stop_words])
