import re
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer
from nltk.tokenize import word_tokenize

# Initialize stemmer and stopwords
stemmer = SnowballStemmer("spanish")
stop_words = set(stopwords.words('spanish'))

def preprocess_text(text):
    # Normalize text
    text = text.lower()
    text = re.sub(r'[^a-záéíóúñü\s]', '', text)

    # Tokenize text
    tokens = word_tokenize(text)

    # Remove stopwords and apply stemming
    processed_tokens = [stemmer.stem(word) for word in tokens if word not in stop_words]

    return processed_tokens
