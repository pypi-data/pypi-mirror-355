import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)

def remove_stopwords(text: str, lang='english'):
    tokens = word_tokenize(text)
    stop_words = set(stopwords.words(lang))
    filtered = [word for word in tokens if word.lower() not in stop_words]
    return ' '.join(filtered)
