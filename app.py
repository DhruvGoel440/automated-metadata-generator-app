#Import modules
import streamlit as st
import os, tempfile, json, hashlib
import metadata_gen as mg

#Streamlit page setup
st.set_page_config(
    page_title="Metadata Generator",
    layout="wide",
    initial_sidebar_state="collapsed"
)
st.markdown("# Automated Metadata Generator")

#File uploader
uploaded_files = st.file_uploader(
    "📁 Upload documents (PDF, DOCX, TXT, Image)", 
    type=["pdf", "docx", "txt", "png", "jpg", "jpeg"], 
    accept_multiple_files=True
)

#Processing the uploaded files
if uploaded_files:
    for uploaded_file in uploaded_files:
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()
        
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext)
        tmp_file.write(uploaded_file.read())
        tmp_file.close()

        #Extracting text and analyzing
        raw_text = mg.read_document(tmp_file.name, file_ext)
        metadata = mg.extract_metadata(raw_text)
        stats = mg.get_document_stats(raw_text)

        doc_hash = hashlib.md5(uploaded_file.name.encode()).hexdigest()

        st.markdown("----")
        st.markdown(f"### 📝 Document ID: `{doc_hash}`")
        st.metric("📄 Filename", uploaded_file.name)

        with st.expander("📈 File Details", expanded=True):
            col1, col2, col3 = st.columns(3)
            col1.metric("📦 File Size", f"{os.path.getsize(tmp_file.name) / 1024:.2f} KB")
            col2.metric("📁 File Type", "Document")
            col3.metric("🧾 Content Type", uploaded_file.type)

        #Summary and keywords
        with st.expander("📑 Summary & Keywords", expanded=True):
            st.subheader("📝 Summary")
            st.write(metadata["summary"])

            st.subheader("🔑 Keywords")
            st.markdown(
                "".join(
                    f"<span style='display:inline-block;background:#e0f0ff;color:#004080;"
                    f"padding:5px 10px;border-radius:15px;margin:2px;font-size:14px;'>{kw}</span>"
                    for kw in metadata["keywords"]
                ),
                unsafe_allow_html=True
            )

        #Basic metrics
        with st.expander("📈 Document Metrics", expanded=True):
            col1, col2, col3 = st.columns(3)
            col1.metric("Word Count", stats["word_count"])
            col2.metric("Sentences", stats["sentence_count"])
            col3.metric("Named Entities", stats["entity_count"])

        with st.expander("🧾 Structured Metadata"):
            for title, content in metadata["structured_metadata"].items():
                st.markdown(f"#### {title}")
                st.write(content)

        #Wordcloud & Keyword bar chart
        st.markdown("### 🔎 Keyword Insights")
        col_wc, col_bar = st.columns(2)

        with col_wc:
            st.markdown("#### ☁️ Word Cloud")
            st.image(mg.create_wordcloud_image(raw_text).resize((700, 400)))

        with col_bar:
            st.markdown("#### 📊 Keyword Relevance")
            st.image(mg.keyword_score_bar_image(metadata["keyword_scores"]).resize((700, 400)))

        with st.expander("🧠 Named Entity Recognition"):
            st.markdown(mg.visualize_named_entities(raw_text), unsafe_allow_html=True)

        #Download JSON metadata of the document
        json_filename = f"{uploaded_file.name}_metadata.json"
        with open(json_filename, "w") as json_out:
            json.dump(metadata, json_out, indent=2)
        with open(json_filename, "rb") as json_in:
            st.download_button(
                label="⬇️ Download Metadata JSON",
                data=json_in,
                file_name=json_filename,
                mime="application/json"
            )