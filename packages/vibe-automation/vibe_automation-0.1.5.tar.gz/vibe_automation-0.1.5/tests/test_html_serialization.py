from va.agent.web_agent import serialize_accessibility_tree_to_html


class TestHTMLSerialization:
    """Test cases for accessibility tree HTML serialization."""

    def test_empty_tree(self):
        """Test serialization of empty tree."""
        result = serialize_accessibility_tree_to_html({})
        assert result == ""

    def test_none_tree(self):
        """Test serialization of None tree."""
        result = serialize_accessibility_tree_to_html(None)
        assert result == ""

    def test_simple_element_with_name(self):
        """Test serialization of simple element with name."""
        tree = {"role": "button", "name": "Click me", "attributes": {"tf623_id": "123"}}
        result = serialize_accessibility_tree_to_html(tree)
        expected = '<button va_id="123" title="Click me">Click me</button>'
        assert result == expected

    def test_simple_element_without_name(self):
        """Test serialization of simple element without name."""
        tree = {"role": "div", "attributes": {"tf623_id": "456"}}
        result = serialize_accessibility_tree_to_html(tree)
        expected = '<div va_id="456"></div>'
        assert result == expected

    def test_element_with_multiple_attributes(self):
        """Test serialization of element with multiple attributes."""
        tree = {
            "role": "input",
            "name": "Username",
            "attributes": {
                "tf623_id": "789",
                "type": "text",
                "placeholder": "Enter username",
                "required": "true",
            },
        }
        result = serialize_accessibility_tree_to_html(tree)
        expected = '<input va_id="789" title="Username" type="text" placeholder="Enter username" required="true">Username</input>'
        assert result == expected

    def test_element_with_escaped_attributes(self):
        """Test proper escaping of quotes in attributes."""
        tree = {
            "role": "button",
            "name": 'Click "Submit" button',
            "attributes": {
                "tf623_id": "999",
                "data-tooltip": "This is a 'special' button",
            },
        }
        result = serialize_accessibility_tree_to_html(tree)
        expected = '<button va_id="999" title="Click &quot;Submit&quot; button" data-tooltip="This is a &#39;special&#39; button">Click &quot;Submit&quot; button</button>'
        assert result == expected

    def test_nested_elements(self):
        """Test serialization of nested elements."""
        tree = {
            "role": "form",
            "name": "Login Form",
            "attributes": {"tf623_id": "100"},
            "children": [
                {
                    "role": "textbox",
                    "name": "Username",
                    "attributes": {"tf623_id": "101", "type": "text"},
                },
                {
                    "role": "textbox",
                    "name": "Password",
                    "attributes": {"tf623_id": "102", "type": "password"},
                },
                {
                    "role": "button",
                    "name": "Login",
                    "attributes": {"tf623_id": "103", "type": "submit"},
                },
            ],
        }
        result = serialize_accessibility_tree_to_html(tree)
        expected = """<form va_id="100" title="Login Form">
  <textbox va_id="101" title="Username" type="text">Username</textbox>
  <textbox va_id="102" title="Password" type="password">Password</textbox>
  <button va_id="103" title="Login" type="submit">Login</button>
</form>"""
        assert result == expected

    def test_deeply_nested_elements(self):
        """Test serialization of deeply nested elements."""
        tree = {
            "role": "navigation",
            "attributes": {"tf623_id": "200"},
            "children": [
                {
                    "role": "list",
                    "attributes": {"tf623_id": "201"},
                    "children": [
                        {
                            "role": "listitem",
                            "attributes": {"tf623_id": "202"},
                            "children": [
                                {
                                    "role": "link",
                                    "name": "Home",
                                    "attributes": {"tf623_id": "203", "href": "/home"},
                                }
                            ],
                        }
                    ],
                }
            ],
        }
        result = serialize_accessibility_tree_to_html(tree)
        expected = """<navigation va_id="200">
  <list va_id="201">
    <listitem va_id="202">
      <link va_id="203" title="Home" href="/home">Home</link>
    </listitem>
  </list>
</navigation>"""
        assert result == expected

    def test_element_with_empty_attributes(self):
        """Test serialization handles empty or None attribute values."""
        tree = {
            "role": "div",
            "name": "Test",
            "attributes": {
                "tf623_id": "300",
                "empty_attr": "",
                "none_attr": None,
                "valid_attr": "value",
                "whitespace_attr": "   ",
            },
        }
        result = serialize_accessibility_tree_to_html(tree)
        # Should only include non-empty attributes
        expected = '<div va_id="300" title="Test" valid_attr="value">Test</div>'
        assert result == expected

    def test_element_without_tf623_id(self):
        """Test serialization of element without tf623_id."""
        tree = {
            "role": "text",
            "name": "Some text content",
            "attributes": {"class": "text-content"},
        }
        result = serialize_accessibility_tree_to_html(tree)
        expected = '<text title="Some text content" class="text-content">Some text content</text>'
        assert result == expected

    def test_mixed_children_with_and_without_names(self):
        """Test serialization of parent with mix of named and unnamed children."""
        tree = {
            "role": "section",
            "attributes": {"tf623_id": "400"},
            "children": [
                {"role": "heading", "name": "Title", "attributes": {"tf623_id": "401"}},
                {"role": "div", "attributes": {"tf623_id": "402"}},
                {
                    "role": "paragraph",
                    "name": "Some text content",
                    "attributes": {"tf623_id": "403"},
                },
            ],
        }
        result = serialize_accessibility_tree_to_html(tree)
        expected = """<section va_id="400">
  <heading va_id="401" title="Title">Title</heading>
  <div va_id="402"></div>
  <paragraph va_id="403" title="Some text content">Some text content</paragraph>
</section>"""
        assert result == expected

    def test_generic_role_fallback(self):
        """Test that elements without role get 'generic' role."""
        tree = {"name": "No role specified", "attributes": {"tf623_id": "500"}}
        result = serialize_accessibility_tree_to_html(tree)
        expected = (
            '<generic va_id="500" title="No role specified">No role specified</generic>'
        )
        assert result == expected

    def test_custom_indentation(self):
        """Test serialization with custom indentation level."""
        tree = {"role": "button", "name": "Test", "attributes": {"tf623_id": "600"}}
        result = serialize_accessibility_tree_to_html(tree, indent=2)
        expected = '    <button va_id="600" title="Test">Test</button>'
        assert result == expected

    def test_iframe_content_serialization(self):
        """Test serialization of iframe-like structure with nested content."""
        tree = {
            "role": "iframe",
            "attributes": {"tf623_id": "700", "src": "embedded-content.html"},
            "children": [
                {
                    "role": "document",
                    "attributes": {"tf623_id": "701"},
                    "children": [
                        {
                            "role": "button",
                            "name": "Embedded Button",
                            "attributes": {"tf623_id": "702"},
                        }
                    ],
                }
            ],
        }
        result = serialize_accessibility_tree_to_html(tree)
        expected = """<iframe va_id="700" src="embedded-content.html">
  <document va_id="701">
    <button va_id="702" title="Embedded Button">Embedded Button</button>
  </document>
</iframe>"""
        assert result == expected

    def test_complex_form_structure(self):
        """Test serialization of complex form with various input types."""
        tree = {
            "role": "form",
            "name": "Contact Form",
            "attributes": {"tf623_id": "800", "method": "post"},
            "children": [
                {
                    "role": "group",
                    "name": "Personal Information",
                    "attributes": {"tf623_id": "801"},
                    "children": [
                        {
                            "role": "textbox",
                            "name": "First Name",
                            "attributes": {"tf623_id": "802", "required": "true"},
                        },
                        {
                            "role": "textbox",
                            "name": "Email",
                            "attributes": {"tf623_id": "803", "type": "email"},
                        },
                    ],
                },
                {
                    "role": "listbox",
                    "name": "Country",
                    "attributes": {"tf623_id": "804"},
                    "children": [
                        {
                            "role": "option",
                            "name": "United States",
                            "attributes": {"tf623_id": "805", "value": "us"},
                        },
                        {
                            "role": "option",
                            "name": "Canada",
                            "attributes": {"tf623_id": "806", "value": "ca"},
                        },
                    ],
                },
                {
                    "role": "button",
                    "name": "Submit",
                    "attributes": {"tf623_id": "807", "type": "submit"},
                },
            ],
        }
        result = serialize_accessibility_tree_to_html(tree)
        expected = """<form va_id="800" title="Contact Form" method="post">
  <group va_id="801" title="Personal Information">
    <textbox va_id="802" title="First Name" required="true">First Name</textbox>
    <textbox va_id="803" title="Email" type="email">Email</textbox>
  </group>
  <listbox va_id="804" title="Country">
    <option va_id="805" title="United States" value="us">United States</option>
    <option va_id="806" title="Canada" value="ca">Canada</option>
  </listbox>
  <button va_id="807" title="Submit" type="submit">Submit</button>
</form>"""
        assert result == expected

    def test_edge_cases_with_special_characters(self):
        """Test serialization with various special characters and edge cases."""
        tree = {
            "role": "text",
            "name": "Special chars: <>&\"'",
            "attributes": {
                "tf623_id": "900",
                "data-content": "Contains <tags> & \"quotes\" and 'apostrophes'",
            },
        }
        result = serialize_accessibility_tree_to_html(tree)
        expected = '<text va_id="900" title="Special chars: &lt;&gt;&amp;&quot;&#39;" data-content="Contains &lt;tags&gt; &amp; &quot;quotes&quot; and &#39;apostrophes&#39;">Special chars: &lt;&gt;&amp;&quot;&#39;</text>'
        assert result == expected
