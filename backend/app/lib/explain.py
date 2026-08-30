"""LLM explanation. Grok first, then Ollama, then a local template.

The model never computes ranks or assignments. It only restates numbers.
"""

from __future__ import annotations

import json
import os
from typing import Any

import httpx

from app.lib.fallback_explain import fallback_explanation

SYSTEM = """You are an operations brief writer for a coastal town cleanup desk.
You receive already-computed dispatch numbers. You MUST NOT calculate, re-rank, estimate, or invent
any values. Restate only the numbers provided. Use plain language a non-expert can follow.
Never claim machine-learning bloom prediction. Cleanup uses an exact hour budget picker.
Scouting is a separate list for beaches nobody has checked. Weather is live Open-Meteo, not a trained forecast.
Dollar figures are the town's own estimates.
Return JSON only, matching the schema exactly.
"""

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
XAI_URL = os.getenv("XAI_URL", "https://api.x.ai/v1")
XAI_MODEL = os.getenv("XAI_MODEL", "grok-4.6")


def _xai_key() -> str:
    return (os.getenv("XAI_API_KEY") or "").strip()


def _payload_for_model(state: dict[str, Any]) -> dict[str, Any]:
    def zone_brief(z: dict[str, Any]) -> dict[str, Any]:
        return {
            "name": z["name"],
            "severity": z["meanSeverity"],
            "economicExposure": z["immediateExposure"],
            "cleanupValue": z["cleanupValue"],
            "uncertaintyBonus": z["uncertaintyBonus"],
            "exploitScore": z["exploitScore"],
            "scoutPriority": z["scoutPriority"],
            "crewHours": z["requiredCrewHours"],
            "impactPerCrewHour": z["impactPerCrewHour"],
            "forecastRisk": z["forecastRisk"],
            "inspectionCount": z["inspectionCount"],
            "operatingCost": z["operatingCost"],
        }

    community = (state.get("community") or {}).get("name") or "this town"
    return {
        "community": community,
        "weather": state.get("weather"),
        "metrics": state.get("metrics"),
        "settings": state.get("settings"),
        "selectedCleanup": [zone_brief(z) for z in state.get("cleanupNow") or []],
        "unfunded": [zone_brief(z) for z in (state.get("unfunded") or [])[:3]],
        "scoutRecommendations": [zone_brief(z) for z in state.get("scoutNext") or []],
        "containment": [zone_brief(z) for z in state.get("containment") or []],
        "changes": state.get("changes") or [],
        "method": state.get("selection"),
    }


def _parse_model_json(text: str) -> dict[str, Any] | None:
    raw = text.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        raw = raw.replace("json", "", 1).strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start < 0 or end < 0:
            return None
        try:
            data = json.loads(raw[start : end + 1])
        except json.JSONDecodeError:
            return None
    required = ("summary", "cleanupRationale", "scoutingRationale", "tradeoffs", "caveat")
    if not all(k in data for k in required):
        return None
    if not isinstance(data["cleanupRationale"], list):
        return None
    return data


def _extract_responses_text(data: dict[str, Any]) -> str:
    if isinstance(data.get("output_text"), str) and data["output_text"].strip():
        return data["output_text"]
    chunks: list[str] = []
    for item in data.get("output") or []:
        for content in item.get("content") or []:
            if content.get("type") in ("output_text", "text") and content.get("text"):
                chunks.append(content["text"])
    return "\n".join(chunks)


async def grok_status() -> dict[str, Any]:
    key = _xai_key()
    return {
        "ok": bool(key),
        "provider": "xAI Grok",
        "model": XAI_MODEL,
        "configured": bool(key),
    }


async def ollama_status() -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=2.5) as client:
            response = await client.get(f"{OLLAMA_URL}/api/tags")
            response.raise_for_status()
            models = [m.get("name") for m in response.json().get("models", [])]
            return {"ok": True, "models": models, "url": OLLAMA_URL}
    except Exception:
        return {"ok": False, "models": [], "url": OLLAMA_URL}


async def _pick_ollama_model() -> str | None:
    configured = os.getenv("OLLAMA_MODEL")
    status = await ollama_status()
    names = status.get("models") or []
    if configured and any(configured in n or n.startswith(configured) for n in names):
        return configured
    for candidate in (configured, "llama3.2", "llama3.1", "llama3", "mistral", "qwen2.5", "gemma2", "phi3"):
        if not candidate:
            continue
        for name in names:
            if name == candidate or name.startswith(f"{candidate}:"):
                return name
    return names[0] if names else configured


