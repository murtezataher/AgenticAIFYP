import streamlit as st
import PyPDF2
import pandas as pd
import torch
from torch.nn.functional import cosine_similarity
from transformers import AutoTokenizer, AutoModel

# ----------------- App Config -----------------

st.set_page_config(page_title="Agentic AI Recruiter", layout="wide")
st.title("🤖 Agentic AI for Candidate Selection & Interview")

# ----------------- Load Model -----------------

@st.cache_resource(show_spinner=True)
def load_model():
model_name = "LlamaFactoryAI/cv-job-description-matching"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)
return tokenizer, model

tokenizer, model = load_model()

# ----------------- Helper Function -----------------

def get_embedding(text):
inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
with torch.no_grad():
outputs = model(**inputs, output_hidden_states=True)
embeddings = outputs.last_hidden_state.mean(dim=1)
return embeddings

def calculate_score(cv_text, job_desc):
cv_emb = get_embedding(cv_text)
job_emb = get_embedding(job_desc)
score = cosine_similarity(cv_emb, job_emb)
return float(score.item() * 100)  # scale 0-100

# ----------------- Tabs -----------------

tabs = st.tabs(["📂 Resume Screening", "🗣️ AI Interview", "✅ Final Shortlist"])

# ----------------- Resume Screening Tab -----------------

with tabs[0]:
st.header("📂 Resume Screening")

```
# Define job descriptions
job_roles = {
    "Software Developer": "We are looking for a Software Developer with strong skills in Python, Java, and problem-solving.",
    "Data Scientist": "We are looking for a Data Scientist skilled in Python, SQL, and Machine Learning.",
    "Network Engineer": "We are looking for a Network Engineer familiar with TCP/IP, routing, and firewalls."
}

selected_job = st.selectbox("Choose a job to apply for:", list(job_roles.keys()))
job_desc = job_roles[selected_job]
st.write("**Job Description:**", job_desc)

uploaded_files = st.file_uploader(
    "Upload candidate resumes (PDF)", type=["pdf"], accept_multiple_files=True
)

if uploaded_files and st.button("Submit Application(s)"):
    if "applications" not in st.session_state:
        st.session_state["applications"] = {}
    if "processed_files" not in st.session_state:
        st.session_state["processed_files"] = {}
    if selected_job not in st.session_state["applications"]:
        st.session_state["applications"][selected_job] = []
    if selected_job not in st.session_state["processed_files"]:
        st.session_state["processed_files"][selected_job] = set()

    for file in uploaded_files:
        candidate_name = file.name.replace(".pdf", "")
        if candidate_name in st.session_state["processed_files"][selected_job]:
            continue

        reader = PyPDF2.PdfReader(file)
        text = "".join([page.extract_text() for page in reader.pages if page.extract_text()])

        # ✅ Calculate Job-Fit Score using pretrained model
        score = calculate_score(text, job_desc)

        st.session_state["applications"][selected_job].append({
            "Name": candidate_name,
            "Applied For": selected_job,
            "Extracted Text": text[:300] + "...",
            "Job-Fit Score": round(score, 2),
            "Interviewed": False
        })

        st.session_state["processed_files"][selected_job].add(candidate_name)

    # Display candidate ranking
    job_apps = st.session_state["applications"][selected_job]
    if job_apps:
        st.subheader(f"📊 Candidate Ranking for {selected_job}")
        job_df = pd.DataFrame(job_apps).sort_values(
            by="Job-Fit Score", ascending=False
        ).reset_index(drop=True)
        st.dataframe(job_df[["Name", "Job-Fit Score"]])
    else:
        st.info(f"👆 No applications yet for {selected_job}.")

else:
    st.info("👆 Select a job, upload resumes, and click **Submit Application(s)** to lock them in.")
```

# ----------------- AI Interview Tab -----------------

with tabs[1]:
st.header("🗣️ AI Technical Interview")
# Keep existing interview prototype (text Q&A with mock scoring)
if "applications" in st.session_state and len(st.session_state["applications"]) > 0:
all_apps = []
for job_apps in st.session_state["applications"].values():
all_apps.extend(job_apps)
df = pd.DataFrame(all_apps)
available_apps = df[df["Interviewed"] == False][["Name", "Applied For"]]
if available_apps.empty:
st.info("✅ All applications have been interviewed.")
else:
options = [f"{row['Name']} ({row['Applied For']})" for _, row in available_apps.iterrows()]
choice = st.selectbox("Select an application to interview", options)
if choice:
selected_name, selected_job = choice.split(" (")
selected_job = selected_job.replace(")", "")
st.write(f"**Candidate:** {selected_name}")
st.write(f"**Applied for:** {selected_job}")
if st.button("Start Interview"):
st.session_state["interviewing"] = True
st.session_state["q_num"] = 1
st.session_state["answers"] = []
st.session_state["candidate_job"] = selected_job
st.session_state["current_candidate"] = selected_name
else:
st.info("👆 Upload and submit at least one application first.")

# ----------------- Final Shortlist Tab -----------------

with tabs[2]:
st.header("✅ Final Shortlist")
# Keep existing mock shortlist (to implement later)
if "results" in st.session_state and len(st.session_state["results"]) > 0:
results_df = pd.DataFrame(st.session_state["results"])
jobs = results_df["Job Role"].unique()
for job in jobs:
st.markdown(f"### 🏆 Top Candidates for {job}")
job_df = results_df[results_df["Job Role"] == job]
shortlist = job_df.sort_values(by="Interview Score", ascending=False).head(3)
st.dataframe(shortlist[["Name", "Interview Score", "Feedback"]])
st.success("These candidates are applicable for final human interviews.")
else:
st.info("👆 Complete at least one interview to see shortlist.")
