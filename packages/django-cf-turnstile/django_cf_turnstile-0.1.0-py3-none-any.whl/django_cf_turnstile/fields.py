import logging
import sys

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from django_cf_turnstile import client
from django_cf_turnstile.widgets import TurnstileImplicitWidget

logger = logging.getLogger(__name__)


# https://developers.cloudflare.com/turnstile/troubleshooting/testing/
TEST_SITE_KEY = "1x00000000000000000000AA"
TEST_SECRET_KEY = "1x0000000000000000000000000000000AA"


class TurnstileCaptchaField(forms.CharField):
    widget = TurnstileImplicitWidget
    default_error_messages = {
        "captcha_invalid": _("Error verifying CAPTCHA, please try again."),
        "captcha_error": _("Error verifying CAPTCHA, please try again."),
        "required": _("Error verifying CAPTCHA, please try again."),
    }

    def __init__(self, site_key=None, secret_key=None, label="", *args, **kwargs):
        super().__init__(label=label, *args, **kwargs)

        self.required = True
        self.site_key = site_key or getattr(
            settings, "CF_TURNSTILE_SITE_KEY", TEST_SITE_KEY
        )
        self.secret_key = secret_key or getattr(
            settings, "CF_TURNSTILE_SECRET_KEY", TEST_SECRET_KEY
        )

        # Update widget attrs with data-sitekey.
        self.widget.attrs["data-sitekey"] = self.site_key

    def get_remote_ip(self):
        f = sys._getframe()
        while f:
            request = f.f_locals.get("request")
            if request:
                remote_ip = request.META.get("REMOTE_ADDR", "")
                forwarded_ip = request.META.get("HTTP_X_FORWARDED_FOR", "")
                ip = remote_ip if not forwarded_ip else forwarded_ip
                return ip
            f = f.f_back

    def validate(self, value):
        super().validate(value)

        data = {
            "secret": self.secret_key,
            "response": value,
            "remoteip": self.get_remote_ip(),
        }

        status, json_body = client.post_form(
            url="https://challenges.cloudflare.com/turnstile/v0/siteverify",
            data_dict=data,
            as_json=True,
        )

        if json_body is None:
            # We failed to get a response
            raise ValidationError(
                self.error_messages["captcha_error"], code="captcha_error"
            )

        success = json_body.get("success")
        error_code = next(iter(json_body.get("error-codes")), "captcha_error")

        if success is None or not isinstance(success, bool):
            logger.info("Captcha validation failed due to: %s" % error_code)
            raise ValidationError(self.error_messages["captcha_error"], code=error_code)

        elif success is False:
            raise ValidationError(
                self.error_messages["captcha_invalid"], code=error_code
            )
