from django import forms
from django.core.exceptions import ValidationError

from hasker.models.hasker import Question


class BootstrapMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'


class QuestionForm(BootstrapMixin, forms.ModelForm):
    tag = forms.CharField(label='Tags', help_text='3 tags max', required=False)

    class Meta:
        model = Question
        fields = ('title', 'text')
        widgets = {
            'text': forms.Textarea(attrs={'rows': 5}),
            'tag': forms.TextInput,
        }

    def clean_tag(self):
        text = self.cleaned_data['tag']
        if len(text.split(',')) > 3:
            raise ValidationError('3 tags max')
        return text


class AnswerForm(BootstrapMixin, forms.Form):
    answer = forms.CharField(label='Answer', widget=(forms.Textarea(attrs={'required': True, 'rows': 5})))



