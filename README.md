<div align="center">

# 🏝️ Smart AI Resume Analyzer 🏝️

**Your Intelligent Career Partner**

Smart AI Resume Analyzer is an all-in-one tool to analyze, optimize, and craft resumes that stand out, helping you land your dream job.

Built by **Shubham Choubey**

</div>

## 🔗 Helpful Links

- [![AI Models Badge](https://img.shields.io/badge/AI%20Models-Documentation-purple?style=for-the-badge&logo=openai&logoColor=white)](AI_MODELS.md)
- [![Contribution Guide Badge](https://img.shields.io/badge/Contribution%20Guide-Read%20Here-brightgreen?style=for-the-badge&logo=github&logoColor=white)](.github/CONTRIBUTING.md)

## 🚀 What Makes It Different?

**Next-Level Features for Success:**

1. 🕵️ **Deep Resume Analysis**
   - 🛡️ ATS Compatibility Score
   - 🔑 Keyword Gap Analysis
   - 🧩 Role-specific Feedback
   - 📊 Skills Gap Breakdown

2. 🎨 **AI-Powered Resume Builder**
   - Themes that Shine (Modern, Minimal, Professional, Creative)
   - Smart Content Suggestions
   - ATS-Optimized Formatting
   - Customizable Sections

3. 🤖 **AI Optimization Engine**
   - 💡 Keyword Highlighting
   - ✍️ Content Enhancement Tips
   - 🌟 Industry-Specific Insights

**🎉 Why Use Smart Resume AI?**
Get real-time feedback, boost your resume's impact, and maximize your chances of getting shortlisted — all with a sleek, intuitive interface.

## 🧰 Tech Stack

<details>
  <summary>🌐 Frontend</summary>

| Technology | Role |
|---|---|
| [Streamlit](https://streamlit.io/) | Builds interactive and user-friendly web apps for resume analysis. |
| HTML | Provides the basic structure for web pages. |
| CSS | Adds styling and layouts to the frontend. |
| JavaScript | Enables interactivity and dynamic behavior for the web pages. |

</details>

<details>
  <summary>⚙️ Backend</summary>

| Technology | Role |
|---|---|
| [Streamlit](https://streamlit.io/) | Handles backend logic and integrates machine learning models. |
| [Python](https://www.python.org/) | Core programming language for implementing functionality. |

</details>

<details>
  <summary>🗄️ Database</summary>

| Technology | Role |
|---|---|
| [SQLite3](https://www.sqlite.org/index.html) | Stores and retrieves resume data for efficient processing. |

</details>

<details>
  <summary>📦 Modules</summary>

| Technology | Role |
|---|---|
| [spaCy](https://spacy.io/) | NLP for keyword analysis and ATS compatibility checks. |
| [python-docx](https://python-docx.readthedocs.io/en/latest/) | Word document editing for resume customization. |
| [PyPDF2](https://pypdf2.readthedocs.io/en/latest/) | Processes PDF files for extracting and analyzing resumes. |
| [scikit-learn](https://scikit-learn.org/) | Drives machine learning models for resume optimization. |
| [Plotly](https://plotly.com/) | Interactive charts for skills gap and keyword analysis. |
| [NLTK](https://www.nltk.org/) | Tokenization, stemming, and text preprocessing. |
| [openpyxl](https://openpyxl.readthedocs.io/en/stable/) | Reading, writing, and exporting Excel files. |

</details>

## 💡 How It Works

1. **Upload or Start from Scratch**
   Import your resume in PDF/Word or create one from scratch with the AI-powered builder.

2. **Analyze Your Resume**
   - ATS Compatibility: ensure your resume meets recruiter expectations.
   - Keyword Insights: find and fill gaps in your content.
   - Skills Gap Analysis: discover key skills missing for your target role.

3. **Build a Stunning Resume**
   Select from multiple templates and customize sections like skills, achievements, or hobbies.

4. **Download & Apply**
   Export your resume in PDF format, ready for submission.

## 🛠️ Setup Instructions

Follow the steps below to set up and run **Smart AI Resume Analyzer** on your local machine.

1. **Clone the repository:**

   ```bash
   git clone https://github.com/<your-github-username>/Smart-AI-Resume-Analyzer.git
   cd Smart-AI-Resume-Analyzer
   ```

2. **Create a virtual environment (optional but recommended):**

   ```bash
   python -m venv venv
   ```

   Activate it:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Download the spaCy model:**

   ```bash
   python -m spacy download en_core_web_sm
   ```

5. **Configure environment variables (required for AI analysis):**

   Create a `.env` file inside the `utils/` directory:

   ```env
   GOOGLE_API_KEY=your_google_gemini_api_key
   ```

   Get a free Gemini API key at [Google AI Studio](https://aistudio.google.com/app/apikey).

   > 🔐 Do not commit your `.env` file to version control — it should be listed in `.gitignore`.

6. **Run the application:**

   ```bash
   streamlit run app.py
   ```

## 🔑 Admin Login Credentials (default/demo)

- **Username:** `admin@example.com`
- **Password:** `admin123`

The Admin Section becomes visible after login, below the Dashboard section. Change these credentials before deploying publicly.

## ☁️ Deploying to Streamlit Community Cloud

1. Push this repository to your own GitHub account.
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Create a new app, pointing to your repo/branch and `app.py` as the entry point.
4. Add `GOOGLE_API_KEY` as a secret in the app's settings.
5. Deploy.

## 📄 License

This project is licensed under the [MIT License](LICENSE). See the `LICENSE` file for details.

This project began as an open-source fork and has been substantially customized and extended.
