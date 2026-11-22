# Interview guide: Employee Verification Portal

## 30-second pitch
"I built a face-recognition employee verification portal. A security guard logs in, uploads a photo, and the system
detects the face with OpenCV YuNet, turns it into a 128-number embedding with a pretrained SFace CNN, and a logistic
regression picks the employee. If the face isn't similar enough to anyone enrolled, it says UNKNOWN instead of guessing.
Then a RAG assistant answers questions like 'can this person enter the R&D lab?' from the company policies, with
sources. My first version was a CNN from scratch at 62% accuracy; switching to transfer learning took it to 97%."

## Skills it shows
- **Deep learning / computer vision:** CNNs, transfer learning, face detection, alignment, embeddings, cosine similarity.
- **Machine learning:** logistic regression, cross-validation, precision / recall / F1, confusion matrix, open-set threshold.
- **GenAI / NLP:** RAG, chunking, TF-IDF embeddings, FAISS vector search, prompt design, citations, LangChain, Groq LLM.
- **Backend:** FastAPI, REST APIs, SQLAlchemy + SQLite, JWT auth, bcrypt, role-based access, background training thread.
- **Frontend:** React, Vite, file upload, webcam capture.
- **Engineering:** pytest, project structure, privacy (no photos in git).

## Demo (3 minutes)
1. Log in as admin → **Verify** → upload my photo → MATCH, similarity ~1.0, my details and allowed zones.
2. Upload a stranger (any face not enrolled) → **UNKNOWN**, similarity ~0.28. "It doesn't force a wrong name."
3. Upload a photo of Topple → MATCH but **Suspended**: no zones, warning shown.
4. In the chat under the result ask "Can this employee enter the R&D lab?" → answer with [S1] sources.
5. **Enrol & Train** → show 97.4% accuracy, F1 0.97 and the confusion matrix.

## The face pipeline, step by step
1. **Detect (YuNet):** a small CNN detector in OpenCV. Returns the face box and 5 landmarks. Photos with no face are skipped.
2. **Align:** rotate and scale so the eyes are level and in fixed positions, crop 112×112. Same pose in, better embeddings out.
3. **Embed (SFace):** a CNN pretrained on millions of faces maps the face to 128 numbers. Same person → vectors close together.
4. **Classify:** logistic regression on the embeddings gives the most likely employee (top 3 shown).
5. **Open-set check:** cosine similarity to that employee's enrolled faces. ≥ 0.45 → MATCH, else UNKNOWN.
   I picked 0.45 from my data: same-person pairs average ~0.73, different people ~0.36.

## The CNN story (likely question: "why not your own CNN?")
- My original model: 4 conv blocks (32/64/128/256 filters, 4×4 kernels, max-pooling), dense 128 → dropout 0.3 → dense 64 → softmax.
  Augmentation (flip, rotation, zoom), early stopping.
- On aligned faces it got **62.5% accuracy, F1 0.49** (60 train / 16 test). On the original unaligned crops it was ~31%.
- Reason: ~8 photos per person is far too little to learn faces from scratch; the CNN overfits.
- Fix: **transfer learning**. SFace already learned face features; I only train a light classifier → **97.4%, F1 0.97**.
- I kept the CNN as `scripts/train_cnn.py` so the comparison is reproducible.

## Evaluation
- 5-fold stratified cross-validation: every photo is predicted by a model that never saw it.
- Accuracy 97.4%, precision 0.97, recall 0.98, F1 0.97 (macro). 2 mistakes out of 76 (Rinku→Bubu, Udit→Ritika).
- Macro F1 because classes are small and unequal (6 to 12 photos).

## RAG, step by step
1. **Documents:** 5 markdown policies I wrote (access control, verification procedure, leave, biometric privacy, visitors).
2. **Chunking:** split by markdown headings, then ~700 characters with 100 overlap. Each chunk keeps "[policy > section]".
3. **Embeddings + index:** TF-IDF vectors (1–2 word n-grams), stored in FAISS.
4. **Retrieve:** top 4 chunks by similarity. If an employee was verified, their record is added as source S1.
5. **Generate:** Groq Llama 3.1 8B, temperature 0.1, told to answer only from the sources and cite [S1], [S2]. If the
   answer isn't there it must say so.
6. **No API key:** falls back to returning the best matching policy lines, so the app still works offline.

**Why TF-IDF, not neural embeddings?** Policies use exact words ("L3", "R&D lab", "sick leave"); TF-IDF matches those
well, it is fast and needs no download. With many more documents I'd switch to sentence-transformer embeddings.

## Backend and security
- FastAPI routers: auth, employees, recognition, knowledge, admin.
- Login returns a JWT (8 hours). Every API checks the token; admin-only routes check the role (security user → 403).
- Passwords hashed with bcrypt. Face data and the database are git-ignored.
- Training runs in a background thread; the page polls `/api/train/status`.
- Every verification is logged (user, time, predicted person, similarity, result).

## Likely questions
- **What if two people look alike?** Classifier probabilities are close; the top 3 are shown and the guard follows the policy (ID card check).
- **Spoofing with a printed photo?** Not handled; I'd add a liveness model (blink / depth). I state this as a limitation.
- **Adding a new employee?** Upload 5+ photos and click Train; it retrains in seconds because only the classifier is trained.
- **Why logistic regression, not SVM / k-NN?** Embeddings are already well separated, so a linear model is enough and gives probabilities. k-NN would also work.
- **Why cosine similarity?** Embeddings are normalised; cosine measures the angle, which is what SFace was trained for.
- **Hallucination in RAG?** Low temperature, "answer only from sources", citations, and an explicit "not in the documents" answer.
- **Scaling to 10,000 employees?** Store embeddings in a vector index (FAISS) and match by nearest neighbour; move SQLite to PostgreSQL.

## Key numbers
76 photos · 9 people · 112×112 aligned faces · 128-d embeddings · threshold 0.45 · SFace 97.4% / F1 0.97 ·
CNN from scratch 62.5% / F1 0.49 · stranger similarity 0.28 · 5 policies · top-4 retrieval · 8 tests.

## Resume lines
- Built a full-stack face-recognition employee verification portal (FastAPI, React, SQLite, JWT) using YuNet detection and
  SFace embeddings with a logistic-regression classifier, reaching **97.4% accuracy (F1 0.97, 5-fold CV)** vs 62.5% for a CNN trained from scratch.
- Added an open-set similarity threshold that rejects unknown faces, and a RAG policy assistant (LangChain, FAISS, Llama 3.1)
  that answers access and policy questions with cited sources.
