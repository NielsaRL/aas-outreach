from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

from outreach.models import EventVolunteer, Volunteer


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


class EventVolunteerSignupForm(forms.ModelForm):
    class Meta:
        model = EventVolunteer
        fields = (
            "role",
            "telescope_count",
            "notes",
        )

        widgets = {
            "role": forms.RadioSelect(
                attrs={
                    "class": "form-check-input",
                }
            ),
            "telescope_count": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0,
                    "step": 1,
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Anything the host should know?",
                }
            ),
        }

        labels = {
            "role": "How would you like to help?",
            "telescope_count": "How many telescopes are you bringing?",
            "notes": "Notes",
        }

    def clean(self):
        cleaned_data = super().clean()

        role = cleaned_data.get("role")
        telescope_count = cleaned_data.get("telescope_count")

        if role == "TELESCOPE":
            if telescope_count is None or telescope_count < 1:
                self.add_error(
                    "telescope_count",
                    "Please enter how many telescopes you are bringing.",
                )
        else:
            cleaned_data["telescope_count"] = None

        return cleaned_data