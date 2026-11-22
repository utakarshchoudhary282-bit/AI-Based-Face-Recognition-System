# AI-Based Face Recognition System: Employee Verification Portal

A full-stack web app for a company's security desk. A security user signs in, uploads or captures a photo, and the
system finds the face, recognises the employee and shows their details and allowed zones. A **RAG policy assistant**
then answers questions such as "Can this person enter the R&D lab?" using only the company's policy documents, with
numbered sources.

| Part | Built with |
|---|---|
| Backend API | Python, FastAPI, SQLAlchemy + SQLite, JWT login, bcrypt passwords |
| Face detection | OpenCV YuNet (finds the face and 5 landmarks: eyes, nose, mouth corners) |
| Face recognition | Pretrained **SFace** CNN (128-number face embeddings) + logistic regression classifier |
| My CNN baseline | 4-layer Keras CNN trained from scratch (`scripts/train_cnn.py`) for comparison |
| RAG assistant | LangChain, FAISS vector search, Groq Llama 3.1 8B (works without a key in a simpler mode) |
| Frontend | React 19 + Vite |

## Results on my dataset (76 photos, 9 people)

| Model | Accuracy | F1 (macro) | How it was tested |
|---|---|---|---|
| SFace embeddings + logistic regression (used in the app) | **97.4%** | **0.97** | 5-fold cross-validation |
| 4-layer CNN trained from scratch (my original model) | 62.5% | 0.49 | 80/20 split (60 train / 16 test) |

A stranger's photo gets similarity 0.28, below the 0.45 threshold, so it is reported as **UNKNOWN** instead of being
forced onto an employee. Photos of the same person average about 0.73; photos of different people about 0.36.

**Why the CNN from scratch loses:** with ~8 photos per person a CNN cannot learn what makes faces different. SFace was
already trained on millions of faces, so I only train a small classifier on top of its embeddings (transfer learning).

## How it works

```
Photo ─▶ YuNet: find face + landmarks ─▶ align to 112×112 ─▶ SFace: 128-d embedding
      ─▶ logistic regression: most likely employee
      ─▶ cosine similarity to that employee's enrolled faces ≥ 0.45 ?  MATCH : UNKNOWN
      ─▶ employee record from SQLite + allowed zones from access level and status

Question ─▶ FAISS search over policy chunks (top 4) + verified employee's record
         ─▶ LLM answers only from those sources and cites [S1], [S2]...
```

### Pages
- **Verify**: upload or webcam photo → MATCH / UNKNOWN / NO_FACE, employee card, allowed zones, ask-about-this-person chat.
- **Assistant**: policy questions, optionally about a chosen employee.
- **Policies**: the 5 policy documents the assistant searches.
- **Employees** (admin): add, edit, delete employees; upload face photos per person.
- **Enrol & Train** (admin): upload a zip with one folder per person, train, see accuracy / precision / recall / F1 and the confusion matrix.
- **Logs** (admin): every verification with user, time, result and similarity.

Two roles: **admin** (everything) and **security** (Verify, Assistant, Policies).

## Run it on Windows
1. Install Python 3.12 from python.org (tick "Add python.exe to PATH").
2. Double-click `run_windows.bat`. The first run installs packages and downloads the SFace model (about 5 minutes).
3. The browser opens http://localhost:8000. Sign in with `admin` / `Admin@123`.
4. Enrol & Train → upload a zip like `project 1/udit/*.jpg`, `project 1/rinku/*.jpg` … → Train model.

### Or from a terminal
```bash
cd backend
python -m venv .venv && .venv\Scripts\activate        # Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env                                  # Linux/Mac: cp
python -m scripts.manage import-folder "D:\project 1"   # one folder per person
python -m scripts.manage details scripts/employees.sample.json
python -m scripts.manage train
uvicorn app.main:app --port 8000
```

Optional: put a free Groq key in `backend/.env` (`GROQ_API_KEY=...`) for LLM answers. Without it the assistant returns
the most relevant policy lines with their sources.

### Run the CNN comparison
```bash
pip install -r requirements-cnn.txt     # adds TensorFlow
python -m scripts.train_cnn             # trains the 4-layer CNN on the same faces and prints accuracy + F1
```

### Tests
```bash
pip install -r requirements-dev.txt
pytest          # 8 tests: login, roles, face detection, UNKNOWN rule, enrol → train → verify, RAG
```

## Project layout
```
backend/
  app/
    main.py            FastAPI app, serves the React build
    config.py db.py security.py schemas.py
    face/              detector.py (YuNet) · embedder.py (SFace) · dataset.py · sface_model.py (classifier) · service.py
    rag/               documents.py · embeddings.py · index.py (FAISS) · llm.py · assistant.py
    routers/           auth · employees · recognition · knowledge · admin
  knowledge_base/policies/   5 policy documents (markdown)
  scripts/           manage.py (import / train from the command line) · train_cnn.py (CNN baseline)
  tests/
frontend/src/        React pages and components (built into frontend/dist)
```

## Privacy
Face photos, the trained model and the database live in `backend/data/`, which is git-ignored and never uploaded.
Day-to-day verification photos are not stored, only a log line. Passwords are bcrypt-hashed.

## Limitations
- Small dataset (76 photos); results would need re-checking with more people and harder photos.
- A printed photo could fool it: there is no liveness (anti-spoofing) check.
- The 0.45 threshold was picked from my data (same person ≈ 0.73, different ≈ 0.36) and should be re-tuned for a new group.
