"""Project model — generated projects with files, status, and config."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Text, JSON, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base, safe_iso


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")

    # Status: draft | planning | in_progress | testing | deploying | deployed | archived
    status: Mapped[str] = mapped_column(String(30), default="draft")
    # Current stage: discover | architect | build | test | teach | deploy
    current_stage: Mapped[str] = mapped_column(String(30), default="architect")

    # Link to the selected problem and research report
    problem_id: Mapped[str] = mapped_column(String(36), ForeignKey("problem_candidates.id"), nullable=True)
    research_report_id: Mapped[str] = mapped_column(String(36), ForeignKey("research_reports.id"), nullable=True, index=True)

    # Blueprint stored as JSON
    blueprint: Mapped[dict] = mapped_column(JSON, default=dict)

    # Tech stack and architecture decisions
    tech_stack: Mapped[dict] = mapped_column(JSON, default=dict)
    architecture: Mapped[dict] = mapped_column(JSON, default=dict)

    # GitHub info
    github_repo_url: Mapped[str] = mapped_column(String(500), nullable=True)
    github_repo_name: Mapped[str] = mapped_column(String(200), nullable=True)
    github_branch: Mapped[str] = mapped_column(String(100), nullable=True)
    last_commit_sha: Mapped[str] = mapped_column(String(40), nullable=True)

    # Deployment info
    deploy_provider: Mapped[str] = mapped_column(String(50), nullable=True)
    deploy_url: Mapped[str] = mapped_column(String(500), nullable=True)
    deploy_status: Mapped[str] = mapped_column(String(30), nullable=True)
    last_deploy_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Tasks checklist
    tasks: Mapped[list] = mapped_column(JSON, default=list)

    # Relationships
    owner = relationship("User", back_populates="projects")
    files = relationship("ProjectFile", back_populates="project", cascade="all, delete-orphan")
    problem = relationship("ProblemCandidate", back_populates="project")
    research_report = relationship("ResearchReport", foreign_keys=[research_report_id])

    def to_dict(self):
        # Derive stage dynamically if not set
        stage = getattr(self, "current_stage", None)
        if not stage:
            if self.status in ("deployed",):
                stage = "deploy"
            elif self.status in ("verified", "testing"):
                stage = "test"
            elif self.status in ("in_progress", "built"):
                stage = "build"
            elif self.blueprint:
                stage = "architect"
            else:
                stage = "discover"

        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "name": self.name,
            "title": self.name,
            "description": self.description,
            "status": self.status,
            "current_stage": stage,
            "problem_id": self.problem_id,
            "research_report_id": getattr(self, "research_report_id", None),
            "blueprint": self.blueprint or {},
            "tech_stack": self.tech_stack or {},
            "architecture": self.architecture or {},
            "tasks": self.tasks or [],
            "github_repo_url": self.github_repo_url,
            "deploy_url": self.deploy_url,
            "deploy_status": self.deploy_status,
            "created_at": safe_iso(self.created_at),
            "updated_at": safe_iso(self.updated_at),
        }


class ProjectFile(Base):
    __tablename__ = "project_files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, default="")
    language: Mapped[str] = mapped_column(String(50), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="files")

    def to_dict(self):
        return {
            "id": self.id,
            "path": self.path,
            "content": self.content,
            "language": self.language,
            "description": self.description,
            "version": self.version,
        }
