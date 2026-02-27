import sys
from transformers import pipeline

CATEGORIES = ["Procurement",
               "Logistics",
               "Quality Control",
               "Payment",
               "General Inquiry",
               "Spam/Other"]

MODEL_NAME = "MoritzLaurer/deberta-v3-large-zeroshot-v2.0"

# Stores the conversation thread as a list of dicts: {"role": "...", "content": "..."}
email_thread = []

def classify_email(email_text: str, min_confidence: float = 0.45):
    """Classify the email into a category using zero-shot classification."""
    classifier = pipeline("zero-shot-classification", model=MODEL_NAME)
    result = classifier(email_text, candidate_labels=CATEGORIES)
    top_category = result['labels'][0]
    confidence = result['scores'][0]
    if confidence < min_confidence:
        top_category = "Spam/Other"
        confidence = 1.0 - confidence
    return top_category, confidence


def generate_human_response(email_text: str, category: str, sender_name: str = "there") -> str:
    """
    Generate a natural, human-like response to an email, while maintaining
    awareness of the full conversation thread.

    Args:
        email_text  : The latest incoming email text.
        category    : The classified category of the email.
        sender_name : Name/alias of the sender for personalised greeting.

    Returns:
        A string containing the drafted reply.
    """

    # ------------------------------------------------------------------ #
    # 1. Append the incoming email to the thread                          #
    # ------------------------------------------------------------------ #
    email_thread.append({"role": "user", "content": email_text})

    # ------------------------------------------------------------------ #
    # 2. Build a thread summary so the model understands prior context    #
    # ------------------------------------------------------------------ #
    thread_context = ""
    if len(email_thread) > 1:               # there is prior history
        prior_exchanges = email_thread[:-1] # everything except the latest email
        thread_context = "Previous exchanges in this thread:\n"
        for i, msg in enumerate(prior_exchanges, 1):
            role_label = "Received" if msg["role"] == "user" else "Sent"
            thread_context += f"  [{i}] {role_label}: {msg['content'][:300]}\n"
        thread_context += "\n"

    # ------------------------------------------------------------------ #
    # 3. Category-specific tone/instruction hints                         #
    # ------------------------------------------------------------------ #
    tone_hints = {
        "Procurement"    : "Acknowledge the procurement request, confirm details, and mention next steps.",
        "Logistics"      : "Address the shipment or delivery concern professionally and provide a status or ETA if possible.",
        "Quality Control": "Take the quality concern seriously, apologise if needed, and outline corrective actions.",
        "Payment"        : "Acknowledge the payment query, state the current status, and clarify any outstanding points.",
        "General Inquiry": "Answer the inquiry helpfully and invite any follow-up questions.",
        "Spam/Other"     : "Politely acknowledge the message without committing to anything specific.",
    }
    hint = tone_hints.get(category, "Reply professionally and helpfully.")

    # ------------------------------------------------------------------ #
    # 4. Compose the full prompt                                          #
    # ------------------------------------------------------------------ #
    prompt = (
        f"You are a professional supply-chain coordinator replying to business emails.\n"
        f"Write a short, natural, human-like reply — no bullet points, no stiff corporate "
        f"language, just clear and friendly business prose.\n\n"
        f"{thread_context}"
        f"Latest email received (category: {category}):\n{email_text}\n\n"
        f"Guidance: {hint}\n\n"
        f"Begin the reply with 'Hi {sender_name},' and end with a courteous sign-off.\n"
        f"Reply:"
    )

    # ------------------------------------------------------------------ #
    # 5. Generate with a better open-source model                         #
    #    Switch to 'tiiuae/falcon-7b-instruct' or 'mistralai/Mistral-7B-  #
    #    Instruct-v0.2' for much better quality if your hardware allows.  #
    # ------------------------------------------------------------------ #
    generator = pipeline(
        "text-generation",
        model="facebook/opt-1.3b",      # upgrade this for better quality
        max_new_tokens=200,
        do_sample=True,
        temperature=0.75,               # slight creativity without going off-track
        top_p=0.92,
        repetition_penalty=1.15,
    )

    raw = generator(prompt)[0]["generated_text"]

    # Strip the prompt prefix so only the reply text is returned
    response_text = raw[len(prompt):].strip()

    # ------------------------------------------------------------------ #
    # 6. Save our outgoing reply back into the thread                     #
    # ------------------------------------------------------------------ #
    email_thread.append({"role": "assistant", "content": response_text})

    return response_text


def generate_response(email_text, category):
    """Legacy wrapper — kept for backwards compatibility."""
    return generate_human_response(email_text, category)


# ------------------------------------------------------------------ #
# CLI entry-point                                                     #
# ------------------------------------------------------------------ #
if __name__ == "__main__":
    print("Supply-chain Email Assistant  (type 'quit' to exit)\n")

    while True:
        email_input = input("Paste incoming email (or 'quit'): ").strip()
        if email_input.lower() == "quit":
            break
        if not email_input:
            continue

        sender = input("Sender name/alias (press Enter to skip): ").strip() or "there"

        category, confidence = classify_email(email_input)
        print(f"\nClassified: {category}  (confidence: {confidence:.2f})")

        reply = generate_human_response(email_input, category, sender_name=sender)
        print("\n--- Draft Reply ---")
        print(reply)
        print("-------------------\n")
