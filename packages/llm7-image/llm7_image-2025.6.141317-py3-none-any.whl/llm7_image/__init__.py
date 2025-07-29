from __future__ import annotations

import base64
from typing import Literal
from urllib.parse import quote_plus

import requests


class GenerationError(RuntimeError):
    """Raised when the LLM7 image generation API returns an error."""


def generate_image(
    prompt: str,
    *,
    token: str,
    w: int = 1000,
    h: int = 1000,
    seed: int = 0,
    model: Literal[1, 2] = 1,
    timeout: float | tuple[float, float] = (5, 300),
) -> str:  # noqa: WPS231
    """
    Send a request to ``http://api.llm7.io/prompt`` and return the final image URL.

    Parameters
    ----------
    prompt:
        Text prompt (1–10 000 chars).
    token:
        LLM7 API token.
    w, h:
        Output size in pixels (100–1500, inclusive).
    seed:
        RNG seed (0–1_000_000_000).
    model:
        Diffusion model: ``1`` or ``2``.
    timeout:
        ``requests`` timeout (connect, read) in seconds.

    Returns
    -------
    str
        Absolute URL of the generated JPEG.

    Raises
    ------
    ValueError
        If any parameter is outside its allowed range.
    GenerationError
        If the API responds with an error.
    """
    if not prompt or len(prompt) > 10_000:
        raise ValueError("`prompt` must be 1–10 000 characters long.")
    if not (100 <= w <= 1500 and 100 <= h <= 1500):
        raise ValueError("`w` and `h` must be between 100 and 1500.")
    if seed < 0 or seed > 1_000_000_000:
        raise ValueError("`seed` must be between 0 and 1 000 000 000.")
    if model not in (1, 2):
        raise ValueError("`model` must be 1 or 2.")
    if not token:
        raise ValueError("`token` is required.")

    quoted_prompt = quote_plus(prompt, safe="")
    base_url = "http://api.llm7.io/prompt"
    params = {
        "w": w,
        "h": h,
        "seed": seed,
        "model": model,
        "token": quote_plus(token),
    }

    resp = requests.get(
        f"{base_url}/{quoted_prompt}",
        params=params,
        allow_redirects=False,
        timeout=timeout,
    )

    if resp.status_code in {301, 302, 307, 308}:  # redirect to CDN
        location = resp.headers.get("Location")
        if not location:
            raise GenerationError("Redirect without Location header.")
        return location

    # Some deployments may stream the image directly (200).
    if resp.ok and resp.headers.get("Content-Type", "").startswith("image/"):
        encoded = base64.b64encode(resp.content).decode()
        return f"data:{resp.headers['Content-Type']};base64,{encoded}"

    # Otherwise, surface the error message.
    try:
        detail = resp.json().get("detail", resp.text)
    except ValueError:  # not JSON
        detail = resp.text
    raise GenerationError(f"LLM7 API returned {resp.status_code}: {detail}")
