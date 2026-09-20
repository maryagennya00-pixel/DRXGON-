# ============================================
# arya/vision.py
# ARYA Vision Layer — image understanding
# ============================================

import warnings
warnings.filterwarnings("ignore")

from groq import Groq
from config import GROQ_API_KEY, VISION_MODEL
import base64, requests, re
from pathlib import Path

groq_client = Groq(api_key=GROQ_API_KEY)


def encode_image_file(image_path: str) -> tuple:
    """Encode local image to base64. Returns (base64_data, mime_type)"""
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    ext_map = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png",  ".gif": "image/gif",
        ".webp": "image/webp"
    }
    mime_type = ext_map.get(path.suffix.lower(), "image/jpeg")

    with open(image_path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")

    return data, mime_type


def encode_image_url(image_url: str) -> tuple:
    """Download image from URL and encode to base64"""
    headers  = {"User-Agent": "Mozilla/5.0 (compatible; ARYA/1.0)"}
    response = requests.get(image_url, headers=headers, timeout=15)
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "image/jpeg").split(";")[0]
    data = base64.standard_b64encode(response.content).decode("utf-8")

    return data, content_type


def clean_vision_response(text: str) -> str:
    """Remove <think> tags from reasoning models"""
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()


def analyze_image(image_source: str,
                   question: str = "Describe this image in detail.",
                   context: str = "") -> dict:
    """
    Analyze an image using Groq vision model.
    image_source: file path or URL
    """
    print(f"  [Vision] Analyzing image...")

    try:
        if image_source.startswith("http://") or image_source.startswith("https://"):
            image_data, mime_type = encode_image_url(image_source)
        else:
            image_data, mime_type = encode_image_file(image_source)

        full_question = f"{context}\n\nQuestion: {question}" if context else question

        response = groq_client.chat.completions.create(
            model=VISION_MODEL,
            max_tokens=800,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_data}"}},
                    {"type": "text", "text": full_question}
                ]
            }]
        )

        raw_text   = response.choices[0].message.content
        clean_text = clean_vision_response(raw_text)

        print(f"  [Vision] Analysis complete: {len(clean_text)} chars")

        return {"description": clean_text, "model_used": VISION_MODEL, "error": None}

    except Exception as e:
        return {"description": f"Vision analysis failed: {e}", "model_used": VISION_MODEL, "error": str(e)}


# ── SPECIALIZED VISION FUNCTIONS ──────────────

def describe_image(image_source: str) -> str:
    result = analyze_image(
        image_source,
        "Describe this image in detail. List all objects, text, colors, and notable features."
    )
    return result["description"]


def read_text_in_image(image_source: str) -> str:
    result = analyze_image(
        image_source,
        "Extract ALL text visible in this image. Return it exactly as it appears. "
        "If there is no text, say 'No text found'."
    )
    return result["description"]


def analyze_document_image(image_source: str) -> str:
    result = analyze_image(
        image_source,
        """Analyze this document or screenshot:
1. What type of document is this?
2. What is the main content or purpose?
3. List all key information, numbers, or data points visible
4. Are there any action items or important deadlines visible?"""
    )
    return result["description"]


def check_for_issues(image_source: str) -> str:
    result = analyze_image(
        image_source,
        """Inspect this image as a quality analyst:
1. Visible problems, errors, or defects
2. Severity: Minor / Moderate / Severe
3. Recommended action
4. Confidence: Low / Medium / High"""
    )
    return result["description"]


def vision_node_helper(image_source: str, user_question: str, memory_context: str = "") -> str:
    """Vision helper for ARYA agents — called when a user shares an image."""
    q_lower = user_question.lower()

    if any(w in q_lower for w in ["text", "read", "ocr", "extract text"]):
        description = read_text_in_image(image_source)
    elif any(w in q_lower for w in ["document", "screenshot", "screen"]):
        description = analyze_document_image(image_source)
    elif any(w in q_lower for w in ["problem", "error", "issue", "damage", "wrong"]):
        description = check_for_issues(image_source)
    else:
        description = describe_image(image_source)

    return f"[Image Analysis]\n{description}"