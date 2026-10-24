
from django import forms
from django.contrib.auth.password_validation import validate_password

from .models import User


class RegistrationForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
        validators=[validate_password],
    )
    password2 = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput,
    )

    class Meta:
        model = User
        fields = ["name", "email"]

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "An account with this email already exists."
            )

        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1:
            if len(password1) < 8:
                self.add_error(
                    "password1",
                    "Password must be at least 8 characters long."
                )

            if not any(char.isalpha() for char in password1):
                self.add_error(
                    "password1",
                    "Password must contain at least one letter."
                )

            if not any(char.isdigit() for char in password1):
                self.add_error(
                    "password1",
                    "Password must contain at least one digit."
                )

        if password1 and password2 and password1 != password2:
            self.add_error(
                "password2",
                "The passwords do not match."
            )

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])

        if commit:
            user.save()

        return user
from django import forms
from .models import User


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["name", "email"]

    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        existing_users = User.objects.filter(
            email__iexact=email
        ).exclude(pk=self.instance.pk)

        if existing_users.exists():
            raise forms.ValidationError(
                "This email address is already in use."
            )

        return email