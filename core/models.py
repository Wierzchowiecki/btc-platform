from django.conf import settings
from django.db import models
from django.utils import timezone
import secrets


class BtcPrice(models.Model):
    date = models.DateField(primary_key=True)
    price_pln = models.DecimalField(max_digits=18, decimal_places=2)
    volume = models.BigIntegerField(null=True, blank=True)
    source = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "btc_price"
        managed = False


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    client_id = models.CharField(max_length=10, unique=True)
    must_set_password = models.BooleanField(default=True)

    otp_code = models.CharField(max_length=128, null=True, blank=True)
    otp_expires_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def generate_client_id() -> str:
        # 10 cyfr, unikalne (sprawdzamy w bazie w pętli)
        while True:
            cid = "".join(secrets.choice("0123456789") for _ in range(10))
            if not UserProfile.objects.filter(client_id=cid).exists():
                return cid

    def otp_is_valid(self, otp: str) -> bool:
        if not self.otp_code or not self.otp_expires_at:
            return False
        if timezone.now() > self.otp_expires_at:
            return False
        return otp == self.otp_code
