from transformers import pipeline
import spacy 
from typing import list,dict

classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli",device = -1)
nlp_en= spacy.load("en_core_web_sm")
nlp_de = spacy.load("de_core_news_sm")

def preprocess_text(text:str) -> str:
    """
    cleans and detect the language of the text 
    """
    if any(ord(c) > 127 for c in text):
        doc = nlp_en(text)
    else:
        doc = nlp_de(text)
    return ' '.join(token.lemma.lower() for token in doc if not token.is_stop)

def classify_email(subject:str,body:str = "") -> Dict[str,str]:
    """_summary_

    Args:
        subject (str): _description_
        body (str, optional): _description_. Defaults to "".

    Returns:
        Dict[str,str]: _description_

        classify single email into category and intent 
    """
    text = f"{subject} {body}".strip()
    text = preprocess_text(text)
    category_labels = ["Procurement", "Vendors/Suppliers", "Shipping/Logistics", 
                       "Invoicing/Billing", "Inventory", "Customs/Compliance"]
    intent_labels = ["Request Quote/Order", "Confirmation/Delivery Update", 
                     "Payment/Invoice Issue", "Complaint/Delay", "General Inquiry"]
    cat_result = classifier(text, category_labels)
    intent_result = classifier(text,intent_labels)

    return {
        "category": cat_result['labels'][0],
        "category_score": cat_result['scores'][0],
        "intent": intent_result['labels'][0],
        "intent_score": intent_result['scores'][0]
    }

def classify_emails(emails:List[Dict]) -> List[Dict]:
    """_summary_ : Process list of fetchde emails

    Args:
        emails (List[Dict]): _description_

    Returns:
        List[Dict]: _description_
    """
    results = []
    for email in emails:
        classification = classify_email(email.get("subject",""), email.get("body",""))
        results.append(**email,**classification)
    return results