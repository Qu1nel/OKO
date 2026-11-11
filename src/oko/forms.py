from django import forms
from django.core.exceptions import ValidationError

from oko.models import Card


def require_text(value: str) -> None:
    if not value.strip():
        raise ValidationError("Добавьте текст.", code="blank")


class CardForm(forms.ModelForm):
    question = forms.CharField(
        label="Вопрос",
        widget=forms.Textarea(attrs={"rows": 4}),
        strip=False,
        validators=[require_text],
        error_messages={"required": "Введите вопрос."},
    )
    answer = forms.CharField(
        label="Ответ",
        widget=forms.Textarea(attrs={"rows": 5}),
        strip=False,
        validators=[require_text],
        error_messages={"required": "Введите ответ."},
    )

    class Meta:
        model = Card
        fields = ("title", "question", "answer")
        labels = {"title": "Название карточки"}
        help_texts = {"title": "Необязательно"}
        error_messages = {"title": {"max_length": "Название должно быть не длиннее %(limit_value)d символов."}}
