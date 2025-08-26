# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import User, StudentCV, CVExperience, CVLanguage
from django.forms import modelformset_factory
import datetime

class StudentRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "password1", "password2")


# CV main form (StudentCV)
class CVForm(forms.ModelForm):
    class Meta:
        model = StudentCV
        fields = ['full_name', 'email', 'phone', 'address', 'objective']
        widgets = {
            'address': forms.Textarea(attrs={'rows':3, 'class': 'form-control'}),
            'objective': forms.Textarea(attrs={'rows':4, 'class': 'form-control'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email') or ''
        return email.strip()


# Top 10 languages (order starts with English, French, Arabic, Spanish as requested)
LANGUAGE_CHOICES = [
    ('', '--- Select language ---'),
    ('English', 'English'),
    ('French', 'French'),
    ('Arabic', 'Arabic'),
    ('Spanish', 'Spanish'),
    ('Chinese (Mandarin)', 'Chinese (Mandarin)'),
    ('Russian', 'Russian'),
    ('Portuguese', 'Portuguese'),
    ('German', 'German'),
    ('Hindi', 'Hindi'),
    ('Bengali', 'Bengali'),
    ('Other', 'Other (specify)'),
]


# Experience form with validation (start <= end)
class CVExperienceForm(forms.ModelForm):
    class Meta:
        model = CVExperience
        fields = ['job_title', 'company', 'city', 'country', 'start_date', 'end_date', 'description']
        widgets = {
            'job_title': forms.TextInput(attrs={'class':'form-control'}),
            'company': forms.TextInput(attrs={'class':'form-control'}),
            'city': forms.TextInput(attrs={'class':'form-control'}),
            'country': forms.TextInput(attrs={'class':'form-control'}),
            'start_date': forms.DateInput(attrs={'type':'date', 'class':'form-control'}),
            'end_date': forms.DateInput(attrs={'type':'date', 'class':'form-control'}),
            'description': forms.Textarea(attrs={'rows':3, 'class':'form-control'}),
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get('start_date')
        end   = cleaned.get('end_date')
        if start and end and start > end:
            raise ValidationError("Start date must be before or equal to end date.")
        # don't allow future start dates (simple sanity check)
        if start and start > datetime.date.today():
            raise ValidationError("Start date cannot be in the future.")
        return cleaned


# Language form (CEFR choices + language select widget)
class CVLanguageForm(forms.ModelForm):
    # override the 'language' field to use a select with our top languages
    language = forms.ChoiceField(choices=LANGUAGE_CHOICES, required=True,
                                 widget=forms.Select(attrs={'class':'form-select language-select'}))

    class Meta:
        model = CVLanguage
        fields = ['language', 'mother_tongue', 'listening', 'reading', 'spoken_interaction', 'spoken_production', 'writing']
        widgets = {
            'mother_tongue': forms.CheckboxInput(attrs={'class':'form-check-input'}),
            'listening': forms.Select(attrs={'class':'form-select'}),
            'reading': forms.Select(attrs={'class':'form-select'}),
            'spoken_interaction': forms.Select(attrs={'class':'form-select'}),
            'spoken_production': forms.Select(attrs={'class':'form-select'}),
            'writing': forms.Select(attrs={'class':'form-select'}),
        }

    def clean(self):
        cleaned = super().clean()
        lang = cleaned.get('language')
        if not lang:
            raise ValidationError("Language name is required.")
        return cleaned


# formset factories to use in view
CVExperienceFormSet = modelformset_factory(
    CVExperience,
    form=CVExperienceForm,
    extra=0,
    can_delete=True
)

CVLanguageFormSet = modelformset_factory(
    CVLanguage,
    form=CVLanguageForm,
    extra=0,
    can_delete=True
)
