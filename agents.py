"""
agents.py — SupportAI Pro
Smart conversation flow — always asks for problem before escalating.
"""

import json
import faiss
import numpy as np
from groq import Groq
from sentence_transformers import SentenceTransformer
from datetime import datetime
from knowledge_base import KNOWLEDGE_BASE

MODEL = "llama-3.3-70b-versatile"

_embedder = None
_index    = None
_kb       = None

def _build_index():
    global _embedder, _index, _kb
    if _index is not None:
        return
    _embedder  = SentenceTransformer("all-MiniLM-L6-v2")
    _kb        = KNOWLEDGE_BASE
    questions  = [item["question"] for item in _kb]
    embeddings = _embedder.encode(questions, convert_to_numpy=True)
    dim        = embeddings.shape[1]
    _index     = faiss.IndexFlatIP(dim)
    faiss.normalize_L2(embeddings)
    _index.add(embeddings)

def retrieve_faq(query, top_k=2, threshold=0.45):
    _build_index()
    q_vec = _embedder.encode([query], convert_to_numpy=True)
    faiss.normalize_L2(q_vec)
    scores, indices = _index.search(q_vec, top_k)
    return [{**_kb[idx], "score": float(score)}
            for score, idx in zip(scores[0], indices[0]) if score >= threshold]


# ── System prompts ────────────────────────────────────────────────

INTENT_SYSTEM = """
You are an intent classifier for a customer support system.
Classify the user message into EXACTLY ONE of:
  FAQ       - a simple question answerable from a knowledge base
  TICKET    - a technical or account issue needing investigation
  ESCALATE  - user is angry, frustrated, or wants a manager/senior agent
  CHITCHAT  - greeting, thanks, or off-topic small talk
  NEED_INFO - user mentioned a problem but has not given enough details

Rules:
- "speak to manager", "need a manager", "escalate", "frustrated", "unacceptable" → ESCALATE
- "problem", "issue", "not working", "help" with NO specific details → NEED_INFO
- Specific issue with details → TICKET
- Clear question → FAQ
- Greeting or thanks → CHITCHAT

Respond with ONLY the category word. No explanation.
"""

CLASSIFY_SYSTEM = """
You are a customer support classifier.
Analyze the user message and respond with ONLY a JSON object:
{
  "department": "BILLING" | "TECHNICAL" | "ACCOUNT" | "GENERAL",
  "priority": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
  "urgency": "low" | "medium" | "high" | "critical",
  "issue_type": "short phrase describing the issue",
  "summary": "one sentence summary",
  "suggested_action": "what support team should do first",
  "estimated_resolution": "e.g. immediately, 1-2 hours, 1 business day"
}

Priority rules:
- CRITICAL: system down, data loss, security breach, payment fraud
- HIGH: cannot access account, billing error, app completely broken
- MEDIUM: feature not working, billing question, account change
- LOW: general inquiry, FAQ question, greeting, chitchat

Department rules:
- BILLING: payments, charges, refunds, subscriptions, invoices
- TECHNICAL: bugs, crashes, API, integration, performance
- ACCOUNT: login, password, profile, team, deletion
- GENERAL: general questions, greetings, feedback, FAQ

Respond ONLY with valid JSON. No extra text.
"""

CLARIFY_SYSTEM = """
You are a helpful customer support assistant.
The user mentioned a problem but has not given enough details.
Ask ONE clear friendly question to understand what exactly is the issue.
Keep it short and warm. One question only.
"""

ASK_BEFORE_ESCALATE_SYSTEM = """
You are a helpful empathetic customer support assistant.
The customer wants to speak to a manager or escalate.
Before escalating, you need to understand their issue so the right team can help.
Ask them ONE warm empathetic question to find out what problem they are experiencing.
Acknowledge their frustration first, then ask.
Keep it short. One question only. Do NOT escalate yet.
"""

FAQ_REPLY_SYSTEM = """
You are a helpful customer support assistant.
Use ONLY the provided FAQ context to answer.
After answering, ask if there is anything else you can help with.
Be concise and friendly. Under 100 words.
"""

TICKET_REPLY_SYSTEM = """
You are a helpful customer support agent.
A support ticket has been created. Your response must:
1. Acknowledge the specific problem described
2. Confirm ticket ID and which department is handling it
3. Give priority level and realistic resolution timeline
4. Ask if there is anything else to note for the team
Be empathetic and professional. Under 120 words.
"""

