from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse
from context_gatherer import gather_context
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Function to generate content using Groq API
def generate_script(user_idea):
    context = gather_context(user_idea)

    prompt = f"""
You're a social media strategist and script writer for content creators.

The creator wants to make content about: "{user_idea}"
Here’s real-world context (Reddit, Brave Search, Wikipedia):

{context}

Based on this, generate:

1. A 1-minute **Instagram Reel script** — punchy, fast-paced, visual focus
2. A compelling **X (Twitter) post or short thread** — punchy, informative or opinion-based
3. A 1-minute **YouTube Short script** — more structured, story or fact-style, with a strong hook and call to action

Make each one stand on its own. Don't repeat the same script for all 3. Make it WhatsApp-friendly and beginner creator friendly.
"""

    print("🔁 Sending to Groq with prompt:")
    print(prompt)
    print("📬 Waiting for response...")

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

        print("✅ Groq status code:", response.status_code)
        print("🧠 Raw response text:", response.text)

        data = response.json()

        reply_text = data["choices"][0]["message"]["content"]
        print("📝 Final reply:", reply_text)
        return reply_text

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
