import os
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import anthropic

app = Flask(__name__, static_folder="static")
CORS(app, origins="*")

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are a Tamil language tutor. The student has basic Tamil knowledge. Be concise and direct — get to the point immediately, no preamble like "Great question!".
Rules:
- Keep responses short (max 150 words unless a complex grammar topic)
- No markdown (no **, no ##, no ---)
- Use plain text with line breaks only
- Format examples as: Tamil → romanisation → meaning
- One or two examples max unless asked for more
- Never ask follow-up questions at the end
- Whenever you write a Tamil sentence or phrase, always follow it immediately with a word-by-word breakdown on separate lines in this format: word (romanisation) = meaning
- Do not skip the breakdown even for short phrases
- Always use simple informal romanisation (e.g. vanakkam, naan, kadai, poren) — never use diacritics or special characters like ā, ṭ, ṇ, ḻ, ē, ī, ū, ṟ, ḷ, ṉ
- If a document or file is provided, read it and extract relevant Tamil content or answer based on it directly
- If there is no Tamil text in uploaded images or documents and no instructions for what to do, do NOT translate or generate Tamil. Respond normally in plain English instead.
- Do not invent Tamil translations for non-Tamil content.
- Only provide Tamil + breakdown when the user explicitly asks for Tamil OR when Tamil text is present."""

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
        # Normalize message content (important for files)
        formatted_messages = []

        for msg in messages:
            content = msg["content"]

            # If already structured (images/docs), keep it
            if isinstance(content, list):
                formatted_messages.append({
                    "role": msg["role"],
                    "content": content
                })
            else:
                # Plain text fallback
                formatted_messages.append({
                    "role": msg["role"],
                    "content": [{"type": "text", "text": content}]
                })

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=formatted_messages
        )

        reply = response.content[0].text
        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/translate-image', methods=['POST'])
def translate_image():
    data = request.json
    image_data = data.get('image')
    media_type = data.get('mediaType')
    if not image_data or not media_type:
        return jsonify({'error': 'No image provided'}), 400
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system="You are a Tamil translator. When given an image containing Tamil text, extract all Tamil text you can see and provide: 1) The original Tamil text, 2) The romanisation (simple, no diacritics), 3) The English translation. Format clearly with labels.",
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data
                        }
                    },
                    {
                        "type": "text",
                        "text": "Please extract and translate all Tamil text in this image."
                    }
                ]
            }]
        )
        return jsonify({'reply': response.content[0].text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