ESCALATION_SYSTEM = """
You are an empathetic senior customer support specialist handling an escalation.
You now know the customer's specific problem. Your response must:
1. Sincerely apologize for their experience with the SPECIFIC issue
2. Tell them a senior agent from the [DEPARTMENT] team will contact them urgently
3. Give the escalation reference number
4. Give a specific timeline based on priority:
   - CRITICAL/HIGH: within 1 hour
   - MEDIUM: within 2 hours
   - LOW: within 4 hours
5. Ask for their preferred contact method (phone or email)
Be warm, urgent, and human. Under 130 words.
Never say "GENERAL team" — use the specific department name.
"""

CHITCHAT_SYSTEM = """
You are a friendly customer support assistant.
Respond naturally to greetings or small talk.
Mention you can help with billing, technical issues, account management, or general questions.
Keep it short and warm.
"""


# ── LLM helpers ───────────────────────────────────────────────────

def llm_call(client, system, user, temperature=0.3):
    r = client.chat.completions.create(
        model=MODEL,
        messages=[{"role":"system","content":system},
                  {"role":"user","content":user}],
        temperature=temperature, max_tokens=600)
    return r.choices[0].message.content.strip()

def llm_chat(client, system, history, temperature=0.5):
    r = client.chat.completions.create(
        model=MODEL,
        messages=[{"role":"system","content":system}]+history,
        temperature=temperature, max_tokens=600)
    return r.choices[0].message.content.strip()


# ── Classification — runs for EVERY query ─────────────────────────

def classify_issue(client, message, history, intent):
    context = "\n".join([f"{m['role'].upper()}: {m['content']}"
                         for m in history[-4:]])
    context += f"\nUSER: {message}\nINTENT: {intent}"
    raw = llm_call(client, CLASSIFY_SYSTEM, context, temperature=0.1)
    try:
        return json.loads(raw.replace("```json","").replace("```","").strip())
    except Exception:
        if intent == "CHITCHAT":
            return {"department":"GENERAL","priority":"LOW","urgency":"low",
                    "issue_type":"Greeting","summary":message[:60],
                    "suggested_action":"No action needed","estimated_resolution":"N/A"}
        return {"department":"GENERAL","priority":"MEDIUM","urgency":"medium",
                "issue_type":"General issue","summary":message[:60],
                "suggested_action":"Review manually","estimated_resolution":"1 business day"}


# ── Problem keyword check ─────────────────────────────────────────

PROBLEM_KEYWORDS = [
    "charged","payment","bill","refund","cancel","subscription","invoice",
    "crash","error","broken","not working","failed","bug","slow","down",
    "login","password","account","data","lost","deleted","locked",
    "api","integration","sync","loading","blank","freeze",
    "waiting","days","hours","ignored","no response","nobody",
    "wrong","incorrect","missing","duplicate","twice","three times",
    "cannot","can't","unable","won't","doesn't","not loading",
    "hacked","security","breach","unauthorized","fraud","stolen"
]

def has_problem_context(message, history):
    """Check if we know what problem the customer has."""
    full_text = message.lower()
    for m in history[-6:]:
        full_text += " " + m["content"].lower()
    return any(kw in full_text for kw in PROBLEM_KEYWORDS)


# ── Individual agents ─────────────────────────────────────────────

def intent_agent(client, message):
    result = llm_call(client, INTENT_SYSTEM, message, temperature=0.1).strip().upper()
    return result if result in {"FAQ","TICKET","ESCALATE","CHITCHAT","NEED_INFO"} else "FAQ"

def faq_agent(client, message, history):
    retrieved = retrieve_faq(message)
    context   = "\n\n".join([f"Q: {r['question']}\nA: {r['answer']}"
                              for r in retrieved]) if retrieved else "No relevant FAQ found."
    reply = llm_chat(client, FAQ_REPLY_SYSTEM,
                     history + [{"role":"user",
                                 "content":f"FAQ Context:\n{context}\n\nQuestion: {message}"}])
    info  = classify_issue(client, message, history, "FAQ")
    return {"reply":reply,"sources":[r["question"] for r in retrieved],**info}

def ticket_agent(client, message, history):
    info      = classify_issue(client, message, history, "TICKET")
    ticket_id = f"TKT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    prompt    = (f"Ticket ID: {ticket_id}\n"
                 f"Department: {info['department']}\n"
                 f"Priority: {info['priority']}\n"
                 f"Urgency: {info['urgency']}\n"
                 f"Issue: {info['issue_type']}\n"
                 f"Resolution time: {info['estimated_resolution']}\n"
                 f"Customer message: {message}")
    reply = llm_call(client, TICKET_REPLY_SYSTEM, prompt, temperature=0.5)
    return {"reply":reply,"ticket_id":ticket_id,**info}

