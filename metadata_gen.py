# Import modules
import re, io
from pdfminer.high_level import extract_text as extract_pdf_text
import docx
import easyocr
from PIL import Image
import spacy
from keybert import KeyBERT
from transformers import pipeline
from sentence_transformers import SentenceTransformer, util
import matplotlib.pyplot as plt
import numpy as np
from wordcloud import WordCloud

# Load models
nlp_model = spacy.load("en_core_web_sm")
keyword_extractor = KeyBERT()
text_summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
sbert_model = SentenceTransformer("all-MiniLM-L6-v2")
ocr_reader = easyocr.Reader(['en'], gpu=False)

# Function for reading the document uploaded on the app
def read_document(path, extension):
    try:
        if extension == ".pdf":
            return extract_pdf_text(path)
        elif extension == ".docx":
            return "\n".join(para.text for para in docx.Document(path).paragraphs)
        elif extension in [".png", ".jpg", ".jpeg"]:
            lines = ocr_reader.readtext(path, detail=0)
            return "\n".join(lines)
        elif extension == ".txt":
            return open(path, encoding="utf-8").read()
    except Exception as e:
        return f"Could not read file: {e}"
    return ""

# Function to find out if the line is a Potential Heading
def is_potential_heading(line):
    text = line.strip()
    return (
        0 < len(text) <= 100 and (
            text.isupper() or
            text.endswith(":") or
            re.match(r"^\d+[\.\)]", text) or
            text.lower() in [
                "introduction", "background", "challenges", "limitations", "results",
                "discussion", "methodology", "methods", "conclusion", "summary",
                "references", "abstract", "future work"
            ] or
            len(text.split()) <= 5
        )
    )

# Function to divide the text into sections
def segment_text_into_sections(raw_text):
    lines = [line for line in raw_text.split("\n") if line.strip()]
    structured = {}
    heading, buffer = None, []

    for line in lines:
        if is_potential_heading(line):
            if heading and buffer:
                structured[heading] = "\n".join(buffer).strip()
            heading, buffer = line.strip(), []
        else:
            if heading:
                buffer.append(line)

    if heading and buffer:
        structured[heading] = "\n".join(buffer).strip()

    if len(structured) < 3 or all(len(sec.split()) < 50 for sec in structured.values()):
        paras = [p.strip() for p in raw_text.split("\n\n") if len(p.split()) > 30]
        if len(paras) < 3:
            structured = {"Main Content": "\n\n".join(paras)}
        else:
            vectors = sbert_model.encode(paras, normalize_embeddings=True)
            groups = util.community_detection(vectors, min_community_size=1, threshold=0.75)
            structured = {f"Section {i+1}": "\n\n".join(paras[idx] for idx in cluster) for i, cluster in enumerate(groups)}

    return structured

# Function to extract metadata from the text
def extract_metadata(text, fast=True):
    sections = segment_text_into_sections(text)
    summaries, key_terms, keyword_scores = [], [], {}
    named_entities = set()

    if not fast:
        for title, body in sorted(sections.items(), key=lambda x: len(x[1]), reverse=True)[:3]:
            try:
                summary = text_summarizer(body[:1024], max_length=120, min_length=30, do_sample=False)[0]['summary_text']
                summaries.append(f"### {title}\n{summary}")
            except:
                continue
    else:
        try:
            summaries.append(text_summarizer(text[:1024], max_length=150, min_length=40, do_sample=False)[0]['summary_text'])
        except:
            summaries.append("Summary generation failed.")

    if len(sections) > 6:
        top_keywords = keyword_extractor.extract_keywords(text, keyphrase_ngram_range=(1, 2), stop_words="english", top_n=10)
        key_terms = [term for term, _ in top_keywords]
        keyword_scores = dict(top_keywords)
        named_entities = {(ent.text, ent.label_) for ent in nlp_model(text).ents}
    else:
        for _, content in sections.items():
            for term, score in keyword_extractor.extract_keywords(content, keyphrase_ngram_range=(1,2), stop_words="english", top_n=3):
                if term not in keyword_scores:
                    key_terms.append(term)
                    keyword_scores[term] = score
            named_entities.update((ent.text, ent.label_) for ent in nlp_model(content).ents)

    return {
        "summary": "\n\n".join(summaries),
        "structured_metadata": sections,
        "keywords": key_terms,
        "keyword_scores": keyword_scores,
        "named_entities": list(named_entities)
    }

# Function to get word count, sentence count etc. from the text
def get_document_stats(text):
    doc = nlp_model(text)
    return {
        "word_count": len(text.split()),
        "sentence_count": len(list(doc.sents)),
        "entity_count": len(doc.ents)
    }

# Function to create the Wordcloud for the document
def create_wordcloud_image(text):
    return WordCloud(width=800, height=400, background_color="white").generate(text).to_image()

# Function to generate the keyword relevance chart
def keyword_score_bar_image(scores):
    keys, values = list(scores.keys()), list(scores.values())
    fig, ax = plt.subplots(figsize=(6, 4))
    colors = plt.get_cmap("Blues")(plt.Normalize(min(values), max(values))(values))
    bars = ax.barh(keys[::-1], values[::-1], color=colors[::-1])
    ax.set_title("Top Keywords (Relevance)")
    for bar, val in zip(bars, values[::-1]):
        ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height() / 2,
                f"{val:.2f}", va='center', fontsize=9)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    return Image.open(buf)

# Function to render NER tags with HTML highlighting
def visualize_named_entities(text):
    highlight_colors = {
        "ORG": "#ffd966", "PERSON": "#f4cccc", "GPE": "#c9daf8",
        "DATE": "#d9ead3", "MONEY": "#e6b8af", "PRODUCT": "#b4a7d6", "EVENT": "#a2c4c9"
    }
    doc = nlp_model(text)
    result_html, last_idx = "", 0
    for ent in doc.ents:
        result_html += text[last_idx:ent.start_char]
        shade = highlight_colors.get(ent.label_, "#e0e0e0")
        result_html += f"<span style='background:{shade};padding:2px 5px;border-radius:5px;margin:1px;'>{ent.text}<sub style='font-size:10px;color:#333;'>({ent.label_})</sub></span>"
        last_idx = ent.end_char
    result_html += text[last_idx:]
    return result_html