# 🤖 SupportAI Pro — LLM-Powered Customer Support Automation

> An intelligent autonomous customer support system built with LLaMA 3.3 70B, FAISS, and Streamlit.

---

## 🌐 Live Demo

👉[Open Live App](https://x6wzrezmdqqyzpon8ycxwi.streamlit.app)

---

## 📌 Project Overview

SupportAI Pro is an AI-powered customer support automation platform that handles customer queries autonomously using a multi-agent architecture. The system intelligently detects intent, answers FAQs from a knowledge base, classifies and routes support tickets, and escalates frustrated customers to human agents — all in real time.

---

## ✨ Features

### 💬 AI Chatbot
- **Intent Detection** — Classifies every message as FAQ, Ticket, Escalation, or Chitchat
- **FAQ Answering** — Semantic search over knowledge base using RAG + FAISS
- **Smart Clarification** — Always asks for problem details before routing or escalating
- **Ticket Classification** — Assigns priority (LOW/MEDIUM/HIGH/CRITICAL) and department
- **Escalation Handling** — Detects frustration, collects problem details, routes to correct senior agent
- **Multi-turn Memory** — Maintains full conversation context across turns

### 📊 Analytics Dashboard
- Real-time metrics from actual chat sessions
- Intent distribution, ticket priority, department routing charts
- Live query log with department, priority, urgency, resolution time
- Export to Excel and CSV

---

## 🏗️ System Architecture

```
User Message
     ↓
Intent Detector (LLaMA 3.3 70B)
     ↓
┌────────────────────────────────────┐
│  FAQ?      → RAG + FAISS search    │
│  TICKET?   → Classify + route      │
│  ESCALATE? → Ask problem → route   │
│  CHITCHAT? → Friendly reply        │
│  VAGUE?    → Ask for details first │
└────────────────────────────────────┘
     ↓
Full Classification (dept + priority + urgency)
     ↓
Response + Memory Update
     ↓
Real-time Dashboard Capture
```

---

## 🧠 Tech Stack

| Technology | Purpose |
|---|---|
| LLaMA 3.3 70B (Groq) | Primary LLM for all agent reasoning |
| sentence-transformers | FAQ question embedding (all-MiniLM-L6-v2) |
| FAISS | Vector similarity search for FAQ retrieval |
| Streamlit | Web application framework |
| Plotly | Interactive analytics charts |
| Pandas + OpenPyXL | Data processing and Excel export |
| Streamlit Cloud | Production deployment |

---

## 📁 Project Structure

```
customer-support-bot/
├── app.py              ← Main Streamlit app (chatbot + dashboard)
├── agents.py           ← All LLM agent logic and orchestrator
├── knowledge_base.py   ← FAQ data (14 FAQs, easily extensible)
├── requirements.txt    ← Python dependencies
└── README.md           ← This file
```

---

## 🚀 Getting Started

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/customer-support-bot.git
cd customer-support-bot
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set your Groq API key
Get a free key at [console.groq.com](https://console.groq.com)

Create `.streamlit/secrets.toml`:
```toml
GROQ_API_KEY = "gsk_your_key_here"
```

### 4. Run locally
```bash
streamlit run app.py
```

---

## ☁️ Deploy to Streamlit Cloud (Free)

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo, set main file to `app.py`
4. Under **Secrets**, add: `GROQ_API_KEY = "gsk_your_key_here"`
5. Click **Deploy!**

---

## 💡 How It Works

### Smart Escalation Flow
```
User: I want to speak to a manager

Bot:  I understand your frustration. Could you
      tell me what issue you have been
      experiencing so the right senior agent
      can help you?

User: I was charged 3 times for the same order!

Bot:  I sincerely apologize for this billing
      error. Escalating to our BILLING team
      senior agent immediately.
      Ref: ESC-123456 — within 1 hour.
      Would you prefer phone or email?
```

### Every Query Gets Full Classification
| Field | Example |
|---|---|
| Department | BILLING / TECHNICAL / ACCOUNT / GENERAL |
| Priority | LOW / MEDIUM / HIGH / CRITICAL |
| Urgency | low / medium / high / critical |
| Issue type | "Payment charged multiple times" |
| Resolution time | "Within 1 hour" |

---

## 📊 Results

- **88.9%** intent classification accuracy
- **57%** queries auto-resolved without human intervention
- **4 agent types** — FAQ, Ticket, Escalation, Chitchat
- **14 FAQs** across billing, technical, account, general categories

---

## 🔮 Future Enhancements

- WhatsApp / email notifications via Twilio
- SQLite database for persistent storage
- Multilingual support (Tamil, Hindi)
- Real-time sentiment analysis
- Zendesk / Freshdesk API integration
- Voice interface with Groq Whisper

---

## 👨‍💻 Built With

- [Groq](https://groq.com) — Ultra-fast LLM inference
- [Streamlit](https://streamlit.io) — Web app framework
- [FAISS](https://github.com/facebookresearch/faiss) — Vector search
- [sentence-transformers](https://sbert.net) — Text embeddings

---

*Built as part of LLM-Powered Autonomous Business Workflow Automation project*
