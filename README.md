# 🧠 Automated Metadata Generator

A Streamlit-based app that extracts and visualizes metadata from documents (PDF, DOCX, TXT, and Images). It performs AI-powered summarizati
streamlit run app.py
on, keyword extraction, named entity recognition, and more.

# 📍 **Live App: https://automated-metadata-generator-app.streamlit.app**  
👉 [Click Here for App Link](https://automated-metadata-generator-app.streamlit.app/) 👈  

🎬 **Video Demo:**  
📺 [Watch the Demo on Google Drive](https://drive.google.com/file/d/1JzmD3WbEOZeGhpquPUpZegwIeKFOzQQf/view?usp=sharing)
<details>
<summary>▶️ Click to preview the video below (Google Drive embed)</summary>
<iframe src="https://drive.google.com/file/d/1JzmD3WbEOZeGhpquPUpZegwIeKFOzQQf/preview" width="100%" height="480" allow="autoplay"></iframe>
</details>
---

## 🚀 Features

- 📄 Document parsing (PDF, DOCX, TXT, Images)
- 🧾 Structured metadata extraction
- 🧠 AI-based summarization using transformers
- 🔑 Keyword extraction and relevance visualization
- ☁️ Word Cloud generation
- 🧠 Named Entity Recognition (NER)

---

## 📦 Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/metadata-generator.git
cd metadata-generator
```

2. Install dependencies:
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

## ▶️ Run Locally
```bash
streamlit run app.py
```

## 🌐 Deployment on Streamlit Cloud
- To deploy this project on Streamlit Community Cloud:
    1. Push this project to a GitHub repository.
    2. Log into Streamlit Cloud with your GitHub account.
    3. Click "New App".
    4. Select your repository and set app.py as the main file.
    5. Click "Deploy".