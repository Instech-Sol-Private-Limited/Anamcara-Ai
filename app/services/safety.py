def check_safety(text):
    t = text.lower()

    if any(x in t for x in ["kill myself", "suicide", "harm myself", "end my life"]):
        return {
            "flag": True,
            "type": "self_harm",
            "response": "I’m really sorry you’re feeling this way. You’re not alone. "
                        "I can't help with self-harm, but I can stay with you and offer grounding support. "
                        "Talking to someone you trust or a local hotline might help.",
            "suggestedModules": [
                {"moduleKey": "hope", "reason": "crisis-safe guidance"}
            ]
        }

    return {"flag": False}