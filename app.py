import streamlit as st
import PyPDF2
import pandas as pd
import random

# ----------------- App Config -----------------
st.set_page_config(page_title="Agentic AI Recruiter", layout="wide")

st.title("🤖 Agentic AI for Candidate Selection & Interview")

# Tabs for navigation
tabs = st.tabs(["📂 Resume Screening", "🗣️ AI Interview", "✅ Final Shortlist"])

# ----------------- Resume Screening Tab -----------------
with tabs[0]:
    st.header("📂 Resume Screening")

    # Define job descriptions
    job_roles = {
        "Software Developer": "We are looking for a Software Developer with strong skills in Python, Java, and problem-solving.",
        "Data Scientist": "We are looking for a Data Scientist skilled in Python, SQL, and Machine Learning.",
        "Network Engineer": "We are looking for a Network Engineer familiar with TCP/IP, routing, and firewalls."
    }

    # Dropdown for job selection
    selected_job = st.selectbox("Choose a job to apply for:", list(job_roles.keys()))
    job_desc = job_roles[selected_job]
    st.write("**Job Description:**", job_desc)

    uploaded_files = st.file_uploader(
        "Upload candidate resumes (PDF)", type=["pdf"], accept_multiple_files=True
    )

    # ✅ Add button to confirm applications
    if uploaded_files and st.button("Submit Application(s)"):
        if "applications" not in st.session_state:
            st.session_state["applications"] = {}  # store per job
        if "processed_files" not in st.session_state:
            st.session_state["processed_files"] = {}

        # ensure job key exists
        if selected_job not in st.session_state["applications"]:
            st.session_state["applications"][selected_job] = []
        if selected_job not in st.session_state["processed_files"]:
            st.session_state["processed_files"][selected_job] = set()

        for file in uploaded_files:
            candidate_name = file.name.replace(".pdf", "")

            # Skip if already added for this job
            if candidate_name in st.session_state["processed_files"][selected_job]:
                continue

            reader = PyPDF2.PdfReader(file)
            text = "".join([page.extract_text() for page in reader.pages if page.extract_text()])

            # Mock scoring (simple keyword overlap + randomness)
            keywords = job_desc.lower().split()
            score = sum(1 for kw in keywords if kw in text.lower())
            score = min(100, score * 10 + random.randint(20, 40))

            # Save application for this job only
            st.session_state["applications"][selected_job].append({
                "Name": candidate_name,
                "Applied For": selected_job,
                "Extracted Text": text[:300] + "...",
                "Job-Fit Score": score,
                "Interviewed": False
            })

            # mark processed for this job
            st.session_state["processed_files"][selected_job].add(candidate_name)

    # Show candidate ranking ONLY for the currently selected job
    if "applications" in st.session_state and selected_job in st.session_state["applications"]:
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

# ----------------- AI Interview Tab -----------------
with tabs[1]:
    st.header("🗣️ AI Technical Interview")

    if "applications" in st.session_state and len(st.session_state["applications"]) > 0:
        # flatten applications across all jobs
        all_apps = []
        for job_apps in st.session_state["applications"].values():
            all_apps.extend(job_apps)

        df = pd.DataFrame(all_apps)

        # Filter only non-interviewed applications
        available_apps = df[df["Interviewed"] == False][["Name", "Applied For"]]

        if available_apps.empty:
            st.info("✅ All applications have been interviewed.")
        else:
            # Show candidate + job pair
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

    # Handle interview questions
    if st.session_state.get("interviewing", False):
        interview_questions = {
            "Software Developer": [
                "What are the principles of Object-Oriented Programming?",
                "Explain the difference between Python and Java.",
                "How would you optimize a slow algorithm in code?"
            ],
            "Data Scientist": [
                "What is the difference between supervised and unsupervised learning?",
                "How do you handle missing data in a dataset?",
                "Explain bias-variance tradeoff in machine learning."
            ],
            "Network Engineer": [
                "Explain the difference between TCP and UDP.",
                "What is the role of a subnet mask?",
                "How would you troubleshoot a network latency issue?"
            ]
        }

        job = st.session_state["candidate_job"]
        candidate = st.session_state["current_candidate"]
        q_list = interview_questions.get(job, ["Tell me about yourself."])

        q_num = st.session_state["q_num"]

        if q_num <= len(q_list):
            st.write(f"**Q{q_num}:** {q_list[q_num-1]}")
            answer = st.text_area("Candidate's answer:")

            if st.button("Submit Answer", key=f"q{q_num}"):
                st.session_state["answers"].append(answer)
                st.session_state["q_num"] += 1

        else:
            st.success(f"✅ Interview Complete for {candidate} ({job})!")
            st.balloons()

            # Mock feedback
            feedback = random.choice([
                "Candidate shows strong technical knowledge.",
                "Candidate has basic understanding but needs improvement.",
                "Excellent problem-solving and conceptual clarity."
            ])
            st.write("**AI Feedback:**", feedback)

            # Save final score
            score = random.randint(60, 100)
            if "results" not in st.session_state:
                st.session_state["results"] = []
            st.session_state["results"].append({
                "Name": candidate,
                "Job Role": job,
                "Interview Score": score,
                "Feedback": feedback
            })

            # Mark application as interviewed
            for app in st.session_state["applications"][job]:
                if app["Name"] == candidate:
                    app["Interviewed"] = True

            # Reset interview state
            st.session_state["interviewing"] = False
            st.session_state["current_candidate"] = None

# ----------------- Final Shortlist Tab -----------------
with tabs[2]:
    st.header("✅ Final Shortlist")

    if "results" in st.session_state and len(st.session_state["results"]) > 0:
        results_df = pd.DataFrame(st.session_state["results"])

        # Show shortlist per job
        jobs = results_df["Job Role"].unique()
        for job in jobs:
            st.markdown(f"### 🏆 Top Candidates for {job}")
            job_df = results_df[results_df["Job Role"] == job]
            shortlist = job_df.sort_values(by="Interview Score", ascending=False).head(3)
            st.dataframe(shortlist[["Name", "Interview Score", "Feedback"]])

        st.success("These candidates are applicable for final human interviews.")
    else:
        st.info("👆 Complete at least one interview to see shortlist.")
