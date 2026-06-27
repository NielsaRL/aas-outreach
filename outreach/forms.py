from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

from .models import Volunteer


class VolunteerRegistrationForm(forms.Form):
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    email = forms.EmailField()
    phone = forms.CharField(max_length=50, required=False)
    equipment_owned = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text="List any telescopes, binoculars, tables, canopies, lights, or other outreach equipment."
    )

    username = forms.CharField(max_length=150)
    password1 = forms.CharField(widget=forms.PasswordInput, label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm password")

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("That username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A login already exists with that email.")
        return email

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get("password1")
        password2 = cleaned.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match.")

        if password1:
            validate_password(password1)

        return cleaned

    def save(self):
        first_name = self.cleaned_data["first_name"]
        last_name = self.cleaned_data["last_name"]
        email = self.cleaned_data["email"]
        phone = self.cleaned_data["phone"]
        equipment_owned = self.cleaned_data["equipment_owned"]
        username = self.cleaned_data["username"]
        password = self.cleaned_data["password1"]

        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )

        volunteer_name = f"{first_name} {last_name}".strip()

        volunteer = Volunteer.objects.filter(email__iexact=email, user__isnull=True).first()

        if volunteer:
            volunteer.user = user
            if not volunteer.first_name:
                volunteer.first_name = first_name
            if not volunteer.last_name:
                volunteer.last_name = last_name
            volunteer.phone = volunteer.phone or phone
            volunteer.equipment_owned = volunteer.equipment_owned or equipment_owned
            volunteer.active = True
            volunteer.save()
        else:
            volunteer = Volunteer.objects.create(
                user=user,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                equipment_owned=equipment_owned,
                active=True,
            )

        return user