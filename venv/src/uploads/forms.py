from django import forms

from uploads.models import Document


class DocumentForm(forms.ModelForm):
    description = forms.CharField(widget=forms.Textarea)
    class Meta:
        model = Document
        fields = ('description', 'document' )
