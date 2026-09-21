"""Agents package: LLM-backed review agents (Phase 10+).

Phase 10 adds the Security Review Agent; later phases add the Test Writer and
Synthesis agents. Agents depend on the :class:`LLMProvider` abstraction from
the LLM layer, never on a concrete provider.
"""