from django import forms
from django.forms import ModelForm, inlineformset_factory

from .models import Position, PositionSkillRequirement, Skill, Tag

class PositionStep1Form(ModelForm):
    """Step 1: core Position fields (title, company, description, status, tags)."""
    class Meta:
        model = Position
        fields = ['title', 'company', 'description', 'status', 'tags']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'tags':        forms.CheckboxSelectMultiple(),
        }

class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ['name', 'category']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Skill name',
            }),
            'category': forms.Select(attrs={
                'class': 'form-select',
            }),
        }

class TagForm(forms.ModelForm):
    """AJAX “create new tag” mini‐form."""
    class Meta:
        model = Tag
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'New tag name'
            }),
        }

# Step 2 inline formset for PositionSkillRequirement:
PositionSkillFormSet = inlineformset_factory(
    Position,
    PositionSkillRequirement,
    fields=('skill', 'level_pct', 'importance'),
    extra=1,
    can_delete=True,
    widgets={
        'level_pct': forms.NumberInput(attrs={'min': 0, 'max': 100, 'step': 10}),
    }
)
