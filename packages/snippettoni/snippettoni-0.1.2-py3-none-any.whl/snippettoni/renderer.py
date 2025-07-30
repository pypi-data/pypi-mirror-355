from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, Template, select_autoescape


class SnippetRenderer:
    TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
    ENV = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(),
    )

    def __init__(
        self,
        languages: list[str] | None = None,
        external_templates: dict[str, str] | None = None,
    ):
        self.external_templates = self.load_overridden_templates(external_templates or {})
        available_languages = self.available_languages()
        if languages:
            languages = [language.lower() for language in languages]
            unsupported_languages = set(languages) - set(available_languages)
            if unsupported_languages:
                raise Exception(f"Unsupported language(s): {', '.join(unsupported_languages)}")
            self.languages = languages
        else:
            self.languages = list(available_languages)

    def load_overridden_templates(self, overrides: dict[str, Any]) -> dict[str, Template]:
        templates_map = {}
        for language, template in overrides.items():
            template_path = Path(template).expanduser().resolve()
            if not template_path.exists() or not template_path.is_file():
                raise FileNotFoundError(f"Template not found: {template_path}.")
            with open(template_path) as f:
                templates_map[language.lower()] = self.ENV.from_string(f.read())
        return templates_map

    def available_languages(self) -> set[str]:
        return set(
            [template.stem for template in self.TEMPLATE_DIR.glob("*.j2")]
            + list(self.external_templates.keys())
        )

    def get_snippets(
        self,
        method: str,
        url: str,
        headers: dict[str, str] | None,
        body: dict[str, Any] | None,
    ) -> dict[str, str]:
        snippets = {}
        for language in self.languages:
            if language in self.external_templates:
                template = self.external_templates[language]
            else:
                template = self.ENV.get_template(f"{language}.j2")
            snippets[language] = template.render(
                {
                    "method": method,
                    "url": url,
                    "headers": headers,
                    "body": body,
                }
            )
        return snippets
