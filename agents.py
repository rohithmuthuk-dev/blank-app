"""NOVA specialist-agent orchestration using an OpenAI-compatible API."""
from __future__ import annotations
import os
import requests
from typing import Callable

DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openrouter/free"

class AIProviderError(RuntimeError):
    pass

class AIClient:
    def __init__(self, api_key=None, base_url=None, model=None):
        self.api_key = api_key or os.getenv("AI_API_KEY", "")
        self.base_url = (base_url or os.getenv("AI_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.model = model or os.getenv("AI_MODEL", DEFAULT_MODEL)

    def chat(self, system: str, user: str, temperature: float = 0.4) -> str:
        if not self.api_key:
            raise AIProviderError("Add OPENROUTER_API_KEY in Streamlit app Secrets.")
        try:
            response = requests.post(
                self.base_url + "/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json",
                         "HTTP-Referer": "https://nova-ai.streamlit.app", "X-Title": "NOVA AI"},
                json={"model": self.model, "temperature": temperature,
                      "messages": [{"role":"system","content":system},{"role":"user","content":user}]},
                timeout=90,
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()
        except requests.RequestException as exc:
            detail = getattr(getattr(exc,"response",None),"text","")
            raise AIProviderError(f"OpenRouter request failed: {detail or exc}") from exc
        except (KeyError, IndexError, TypeError) as exc:
            raise AIProviderError("Unexpected response from OpenRouter.") from exc

class Agent:
    def __init__(self,name,instructions,client):
        self.name,self.instructions,self.client=name,instructions,client
    def run(self,task,context=""):
        return self.client.chat(self.instructions,f"Task:\n{task}\n\nContext:\n{context or 'None'}")

class NovaOrchestrator:
    def __init__(self,client,progress:Callable[[str],None]|None=None):
        self.client=client
        self.progress=progress or (lambda _:None)
        self.planner=Agent("Planner","You are NOVA Planner. Break the request into steps and name needed specialists: Researcher, Coder, Analyst. Flag risky external actions for approval. Never claim work happened if it did not.",client)
        self.researcher=Agent("Researcher","You are NOVA Researcher. Prepare a careful research brief. Separate facts from assumptions. Do not invent sources or claim to browse without a search tool.",client)
        self.coder=Agent("Coder","You are NOVA Coder. Write secure, practical code and explain files and tests. Do not claim code was run unless it was.",client)
        self.analyst=Agent("Analyst","You are NOVA Analyst. Solve the task clearly, state assumptions, and produce actionable output.",client)
        self.reviewer=Agent("Reviewer","You are NOVA Reviewer. Check correctness, completeness, unsupported claims, and safety. Return a corrected final answer.",client)
    def run(self,task,memory=""):
        out={}
        self.progress("Planner is preparing the task plan…")
        out["plan"]=self.planner.run(task,memory)
        lower=out["plan"].lower()
        if any(word in lower for word in ("research","web","source","investigate")):
            self.progress("Research Agent is working…")
            out["research"]=self.researcher.run(task,out["plan"]+"\n"+memory)
        if any(word in lower for word in ("code","software","program","develop","build")):
            self.progress("Coding Agent is working…")
            out["coding"]=self.coder.run(task,out["plan"]+"\n"+memory)
        self.progress("Analyst is preparing the response…")
        out["analysis"]=self.analyst.run(task,"\n\n".join(f"{k}:\n{v}" for k,v in out.items()))
        self.progress("Reviewer is checking the result…")
        out["final"]=self.reviewer.run(task,"\n\n".join(f"{k}:\n{v}" for k,v in out.items()))
        return out
