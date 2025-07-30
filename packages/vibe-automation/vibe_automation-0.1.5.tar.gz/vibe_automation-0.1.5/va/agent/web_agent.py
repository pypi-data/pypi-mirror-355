import os
from pydantic import BaseModel

from anthropic.types import TextBlock
import anthropic


class PageElement(BaseModel):
    id: str
    iframe_path: str | None


def serialize_accessibility_tree_to_html(tree: dict, indent: int = 0) -> str:
    """
    Serialize accessibility tree to HTML-like structure for more efficient LLM consumption.

    Args:
        tree: The accessibility tree dictionary
        indent: Current indentation level for pretty printing

    Returns:
        HTML-like string representation of the accessibility tree
    """
    if not tree:
        return ""

    def escape_html(text: str) -> str:
        """Escape HTML special characters."""
        if not text:
            return text
        return (
            str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
        )

    role = tree.get("role", "generic")
    name = tree.get("name", "")
    attributes = tree.get("attributes", {})
    children = tree.get("children", [])

    # Start building the HTML tag
    indent_str = "  " * indent
    tag_parts = [f"<{role}"]

    # Add tf623_id as the primary identifier
    if "tf623_id" in attributes:
        tag_parts.append(f' va_id="{attributes["tf623_id"]}"')

    # Add name as title attribute if present
    if name:
        escaped_name = escape_html(name)
        tag_parts.append(f' title="{escaped_name}"')

    # Add other relevant attributes
    for attr, value in attributes.items():
        if attr == "tf623_id":
            continue  # Already handled as id
        if value and str(value).strip():
            escaped_value = escape_html(str(value))
            tag_parts.append(f' {attr}="{escaped_value}"')

    # Close opening tag
    opening_tag = "".join(tag_parts) + ">"

    # Handle children
    if children:
        result = [f"{indent_str}{opening_tag}"]
        # Process children
        for child in children:
            child_html = serialize_accessibility_tree_to_html(child, indent + 1)
            if child_html:
                result.append(child_html)
        result.append(f"{indent_str}</{role}>")
        return "\n".join(result)
    else:
        # Self-closing or text content
        if name:
            escaped_name_content = escape_html(name)
            return f"{indent_str}{opening_tag}{escaped_name_content}</{role}>"
        else:
            return f"{indent_str}{opening_tag}</{role}>"


def locate_element_prompt(prompt: str, accessibility_tree: dict) -> str:
    html_structure = serialize_accessibility_tree_to_html(accessibility_tree)
    return f"""
Given the following HTML structure, find the element that matches user's instruction. 
 
User's instruction: {prompt}
 
HTML structure:
{html_structure}
 
Only return the element ID (va_id attribute) without any other content without any quote. If the element cannot be found, return empty string.
    """


class WebAgent:
    """
    Base agent class for general browser automation.

    Takes a browser instance and uses Claude to perform dynamic actions based on goals.

    Base class sets up the anthropic client, and provides basic functionality like taking screenshots
    """

    def __init__(self):
        """
        Create a new GenericAgent instance.
        """
        self.model = "claude-3-7-sonnet-20250219"
        self.max_iterations = 100  # Maximum number of actions to prevent infinite loops

        # Use API key from environment variable if not provided
        anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")

        if not anthropic_api_key:
            raise ValueError(
                "Claude API key not provided. Please provide it via the api_key parameter "
                "or set the ANTHROPIC_API_KEY environment variable."
            )

        self.client = anthropic.Anthropic(api_key=anthropic_api_key)

    def query_element(
        self, prompt: str, accessibility_tree: dict
    ) -> PageElement | None:
        text_prompt = locate_element_prompt(prompt, accessibility_tree)
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system="""Find an element that best matches user's instruction""",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": text_prompt,
                        }
                    ],
                }
            ],
        )
        for block in response.content:
            if block.type == "text":
                if isinstance(block, TextBlock):
                    content = block.text
                    continue
        element_id = content if content else None
        return PageElement(id=element_id, iframe_path=None)
