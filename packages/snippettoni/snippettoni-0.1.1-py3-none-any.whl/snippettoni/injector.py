from pathlib import Path
from typing import Any

from prance import ResolvingParser
from prance.util.resolver import RefResolver

from snippettoni.renderer import SnippetRenderer


def extract_auth_headers(
    operation: dict[str, Any],
    global_security: list[dict[str, list[str]]],
    security_schemes: dict[str, Any],
) -> dict[str, str]:
    headers = {}
    security = operation.get("security", global_security)

    for sec_req in security:
        for sec_name in sec_req:
            scheme = security_schemes.get(sec_name, {})
            type_ = scheme.get("type")

            if type_ == "http":
                if scheme.get("scheme") == "bearer":
                    headers["Authorization"] = "Bearer <token>"
                elif scheme.get("scheme") == "basic":
                    headers["Authorization"] = "Basic <base64-credentials>"

            elif type_ == "apiKey" and scheme.get("in") == "header":
                name = scheme.get("name", "X-API-Key")
                headers[name] = "<api_key>"

    return headers


def generate_example_from_schema(schema: dict[str, Any]) -> Any:
    """Improved example generator for OpenAPI JSON Schema."""
    if not isinstance(schema, dict):
        return None
    if "examples" in schema:
        return schema["examples"]
    if "default" in schema:
        return schema["default"]
    if "enum" in schema:
        return schema["enum"][0]

    schema_type = schema.get("type")

    if "oneOf" in schema:
        return generate_example_from_schema(schema["oneOf"][0])
    if "anyOf" in schema:
        return generate_example_from_schema(schema["anyOf"][0])
    if "allOf" in schema:
        merged = {}
        for sub_schema in schema["allOf"]:
            merged.update(sub_schema)
        return generate_example_from_schema(merged)

    if schema_type == "object" or "properties" in schema:
        props = schema.get("properties", {})
        return {k: generate_example_from_schema(v) for k, v in props.items()}

    if schema_type == "array":
        item_schema = schema.get("items", {})
        return [generate_example_from_schema(item_schema)]

    if schema_type == "string":
        fmt = schema.get("format", "")
        return "2025-01-01T12:00:00Z" if fmt == "date-time" else "string"
    if schema_type == "integer":
        return 0
    if schema_type == "number":
        return 0.0
    if schema_type == "boolean":
        return True
    return None


def extract_request_body_example(op: dict[str, Any]) -> Any:
    """Get example from request body or generate it from schema."""
    content = op.get("requestBody", {}).get("content", {})
    app_json = content.get("application/json", {})

    if "example" in app_json:
        return app_json["example"]
    elif "examples" in app_json:
        ex = next(iter(app_json["examples"].values()))
        return ex.get("value")
    elif "schema" in app_json:
        return generate_example_from_schema(app_json["schema"])
    return None


def get_base_url_from_servers(spec):
    if "servers" not in spec or not spec["servers"]:
        return "https://example.com"

    return spec["servers"][0]["url"]


def inject_code_samples(
    source: Path | str | dict,
    renderer: SnippetRenderer,
    base_url: str | None = None,
) -> Any:
    options: dict[str, Any] = {
        "lazy": True,
        "strict": False,
    }
    if isinstance(source, dict):
        resolver = RefResolver(source, url="/", strict=False)
        resolver.resolve_references()
        spec = resolver.specs
    else:
        if isinstance(source, Path):
            options["url"] = str(source.resolve())
        else:
            options["spec_string"] = source

        parser = ResolvingParser(**options)
        parser.parse()
        spec = parser.specification

    if not base_url:
        base_url = get_base_url_from_servers(spec)

    for path, methods in spec.get("paths", {}).items():
        for method in methods:
            op = methods[method]

            headers = {}

            auth_headers = extract_auth_headers(
                op, spec.get("security", []), spec.get("components", {}).get("securitySchemes", {})
            )

            if auth_headers:
                headers.update(auth_headers)

            example_body = None

            if method in ["post", "put", "patch"]:
                example_body = extract_request_body_example(op)
                if example_body:
                    headers["Content-Type"] = "application/json"

            full_url = base_url.rstrip("/") + path
            op["x-codeSamples"] = []
            context = {
                "method": method.upper(),
                "url": full_url,
                "headers": headers,
                "body": example_body,
            }
            snippets = renderer.get_snippets(**context)

            for lang, rendered in snippets.items():
                op["x-codeSamples"].append(
                    {"lang": lang, "label": lang.capitalize(), "source": rendered}
                )

    return spec
