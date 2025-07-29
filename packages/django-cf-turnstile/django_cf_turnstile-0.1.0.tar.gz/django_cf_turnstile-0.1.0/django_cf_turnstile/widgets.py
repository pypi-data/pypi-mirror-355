from django.forms import widgets


class TurnstileBase(widgets.Widget):
    pass


class TurnstileImplicitWidget(TurnstileBase):
    input_type = "text"
    template_name = "turnstile/widget_implicit.html"

    def value_from_datadict(self, data, files, name):
        """
        With implicit rendering the generated captcha field
        will have the name cf-turnstile-response
        """
        return data.get("cf-turnstile-response")
