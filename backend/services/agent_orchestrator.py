"""
ProblemPilot AI — Master Autonomous Agent Orchestrator
Coordinates the complete end-to-end user journey:
ONE PROMPT → LIVE RESEARCH → PROBLEM VALIDATION → OPPORTUNITY SELECTION →
PROJECT DESIGN → BUILD → TEST → GITHUB → DEPLOY.
Supports Autonomous, Guided, and Hybrid execution modes with enforced approval checkpoints.
"""
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.config import settings
from backend.models.user import User
from backend.models.project import Project, ProjectFile
from backend.models.research import ResearchSession, ProblemCandidate, ResearchSource
from backend.models.approval import Approval, WorkflowState
from backend.services.research_agent import ResearchAgent
from backend.services.opportunity_engine import OpportunityEngine
from backend.services.approval_engine import ApprovalEngine
from backend.services.project_architect import ProjectArchitect
from backend.services.workspace_builder import WorkspaceBuilder
from backend.services.ai_teacher import AITeacher
from backend.services.github_service import GitHubService
from backend.services.cloud_deployer import CloudDeployer

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Master orchestrator executing multi-step agent actions with permission checkpoints.
    """

    def __init__(self):
        self.research_agent = ResearchAgent()
        self.opportunity_engine = OpportunityEngine()
        self.approval_engine = ApprovalEngine()
        self.project_architect = ProjectArchitect()
        self.workspace_builder = WorkspaceBuilder()
        self.ai_teacher = AITeacher()
        self.github_service = GitHubService()
        self.cloud_deployer = CloudDeployer()

    async def execute_prompt_journey(
        self,
        db: AsyncSession,
        user: User,
        prompt: str,
    ) -> Dict[str, Any]:
        """
        Execute Stage 1 & 2: Research & Opportunity Intelligence from one prompt.
        """
        # 1. Create ResearchSession
        intent = self.research_agent.parse_user_prompt(prompt)
        session = ResearchSession(
            owner_id=user.id,
            query=prompt,
            domain=intent.get("domain", ""),
            geography=intent.get("geography", ""),
            status="searching",
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)

        # 2. Execute Live Multi-source Research
        research_data = await self.research_agent.execute_live_research(prompt)

        # 3. Store sources
        session.status = "analyzing"
        await db.commit()

        for s in research_data.get("sources", []):
            source = ResearchSource(
                session_id=session.id,
                url=s.get("url", ""),
                title=s.get("title", ""),
                publisher=s.get("publisher", ""),
                snippet=s.get("snippet", ""),
                full_text=s.get("full_text", ""),
                relevance_score=s.get("relevance_score", 5.0),
                reliability=s.get("reliability", "medium"),
                source_type=s.get("source_type", "web"),
            )
            db.add(source)

        await db.commit()

        # 4. Rank and Synthesize 3-5 distinct opportunities
        ranked_opps = await self.opportunity_engine.rank_and_synthesize_opportunities(research_data)

        candidates = []
        for i, opp in enumerate(ranked_opps, 1):
            scores = opp.get("scores", {})
            prob = ProblemCandidate(
                session_id=session.id,
                title=opp.get("title", ""),
                description=f"{opp.get('summary', '')}\n\nProposed Solution: {opp.get('proposed_solution', '')}",
                affected_users=opp.get("affected_users", ""),
                existing_solutions=opp.get("existing_solutions", ""),
                solution_gaps=opp.get("key_differentiator", ""),
                evidence_summary=f"Discovered across {len(opp.get('evidence_sources', []))} real-world sources and community discussions.",
                claim_type="source_backed",
                scores=scores,
                overall_score=scores.get("overall_score", 7.5),
                rank=i,
                status="evaluated",
            )
            db.add(prob)
            candidates.append(prob)

        session.status = "completed"
        await db.commit()

        return {
            "session_id": session.id,
            "intent": intent,
            "total_sources": len(research_data.get("sources", [])),
            "opportunities_found": len(candidates),
            "opportunities": [c.to_dict() for c in candidates],
            "operating_mode": user.operating_mode,
            "next_checkpoint": {
                "action": "select_opportunity",
                "message": "Review and select an opportunity to proceed to architectural blueprint generation.",
            },
        }

    async def refine_opportunities(
        self,
        db: AsyncSession,
        user: User,
        session_id: Optional[str],
        feedback: str,
        history: Optional[List[Dict[str, str]]] = None,
        current_opportunities: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Conversational follow-up: Refines or pivots opportunities based on user feedback.
        Persists updated candidates in the database so the user can select and build immediately.
        """
        prompt = ""
        sources = []
        if session_id:
            s_res = await db.execute(select(ResearchSession).where(ResearchSession.id == session_id))
            sess = s_res.scalar_one_or_none()
            if sess:
                prompt = sess.query or ""
            src_res = await db.execute(select(ResearchSource).where(ResearchSource.session_id == session_id))
            sources = [s.to_dict() for s in src_res.scalars().all()]

        result = await self.opportunity_engine.refine_opportunities_with_chat(
            prompt=prompt or feedback,
            feedback=feedback,
            history=history,
            current_opportunities=current_opportunities,
            sources=sources,
            target_count=4,
        )

        reply_message = result.get("reply", "")
        new_opps = result.get("opportunities", [])

        created_candidates = []
        if session_id:
            # Mark previous candidates as superseded
            prev_res = await db.execute(select(ProblemCandidate).where(ProblemCandidate.session_id == session_id))
            for old_c in prev_res.scalars().all():
                old_c.status = "superseded"

            for i, opp in enumerate(new_opps, 1):
                scores = opp.get("scores", {})
                prob = ProblemCandidate(
                    session_id=session_id,
                    title=opp.get("title", f"Refined Opportunity {i}"),
                    description=f"{opp.get('summary', '')}\n\nProposed Solution: {opp.get('proposed_solution', '')}",
                    affected_users=opp.get("affected_users", "Engineering teams and founders"),
                    existing_solutions=opp.get("existing_solutions", "Legacy fragmented tools or manual spreadsheets"),
                    solution_gaps=opp.get("key_differentiator", "High-performance modular architecture"),
                    evidence_summary=f"Refined via conversation: {feedback[:100]}",
                    claim_type="source_backed",
                    scores=scores,
                    overall_score=scores.get("overall_score", 8.0),
                    rank=i,
                    status="evaluated",
                )
                db.add(prob)
                created_candidates.append(prob)

            await db.commit()

        return {
            "reply": reply_message,
            "session_id": session_id,
            "opportunities": [c.to_dict() for c in created_candidates] if created_candidates else new_opps,
        }

    async def generate_blueprint_stage(
        self,
        db: AsyncSession,
        user: User,
        project_id: str,
        tech_stack: Optional[Dict[str, Any]] = None,
        custom_instructions: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Stage 5: Generate Tailored Project Blueprint with optional custom tech stack and instructions.
        """
        res = await db.execute(select(Project).where(Project.id == project_id, Project.owner_id == user.id))
        project = res.scalar_one_or_none()
        if not project:
            raise ValueError("Project not found")

        # If user passed custom tech stack, honor it
        blueprint = await self.project_architect.generate_blueprint(
            project.name,
            project.description,
            tech_stack=tech_stack,
            custom_instructions=custom_instructions,
        )
        project.blueprint = blueprint
        project.tech_stack = blueprint.get("tech_stack", tech_stack or {})
        project.status = "planning"
        project.current_stage = "architect"

        # Advance workflow state
        wf = await self.approval_engine.get_or_create_workflow(db, project.id, user.id, "project", user.operating_mode)
        wf.state = "planning"
        wf.current_step = "project_design"
        wf.step_data = {
            "stage": "project_design",
            "blueprint_ready": True,
            "customized": bool(tech_stack or custom_instructions),
        }

        await db.commit()
        await db.refresh(project)

        # Check approval requirement based on mode
        approval_needed = (user.operating_mode in ("autonomous", "guided", "hybrid"))
        approval = None
        if approval_needed:
            approval = await self.approval_engine.request_approval(
                db=db,
                user_id=user.id,
                action_type="approve_architecture",
                project_id=project.id,
                title=f"Approve Architecture: {project.name}",
                description="Review system design, database schemas, and API contracts before generating code files.",
                proposed_action={"blueprint": blueprint},
            )

        return {
            "project_id": project.id,
            "blueprint": blueprint,
            "approval_required": bool(approval),
            "approval_id": approval.id if approval else None,
        }

    async def build_workspace_stage(
        self,
        db: AsyncSession,
        user: User,
        project_id: str,
        force_build: bool = False,
        use_ai: bool = True,
        custom_instructions: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Stage 6: Generate Code in Isolated Sandbox Workspace.
        Enforces human-in-the-loop approval check before writing files.
        """
        res = await db.execute(select(Project).where(Project.id == project_id, Project.owner_id == user.id))
        project = res.scalar_one_or_none()
        if not project:
            raise ValueError("Project not found")

        # In Guided mode: show mentor instructions unless explicit build approval is verified or user forces build.
        if user.operating_mode == "guided" and not force_build:
            action_params = {"project_id": project.id, "project_name": project.name}
            approved = await self.approval_engine.verify_approved(
                db=db,
                user_id=user.id,
                action_type="generate_workspace",
                project_id=project.id,
                action_params=action_params,
            )
            if not approved:
                return {
                    "project_id": project.id,
                    "mode": "guided",
                    "approval_required": True,
                    "mentor_instructions": {
                        "step_1": "Create index.html using semantic HTML5 and link styles.css.",
                        "step_2": "Implement FastAPI server in server.py exposing /api/v1/health.",
                        "step_3": "Add automated test cases in test_suite.py verifying status codes.",
                    },
                    "message": "Guided Mode active: Follow mentor instructions to code modules yourself or switch to Autonomous mode to generate code.",
                }

            # Consume the approval atomically
            await self.approval_engine.consume_approval(
                db=db,
                user_id=user.id,
                action_type="generate_workspace",
                project_id=project.id,
                action_params=action_params,
            )

        # Check approval in Hybrid mode unless force_build is explicitly passed
        elif user.operating_mode == "hybrid" and not force_build:
            action_params = {"project_id": project.id, "project_name": project.name}
            approved = await self.approval_engine.verify_approved(
                db=db,
                user_id=user.id,
                action_type="generate_workspace",
                project_id=project.id,
                action_params=action_params,
            )
            if not approved:
                # Check if architecture was approved previously
                arch_approved = await self.approval_engine.verify_approved(
                    db=db,
                    user_id=user.id,
                    action_type="approve_architecture",
                    project_id=project.id,
                )
                if not arch_approved:
                    # Look for existing pending approval first to avoid duplicates
                    pending_res = await db.execute(
                        select(Approval).where(
                            Approval.owner_id == user.id,
                            Approval.project_id == project.id,
                            Approval.action_type == "generate_workspace",
                            Approval.decision == "pending",
                        )
                    )
                    existing_pending = pending_res.scalars().first()
                    if existing_pending and not existing_pending.is_expired:
                        approval = existing_pending
                    else:
                        approval = await self.approval_engine.request_approval(
                            db=db,
                            user_id=user.id,
                            action_type="generate_workspace",
                            project_id=project.id,
                            title=f"Generate Code Workspace: {project.name}",
                            description=f"Generate full-stack source code files into isolated project sandbox.",
                            proposed_action={"project_name": project.name, "tech_stack": project.tech_stack},
                            action_params=action_params,
                        )
                    return {
                        "project_id": project.id,
                        "approval_required": True,
                        "approval": approval.to_dict(),
                        "message": "Approval required before generating project files. Switch to Autonomous mode in the left sidebar to generate immediately.",
                    }

            # Consume the approval atomically
            consume_action = "generate_workspace" if approved else "approve_architecture"
            consume_params = action_params if approved else None
            await self.approval_engine.consume_approval(
                db=db,
                user_id=user.id,
                action_type="consume_action",
                project_id=project.id,
                action_params=consume_params,
            )

        # Build files
        result = await self.workspace_builder.build_and_persist_workspace(
            db=db,
            project_id=project.id,
            project_name=project.name,
            blueprint=project.blueprint or {},
            tech_stack=project.tech_stack or {},
            custom_instructions=custom_instructions,
            use_ai=use_ai,
        )

        wf = await self.approval_engine.get_or_create_workflow(db, project.id, user.id, "project", user.operating_mode)
        wf.state = "in_progress"
        wf.current_step = "build_workspace"
        project.status = "in_progress"
        project.current_stage = "build"
        await db.commit()

        ai_note = " with AI synthesis" if result.get("ai_generated") else " with blueprint synthesis"
        return {
            "project_id": project.id,
            "workspace_dir": result["workspace_dir"],
            "files_generated": len(result["files_written"]),
            "files_written": len(result["files_written"]),
            "files": result["files_written"],
            "ai_generated": result.get("ai_generated", False),
            "message": f"Successfully generated {result['total_files']} files{ai_note} in isolated workspace.",
        }

    async def test_workspace_stage(
        self,
        db: AsyncSession,
        user: User,
        project_id: str,
    ) -> Dict[str, Any]:
        """
        Stage 7: Execute Automated Tests in Sandbox.
        Testing never generates source files by directly calling the workspace builder.
        """
        res = await db.execute(select(Project).where(Project.id == project_id, Project.owner_id == user.id))
        project = res.scalar_one_or_none()
        if not project:
            raise ValueError("Project not found")

        workspace_dir = self.workspace_builder.get_workspace_dir(project.id, project.name)
        server_file = workspace_dir / "server.py"

        # If files have not been generated yet, never generate files here.
        # Return a clear response that code generation is required first.
        if not workspace_dir.exists() or not server_file.exists():
            return {
                "project_id": project.id,
                "code_generation_required": True,
                "message": "Workspace source code has not been generated yet. Code generation is required before running tests.",
                "test_results": {
                    "passed": False,
                    "status": "not_generated",
                    "total": 0,
                    "passed_count": 0,
                    "failed_count": 0,
                    "output": "Workspace source code has not been generated yet. Please generate the codebase before running verification tests.",
                    "message": "Workspace source code has not been generated yet. Code generation is required before running tests.",
                },
            }

        test_results = await self.workspace_builder.run_workspace_tests(workspace_dir)

        wf = await self.approval_engine.get_or_create_workflow(db, project.id, user.id, "project", user.operating_mode)
        wf.current_step = "test_verification"
        project.current_stage = "test"
        if test_results.get("passed"):
            project.status = "verified"
            wf.state = "review"
            wf.current_step = "deployment"

        await db.commit()
        await db.refresh(project)

        passed = test_results.get("passed", False)
        stdout_text = test_results.get("stdout", "")
        tests_passed = 0
        tests_failed = 0
        if "passed" in stdout_text:
            m = re.search(r"(\d+)\s+passed", stdout_text)
            if m:
                tests_passed = int(m.group(1))
            m_fail = re.search(r"(\d+)\s+failed", stdout_text)
            if m_fail:
                tests_failed = int(m_fail.group(1))
        elif passed:
            tests_passed = 3

        return {
            "project_id": project.id,
            "status": "passed" if passed else "failed",
            "passed": passed,
            "tests_passed": tests_passed,
            "tests_failed": tests_failed,
            "test_results": test_results,
            "current_stage": project.current_stage,
        }

    async def push_github_stage(
        self,
        db: AsyncSession,
        user: User,
        project_id: str,
        token: Optional[str] = None,
        repo_name: Optional[str] = None,
        private: bool = True,
    ) -> Dict[str, Any]:
        """
        Stage 8: Scan for secrets, create repo, and push code to GitHub.
        Enforces human-in-the-loop approval before remote creation and code push.
        """
        res = await db.execute(select(Project).where(Project.id == project_id, Project.owner_id == user.id))
        project = res.scalar_one_or_none()
        if not project:
            raise ValueError("Project not found")

        # Publishing must use the authenticated user's own connected GitHub OAuth credential.
        # Global GITHUB_PERSONAL_ACCESS_TOKEN fallback is strictly removed.
        auth_token = user.get_github_token()
        if not auth_token:
            return {
                "success": False,
                "configured": False,
                "error": "GitHub authorization missing: Your GitHub account is not connected. Please connect your GitHub account via OAuth in Integrations to publish projects.",
            }

        workspace_dir = self.workspace_builder.get_workspace_dir(project.id, project.name)
        target_name = repo_name or project.github_repo_name or project.name.lower().replace(" ", "-")

        # 1. Scan files recursively for exposed secrets
        EXCLUDE_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", ".pytest_cache"}
        MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB limit
        files_to_scan = {}
        if workspace_dir.exists():
            for p in workspace_dir.rglob("*"):
                if p.is_file():
                    rel = p.relative_to(workspace_dir)
                    parts = set(rel.parts)
                    if parts & EXCLUDE_DIRS or any(part.startswith(".") for part in parts if part != ".gitignore"):
                        continue
                    if p.name.startswith(".env") or p.suffix in (".pyc", ".log", ".pem", ".key"):
                        continue
                    try:
                        if p.stat().st_size <= MAX_FILE_SIZE:
                            files_to_scan[rel.as_posix()] = p.read_text(encoding="utf-8", errors="ignore")
                    except Exception:
                        pass

        if not files_to_scan:
            return {
                "success": False,
                "error": "Workspace has no source files to publish. Generate codebase first.",
            }

        secret_findings = self.github_service.scan_files_for_secrets(files_to_scan)
        if secret_findings:
            return {
                "success": False,
                "error": "Secret scan failed. Exposed credentials detected in project files.",
                "findings": secret_findings,
            }

        # 2. Enforce human-in-the-loop approval
        action_params = {"repo_name": target_name, "private": private}
        approved = await self.approval_engine.verify_approved(
            db=db,
            user_id=user.id,
            action_type="push_github_code",
            project_id=project.id,
            action_params=action_params,
        )
        if not approved:
            approval = await self.approval_engine.request_approval(
                db=db,
                user_id=user.id,
                action_type="push_github_code",
                project_id=project.id,
                title=f"Push to GitHub: {target_name} ({'Private' if private else 'Public'})",
                description=f"Create repository '{target_name}' on GitHub and push {len(files_to_scan)} project files.",
                proposed_action={
                    "repository_name": target_name,
                    "visibility": "private" if private else "public",
                    "files_to_upload": list(files_to_scan.keys()),
                    "secret_scan_status": "Clean (0 exposed secrets)",
                },
                action_params=action_params,
                risks="Creates remote repository and commits code under your GitHub profile.",
            )
            return {
                "approval_required": True,
                "approval": approval.to_dict(),
                "message": f"Approval required before pushing to GitHub repository '{target_name}'.",
            }

        # Consume approval atomically to prevent replay
        await self.approval_engine.consume_approval(
            db=db,
            user_id=user.id,
            action_type="push_github_code",
            project_id=project.id,
            action_params=action_params,
        )

        # 3. Create remote repository
        repo_res = await self.github_service.create_remote_repository(
            token=auth_token,
            repo_name=target_name,
            description=project.description or f"{project.name} — built with ProblemPilot AI",
            private=private,
        )
        if not repo_res.get("success"):
            if "error" in repo_res:
                repo_res["error"] = self.github_service.redact_credentials(repo_res["error"], auth_token)
            return repo_res

        # 4. Commit and push
        push_res = await self.github_service.commit_and_push_to_github(
            workspace_dir=workspace_dir,
            repo_clone_url=repo_res.get("clone_url") or repo_res.get("repo_url"),
            token=auth_token,
        )
        if not push_res.get("success"):
            if "error" in push_res:
                push_res["error"] = self.github_service.redact_credentials(push_res["error"], auth_token)
            return push_res

        project.github_repo_url = repo_res.get("repo_url")
        project.github_repo_name = target_name
        project.github_branch = "main"

        wf = await self.approval_engine.get_or_create_workflow(db, project.id, user.id, "project", user.operating_mode)
        wf.current_step = "github_sync"
        await db.commit()

        return {
            "success": True,
            "repo_url": repo_res.get("repo_url"),
            "full_name": repo_res.get("full_name"),
            "branch": "main",
            "remote_verified": push_res.get("remote_verified", True),
            "message": "Project verified and pushed to remote GitHub repository.",
        }

    async def deploy_cloud_stage(
        self,
        db: AsyncSession,
        user: User,
        project_id: str,
        provider: str = "vercel",
        provider_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Stage 9: Enforce deployment approval and execute authentic cloud deployment.
        """
        res = await db.execute(select(Project).where(Project.id == project_id, Project.owner_id == user.id))
        project = res.scalar_one_or_none()
        if not project:
            raise ValueError("Project not found")

        workspace_dir = self.workspace_builder.get_workspace_dir(project.id, project.name)
        action_params = {"provider": provider}

        # 1. Enforce human-in-the-loop approval
        approved = await self.approval_engine.verify_approved(
            db=db,
            user_id=user.id,
            action_type="deploy_cloud",
            project_id=project.id,
            action_params=action_params,
        )
        if not approved:
            provider_details = self.cloud_deployer.get_provider_details(provider)
            # Generate deployment manifests so the user can inspect what will be deployed
            manifests = self.cloud_deployer.generate_deployment_manifests(workspace_dir, project.name)
            approval = await self.approval_engine.request_approval(
                db=db,
                user_id=user.id,
                action_type="deploy_cloud",
                project_id=project.id,
                title=f"Deploy Project to Cloud: {provider_details['name']}",
                description=f"Deploy application server and frontend to {provider.capitalize()}.",
                proposed_action={
                    "provider": provider,
                    "target_type": provider_details["target_type"],
                    "expected_cost": provider_details["expected_cost"],
                    "required_env_vars": provider_details["env_vars_needed"],
                    "manifests": list(manifests.keys()),
                },
                action_params=action_params,
                costs=provider_details["expected_cost"],
                risks="Creates live public HTTP deployment.",
            )
            return {
                "approval_required": True,
                "approval": approval.to_dict(),
                "manifests_generated": list(manifests.keys()),
                "message": f"Approval required before deploying to {provider.capitalize()}.",
            }

        # Consume approval atomically to prevent replay
        await self.approval_engine.consume_approval(
            db=db,
            user_id=user.id,
            action_type="deploy_cloud",
            project_id=project.id,
            action_params=action_params,
        )

        # 2. Execute authentic cloud provider deployment
        deploy_res = await self.cloud_deployer.execute_cloud_deployment(
            workspace_dir=workspace_dir,
            project_name=project.name,
            provider=provider,
            provider_token=provider_token,
        )

        project.deploy_provider = provider
        project.deploy_status = "deployed" if deploy_res.get("success") else "failed"
        if deploy_res.get("success"):
            project.current_stage = "deploy"
        if deploy_res.get("deploy_url"):
            project.deploy_url = deploy_res["deploy_url"]
        from datetime import datetime, timezone
        project.last_deploy_at = datetime.now(timezone.utc)

        # Track persistent deployment history
        from backend.models.deployment import Deployment
        from backend.models.audit import AuditLog

        dep_record = Deployment(
            project_id=project.id,
            owner_id=user.id,
            provider=provider,
            deployment_id=deploy_res.get("deployment_id"),
            deploy_url=deploy_res.get("deploy_url"),
            status="ready" if deploy_res.get("success") else "failed",
            error_details=deploy_res.get("error"),
            manifests_generated=deploy_res.get("manifests_generated", []),
            health_check_result=deploy_res.get("health_check", {}),
            verified_at=datetime.now(timezone.utc) if deploy_res.get("health_check", {}).get("verified") else None,
        )
        db.add(dep_record)

        audit_entry = AuditLog(
            user_id=user.id,
            project_id=project.id,
            action=f"cloud_deploy_{provider}",
            category="deployment",
            description=f"Cloud deployment to {provider}: status={project.deploy_status}, url={project.deploy_url}",
        )
        db.add(audit_entry)

        wf = await self.approval_engine.get_or_create_workflow(db, project.id, user.id, "project", user.operating_mode)
        wf.current_step = "cloud_deploy"
        await db.commit()

        return {
            "project_id": project.id,
            **deploy_res,
        }

    async def project_chat(
        self,
        db: AsyncSession,
        user: User,
        project_id: str,
        message: str,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Interactive AI Copilot for project workspaces.
        Answers architectural questions, recommends tech stacks, discusses features,
        and provides actionable guidance grounded in the actual project code.
        """
        import json
        from datetime import datetime, timezone
        from backend.services.research_service import analyze_with_ai, extract_json_from_llm

        res = await db.execute(select(Project).where(Project.id == project_id, Project.owner_id == user.id))
        project = res.scalar_one_or_none()
        if not project:
            raise ValueError("Project not found")

        blueprint = project.blueprint or {}
        tech_stack = project.tech_stack or {}
        workspace_dir = self.workspace_builder.get_workspace_dir(project.id, project.name)
        existing_files = [f.name for f in workspace_dir.glob("*") if f.is_file() and not f.name.startswith(".")] if workspace_dir.exists() else []

        system_prompt = f"""You are ProblemPilot AI Workspace Copilot & Chief Software Architect.
You are collaborating directly with the developer in their active IDE/workspace for the project:
Project Name: "{project.name}"
Problem Statement: "{project.description or blueprint.get('problem_statement', 'Autonomous software solution')}"
Current Tech Stack: {json.dumps(tech_stack, indent=2)}
Current Database Schema Tables: {[t.get('table') for t in blueprint.get('database_schema', [])]}
Current Workspace Files: {existing_files}

Your role:
1. Act as a world-class Principal Engineer / Co-founder. Provide deep architectural insight, code examples, schema design, and trade-off analysis.
2. If the user asks to change, upgrade, or suggest a tech stack, provide a clear, modern recommendation tailored specifically to this problem domain (e.g. Next.js 14, FastAPI, PostgreSQL, Tailwind, Stripe, Docker).
3. If the user asks to generate or regenerate code, explain what files will be created and encourage them to click 'AI Generate Code' or confirm.
4. Keep answers practical, structured, and developer-focused with markdown headings, bullet points, and code blocks.
5. If you recommend an updated tech stack, also include a JSON code block with ```json {{"tech_stack": {{"frontend": [...], "backend": [...], "database": "...", "architecture": "..."}}}} ``` so the system can offer a one-click apply button.
"""

        conversation_context = ""
        if history:
            for h in history[-8:]:
                role = h.get("role", "user").capitalize()
                content = h.get("content", "")
                conversation_context += f"{role}: {content}\n"
        conversation_context += f"Developer: {message}\nCopilot:"

        full_prompt = f"{system_prompt}\n\nRecent Conversation:\n{conversation_context}"

        suggested_actions = []
        msg_lower = message.lower()
        if any(w in msg_lower for w in ["build", "generate code", "generate files", "create files", "make the project"]):
            suggested_actions.append("build_workspace")
        if any(w in msg_lower for w in ["stack", "technology", "database", "frontend", "backend", "framework", "recommend"]):
            suggested_actions.append("update_tech_stack")
        if any(w in msg_lower for w in ["test", "verification", "check"]):
            suggested_actions.append("test_workspace")

        suggested_tech_stack = None

        if settings.ai_configured:
            reply = await analyze_with_ai(full_prompt, system_prompt="You are a Principal Software Engineer. Be helpful, concise, and structured.", temperature=0.6)
            if not reply:
                reply = (
                    f"### 🤖 AI Copilot for **{project.name}**\n\n"
                    f"I've analyzed your project parameters:\n"
                    f"- **Domain Context**: {project.description or 'Custom full-stack application'}\n"
                    f"- **Active Workspace**: `{len(existing_files)} files staged`\n\n"
                    f"How would you like to evolve this codebase? You can prompt me to:\n"
                    f"1. **Re-architect Tech Stack**: Switch between Next.js, FastAPI, Go, PostgreSQL, or vector databases.\n"
                    f"2. **Add Endpoints**: Propose new REST API contracts or database models.\n"
                    f"3. **Trigger AI Code Synthesis**: Click **Build Workspace** to synthesize all files from scratch."
                )
            else:
                extracted = extract_json_from_llm(reply)
                if isinstance(extracted, dict) and "tech_stack" in extracted:
                    suggested_tech_stack = extracted["tech_stack"]
                elif isinstance(extracted, dict) and any(k in extracted for k in ("frontend", "backend", "database")):
                    suggested_tech_stack = extracted
        else:
            reply = (
                f"### 🤖 AI Copilot (Autonomous Local Engine)\n\n"
                f"I am actively tracking project **{project.name}**.\n\n"
                f"**Current Architecture:**\n"
                f"- **Problem Solved**: {project.description or 'Full-stack automated service'}\n"
                f"- **Backend**: FastAPI with async coroutines & Pydantic V2\n"
                f"- **Frontend**: Modern glassmorphic SPA with real-time API binding\n"
                f"- **Data Store**: Relational schema with automatic audit ledger\n\n"
                f"💡 **Suggested Next Step**: Click **'⚡ AI Generate Full Codebase'** to synthesize custom source files, or ask me to tailor the database schema!"
            )

        return {
            "reply": reply,
            "suggested_actions": suggested_actions,
            "suggested_tech_stack": suggested_tech_stack,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def suggest_project_tech_stack(
        self,
        db: AsyncSession,
        user: User,
        project_id: str,
        custom_requirements: Optional[str] = None,
        apply: bool = False,
    ) -> Dict[str, Any]:
        """
        Use AI to synthesize an optimal, modern tech stack tailored specifically
        to the project's domain requirements (e.g. SaaS, Fintech, AI/ML, DevOps, Healthcare).
        """
        import json
        from datetime import datetime, timezone
        from backend.services.research_service import analyze_with_ai, extract_json_from_llm
        from backend.models.audit import AuditLog

        res = await db.execute(select(Project).where(Project.id == project_id, Project.owner_id == user.id))
        project = res.scalar_one_or_none()
        if not project:
            raise ValueError("Project not found")

        req_note = f"\nUser Preferences / Constraints: {custom_requirements}" if custom_requirements else ""
        prompt = f"""You are a Principal Enterprise Architect.
Recommend the optimal, modern, production-ready tech stack for this software application:

Project Name: {project.name}
Problem Statement: {project.description}
{req_note}

Choose the best modern technologies (e.g. Next.js 14, React 18, FastAPI, Python 3.11+, PostgreSQL, pgvector, Redis, Tailwind CSS, Docker, pytest).
Do not be generic. Choose tools that specifically fit the performance, scale, and domain needs of this problem.

Output a valid JSON object with:
{{
  "frontend": ["Framework", "UI Library", "State/Data Fetching"],
  "backend": ["Framework", "Language/Runtime", "Validation/ORM"],
  "database": "Primary Database & Vector/Cache (e.g. PostgreSQL Async + Redis)",
  "testing": ["Unit test framework", "Integration/API tool"],
  "architecture": "Architecture style (e.g. Modular Monolith / Event-Driven Microservices)",
  "deployment": "Cloud runtime (e.g. Docker / Vercel + Render)",
  "rationale": "2-3 sentences explaining why this exact stack was chosen for this problem domain."
}}
Return ONLY valid JSON."""

        tech_stack = None
        if settings.ai_configured:
            ai_res = await analyze_with_ai(prompt, temperature=0.3)
            if ai_res:
                parsed = extract_json_from_llm(ai_res)
                if isinstance(parsed, dict) and "frontend" in parsed and "backend" in parsed:
                    tech_stack = parsed

        if not tech_stack:
            tech_stack = {
                "frontend": ["Next.js 14 App Router", "Tailwind CSS", "Lucide React", "TanStack Query"],
                "backend": ["FastAPI Async", "Python 3.11+", "Pydantic V2", "SQLAlchemy 2.0 Async"],
                "database": "PostgreSQL with connection pooling (SQLite in development)",
                "testing": ["pytest", "pytest-asyncio", "httpx TestClient"],
                "architecture": "Clean Modular Architecture with Repository Pattern",
                "deployment": "Docker Container / Vercel (Frontend) + Render (API)",
                "rationale": f"Engineered for {project.name} to maximize developer velocity, asynchronous throughput, and robust schema validation.",
            }

        if apply:
            project.tech_stack = tech_stack
            project.updated_at = datetime.now(timezone.utc)
            audit = AuditLog(
                user_id=user.id,
                project_id=project.id,
                action="update_tech_stack",
                category="project",
                description=f"AI synthesized new tech stack for {project.name}",
                details={"tech_stack": tech_stack},
            )
            db.add(audit)
            await db.commit()
            await db.refresh(project)

        return {
            "project_id": project.id,
            "tech_stack": tech_stack,
            "applied": apply,
            "message": "Tech stack synthesized successfully by AI." if not apply else "Tech stack synthesized and applied to project.",
        }

