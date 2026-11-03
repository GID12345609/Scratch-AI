import os
import logging
import requests

from flask import Flask, request, jsonify

app = Flask(__name__)

BASE_URL = "https://penguingpt.gpgpg4445.workers.dev/v1"
CHAT_URL = BASE_URL + "/chat/completions"
MODELS_URL = BASE_URL + "/models"

MODEL = os.getenv("AI_MODEL", "gpt-6")
API_KEY = os.getenv("PENGUINGPT_API_KEY", "")

SYSTEM_PROMPT = (
    "You are ScratchGrok AI, powered by PenguinGPT. "
    "Answer accurately, clearly and naturally. "
    "Support Vietnamese and English."
)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("ScratchGrok")

session = requests.Session()


def headers():
    result = {
        "Content-Type": "application/json"
    }

    if API_KEY:
        result["Authorization"] = "Bearer " + API_KEY

    return result


@app.after_request
def cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.route("/")
def home():
    return jsonify({
        "name": "ScratchGrok AI",
        "status": "online",
        "provider": "PenguinGPT",
        "model": MODEL,
        "base_url": BASE_URL,
        "endpoint": "/translate?text=Hello"
    })


@app.route("/health")
def health():
    return jsonify({
        "ok": True,
        "provider": "PenguinGPT",
        "model": MODEL
    })


@app.route("/models")
def models():
    try:
        r = session.get(
            MODELS_URL,
            headers=headers(),
            timeout=30
        )

        try:
            data = r.json()
        except ValueError:
            data = {"raw": r.text[:3000]}

        return jsonify({
            "http_status": r.status_code,
            "provider": "PenguinGPT",
            "selected_model": MODEL,
            "response": data
        }), r.status_code

    except requests.RequestException as e:
        return jsonify({
            "error": str(e),
            "provider": "PenguinGPT"
        }), 502


@app.route("/translate", methods=["GET", "OPTIONS"])
def translate():

    if request.method == "OPTIONS":
        return "", 204

    prompt = request.args.get("text", "").strip()

    if not prompt:
        return jsonify({"result": "Please enter a prompt."})

    if len(prompt) > 12000:
        return jsonify({"result": "Prompt too long."}), 413

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.7,
        "max_tokens": 2048,
        "stream": False
    }

    try:
        log.info("PenguinGPT request: model=%s", MODEL)

        r = session.post(
            CHAT_URL,
            json=payload,
            headers=headers(),
            timeout=120
        )

        try:
            data = r.json()
        except ValueError:
            data = {"raw": r.text[:3000]}

        if not r.ok:
            log.error(
                "PenguinGPT HTTP %s: %s",
                r.status_code,
                data
            )

            return jsonify({
                "result": "PenguinGPT HTTP " + str(r.status_code),
                "details": data,
                "model": MODEL
            }), 502

        result = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )

        if isinstance(result, list):
            result = "\n".join(
                str(item.get("text", ""))
                for item in result
                if isinstance(item, dict)
            )

        if not result:
            return jsonify({
                "result": "PenguinGPT returned an empty response.",
                "details": data
            }), 502

        log.info("Response received: %s characters", len(result))

        return jsonify({
            "result": str(result)
        })

    except requests.Timeout:
        return jsonify({
            "result": "PenguinGPT request timed out."
        }), 504

    except requests.RequestException as e:
        log.exception("PenguinGPT connection error")

        return jsonify({
            "result": "Connection error: " + str(e)
        }), 502


if __name__ == "__main__":
    print("=" * 50)
    print("       SCRATCHGROK AI")
    print("       PROVIDER: PENGUINGPT")
    print("       MODEL:", MODEL)
    print("       PORT: 443")
    print("=" * 50)

    app.run(
        host="127.0.0.1",
        port=443,
        ssl_context=("cert.pem", "key.pem"),
        threaded=True
    )
