# pr_agent/core/summarizer.py

from dotenv import load_dotenv
load_dotenv()   

import time
from tiktoken import encoding_for_model
from pydantic_ai import Agent
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from pydantic_ai.exceptions import ModelHTTPError
from pr_agent.settings import settings

#gemini_key = os.environ["GEMINI_API_KEY"]
# ─── Instantiate a single Gemini‐Flash agent ───────────────────────────────
# (it will read your API key and model name from settings)

agent = Agent(
    settings.GEMINI_MODEL,            # e.g. "gemini-1.5-flash-latest"
    provider=GoogleGLAProvider(api_key=settings.GEMINI_API_KEY),
    system_prompt=(
        "You are a summarization assistant. "
        "Given a block of text, extract its most important sentences "
        "and return a clear, concise summary."
        "Remove any formatting characters like the newline character \n or ** and others."
    ),
    output_type=str,
)

# def call_gemini(prompt: str, max_tokens: int) -> str:
#     """
#     Send `prompt` to Gemini-Flash and return the generated text.
#     """
#     resp = agent.run_sync(prompt, max_output_tokens=max_tokens)
#     return resp.output.strip()

def call_gemini(prompt: str, max_tokens: int) -> str:
    """
    Send `prompt` to Gemini-Flash and return the generated text,
    retrying up to 3 times on HTTP 503 errors.
    """
    max_retries = 3
    delay = 1
    for attempt in range(max_retries):
        try:
            resp = agent.run_sync(prompt, max_output_tokens=max_tokens)
            return resp.output.strip()
        except ModelHTTPError as e:
            # retry on transient “503 Service Unavailable”
            if getattr(e, "status_code", None) == 503 and attempt < max_retries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            raise


def extract_summary(text: str) -> str:
    """
    Summarize `text` using a 3-branch strategy:
      • < 800 words:    extract 5 sentences (then truncate if >300 words)
      • 800–2000 words: extract 8 sentences (then truncate if >250 words)
      • > 2000 words:   chunk into ~500-word pieces, extract 2 sentences each,
                        concat and truncate if >300 words
    Finally enforce an absolute token limit via one more Gemini call.
    """
    words = text.split()
    n = len(words)

    # ─── Branch 1: short docs (<800 words) ───────────────────────────────
    if n < 800:
        summary = call_gemini(
            f"Extract the 5 most important sentences from the following text:\n\n{text}",
            max_tokens=512
        )
        if len(summary.split()) > 300:
            summary = call_gemini(
                f"Compress the following text into a concise 200–250 word summary:\n\n{summary}",
                max_tokens=300
            )

    # ─── Branch 2: mid-length docs (800–2000 words) ────────────────────────
    elif n <= 2000:
        summary = call_gemini(
            f"Extract the 8 most important sentences from the following text:\n\n{text}",
            max_tokens=512
        )
        if len(summary.split()) > 250:
            summary = call_gemini(
                f"Rewrite the following into a concise 200–250 word summary:\n\n{summary}",
                max_tokens=300
            )

    # ─── Branch 3: long docs (>2000 words) ────────────────────────────────
    else:
        # break into ~500-word chunks
        # chunks = [" ".join(words[i : i + 500]) for i in range(0, n, 500)]
        # extracted = []
        # for chunk in chunks:
        #     extracted.append(
        #         call_gemini(
        #             f"Extract the 2 most important sentences from the following text:\n\n{chunk}",
        #             max_tokens=128
        #         )
        #     )
        # summary = " ".join(extracted)
        # if len(summary.split()) > 300:
        #     summary = call_gemini(
        #         f"Rewrite the following into a concise 200–250 word summary:\n\n{summary}",
        #         max_tokens=300
        #     )

        # increase chunk size to reduce calls
        chunks = [" ".join(words[i : i + 1000]) for i in range(0, n, 1000)]

        extracted = []
        for chunk in chunks:
            response = call_gemini(
                f"Extract the 3 most important sentences from the following text:\n\n{chunk}",
                max_tokens=150
            )
            extracted.append(response)
            time.sleep(4.5)
        
        summary = " ".join(extracted)
        if len(summary.split()) > 300:
            summary = call_gemini(
                f"Rewrite the following into a concise 200–250 word summary:\n\n{summary}",
                max_tokens=300
            )





    # ─── Final token-limit enforcement ──────────────────────────────────────
    enc    = encoding_for_model(settings.EMBED_TOKEN_MODEL)
    tokens = len(enc.encode(summary))
    if tokens > settings.TOKEN_LIMIT:
        summary = call_gemini(
            f"Reduce the following summary to under {settings.TOKEN_LIMIT} tokens. "
            "Keep it coherent and informative:\n\n" + summary,
            max_tokens=settings.TOKEN_LIMIT
        )

    return summary