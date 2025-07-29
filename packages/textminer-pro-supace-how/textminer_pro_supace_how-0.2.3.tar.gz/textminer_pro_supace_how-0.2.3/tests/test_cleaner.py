import sys
sys.path.append('/content/textminer_pro')
import os
import nltk
from textminer import remove_stopwords, extract_keywords


NLTK_PATH = "/content/nltk_data"
os.environ["NLTK_DATA"] = NLTK_PATH
nltk.data.path.append(NLTK_PATH)


nltk.download('punkt', download_dir=NLTK_PATH)
nltk.download('punkt_tab', download_dir=NLTK_PATH)
nltk.download('stopwords', download_dir=NLTK_PATH)

text = "This is a test sentence with simple words."
print("Stopword 제거 결과:")
print(remove_stopwords(text))

text2 = "Machine learning is fun and powerful."
print("키워드 추출 결과:")
print(extract_keywords(text2))