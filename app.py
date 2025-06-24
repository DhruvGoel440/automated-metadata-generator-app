import streamlit as st
import os, tempfile, json, hashlib
import metadata_gen as mg

st.set_page_config(layout="wide", page_title="Metadata Generator")
st.markdown("## 📄 Automated Metadata Generator")

uploaded = st.file_uploader(
    "Upload documents", 
    type=["pdf", "docx", "txt", "png", "jpg", "jpeg"], 
    accept_multiple_files=True
)

docs_text = []
doc_names = []

if uploaded:
    for file in uploaded:
        suffix = os.path.splitext(file.name)[1].lower()
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp.write(file.read())
        tmp.close()

        text = mg.extract_text_from_path(tmp.name, suffix)
        docs_text.append(text)
        doc_names.append(file.name)

        meta = mg.generate_metadata(text)
        metrics = mg.compute_metrics(text)

        doc_id = hashlib.md5(file.name.encode()).hexdigest()

        st.markdown("---")
        st.markdown(f"### 📘 Document ID: `{doc_id}`")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Filename", file.name)
        col2.metric("File Size", f"{os.path.getsize(tmp.name) / 1024:.2f} KB")
        col3.metric("File Type", "Document")
        col4.metric("Content Type", file.type)

        st.markdown("### 📝 Summary")
        st.write(meta["summary"])

        st.markdown("### 🔑 Keywords")
        for kw in meta["keywords"]:
            st.markdown(
                f"<span style='display:inline-block;background:#e0f0ff;color:#004080;"
                f"padding:5px 10px;border-radius:15px;margin:2px;font-size:14px;'>{kw}</span>",
                unsafe_allow_html=True
            )

        st.markdown("### ☁️ Word Cloud")
        st.image(mg.generate_wordcloud_image(text), use_column_width=True)

        st.markdown("### 📊 Keyword Relevance")
        st.image(mg.keyword_bar_chart_image(meta["keyword_scores"]), use_column_width=True)

        st.markdown("### 📈 Document Metrics")
        col1, col2, col3 = st.columns(3)
        col1.metric("Word Count", metrics["word_count"])
        col2.metric("Sentences", metrics["sentence_count"])
        col3.metric("Named Entities", metrics["entity_count"])

        st.markdown("### 🧠 Named Entity Recognition (NER)")
        st.markdown(mg.render_ner_html(text), unsafe_allow_html=True)

        json_path = f"{file.name}_metadata.json"
        with open(json_path, "w") as f:
            json.dump(meta, f, indent=2)
        with open(json_path, "rb") as f:
            st.download_button(
                label="⬇️ Download Metadata JSON",
                data=f,
                file_name=f"{file.name}_metadata.json",
                mime="application/json"
            )

if len(docs_text) >= 2:
    st.markdown("## 🧠 Topic Modeling across uploaded documents")
    model, topics = mg.fit_topics(docs_text)
    if model:
        st.plotly_chart(model.visualize_barchart(top_n_topics=5))
        st.plotly_chart(model.visualize_topics())