def _instruction(state: dict[str, Any]) -> str:
    payload = _payload_for_model(state)
    return (
        "Explain this already-computed dispatch. Do not compute new numbers.\n"
        + json.dumps(payload, indent=2)
        + "\n\nJSON schema:\n"
        + json.dumps(
            {
                "summary": "string, maximum 70 words, plain English",
                "cleanupRationale": ["string", "string"],
                "scoutingRationale": ["string", "string"],
                "tradeoffs": ["string"],
                "caveat": "string",
            },
            indent=2,
        )
    )


async def explain_with_model(state: dict[str, Any]) -> dict[str, Any]:
    instruction = _instruction(state)
    parsed = await _grok(instruction)
    if parsed:
        parsed["source"] = "grok"
        parsed["model"] = parsed.get("model") or XAI_MODEL
        return parsed
    parsed = await _ollama(instruction)
    if parsed:
        parsed["source"] = "ollama"
        return parsed
    result = fallback_explanation(state)
    result["source"] = "local-fallback"
    result["reason"] = "no-llm"
    return result


async def answer_question(state: dict[str, Any], question: str) -> dict[str, Any]:
    payload = _payload_for_model(state)
    instruction = (
        "Answer the operator question using ONLY the computed dispatch JSON. "
        "Do not invent numbers. Plain English. Return JSON "
        '{"answer":"string max 80 words","caveat":"string"}.\n\n'
        f"Question: {question.strip()[:280]}\n\n"
        f"Dispatch:\n{json.dumps(payload)}"
    )
    parsed = await _grok_freeform(instruction)
    if parsed:
        return {"answer": parsed.get("answer", ""), "caveat": parsed.get("caveat", ""), "source": "grok"}
    parsed = await _ollama(instruction)
    if parsed and parsed.get("summary"):
        return {"answer": parsed["summary"], "caveat": parsed.get("caveat", ""), "source": "ollama"}
    cleanup = ", ".join(z["name"] for z in state.get("cleanupNow") or []) or "no beaches"
    scouts = ", ".join(z["name"] for z in state.get("scoutNext") or []) or "none"
    return {
        "answer": f"Today’s crew list is {cleanup}. Look list: {scouts}. The AI is offline, so this is the computed plan only.",
        "caveat": "Local fallback. No model was available.",
        "source": "local-fallback",
    }


async def _grok(instruction: str) -> dict[str, Any] | None:
    text = await _grok_text(instruction)
    if not text:
        return None
    parsed = _parse_model_json(text)
    if parsed:
        parsed["model"] = XAI_MODEL
    return parsed


async def _grok_freeform(instruction: str) -> dict[str, Any] | None:
    text = await _grok_text(instruction)
    if not text:
        return None
    parsed = _parse_model_json(text)
    if parsed and "answer" in parsed:
        return parsed
    try:
        data = json.loads(text[text.find("{") : text.rfind("}") + 1])
        if "answer" in data:
            return data
    except Exception:
        return {"answer": text[:500], "caveat": "Grok reply was not strict JSON."}
    return None


async def _grok_text(instruction: str) -> str | None:
    key = _xai_key()
    if not key:
        return None
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{XAI_URL}/responses",
                headers=headers,
                json={
                    "model": XAI_MODEL,
                    "store": False,
                    "input": [
                        {"role": "system", "content": SYSTEM},
                        {"role": "user", "content": instruction},
                    ],
                },
            )
            if response.status_code < 400:
                text = _extract_responses_text(response.json())
                if text.strip():
                    return text
            response = await client.post(
                f"{XAI_URL}/chat/completions",
                headers=headers,
                json={
                    "model": XAI_MODEL,
                    "temperature": 0.2,
                    "messages": [
                        {"role": "system", "content": SYSTEM},
                        {"role": "user", "content": instruction},
                    ],
                },
            )
            response.raise_for_status()
            data = response.json()
            return ((data.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
    except Exception:
        return None


async def _ollama(instruction: str) -> dict[str, Any] | None:
    model = await _pick_ollama_model()
    if not model:
        return None
    body = {
        "model": model,
        "stream": False,
        "format": "json",
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": instruction},
        ],
        "options": {"temperature": 0.2},
    }
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(f"{OLLAMA_URL}/api/chat", json=body)
            response.raise_for_status()
            data = response.json()
            text = (data.get("message") or {}).get("content") or ""
            parsed = _parse_model_json(text)
            if parsed:
                parsed["model"] = model
            return parsed
    except Exception:
        return None
