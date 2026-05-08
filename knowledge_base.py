"""
knowledge_base.py
Edit this file to customize the FAQ knowledge base for your use case.
"""

KNOWLEDGE_BASE = [
    # Billing
    {"id": 1, "topic": "billing",
     "question": "How do I cancel my subscription?",
     "answer": "You can cancel at any time from Settings > Billing > Cancel Plan. Access continues until the end of the billing period."},
    {"id": 2, "topic": "billing",
     "question": "Can I get a refund?",
     "answer": "We offer a 14-day money-back guarantee for new customers. Contact billing@support.com with your order ID."},
    {"id": 3, "topic": "billing",
     "question": "How do I update my payment method?",
     "answer": "Go to Settings > Billing > Payment Methods and click 'Add New Card'."},
    {"id": 4, "topic": "billing",
     "question": "Why was I charged twice?",
     "answer": "Duplicate charges are caused by failed transaction retries. Contact billing@support.com and we'll refund the extra charge within 2 business days."},

    # Technical
    {"id": 5, "topic": "technical",
     "question": "The app is not loading. What do I do?",
     "answer": "Clear your browser cache and cookies, then reload. Try a different browser or disable extensions if the issue persists."},
    {"id": 6, "topic": "technical",
     "question": "I forgot my password. How do I reset it?",
     "answer": "Click 'Forgot Password' on the login page and enter your email. A reset link arrives within 2 minutes. Check spam if you don't see it."},
    {"id": 7, "topic": "technical",
     "question": "How do I integrate your API?",
     "answer": "Full API docs are at docs.ourproduct.com/api. You need your API key from Settings > Developer."},
    {"id": 8, "topic": "technical",
     "question": "My data is not syncing.",
     "answer": "Log out and log back in. If syncing fails for more than 30 minutes, contact tech@support.com."},

    # Account
    {"id": 9, "topic": "account",
     "question": "How do I change my email address?",
     "answer": "Go to Settings > Profile > Email. A verification email will confirm the change."},
    {"id": 10, "topic": "account",
     "question": "Can I have multiple users on one account?",
     "answer": "Yes. Pro and Enterprise plans support team seats. Go to Settings > Team to invite members."},
    {"id": 11, "topic": "account",
     "question": "How do I delete my account?",
     "answer": "Account deletion is permanent. Go to Settings > Privacy > Delete Account. Data is erased within 30 days."},

    # General
    {"id": 12, "topic": "general",
     "question": "What are your support hours?",
     "answer": "Our team is available Monday–Friday, 9 AM–6 PM IST. Use live chat for urgent issues."},
    {"id": 13, "topic": "general",
     "question": "Do you offer a free trial?",
     "answer": "Yes, a 14-day free trial with no credit card required. Sign up at ourproduct.com/trial."},
    {"id": 14, "topic": "general",
     "question": "What plans do you offer?",
     "answer": "Free (limited), Pro (₹999/mo), and Enterprise (custom). See ourproduct.com/pricing for full details."},
]
