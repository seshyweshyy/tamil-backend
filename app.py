import os
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import anthropic

app = Flask(__name__, static_folder="static")
CORS(app, origins="*")

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are an expert Tamil language tutor. The student has some basic Tamil knowledge (knows some letters and words) and wants to reach fluency. 

Your job:
- Answer ANY question about Tamil — grammar, script, pronunciation, vocabulary, phrases, culture, history
- Always show Tamil examples in this format: Tamil script → romanisation → English meaning
- Be encouraging, clear, and practical
- When explaining grammar, give real example sentences
- When asked to translate something, give the Tamil script + romanisation + a breakdown of each word
- Keep responses focused but thorough — don't be too brief if the topic needs depth
- You can also have casual Tamil practice conversations — respond in both Tamil and English so the student can follow along

The student is Australian, learning Tamil likely for cultural connection or travel to Tamil Nadu/Sri Lanka."""

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    messages = data.get("messages", [])

    if not messages:
        return jsonify({"error": "No messages provided"}), 400

    try:
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=messages
        )
        reply = response.content[0].text
        return jsonify({"reply": reply})

    except anthropic.AuthenticationError:
        return jsonify({"error": "Invalid API key. Check your ANTHROPIC_API_KEY environment variable."}), 401
    except anthropic.RateLimitError:
        return jsonify({"error": "Rate limit hit. Please wait a moment and try again."}), 429
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
