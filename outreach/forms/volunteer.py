from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

from outreach.models import Volunteer

class VolunteerProfileForm(forms.ModelForm):
    class Meta:
        model = Volunteer
        fields = (
            "first_name",
            "last_name",
            "email",
            "phone",
            "equipment_owned",
        )

        widgets = {
            "equipment_owned": forms.Textarea(attrs={"rows": 4}),
        }