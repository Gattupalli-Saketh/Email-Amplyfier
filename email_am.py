import sys
from transformers import pipeline

CATEGORIES = ["Procurement",
               "Logistics",
               "Quality Control",
               "Payment",
               "General Inquiry",
               "Spam/Other"]

MODEL_NAME = "MoritzLaurer/deberta-v3-large-zeroshot-v2.0"

def classify_email(email_text: str,min_confidence: float = 0.45):

    """_summary_ : Classify the email into a categorgy using zer0- shot classification

    Args:
        email_text (_string_): _Based on thr input type the mail is classified_
    """
    classifier = pipeline("zero-shot-classification",model = MODEL_NAME)
    result = classifier(email_text,candidate_labels = CATEGORIES)
    top_category = result['labels'][0]
    confidence = result['scores'][0]
    if confidence < min_confidence:
        top_category = "Spam/Other"
        confidence = 1.0 - confidence
    return top_category,confidence

def generate_response(email_text,category):
    """_summary_ : Generate an AI response basde on the category by using GPT-2 

    Args:
        email_text (_String_): _The etxt of the email_
        category (_string_): _The category of the email_
    """
    generator = pipeline("text-generation", model="gpt2")
    prompt = f"Email category: {category}. Draft a professional response to this supply chain email: {email_text[:200]}..."  # Truncate for prompt length
    response = generator(prompt, max_length=150, num_return_sequences=1)[0]['generated_text']
    response = response.replace(prompt, "").strip()
    return response

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python classify.py 'Your email text here'")
        sys.exit(1)
    
    email_text = sys.argv[1]
    
    # Classify
    category, confidence = classify_email(email_text)
    print(f"Classified Category: {category} (Confidence: {confidence:.2f})")
    
    # Generate response
    ai_response = generate_response(email_text, category)
    print("\nAI-Generated Draft Response:")
    print(ai_response)
