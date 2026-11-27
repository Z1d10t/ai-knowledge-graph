"""Prompt factory and centralized prompt registry for the knowledge graph system."""

from .community_prompts import (
    COMMUNITY_NAMING_SYSTEM_PROMPT,
    get_community_naming_user_prompt,
)
from .entity_prompts import (
    ENTITY_RESOLUTION_SYSTEM_PROMPT,
    get_entity_resolution_user_prompt,
)
from .inference_prompts import (
    BRIDGE_INFERENCE_SYSTEM_PROMPT,
    HUB_INFERENCE_SYSTEM_PROMPT,
    RELATIONSHIP_INFERENCE_SYSTEM_PROMPT,
    WITHIN_COMMUNITY_INFERENCE_SYSTEM_PROMPT,
    get_bridge_inference_user_prompt,
    get_hub_inference_user_prompt,
    get_relationship_inference_user_prompt,
    get_within_community_inference_user_prompt,
)
from .main_prompts import (
    MATERIALS_SYSTEM_PROMPT,
    MATERIALS_USER_PROMPT,
    MATERIALS_V3_SYSTEM_PROMPT,
    MATERIALS_V3_USER_PROMPT,
    MAIN_SYSTEM_PROMPT,
    MAIN_USER_PROMPT,
)
from .query_prompts import (
    ENTITY_PICK_SYSTEM_PROMPT,
    QUERY_SYSTEM_PROMPT,
    get_entity_pick_user_prompt,
    get_query_user_prompt,
)

__all__ = [
    "PromptFactory",
    "prompt_factory",
    "language_instruction",
    "system_prompt_for",
    "main_prompt_pair",
    "MAIN_SYSTEM_PROMPT",
    "MAIN_USER_PROMPT",
    "MATERIALS_SYSTEM_PROMPT",
    "MATERIALS_USER_PROMPT",
    "MATERIALS_V3_SYSTEM_PROMPT",
    "MATERIALS_V3_USER_PROMPT",
    "ENTITY_RESOLUTION_SYSTEM_PROMPT",
    "get_entity_resolution_user_prompt",
    "RELATIONSHIP_INFERENCE_SYSTEM_PROMPT",
    "get_relationship_inference_user_prompt",
    "WITHIN_COMMUNITY_INFERENCE_SYSTEM_PROMPT",
    "get_within_community_inference_user_prompt",
    "BRIDGE_INFERENCE_SYSTEM_PROMPT",
    "get_bridge_inference_user_prompt",
    "HUB_INFERENCE_SYSTEM_PROMPT",
    "get_hub_inference_user_prompt",
    "COMMUNITY_NAMING_SYSTEM_PROMPT",
    "get_community_naming_user_prompt",
    "QUERY_SYSTEM_PROMPT",
    "get_query_user_prompt",
    "ENTITY_PICK_SYSTEM_PROMPT",
    "get_entity_pick_user_prompt",
]


class PromptFactory:
    """
    A general-purpose prompt registry and generator.

    - Store prompt generator functions or static strings in `self.prompts`.
    - Retrieve prompts dynamically using get_prompt(name, *args, **kwargs).
    - Supports static string templates as well as callables that accept arguments.
    """

    def __init__(self):
        self.prompts = {
            "main_system": MAIN_SYSTEM_PROMPT,
            "main_user": MAIN_USER_PROMPT,
            "main_system_materials": MATERIALS_SYSTEM_PROMPT,
            "main_user_materials": MATERIALS_USER_PROMPT,
            "main_system_materials_v3": MATERIALS_V3_SYSTEM_PROMPT,
            "main_user_materials_v3": MATERIALS_V3_USER_PROMPT,

            "entity_resolution_system": ENTITY_RESOLUTION_SYSTEM_PROMPT,
            "entity_resolution_user": get_entity_resolution_user_prompt,

            "relationship_inference_system": RELATIONSHIP_INFERENCE_SYSTEM_PROMPT,
            "relationship_inference_user": get_relationship_inference_user_prompt,
            "within_community_system": WITHIN_COMMUNITY_INFERENCE_SYSTEM_PROMPT,
            "within_community_user": get_within_community_inference_user_prompt,

            "bridge_inference_system": BRIDGE_INFERENCE_SYSTEM_PROMPT,
            "bridge_inference_user": get_bridge_inference_user_prompt,
            "hub_inference_system": HUB_INFERENCE_SYSTEM_PROMPT,
            "hub_inference_user": get_hub_inference_user_prompt,
            "community_naming_system": COMMUNITY_NAMING_SYSTEM_PROMPT,
            "community_naming_user": get_community_naming_user_prompt,
            "query_system": QUERY_SYSTEM_PROMPT,
            "query_user": get_query_user_prompt,
            "entity_pick_system": ENTITY_PICK_SYSTEM_PROMPT,
            "entity_pick_user": get_entity_pick_user_prompt,
        }

    def get_prompt(self, name: str, *args, **kwargs) -> str:
        """
        Retrieve and optionally format a prompt.

        Args:
            name (str): Registered prompt key.
            *args: Positional args passed to the prompt generator (if callable).
            **kwargs: Keyword args passed to the generator (if callable).

        Returns:
            str: The generated prompt text.
        """
        if name not in self.prompts:
            raise ValueError(f"Prompt '{name}' not found in PromptFactory.")

        prompt_entry = self.prompts[name]

        if callable(prompt_entry):
            return prompt_entry(*args, **kwargs)

        return prompt_entry


prompt_factory = PromptFactory()


def language_instruction(language):
    """Extra system-prompt sentence for non-English output; empty for 'auto'/English/unset."""
    if not language or str(language).strip().lower() in ("auto", "en", "english"):
        return ""
    return (f"\nIMPORTANT: Write all entity names, entity types' values excluded, predicates and community names "
            f"in {str(language).strip()}. Keep the JSON keys in English.")


def system_prompt_for(name, config):
    """Fetch a system prompt and append the configured language instruction (``extraction.language``)."""
    language = (config or {}).get("extraction", {}).get("language", "auto")
    return prompt_factory.get_prompt(name) + language_instruction(language)


def main_prompt_pair(config):
    """Return the ``(system_prompt, user_prompt)`` pair for the active profile.

    The materials profile defaults to the v3 (term-first) prompt as of the terminology
    review; ``[extraction].prompt_version = "v2"`` restores the earlier fact-first prompt
    for reproducing historical runs.
    """
    profile = str(((config or {}).get("profile") or {}).get("name", "generic")).strip().lower()
    suffix = "_materials" if profile == "materials" else ""
    version = str(((config or {}).get("extraction") or {}).get("prompt_version") or "").strip().lower()
    if profile == "materials" and version != "v2":
        suffix += "_v3"
    system = system_prompt_for("main_system" + suffix, config)
    return system, prompt_factory.get_prompt("main_user" + suffix)
