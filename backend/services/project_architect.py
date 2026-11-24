"""
ProblemPilot AI — Project Blueprint & Architecture Architect
Generates comprehensive, non-generic project blueprints, system architectures,
database schemas, API contracts, interview preparation guides, and resume bullets.
"""
import json
import logging
from typing import Dict, Any, Optional

from backend.config import settings
from backend.services.research_service import analyze_with_ai, extract_json_from_llm
from backend.services.blueprint_engine import BlueprintEngine

logger = logging.getLogger(__name__)


class ProjectArchitect:
    """
    Synthesizes tailored software blueprints from validated problem opportunities
    or natural-language requirements using the BlueprintEngine.
    """

    @staticmethod
    def generate_fallback_blueprint(problem_title: str, problem_desc: str, tech_stack: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate a category-aware, complete architectural specification when LLM is unavailable.
        """
        return BlueprintEngine.generate_blueprint_fallback(
            title=problem_title,
            description=problem_desc,
            tech_stack=tech_stack,
        )

    async def generate_blueprint(
        self,
        problem_title: str,
        problem_desc: str,
        tech_stack: Optional[Dict[str, Any]] = None,
        custom_instructions: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate an AI-driven or category-aware project blueprint tailored to
        the user's exact requirements and custom tech stack.
        """
        return await BlueprintEngine.generate_blueprint(
            title=problem_title,
            description=problem_desc,
            tech_stack=tech_stack,
            custom_instructions=custom_instructions,
        )


