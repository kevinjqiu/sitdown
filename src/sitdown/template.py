from jinja2 import Template


def render(template_text: str, **kwargs) -> str:
    """
    Renders a Jinja2 template string with the provided context variables.

    Args:
        template_text (str): The template text in Jinja2 format
        **kwargs: Variable keyword arguments that will be passed as context to the template

    Returns:
        str: The rendered template string
    """
    template = Template(template_text)
    return template.render(**kwargs)
