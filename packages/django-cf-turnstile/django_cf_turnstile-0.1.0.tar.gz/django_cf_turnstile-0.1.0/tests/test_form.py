from unittest import mock

from django import forms
from django.test import TestCase

from django_cf_turnstile import client
from django_cf_turnstile.fields import (
    TEST_SECRET_KEY,
    TEST_SITE_KEY,
    TurnstileCaptchaField,
)


class TestTurnstileCaptchaField(TestCase):

    class TestForm(forms.Form):
        captcha = TurnstileCaptchaField()

    @mock.patch.object(client, "post_form")
    def test_captcha_valid_token(self, mock_post_form):
        # Simulate a successful response from Cloudflare
        mock_post_form.return_value = (200, {"success": True, "error-codes": []})
        form_data = {"cf-turnstile-response": "valid-token-from-frontend"}
        form = self.TestForm(form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["captcha"], "valid-token-from-frontend")

        # Check if client.post_form was called with expected data
        expected_data = {
            "secret": TEST_SECRET_KEY,
            "response": "valid-token-from-frontend",
            "remoteip": mock.ANY,
        }
        mock_post_form.assert_called_once_with(
            url="https://challenges.cloudflare.com/turnstile/v0/siteverify",
            data_dict=expected_data,
            as_json=True,
        )

    @mock.patch.object(client, "post_form")
    def test_captcha_invalid_token(self, mock_post_form):
        # Simulate an invalid token response from Cloudflare
        mock_post_form.return_value = (
            200,
            {"success": False, "error-codes": ["invalid-input-response"]},
        )
        form_data = {"cf-turnstile-response": "invalid-token"}
        form = self.TestForm(form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("captcha", form.errors)
        self.assertEqual(
            form.errors["captcha"],
            [TurnstileCaptchaField.default_error_messages["captcha_invalid"]],
        )

    @mock.patch.object(client, "post_form")
    def test_captcha_api_error_no_json_body(self, mock_post_form):
        # Simulate an API error where no JSON body is returned
        mock_post_form.return_value = (500, None)
        form_data = {"cf-turnstile-response": "some-token"}
        form = self.TestForm(form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("captcha", form.errors)
        self.assertEqual(
            form.errors["captcha"],
            [TurnstileCaptchaField.default_error_messages["captcha_error"]],
        )

    @mock.patch.object(client, "post_form")
    def test_captcha_api_error_malformed_json(self, mock_post_form):
        # Simulate an API error with malformed JSON (e.g., missing 'success')
        mock_post_form.return_value = (
            200,
            {"error-codes": ["bad-request"]},
        )  # 'success' key is missing
        form_data = {"cf-turnstile-response": "some-token"}
        form = self.TestForm(form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("captcha", form.errors)
        self.assertEqual(
            form.errors["captcha"],
            [TurnstileCaptchaField.default_error_messages["captcha_error"]],
        )

    def test_captcha_missing_token_required(self):
        # Test when the token is missing (field is required by default)
        form_data = {}  # No captcha token provided
        form = self.TestForm(form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("captcha", form.errors)
        # The error message for 'required' is overridden in the field
        self.assertEqual(
            form.errors["captcha"],
            [TurnstileCaptchaField.default_error_messages["required"]],
        )

    @mock.patch.object(
        TurnstileCaptchaField, "get_remote_ip", return_value="123.123.123.123"
    )
    @mock.patch.object(client, "post_form")
    def test_captcha_sends_remote_ip(self, mock_post_form, mock_get_ip):
        mock_post_form.return_value = (200, {"success": True, "error-codes": []})
        form_data = {"cf-turnstile-response": "valid-token"}
        form = self.TestForm(form_data)
        self.assertTrue(form.is_valid())  # Process the form

        # Check that get_remote_ip was called
        mock_get_ip.assert_called_once()

        # Check that the IP from get_remote_ip was included in the data sent
        args, kwargs = mock_post_form.call_args
        sent_data = kwargs.get("data_dict", {})
        self.assertEqual(sent_data.get("remoteip"), "123.123.123.123")
