
from google.genai import types


def isStructured(*args):
    """
    Check if any of the arguments is a list of dictionaries.
    This indicates structured input (multi-message format).
    """
    return any(
        isinstance(arg, list) and all(isinstance(i, dict) for i in arg)
        for arg in args
    )


def handleTypedFormat(role: str = "user", content: str = ""):
    """
    Format content for Google GenAI APIs.
    """
    role    = role.lower()
    allowed = {"system", "user", "model"}
    if role not in allowed:
        raise ValueError(
            f"Invalid role '{role}'. Must be one of {', '.join(allowed)}."
        )
    if role == "system":
        return types.Part.from_text(text=content)
    return types.Content(role=role, parts=[types.Part.from_text(text=content)])


def handleJsonFormat(role: str = "user", content: str = ""):
    """
    Format content for OpenAI APIs.
    """
    role    = role.lower()
    allowed = {"system", "developer", "user", "assistant"}
    if role not in allowed:
        raise ValueError(
            f"Invalid role '{role}'. Must be one of {', '.join(allowed)}."
        )
    return {'role': role, 'content': content}

def buildGoogleSafetySettings(harassment="BLOCK_NONE", hateSpeech="BLOCK_NONE", sexuallyExplicit="BLOCK_NONE", dangerousContent="BLOCK_NONE"):
    """
    Construct a list of Google GenAI SafetySetting objects.
    """
    harassment        = harassment.upper()
    hate_speech       = hateSpeech.upper()
    sexually_explicit = sexuallyExplicit.upper()
    dangerous_content = dangerousContent.upper()
    allowed_settings  = {"BLOCK_NONE", "BLOCK_LOW", "BLOCK_MEDIUM", "BLOCK_HIGH", "BLOCK_ALL"}
    for name, val in {
        "harassment": harassment, 
        "hate_speech": hate_speech, 
        "sexually_explicit": sexually_explicit, 
        "dangerous_content": dangerous_content
    }.items():
        if val not in allowed_settings:
            raise ValueError(f"Invalid {name} setting: {val}. Must be one of {', '.join(allowed_settings)}.")

    return [
        types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold=harassment),
        types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold=hate_speech),
        types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold=sexually_explicit),
        types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold=dangerous_content),
    ]
