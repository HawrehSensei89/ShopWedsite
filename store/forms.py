from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import get_language
from .i18n import STRINGS
from .models import Profile

def _T():
    return STRINGS["fa" if (get_language() or "fa").startswith("fa") else "en"]

def _relabel(form, mapping):
    T = _T()
    for name, key in mapping.items():
        if name in form.fields:
            form.fields[name].label = T[key]
            form.fields[name].help_text = ""

MAP = {"username": "username", "email": "email", "first_name": "first_name", "last_name": "last_name",
       "password1": "password", "password2": "password2", "password": "password", "phone": "phone", "address": "address"}

class RegisterForm(UserCreationForm):
    email = forms.EmailField()
    class Meta:
        model = User
        fields = ("email",)
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        _relabel(self, MAP)
        self.fields = {k: self.fields[k] for k in ("email", "password1", "password2")}
    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(username__iexact=email).exists() or User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(_T()["email_taken"])
        return email
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = user.username = self.cleaned_data["email"]
        if commit:
            user.save()
        return user

class UserForm(forms.ModelForm):
    email = forms.EmailField()
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
    def __init__(self, *a, **k):
        super().__init__(*a, **k); _relabel(self, MAP)
    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.exclude(pk=self.instance.pk).filter(username__iexact=email).exists():
            raise forms.ValidationError(_T()["email_taken"])
        return email
    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email
        if commit:
            user.save()
        return user

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("phone", "address")
        widgets = {"address": forms.Textarea(attrs={"rows": 3})}
    def __init__(self, *a, **k):
        super().__init__(*a, **k); _relabel(self, MAP)

class LoginForm(AuthenticationForm):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        _relabel(self, MAP)
        self.fields["username"].label = _T()["email"]
        self.fields["username"].widget.attrs.update({"type": "email", "autocomplete": "email"})
        self.error_messages = {**self.error_messages, "invalid_login": _T()["bad_login"]}
    def clean_username(self):
        return self.cleaned_data["username"].strip().lower()
