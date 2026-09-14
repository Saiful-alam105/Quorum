"""Phase 5 orchestrator: entry point for the Quorum analysis pipeline.

Stages (Phases 6-14) register themselves by appending to STAGES.
"""

from quorum.orchestrator.runner import AnalysisContext, run_analysis_for_pull_request

__all__ = ["AnalysisContext", "run_analysis_for_pull_request"]