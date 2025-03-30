from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse
from context_gatherer import gather_context
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def generate_script(user_idea):
    context = gather_context(user_idea)

    prompt = f"""
You are a niche content strategist for advanced creators on platforms like Instagram and X (Twitter).

The creator wants to make content about: "{user_idea}"

Here's real-world context from Reddit, Brave Search, and Wikipedia:

{context}

Now, create two platform-specific scripts — but keep the following in mind:

🎯 Focus on the *most technically interesting* or *controversial* angle.
💥 Include insights, contradictions, or lesser-known facts. Avoid surface-level summaries.
⚙️ Use precise, domain-specific language where appropriate (especially for tech/science topics).
⛔ Do NOT add generic statements like “this is making waves” or “netizens are divided.”

Generate:

1. A **1-minute Instagram Reel script** — attention-grabbing, opinionated, and tight. No fluff. Write as a single content block with a bold start and a clear conclusion.

2. A **short Twitter (X) thread (max 3 posts)** — sharp, technical, and thought-provoking. Don’t repeat Reel content. Use it to offer a different angle or counterpoint.

Write for creators who are building a niche by showing original thinking, not chasing trends.
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
        print("📝 Final reply (start):", reply_text[:300])
        return reply_text

    except Exception as e:
        print("❌ Error from Groq:", str(e), flush=True)
        return "⚠️ Couldn't generate content. Please try again."


@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    incoming_msg = request.form.get("Body")
    print(f"📩 Received: {incoming_msg}", flush=True)

    reply = generate_script(incoming_msg)

    if not reply or len(reply.strip()) == 0:
        reply = "⚠️ I couldn’t generate a response. Try again in a few seconds."

    # Sanitize markdown and special characters
    reply = reply.replace("**", "").replace("*", "")
    reply = reply.replace("```", "").replace("__", "")
    reply = reply.encode("ascii", "ignore").decode()

    # Extract sections
    sections = reply.split("### ")
    insta, x_post = "", ""
    for section in sections:
        if "Instagram" in section:
            insta = section.strip()
        elif "Twitter" in section or "X" in section:
            x_post = section.strip()

    # Trim if too long
    max_len = 1500
    if len(insta) > max_len:
        insta = insta[:max_len] + "\n\n[Trimmed for WhatsApp]"
    if len(x_post) > max_len:
        x_post = x_post[:max_len] + "\n\n[Trimmed for WhatsApp]"

    # Send messages
    resp = MessagingResponse()
    if insta:
        resp.message("📸 *Instagram Reel Script:*\n\n" + insta)
    if x_post:
        resp.message("🐦 *X / Twitter Thread:*\n\n" + x_post)

    print("📤 Reply sections sent.")
    return Response(str(resp), mimetype="application/xml")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
