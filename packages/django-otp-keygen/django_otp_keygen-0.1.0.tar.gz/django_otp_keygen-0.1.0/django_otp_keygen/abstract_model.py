from django.conf import settings
from django.contrib.auth.hashers import (
    check_password as check_otp,
    make_password as hash_otp,
)
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from django_otp_keygen.constants import OtpStatus
from django_otp_keygen.otp import OTP
from django_otp_keygen.utils import get_otp_expiry_time, get_otp_type_choices


class AbstractOtp(models.Model):
    """
    Abstract model for OTP keys.
    """

    _otp = models.CharField(
        max_length=255,
        editable=False,
        verbose_name=_("OTP"),
        help_text=_("The Protected OTP instance."),
        db_column="otp",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="otps",
        verbose_name=_("User"),
        help_text=_("The user associated with this OTP key."),
    )
    key = models.CharField(
        max_length=255,
        verbose_name=_("Key"),
        help_text=_("The OTP key used for authentication."),
    )
    otp_type = models.CharField(
        max_length=50,
        choices=get_otp_type_choices(),
        verbose_name=_("OTP Type"),
        help_text=_(
            "The type of OTP key. This can be Email, SMS, Registration, or Login."
        ),
    )
    expired_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Expired At"),
        help_text=_("The date and time when the OTP key expires.(in seconds)"),
    )
    status = models.CharField(
        max_length=20,
        choices=OtpStatus.choices,
        default=OtpStatus.PENDING,
        verbose_name=_("Status"),
        help_text=_("The status of the OTP key, e.g., Pending & Verified."),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
        help_text=_("The date and time when the OTP key was created."),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At"),
        help_text=_("The date and time when the OTP key was last updated."),
    )

    class Meta:
        abstract = True
        verbose_name = _("OTP Key")
        verbose_name_plural = _("OTP Keys")
        unique_together = ("user", "otp_type", "key")

    @property
    def otp(self):
        """
        Get the protected OTP instance.
        This property should be overridden in the concrete model to return the actual OTP value.
        """
        return self._otp

    @otp.setter
    def otp(self, value):
        """
        Set the protected OTP instance.
        This property should be overridden in the concrete model to set the actual OTP value.
        """
        self._otp = hash_otp(value)
        self.save()

    @property
    def is_expired(self) -> bool:
        """
        Check if the OTP key is expired.

        :returns: bool, True if the OTP key is expired, False otherwise.
        """
        return self.expired_at and now() > self.expired_at

    @property
    def is_verified(self):
        """
        Check if the OTP key is verified.
        """
        return self.status == OtpStatus.VERIFIED

    @property
    def is_pending(self):
        """
        Check if the OTP key is pending.
        """
        return self.status == OtpStatus.PENDING

    @property
    def is_active(self):
        """
        Check if the OTP key is active.
        """
        return not self.is_expired and self.is_verified

    def set_expired(self):
        """
        Set the OTP key as expired.
        """
        self.expired_at = get_otp_expiry_time()

    def save(self, **kwargs):
        """
        Override the save method to set the expired_at field if not provided.
        """
        if not self.expired_at:
            self.set_expired()
        super().save(**kwargs)

    def generate_otp(self):
        """
        Generate a new OTP.
        """
        return OTP(key=self.key).now()

    def validate_otp(self, otp) -> bool:
        """
        Validate the provided OTP.

        :param otp: str, The OTP to validate.
        :returns: bool, True if the OTP is valid, False otherwise.
        :raises ValidationError: If the OTP is already expired or already verified.
        """
        if self.is_expired:
            raise ValidationError(
                _("The OTP is already expired, please request a new one.")
            )
        if self.is_verified:
            raise ValidationError(_("The OTP is already verified."))
        if check_otp(otp, self._otp) and self.otp:
            self.status = OtpStatus.VERIFIED
            self.save()
            return True
        return False

    def __str__(self):
        """
        String representation of the OTP key.
        """
        return f"{self.user.username} - {self.otp_type} - {self.status}"
