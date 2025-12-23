"""
Project Templates Library for GDIL
Pre-defined templates for common project types with roadmaps and clarification questions.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class ProjectTemplate:
    """A project template with pre-defined structure."""
    id: str
    name: str
    description: str
    category: str
    suggested_brief: str
    end_transformation: str
    roadmap: List[Dict]
    clarifying_questions: List[str]
    tags: List[str] = field(default_factory=list)
    estimated_iterations: int = 5


# Built-in templates
BUILTIN_TEMPLATES: Dict[str, ProjectTemplate] = {
    # Web Development
    "web-app": ProjectTemplate(
        id="web-app",
        name="Web Application",
        description="Build a full-stack web application with frontend and backend",
        category="Web Development",
        suggested_brief="Build a web application with user interface and server-side logic",
        end_transformation="From concept to deployed web application",
        roadmap=[
            {"name": "Requirements & Architecture", "description": "Define features, tech stack, and system design", "priority": 1, "depends_on": []},
            {"name": "Database Schema", "description": "Design data models and relationships", "priority": 2, "depends_on": ["Requirements & Architecture"]},
            {"name": "Backend API", "description": "Implement server endpoints and business logic", "priority": 3, "depends_on": ["Database Schema"]},
            {"name": "Frontend UI", "description": "Build user interface components and pages", "priority": 3, "depends_on": ["Requirements & Architecture"]},
            {"name": "Integration", "description": "Connect frontend to backend APIs", "priority": 4, "depends_on": ["Backend API", "Frontend UI"]},
            {"name": "Testing", "description": "Write and run tests for all components", "priority": 5, "depends_on": ["Integration"]},
            {"name": "Deployment", "description": "Deploy to production environment", "priority": 6, "depends_on": ["Testing"]}
        ],
        clarifying_questions=[
            "What is the main purpose of this web app?",
            "Who are the target users?",
            "What tech stack do you prefer (or should I recommend one)?",
            "Do you need user authentication?",
            "Any specific features or pages required?"
        ],
        tags=["web", "fullstack", "frontend", "backend"],
        estimated_iterations=8
    ),

    "api": ProjectTemplate(
        id="api",
        name="REST API",
        description="Build a RESTful API service with endpoints and data handling",
        category="Web Development",
        suggested_brief="Create a REST API with well-defined endpoints and data models",
        end_transformation="From API specification to working service",
        roadmap=[
            {"name": "API Design", "description": "Define endpoints, request/response formats, and OpenAPI spec", "priority": 1, "depends_on": []},
            {"name": "Data Models", "description": "Create database schemas and ORM models", "priority": 2, "depends_on": ["API Design"]},
            {"name": "Core Endpoints", "description": "Implement CRUD operations for main resources", "priority": 3, "depends_on": ["Data Models"]},
            {"name": "Authentication", "description": "Add auth middleware and token handling", "priority": 3, "depends_on": ["API Design"]},
            {"name": "Validation & Error Handling", "description": "Input validation and consistent error responses", "priority": 4, "depends_on": ["Core Endpoints"]},
            {"name": "Testing & Documentation", "description": "API tests and documentation generation", "priority": 5, "depends_on": ["Validation & Error Handling"]}
        ],
        clarifying_questions=[
            "What resources/entities will this API manage?",
            "What authentication method do you need (JWT, API keys, OAuth)?",
            "Do you have an existing database or starting fresh?",
            "Any rate limiting or quota requirements?",
            "What format for responses (JSON, XML)?"
        ],
        tags=["api", "rest", "backend", "microservice"],
        estimated_iterations=6
    ),

    # Data & Analysis
    "data-analysis": ProjectTemplate(
        id="data-analysis",
        name="Data Analysis",
        description="Analyze a dataset to extract insights and create visualizations",
        category="Data Science",
        suggested_brief="Analyze data to discover patterns, trends, and actionable insights",
        end_transformation="From raw data to insights and recommendations",
        roadmap=[
            {"name": "Data Understanding", "description": "Explore dataset structure, types, and quality", "priority": 1, "depends_on": []},
            {"name": "Data Cleaning", "description": "Handle missing values, outliers, and inconsistencies", "priority": 2, "depends_on": ["Data Understanding"]},
            {"name": "Exploratory Analysis", "description": "Statistical summaries and initial visualizations", "priority": 3, "depends_on": ["Data Cleaning"]},
            {"name": "Deep Analysis", "description": "Correlation analysis, segmentation, trend detection", "priority": 4, "depends_on": ["Exploratory Analysis"]},
            {"name": "Visualizations", "description": "Create charts and dashboards for key findings", "priority": 5, "depends_on": ["Deep Analysis"]},
            {"name": "Report & Recommendations", "description": "Document findings and actionable recommendations", "priority": 6, "depends_on": ["Visualizations"]}
        ],
        clarifying_questions=[
            "What questions are you trying to answer with this data?",
            "What format is your data in (CSV, database, API)?",
            "How large is the dataset?",
            "Are there specific metrics or KPIs you care about?",
            "Who is the audience for the analysis results?"
        ],
        tags=["data", "analysis", "visualization", "insights"],
        estimated_iterations=6
    ),

    "ml-model": ProjectTemplate(
        id="ml-model",
        name="Machine Learning Model",
        description="Train and deploy a machine learning model",
        category="Data Science",
        suggested_brief="Build a machine learning model for prediction or classification",
        end_transformation="From data to trained and deployable ML model",
        roadmap=[
            {"name": "Problem Definition", "description": "Define ML task type, success metrics, and constraints", "priority": 1, "depends_on": []},
            {"name": "Data Preparation", "description": "Clean, transform, and split data for training", "priority": 2, "depends_on": ["Problem Definition"]},
            {"name": "Feature Engineering", "description": "Create and select relevant features", "priority": 3, "depends_on": ["Data Preparation"]},
            {"name": "Model Selection", "description": "Choose and implement candidate algorithms", "priority": 4, "depends_on": ["Feature Engineering"]},
            {"name": "Training & Tuning", "description": "Train models and optimize hyperparameters", "priority": 5, "depends_on": ["Model Selection"]},
            {"name": "Evaluation", "description": "Evaluate performance and validate results", "priority": 6, "depends_on": ["Training & Tuning"]},
            {"name": "Deployment", "description": "Package and deploy model for inference", "priority": 7, "depends_on": ["Evaluation"]}
        ],
        clarifying_questions=[
            "What are you trying to predict or classify?",
            "What data do you have available?",
            "How will the model be used (batch, real-time, API)?",
            "What accuracy/performance is acceptable?",
            "Any constraints (interpretability, latency, size)?"
        ],
        tags=["ml", "machine-learning", "ai", "model"],
        estimated_iterations=8
    ),

    # Code Quality
    "refactor": ProjectTemplate(
        id="refactor",
        name="Code Refactoring",
        description="Improve code quality, structure, and maintainability",
        category="Code Quality",
        suggested_brief="Refactor codebase to improve readability and maintainability",
        end_transformation="From messy code to clean, well-structured codebase",
        roadmap=[
            {"name": "Code Audit", "description": "Identify code smells, technical debt, and problem areas", "priority": 1, "depends_on": []},
            {"name": "Test Coverage", "description": "Add tests before refactoring to ensure safety", "priority": 2, "depends_on": ["Code Audit"]},
            {"name": "Extract Functions", "description": "Break down large functions into smaller units", "priority": 3, "depends_on": ["Test Coverage"]},
            {"name": "Improve Naming", "description": "Rename variables, functions, and classes for clarity", "priority": 3, "depends_on": ["Test Coverage"]},
            {"name": "Remove Duplication", "description": "Extract common code into reusable functions", "priority": 4, "depends_on": ["Extract Functions"]},
            {"name": "Simplify Logic", "description": "Reduce complexity and improve readability", "priority": 5, "depends_on": ["Remove Duplication"]},
            {"name": "Documentation", "description": "Add comments and update documentation", "priority": 6, "depends_on": ["Simplify Logic"]}
        ],
        clarifying_questions=[
            "Which files or modules need refactoring?",
            "What are the main pain points with the current code?",
            "Do you have existing tests?",
            "Any coding standards or style guides to follow?",
            "Are there performance concerns to address?"
        ],
        tags=["refactor", "clean-code", "technical-debt", "quality"],
        estimated_iterations=6
    ),

    "bug-fix": ProjectTemplate(
        id="bug-fix",
        name="Bug Investigation & Fix",
        description="Systematically investigate and fix a bug",
        category="Code Quality",
        suggested_brief="Investigate, reproduce, and fix the reported bug",
        end_transformation="From broken behavior to working feature",
        roadmap=[
            {"name": "Reproduce Bug", "description": "Create reliable steps to reproduce the issue", "priority": 1, "depends_on": []},
            {"name": "Isolate Cause", "description": "Identify the root cause through debugging", "priority": 2, "depends_on": ["Reproduce Bug"]},
            {"name": "Design Fix", "description": "Plan the fix approach and consider side effects", "priority": 3, "depends_on": ["Isolate Cause"]},
            {"name": "Implement Fix", "description": "Apply the fix with minimal changes", "priority": 4, "depends_on": ["Design Fix"]},
            {"name": "Write Test", "description": "Add regression test to prevent recurrence", "priority": 5, "depends_on": ["Implement Fix"]},
            {"name": "Verify & Document", "description": "Verify fix works and document the solution", "priority": 6, "depends_on": ["Write Test"]}
        ],
        clarifying_questions=[
            "What is the expected behavior vs actual behavior?",
            "When did this bug first appear?",
            "Can you provide steps to reproduce?",
            "What have you already tried?",
            "Are there any error messages or logs?"
        ],
        tags=["bug", "debug", "fix", "investigation"],
        estimated_iterations=5
    ),

    # Features
    "new-feature": ProjectTemplate(
        id="new-feature",
        name="New Feature",
        description="Add a new feature to an existing codebase",
        category="Features",
        suggested_brief="Design and implement a new feature",
        end_transformation="From feature idea to working implementation",
        roadmap=[
            {"name": "Requirements", "description": "Define feature scope and acceptance criteria", "priority": 1, "depends_on": []},
            {"name": "Design", "description": "Plan architecture and interface design", "priority": 2, "depends_on": ["Requirements"]},
            {"name": "Implementation", "description": "Write the core feature code", "priority": 3, "depends_on": ["Design"]},
            {"name": "Integration", "description": "Connect feature to existing codebase", "priority": 4, "depends_on": ["Implementation"]},
            {"name": "Testing", "description": "Write unit and integration tests", "priority": 5, "depends_on": ["Integration"]},
            {"name": "Polish", "description": "Handle edge cases and improve UX", "priority": 6, "depends_on": ["Testing"]}
        ],
        clarifying_questions=[
            "What should this feature do?",
            "Who will use this feature?",
            "How does it fit with existing functionality?",
            "Any UI/UX requirements?",
            "What's the priority and timeline?"
        ],
        tags=["feature", "enhancement", "development"],
        estimated_iterations=6
    ),

    # Documentation
    "documentation": ProjectTemplate(
        id="documentation",
        name="Documentation",
        description="Create comprehensive documentation for a project",
        category="Documentation",
        suggested_brief="Write clear and complete documentation",
        end_transformation="From undocumented to fully documented project",
        roadmap=[
            {"name": "Audit Current Docs", "description": "Review existing documentation and identify gaps", "priority": 1, "depends_on": []},
            {"name": "README & Quickstart", "description": "Write introduction and getting started guide", "priority": 2, "depends_on": ["Audit Current Docs"]},
            {"name": "API Reference", "description": "Document all public APIs and interfaces", "priority": 3, "depends_on": ["Audit Current Docs"]},
            {"name": "Tutorials", "description": "Create step-by-step guides for common tasks", "priority": 4, "depends_on": ["README & Quickstart"]},
            {"name": "Architecture Docs", "description": "Document system design and decisions", "priority": 4, "depends_on": ["Audit Current Docs"]},
            {"name": "Review & Polish", "description": "Review for clarity, consistency, and completeness", "priority": 5, "depends_on": ["Tutorials", "Architecture Docs"]}
        ],
        clarifying_questions=[
            "Who is the target audience (developers, users, both)?",
            "What documentation already exists?",
            "Any specific topics that need coverage?",
            "Preferred documentation format (Markdown, Sphinx, etc.)?",
            "Are there code examples to include?"
        ],
        tags=["docs", "documentation", "readme", "guide"],
        estimated_iterations=5
    ),

    # Testing
    "test-suite": ProjectTemplate(
        id="test-suite",
        name="Test Suite",
        description="Create a comprehensive test suite for a project",
        category="Testing",
        suggested_brief="Build automated tests for quality assurance",
        end_transformation="From untested to well-tested codebase",
        roadmap=[
            {"name": "Test Strategy", "description": "Define testing approach and coverage goals", "priority": 1, "depends_on": []},
            {"name": "Test Infrastructure", "description": "Set up testing framework and utilities", "priority": 2, "depends_on": ["Test Strategy"]},
            {"name": "Unit Tests", "description": "Write tests for individual functions/methods", "priority": 3, "depends_on": ["Test Infrastructure"]},
            {"name": "Integration Tests", "description": "Test component interactions", "priority": 4, "depends_on": ["Unit Tests"]},
            {"name": "E2E Tests", "description": "Test complete user flows", "priority": 5, "depends_on": ["Integration Tests"]},
            {"name": "CI Integration", "description": "Set up automated test runs in CI/CD", "priority": 6, "depends_on": ["E2E Tests"]}
        ],
        clarifying_questions=[
            "What testing framework do you use (or prefer)?",
            "What's the current test coverage?",
            "Which areas are most critical to test?",
            "Do you need mocking for external services?",
            "Any CI/CD pipeline to integrate with?"
        ],
        tags=["testing", "tests", "quality", "ci"],
        estimated_iterations=6
    ),

    # CLI Tools
    "cli-tool": ProjectTemplate(
        id="cli-tool",
        name="CLI Tool",
        description="Build a command-line interface tool",
        category="Tools",
        suggested_brief="Create a CLI tool with commands and options",
        end_transformation="From idea to polished command-line tool",
        roadmap=[
            {"name": "Command Design", "description": "Define commands, arguments, and options", "priority": 1, "depends_on": []},
            {"name": "CLI Framework", "description": "Set up argument parsing and help system", "priority": 2, "depends_on": ["Command Design"]},
            {"name": "Core Commands", "description": "Implement main functionality", "priority": 3, "depends_on": ["CLI Framework"]},
            {"name": "Input/Output", "description": "Handle input validation and output formatting", "priority": 4, "depends_on": ["Core Commands"]},
            {"name": "Configuration", "description": "Add config file support and defaults", "priority": 5, "depends_on": ["Core Commands"]},
            {"name": "Packaging", "description": "Make installable via pip/npm/etc.", "priority": 6, "depends_on": ["Configuration"]}
        ],
        clarifying_questions=[
            "What is the main purpose of this CLI tool?",
            "What commands/subcommands do you need?",
            "What language/framework (Python Click, Node Commander, etc.)?",
            "Any interactive prompts needed?",
            "How will users install it?"
        ],
        tags=["cli", "command-line", "tool", "utility"],
        estimated_iterations=6
    ),
}


class ProjectTemplateLibrary:
    """
    Manager for project templates.
    Provides access to built-in and custom templates.
    """

    def __init__(self, memory=None):
        self.memory = memory
        self.templates: Dict[str, ProjectTemplate] = dict(BUILTIN_TEMPLATES)
        self._load_custom_templates()

    def _load_custom_templates(self):
        """Load custom templates from memory."""
        if self.memory:
            try:
                custom = self.memory.retrieve_persistent("custom_templates")
                if custom:
                    for tid, tdata in custom.items():
                        self.templates[tid] = ProjectTemplate(**tdata)
            except Exception:
                pass

    def _save_custom_templates(self):
        """Save custom templates to memory."""
        if self.memory:
            custom = {
                tid: {
                    "id": t.id,
                    "name": t.name,
                    "description": t.description,
                    "category": t.category,
                    "suggested_brief": t.suggested_brief,
                    "end_transformation": t.end_transformation,
                    "roadmap": t.roadmap,
                    "clarifying_questions": t.clarifying_questions,
                    "tags": t.tags,
                    "estimated_iterations": t.estimated_iterations
                }
                for tid, t in self.templates.items()
                if tid not in BUILTIN_TEMPLATES
            }
            self.memory.store_persistent("custom_templates", custom)

    def list_templates(self, category: Optional[str] = None) -> str:
        """List available templates, optionally filtered by category."""
        templates = self.templates.values()

        if category:
            templates = [t for t in templates if t.category.lower() == category.lower()]

        if not templates:
            return "No templates found."

        # Group by category
        by_category: Dict[str, List[ProjectTemplate]] = {}
        for t in templates:
            if t.category not in by_category:
                by_category[t.category] = []
            by_category[t.category].append(t)

        output = "**Available Project Templates:**\n\n"

        for cat, temps in sorted(by_category.items()):
            output += f"**{cat}**\n"
            for t in temps:
                output += f"  `{t.id}` - {t.name}\n"
                output += f"    {t.description}\n"
            output += "\n"

        output += "**Usage:** `/project template <template-id>` or `/project template <id> <customization>`"
        return output

    def get_template(self, template_id: str) -> Optional[ProjectTemplate]:
        """Get a template by ID, with fuzzy matching."""
        # Exact match
        if template_id in self.templates:
            return self.templates[template_id]

        # Fuzzy match by ID or name
        template_id_lower = template_id.lower()
        for tid, template in self.templates.items():
            if template_id_lower in tid.lower() or template_id_lower in template.name.lower():
                return template

        return None

    def get_template_details(self, template_id: str) -> str:
        """Get detailed information about a template."""
        template = self.get_template(template_id)
        if not template:
            return f"Template `{template_id}` not found. Use `/templates` to see available templates."

        output = f"**Template: {template.name}**\n\n"
        output += f"*{template.description}*\n\n"
        output += f"**Category:** {template.category}\n"
        output += f"**Tags:** {', '.join(template.tags)}\n"
        output += f"**Estimated Iterations:** {template.estimated_iterations}\n\n"

        output += f"**End Transformation:**\n{template.end_transformation}\n\n"

        output += "**Roadmap:**\n"
        for i, task in enumerate(template.roadmap, 1):
            deps = f" (depends on: {', '.join(task['depends_on'])})" if task['depends_on'] else ""
            output += f"  {i}. {task['name']}{deps}\n"
            output += f"     {task['description']}\n"

        output += "\n**Clarifying Questions:**\n"
        for i, q in enumerate(template.clarifying_questions, 1):
            output += f"  {i}. {q}\n"

        output += f"\n**Use this template:** `/project template {template.id}`"
        return output

    def create_project_from_template(
        self,
        template_id: str,
        customization: str = ""
    ) -> Optional[Dict]:
        """
        Create project configuration from a template.
        Returns a dict suitable for GDIL project creation.
        """
        template = self.get_template(template_id)
        if not template:
            return None

        # Combine template with customization
        initial_input = template.description
        if customization:
            initial_input = f"{template.description}: {customization}"

        return {
            "template_id": template.id,
            "template_name": template.name,
            "initial_input": initial_input,
            "suggested_brief": template.suggested_brief + (f" - {customization}" if customization else ""),
            "end_transformation": template.end_transformation,
            "roadmap": [dict(task) for task in template.roadmap],  # Deep copy
            "clarifying_questions": list(template.clarifying_questions),
            "estimated_iterations": template.estimated_iterations,
            "customization": customization
        }

    def add_custom_template(self, template: ProjectTemplate) -> bool:
        """Add a custom template."""
        if template.id in BUILTIN_TEMPLATES:
            return False  # Can't override built-ins

        self.templates[template.id] = template
        self._save_custom_templates()
        return True

    def remove_custom_template(self, template_id: str) -> bool:
        """Remove a custom template."""
        if template_id in BUILTIN_TEMPLATES:
            return False  # Can't remove built-ins

        if template_id in self.templates:
            del self.templates[template_id]
            self._save_custom_templates()
            return True
        return False

    def get_categories(self) -> List[str]:
        """Get list of all template categories."""
        return sorted(set(t.category for t in self.templates.values()))

    def search_templates(self, query: str) -> List[ProjectTemplate]:
        """Search templates by keyword."""
        query_lower = query.lower()
        results = []

        for template in self.templates.values():
            # Search in name, description, tags
            if (query_lower in template.name.lower() or
                query_lower in template.description.lower() or
                any(query_lower in tag for tag in template.tags)):
                results.append(template)

        return results
