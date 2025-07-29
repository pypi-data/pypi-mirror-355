from sklearn.feature_extraction.text import TfidfVectorizer

def extract_keywords(text: str, top_n=5):
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform([text])
    scores = zip(vectorizer.get_feature_names_out(), tfidf_matrix.toarray()[0])
    sorted_words = sorted(scores, key=lambda x: x[1], reverse=True)
    return [word for word, score in sorted_words[:top_n]]