def escalation_agent(client, message, history):
    info   = classify_issue(client, message, history, "ESCALATE")
    ref_id = f"ESC-{datetime.now().strftime('%H%M%S')}"
    prompt = (f"Reference ID: {ref_id}\n"
              f"Department: {info['department']}\n"
              f"Priority: {info['priority']}\n"
              f"Urgency: {info['urgency']}\n"
              f"Issue: {info['issue_type']}\n"
              f"Customer message: {message}")
    system = ESCALATION_SYSTEM.replace("[DEPARTMENT]", info["department"])
    reply  = llm_call(client, system, prompt, temperature=0.6)
    return {"reply":reply,"ref_id":ref_id,**info}

def ask_before_escalate(client, message, history):
    """Ask for problem details before escalating."""
    reply = llm_chat(client, ASK_BEFORE_ESCALATE_SYSTEM,
                     history + [{"role":"user","content":message}],
                     temperature=0.5)
    info  = classify_issue(client, message, history, "NEED_INFO")
    return {"reply":reply,**info}

def clarify_agent(client, message, history):
    reply = llm_chat(client, CLARIFY_SYSTEM,
                     history + [{"role":"user","content":message}],
                     temperature=0.5)
    info  = classify_issue(client, message, history, "NEED_INFO")
    return {"reply":reply,**info}

def chitchat_agent(client, message, history):
    reply = llm_chat(client, CHITCHAT_SYSTEM,
                     history + [{"role":"user","content":message}],
                     temperature=0.7)
    info  = classify_issue(client, message, history, "CHITCHAT")
    return {"reply":reply,**info}


# ── Orchestrator ──────────────────────────────────────────────────

class CustomerSupportOrchestrator:
    """
    Smart orchestrator:
    - Classifies EVERY query with full metadata
    - Always asks for problem before escalating
    - Never escalates without knowing the issue
    """

    def __init__(self, api_key):
        self.client          = Groq(api_key=api_key)
        self.history         = []
        self.escalated       = False
        self.waiting_details = False
        self.pending_intent  = None
        _build_index()

    def respond(self, user_message):
        # Already escalated
        if self.escalated:
            return {
                "reply":      ("Your case is with our senior support team. "
                               "They will contact you shortly. "
                               "Is there anything else I can note for them?"),
                "intent":     "ESCALATE",
                "department": "-", "priority":"-",
                "urgency":    "-", "issue_type":"-",
                "summary":    user_message[:60],
            }

        # We asked for details last turn — now process with full context
        if self.waiting_details:
            self.waiting_details = False
            pending = self.pending_intent
            self.pending_intent  = None

            if pending == "ESCALATE":
                result = {"intent":"ESCALATE"}
                result.update(escalation_agent(self.client, user_message, self.history))
                self.escalated = True
            else:
                result = {"intent":"TICKET"}
                result.update(ticket_agent(self.client, user_message, self.history))

            self._update_memory(user_message, result["reply"])
            return result

        # Detect intent
        intent = intent_agent(self.client, user_message)
        result = {"intent": intent}

        if intent == "CHITCHAT":
            result.update(chitchat_agent(self.client, user_message, self.history))

        elif intent == "FAQ":
            faq_result = faq_agent(self.client, user_message, self.history)
            result.update(faq_result)
            # If no FAQ match found, ask for more details
            if not faq_result.get("sources"):
                result.update(clarify_agent(self.client, user_message, self.history))
                result["intent"]     = "NEED_INFO"
                self.waiting_details = True
                self.pending_intent  = "TICKET"

        elif intent == "NEED_INFO":
            result.update(clarify_agent(self.client, user_message, self.history))
            self.waiting_details = True
            self.pending_intent  = "TICKET"

        elif intent == "TICKET":
            result.update(ticket_agent(self.client, user_message, self.history))

        elif intent == "ESCALATE":
            # ALWAYS check if we know the actual problem
            if has_problem_context(user_message, self.history):
                # We know the problem — escalate now
                result.update(escalation_agent(self.client, user_message, self.history))
                self.escalated = True
            else:
                # We don't know the problem — ask first
                result.update(ask_before_escalate(self.client, user_message, self.history))
                result["intent"]     = "NEED_INFO"
                self.waiting_details = True
                self.pending_intent  = "ESCALATE"

        self._update_memory(user_message, result["reply"])
        return result

    def _update_memory(self, user_message, reply):
        self.history.append({"role":"user",      "content":user_message})
        self.history.append({"role":"assistant",  "content":reply})
        if len(self.history) > 20:
            self.history = self.history[-20:]
