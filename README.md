# AI-Powered Warranty Claims Decision System

## 🚀 Overview
This project is an end-to-end **agentic AI system** that automates warranty claim evaluation using:
- Retrieval-Augmented Generation (RAG)
- Rule-based fraud detection
- Graph-based workflow orchestration (LangGraph)

The system processes claims and outputs:
- APPROVE
- REJECT
- REVIEW (human-in-the-loop)

---

## 🧠 Key Features
- Agentic workflow using state machine
- RAG pipeline with FAISS + reranking
- Fraud detection with risk scoring
- Coverage validation using policy data
- Human review fallback for uncertain cases
- Evaluation pipeline with golden dataset
- Audit logs for explainability

---

## ⚙️ Tech Stack
- Python, FastAPI
- LangChain, LangGraph
- FAISS (vector search)
- Sentence Transformers (embeddings)
- Pydantic (validation)
- SQLite (storage)

---

## 📊 System Flow
1. Claim submitted via API  
2. Input validation  
3. Policy retrieval (RAG)  
4. Fraud score calculation  
5. Coverage check  
6. Decision routing (APPROVE / REJECT / REVIEW)  
7. Audit logging + response  

---

## 🧪 Evaluation
- Uses a golden test dataset
- Measures accuracy and system performance
- Helps detect regressions

---

## ▶️ How to Run

```bash
pip install -r requirements.txt
uvicorn src.api:app --reload

Open:
http://127.0.0.1:8000/docs


📁 Project Structure
src/
├── api.py
├── graph.py
├── nodes.py
├── fraud_detection.py
├── rag/
├── evaluation/
├── database.py


🌟 Future Improvements

ML-based fraud detection
Hybrid retrieval (keyword + vector)
Monitoring and observability
Scalable deployment (Postgres, Redis)

📌 Author
Mohd Fardeen Khan