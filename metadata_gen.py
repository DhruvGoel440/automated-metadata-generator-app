import os, io, json
from pdfminer.high_level import extract_text
import docx
import pytesseract
from PIL import Image
import spacy
from keybert import KeyBERT
from bertopic import BERTopic
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import numpy as np

try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
except:
    #from spacy.cli import download
    # download("en_core_web_sm")
    import spacy
    nlp = spacy.load("en_core_web_sm")

kw_model = KeyBERT()
topic_model = BERTopic()
clf = LogisticRegression()
tfidf = TfidfVectorizer(max_features=1000)

def extract_text_from_path(path, suffix):
    if suffix == ".pdf":
        return extract_text(path)
    if suffix == ".docx":
        doc = docx.Document(path)
        return "\n".join(p.text for p in doc.paragraphs)
    if suffix in [".png", ".jpg", ".jpeg"]:
        img = Image.open(path)
        return pytesseract.image_to_string(img)
    if suffix == ".txt":
        return open(path, encoding="utf-8").read()
    return ""

def generate_metadata(text):
    doc = nlp(text)
    title = next(doc.sents).text if doc.sents else ""
    summary = " ".join([sent.text for _, sent in zip(range(3), doc.sents)])
    
    raw_keywords = kw_model.extract_keywords(
        text,
        keyphrase_ngram_range=(1, 2),
        stop_words="english",
        top_n=10,
        use_maxsum=True,
        nr_candidates=20
    )
    
    keywords = [kw for kw, _ in raw_keywords]
    keyword_scores = dict(raw_keywords)
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    
    return {
        "title": title,
        "summary": summary,
        "keywords": keywords,
        "keyword_scores": keyword_scores,
        "named_entities": entities
    }

def compute_metrics(text):
    doc = nlp(text)
    return {
        "word_count": len(text.split()),
        "sentence_count": len(list(doc.sents)),
        "entity_count": len(doc.ents)
    }

def generate_wordcloud_image(text):
    wc = WordCloud(width=800, height=400, background_color="white").generate(text)
    return wc.to_image()

def keyword_bar_chart_image(keyword_scores):
    keywords = list(keyword_scores.keys())
    scores = list(keyword_scores.values())
    
    fig, ax = plt.subplots(figsize=(6, 4))
    cmap = plt.get_cmap("Blues")
    norm = plt.Normalize(min(scores), max(scores))
    colors = cmap(norm(scores))

    bars = ax.barh(keywords[::-1], scores[::-1], color=colors[::-1])
    ax.set_title("Top Keywords (Relevance Score)")

    for bar, score in zip(bars, scores[::-1]):
        width = bar.get_width()
        ax.text(width + 0.01, bar.get_y() + bar.get_height() / 2,
                f"{score:.2f}", va='center', fontsize=9, color='black')

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    return Image.open(buf)

def render_ner_html(text):
    doc = nlp(text)
    colors = {
        "ORG": "#ffd966",
        "PERSON": "#f4cccc",
        "GPE": "#c9daf8",
        "DATE": "#d9ead3",
        "MONEY": "#e6b8af",
        "PRODUCT": "#b4a7d6",
        "EVENT": "#a2c4c9"
    }
    html = ""
    last = 0
    for ent in doc.ents:
        html += text[last:ent.start_char]
        color = colors.get(ent.label_, "#e0e0e0")
        html += f"<span style='background:{color};padding:2px 5px;border-radius:5px;margin:1px;'>{ent.text}<sub style='font-size:10px;color:#333;'>({ent.label_})</sub></span>"
        last = ent.end_char
    html += text[last:]
    return html

def fit_topics(docs):
    if len(docs) < 2:
        return None, None
    topics, probs = topic_model.fit_transform(docs)
    return topic_model, topics
