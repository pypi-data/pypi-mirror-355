from django import forms
from django.test import TestCase

from django_cf_turnstile.fields import (
    TEST_SECRET_KEY,
    TEST_SITE_KEY,
    TurnstileCaptchaField,
)


class CaptchaSignupForm(forms.Form):
    captcha = TurnstileCaptchaField()


class CustomCaptchaSignupForm(forms.Form):
    captcha = TurnstileCaptchaField(
        label="TestCaptcha", site_key="CUSTOM_SITE_KEY", secret_key="CUSTOM_SECRET_KEY"
    )


class CaptchaFormRenderTest(TestCase):
    def test_form_renders_script(self):
        form = CaptchaSignupForm()
        rendered_form = form.as_p()

        script = '<script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>'
        self.assertIn(script, rendered_form)

    def test_form_renders_turnstile_widget(self):
        form = CaptchaSignupForm()
        rendered_form = form.as_p()

        widget_div = '<div class="cf-turnstile"'
        self.assertIn(widget_div, rendered_form)

        sitekey_attr = f'data-sitekey="{TEST_SITE_KEY}"'
        self.assertIn(sitekey_attr, rendered_form)

    def test_form_does_not_leak_secret(self):
        form = CaptchaSignupForm()
        rendered_form = form.as_p()

        self.assertNotIn(TEST_SECRET_KEY, rendered_form)

    def test_form_no_labels(self):
        form = CaptchaSignupForm()
        rendered_form = form.as_p()

        self.assertNotIn("<label", rendered_form)

    def test_form_field_overrides(self):
        form = CustomCaptchaSignupForm()
        rendered_form = form.as_p()

        label = '<label for="id_captcha">TestCaptcha:</label>'
        self.assertIn(label, rendered_form)

        sitekey_attr = f'data-sitekey="CUSTOM_SITE_KEY"'
        self.assertIn(sitekey_attr, rendered_form)
