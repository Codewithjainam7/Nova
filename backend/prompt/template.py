from typing import Dict, Optional, List
from backend.prompt.schema import PromptType, PromptTemplate
from backend.core.logger import app_logger

class PromptVersionManager:
    def __init__(self):
        self._versions: Dict[str, List[PromptTemplate]] = {}

    def add_version(self, template: PromptTemplate):
        if template.name not in self._versions:
            self._versions[template.name] = []
        self._versions[template.name].append(template)

    def get_latest_version(self, name: str) -> Optional[PromptTemplate]:
        versions = self._versions.get(name, [])
        if not versions:
            return None
        # Naive version resolution, assuming sorted or just taking the last added
        return versions[-1]

class PromptTemplateRegistry:
    def __init__(self, version_manager: PromptVersionManager):
        self._templates: Dict[PromptType, str] = {}
        self.version_manager = version_manager

    def register(self, prompt_type: PromptType, template_name: str):
        self._templates[prompt_type] = template_name

    def get_template(self, prompt_type: PromptType) -> Optional[PromptTemplate]:
        template_name = self._templates.get(prompt_type)
        if not template_name:
            return None
        return self.version_manager.get_latest_version(template_name)

class PromptTemplateLoader:
    """Simulates loading templates from disk or database."""
    def __init__(self, registry: PromptTemplateRegistry):
        self.registry = registry

    def load_defaults(self):
        # Dummy default templates for testing
        t1 = PromptTemplate(
            template_id="t-001",
            name="default_planning",
            version="1.0.0",
            content="Plan for user request: {user_input}\nContext:\n{context_text}",
            required_variables=["user_input", "context_text"]
        )
        t2 = PromptTemplate(
            template_id="t-002",
            name="default_conversation",
            version="1.0.0",
            content="Answer the user: {user_input}\nHistory:\n{history_text}",
            required_variables=["user_input", "history_text"]
        )
        
        self.registry.version_manager.add_version(t1)
        self.registry.version_manager.add_version(t2)
        
        self.registry.register(PromptType.PLANNING, "default_planning")
        self.registry.register(PromptType.CONVERSATION, "default_conversation")
        app_logger.info("Loaded default prompt templates.")
