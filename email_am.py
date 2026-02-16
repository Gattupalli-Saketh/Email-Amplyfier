# email_amplifier.py
import os
import win32com.client
from dotenv import load_dotenv
import spacy
from spacy.matcher import PhraseMatcher

import json
from datetime import datetime
import logging

# Setup
load_dotenv()
logging.basicConfig(level=logging.INFO)
nlp = spacy.load("en_core_web_sm")


# === SUPPLY CHAIN NLP CLASSIFIER ===
class SupplyChainClassifier:
    def __init__(self):
        self.nlp = nlp
        self.matcher = PhraseMatcher(self.nlp.vocab)
        self.patterns = [
            "purchase order", "PO ", "PO#", "supplier", "vendor", "delivery date",
            "shipment", "tracking number", "ETA", "inventory", "stock", "backorder",
            "logistics", "freight", "invoice", "payment terms", "RFQ", "quote"
        ]
        phrases = [self.nlp.make_doc(text) for text in self.patterns]
        self.matcher.add("SUPPLY_CHAIN", phrases)

    def is_supply_chain(self, text: str) -> tuple[bool, list]:
        doc = self.nlp(text)
        matches = self.matcher(doc)
        return len(matches) > 0, [doc[start:end].text for match_id, start, end in matches]

    def extract_entities(self, text: str):
        doc = self.nlp(text)
        entities = {
            "PO": [ent.text for ent in doc.ents if ent.label_ == "PO" or "PO" in ent.text.upper()],
            "DATES": [ent.text for ent in doc.ents if ent.label_ == "DATE"],
            "MONEY": [ent.text for ent in doc.ents if ent.label_ == "MONEY"],
            "ORG": [ent.text for ent in doc.ents if ent.label_ == "ORG"]
        }
        return {k: list(set(v)) for k, v in entities.items() if v}


def scan_inbox(max_emails=50, unread_only=True):
    outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
    inbox = outlook.GetDefaultFolder(6)
    items = inbox.Items
    items.Sort("[ReceivedTime]", True)  # Latest first

    classifier = SupplyChainClassifier()
    supply_chain_emails = []

    count = 0
    for item in items:
        if count >= max_emails:
            break
        if not hasattr(item, "Subject"):
            continue
        if unread_only and not item.UnRead:
            continue

        body = item.Body or ""
        subject = item.Subject or ""
        full_text = f"{subject}\n{body}"

        is_sc, keywords = classifier.is_supply_chain(full_text)
        if is_sc:
            entities = classifier.extract_entities(full_text)
            email_data = {
                "item": item,
                "subject": subject,
                "sender": item.SenderEmailAddress,
                "received": item.ReceivedTime,
                "keywords": keywords,
                "entities": entities,
                "body": body[:2000]  # Truncate for AI
            }
            supply_chain_emails.append(email_data)
            logging.info(f"Supply Chain Email: {subject}")
        count += 1

    return supply_chain_emails

def generate_ai_reply(email_data, tone="professional", stakeholder="procurement"):
    prompt = f"""
You are an expert supply chain email assistant for {stakeholder}.

**Email Context:**
Subject: {email_data['subject']}
From: {email_data['sender']}
Keywords: {', '.join(email_data['keywords'])}
Entities: {json.dumps(email_data['entities'], indent=2)}

**Email Body (truncated):**
{email_data['body']}

**Task:**
Write a {tone}, concise, and actionable reply. 
- Acknowledge key points (PO, dates, issues)
- Propose next steps
- Ask clarifying questions if needed
- End with clear CTA

Return only the email body. No explanations.
"""
## Here we need to hange the Model and Inject the new API key 
    try:
        response = openai.ChatCompletion.create(
            model="anthropic/claude-3.5-sonnet",
            messages=[{"role": "user", "content": prompt}],
            headers={"HTTP-Referer": "http://localhost", "X-Title": "Outlook Amplifier"}
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[AI Error: {str(e)}]"
    
def create_draft_reply(email_item, ai_reply):
    reply = email_item.Reply()
    reply.Body = ai_reply + "\n\n" + reply.Body
    reply.Display()  # Opens draft
    return reply

def amplify_emails():
    emails = scan_inbox(max_emails=10, unread_only=True)
    if not emails:
        print("No supply chain emails found.")
        return

    for email in emails:
        ai_reply = generate_ai_reply(email, tone="professional")
        draft = create_draft_reply(email["item"], ai_reply)
        print(f"Draft created for: {email['subject']}")
        # Optional: auto-mark as read
        # email["item"].UnRead = False

if __name__ == "__main__":
    load_dotenv()
    amplify_emails()