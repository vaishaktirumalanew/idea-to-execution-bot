from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse
from context_gatherer import gather_context
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Generate script using Groq + gathered context
def generate_script(user_idea):
    context = gather_context(user_idea)

    prompt = f"""
You are a content creation assistant for Instagram/TikTok creators.

The creator wants to make content about: "{user_idea}"
Here’s some background context from Reddit, Brave Search, and Wikipedia:

{context}

Based on this, generate:
1. A hook (1 line)
2. A 1-minute video script
3. Suggested format (e.g., reel, tweet thread, carousel)
4. Optional CTA or caption idea

Keep it WhatsApp-friendly and beginner-friendly.
"""

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.8
            }
        )

        data = response.json()
        return data["choices"][0]["message"]["content"]

    except Exception as e:
        print("❌ Error from Groq:", str(e), flush=True)
        return "⚠️ Couldn't generate content. Please try again."

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    incoming_msg = request.form.get("Body")
    print(f"📩 Received: {incoming_msg}", flush=True)

    reply = generate_script(incoming_msg)

    resp = MessagingResponse()
    resp.message(reply)
    return Response(str(resp), mimetype="application/xml")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

