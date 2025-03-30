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
You're a social media content scriptwriter for creators.

The creator wants to make content about: "{user_idea}"
Here's real-world context from Reddit, Brave Search, and Wikipedia:

{context}

Based on this, generate the following:

1. A **1-minute Instagram Reel script** with:
   - A short hook/opening
   - Clear and concise content script
   - A brief closing call-to-action
   - No second-by-second breakdown, just one block of text

2. A **short X (Twitter) thread** (max 3 tweets):
   - Clear, insightful, opinion-based or informational
   - Avoid fluff — be direct and helpful

3. A **1-minute YouTube Short script** with:
   - A quick attention-grabber
   - The core message/story
   - A soft ending with CTA or reflection
   - Again, no timestamps — just write like you're scripting for a creator

Be crisp. Emphasize the content of the topic. Avoid repeating the same idea across formats. Write as if it's ready to be filmed.
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

    # Clean up markdown and non-ASCII characters
    reply = reply.replace("**", "").replace("*", "")
    reply = reply.replace("```", "").replace("__", "")
    reply = reply.encode("ascii", "ignore").decode()

    # Split reply into separate sections
    sections = reply.split("### ")
    insta, x_post, yt = "", "", ""
    for section in sections:
        if "Instagram" in section:
            insta = section.strip()
        elif "Twitter" in section or "X" in section:
            x_post = section.strip()
        elif "YouTube" in section:
            yt = section.strip()

    resp = MessagingResponse()
    if insta:
        resp.message("📸 *Instagram Reel Script:*\n\n" + insta[:1500])
    if x_post:
        resp.message("🐦 *X / Twitter Thread:*\n\n" + x_post[:1500])
    if yt:
        resp.message("📺 *YouTube Short Script:*\n\n" + yt[:1500])

    print("📤 Reply sections sent.")
    return Response(str(resp), mimetype="application/xml")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
