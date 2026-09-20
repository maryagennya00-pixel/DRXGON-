# ============================================
# arya/main.py
# Complete ARYA system — all agents wired together
# ============================================

import warnings
warnings.filterwarnings("ignore")

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from router import build_arya_graph, arya_chat
import router
from agents.researcher import researcher_node
from agents.writer     import writer_node
from agents.planner    import planner_node
from agents.analyst    import analyst_node
from agents.news       import news_node
from agents.coder      import coder_node
from memory import (load_profile, update_profile,
                     remember, recall, get_memory_summary, forget, start_session)
from config import AGENTS, ARYA_NAME, ARYA_VERSION
from voice  import voice_input_to_text, clean_for_tts, text_to_speech
from vision import vision_node_helper


def process_input(text: str = None, audio_path: str = None, image_path: str = None,
                   audio_url: str = None, image_url: str = None) -> dict:
    """Process any combination of input modalities."""
    result = {
        "text": text or "", "has_audio": False, "has_image": False,
        "audio_language": None, "image_analysis": None, "combined_input": ""
    }

    audio_source = audio_path or audio_url
    if audio_source:
        print("  [Input] Processing audio...")
        transcript = voice_input_to_text(audio_path=audio_path, audio_url=audio_url)
        if transcript.get("text"):
            result["text"]           = transcript["text"]
            result["has_audio"]      = True
            result["audio_language"] = transcript.get("language")
            print(f"  [Input] Transcribed: '{transcript['text'][:60]}'")
        else:
            print(f"  [Input] Audio failed: {transcript.get('error')}")

    image_source = image_path or image_url
    if image_source:
        print("  [Input] Processing image...")
        question = result["text"] or "Describe this image in detail."
        result["has_image"]      = True
        result["image_analysis"] = vision_node_helper(image_source, question)

    combined = result["text"]
    if result["image_analysis"]:
        combined += f"\n\n{result['image_analysis']}"
    result["combined_input"] = combined.strip()

    return result


def arya_multimodal(text: str = None, audio_path: str = None, image_path: str = None,
                     audio_url: str = None, image_url: str = None,
                     session_id: str = "arya_main", speak: bool = False) -> dict:
    """Full multimodal ARYA interface."""
    inputs = process_input(text=text, audio_path=audio_path, image_path=image_path,
                            audio_url=audio_url, image_url=image_url)

    if not inputs["combined_input"]:
        return {"final_response": "I didn't receive any input. Please try again.",
                "selected_agent": "none"}

    result = chat_with_meta(inputs["combined_input"], session_id)
    result["input_metadata"] = inputs

    if speak and result.get("final_response"):
        tts_text = clean_for_tts(result["final_response"])
        result["tts"] = text_to_speech(tts_text[:600])

    return result

def initialize_arya() -> object:
    """Initialize ARYA with all six specialist agents"""
    print(f"\n{'='*55}")
    print(f"  Initializing {ARYA_NAME} v{ARYA_VERSION}")
    print(f"{'='*55}")

    agent_nodes = {
        "researcher": researcher_node,
        "writer":     writer_node,
        "planner":    planner_node,
        "analyst":    analyst_node,
        "news":       news_node,
        "coder":      coder_node,
    }

    graph = build_arya_graph(agent_nodes)
    router._arya_graph = graph
    start_session()

    print(f"  Agents loaded: {list(agent_nodes.keys())}")
    print(f"  Memory: ready")
    print(f"\n  {ARYA_NAME} is ready.\n")

    return graph


def chat(message: str, session_id: str = "arya_main") -> str:
    """Simple chat interface — returns just the response text"""
    result = arya_chat(message, session_id, router._arya_graph)
    return result.get("final_response", "I couldn't process that.")


def chat_with_meta(message: str, session_id: str = "arya_main") -> dict:
    """Chat with full metadata — agent used, routing reason, etc."""
    result = arya_chat(message, session_id, router._arya_graph)
    agent  = result.get("selected_agent", "unknown")
    return {
        "response":       result.get("final_response", ""),
        "final_response": result.get("final_response", ""),
        "agent":          agent,
        "agent_name":     AGENTS.get(agent, {}).get("name", "Unknown"),
        "routing_reason": result.get("routing_reason", ""),
        "error":          result.get("error"),
    }


if __name__ == "__main__":
    initialize_arya()

    profile = load_profile()
    if not profile.get("name"):
        print("Welcome to ARYA! Let's set up your profile.\n")
        name = input("What's your name? ").strip()
        if name:
            update_profile("name", name)
            remember(f"User's name is {name}", "fact")

        profession = input("What do you do? (optional, press Enter to skip) ").strip()
        if profession:
            update_profile("profession", profession)
            remember(f"User works as: {profession}", "fact")

        print(f"\nGreat! ARYA is ready, {name or 'there'}.\n")
    else:
        name = profile.get("name", "")
        sessions = profile.get("total_sessions", 1)
        print(f"Welcome back, {name}! (Session #{sessions})")
        print(f"Memory: {get_memory_summary()[:100]}...\n")

    print("Type 'quit' to exit | 'memory' to see what I remember | 'forget X' to remove a memory\n")
    print("─" * 55)

    while True:
        try:
            user_input = input(f"\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in ["quit", "exit", "bye"]:
            print(f"\nARYA: Goodbye! See you next time.")
            break

        if user_input.lower() == "memory":
            print(f"\nARYA: {get_memory_summary()}")
            continue

        if user_input.lower().startswith("forget "):
            topic = user_input[7:].strip()
            print(f"\nARYA: {forget(topic)}")
            continue

        if user_input.lower().startswith("remember "):
            fact = user_input[9:].strip()
            remember(fact, "user_stated")
            print(f"\nARYA: Got it — I'll remember that.")
            continue

        if user_input.lower().startswith("image "):
            image_path = user_input[6:].strip()
            question = input("What about this image? ").strip()
            result = arya_multimodal(text=question, image_path=image_path)
            print(f"\n[Vision]\nARYA: {result['final_response']}")
            continue

        if user_input.lower().startswith("voice "):
            audio_path = user_input[6:].strip()
            result = arya_multimodal(audio_path=audio_path)
            print(f"\n[Voice -> {result.get('agent_name','')}]")
            print(f"Transcribed: '{result['input_metadata']['text']}'")
            print(f"ARYA: {result['final_response']}")
            continue

        result = chat_with_meta(user_input)
        print(f"\n[{result['agent_name']}]")
        print(f"\nARYA: {result['response']}")

        if result.get("error"):
            print(f"\nError: {result['error']}")