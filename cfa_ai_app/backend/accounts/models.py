from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

class Client(models.Model):
    name = models.CharField(max_length=255, unique=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class TallyTransaction(models.Model):
    REGISTER_CHOICES = [
        ('sales', 'Sales'),
        ('purchase', 'Purchase'),
        ('payment', 'Payment'),
        ('receipt', 'Receipt'),
        ('journal', 'Journal'),
        ('credit_note', 'Credit Note'),
        ('debit_note', 'Debit Note'),
    ]
    
    # Tally data fields
    voucher_no = models.CharField(max_length=100)
    date = models.DateField()
    party_name = models.CharField(max_length=255)  # Client name from Tally
    narration = models.TextField(blank=True, null=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    register_type = models.CharField(max_length=20, choices=REGISTER_CHOICES)
    
    # Grouping fields
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='transactions', null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['party_name']),
            models.Index(fields=['register_type']),
            models.Index(fields=['date']),
            models.Index(fields=['client']),
        ]
    
    def __str__(self):
        return f"{self.party_name} - {self.voucher_no} ({self.register_type})"

class LedgerEntry(models.Model):
    transaction = models.ForeignKey('TallyTransaction', on_delete=models.CASCADE, related_name='ledger_entries')
    ledger_name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    is_debit = models.BooleanField()
    is_credit = models.BooleanField()
    raw_data = models.JSONField(default=dict)  # Store all original ledger entry fields

    def __str__(self):
        return f"{self.ledger_name}: {self.amount} ({'Dr' if self.is_debit else 'Cr'})"

class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, username, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('employee', 'Employee'),
    ]
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='users', null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee')
    is_active = models.BooleanField(default=True)  # type: ignore
    is_staff = models.BooleanField(default=False)  # type: ignore
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f"{self.email} ({self.role})"

class LedgerOpeningBalance(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='opening_balances')
    ledger_name = models.CharField(max_length=255)
    opening_balance = models.DecimalField(max_digits=15, decimal_places=2)
    group = models.CharField(max_length=255, blank=True)
    raw_balance = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.client.name} - {self.ledger_name}: {self.opening_balance}"

class Token(models.Model):
    key = models.CharField(max_length=40, unique=True)
    user = models.ForeignKey(User, related_name='auth_tokens', on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Token for {self.user.email}: {self.key}"

    class Meta:
        verbose_name = "Token"
        verbose_name_plural = "Tokens"
