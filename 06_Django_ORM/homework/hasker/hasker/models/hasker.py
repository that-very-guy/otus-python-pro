from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse

from hasker.models.managers import QuestionManager

AUTH_USER = get_user_model()


class BaseModel(models.Model):
    created_at = models.DateTimeField('Pub date', auto_now_add=True, editable=False)
    rating = models.PositiveIntegerField('Rating', default=0, editable=False)

    class Meta:
        abstract = True


class Question(BaseModel):
    title = models.CharField('Title', help_text='Title', max_length=254, db_index=True)
    text = models.TextField('Text', help_text='Text')
    tags = models.ManyToManyField('Tag', related_name='questions', blank=True)
    author = models.ForeignKey(AUTH_USER, verbose_name='Author', on_delete=models.PROTECT, related_name='questions')

    objects = QuestionManager()

    def get_answers(self):
        return self.answers.order_by('-is_right', '-rating', 'created_at')


class Answer(BaseModel):
    text = models.TextField('Text')
    question = models.ForeignKey('Question', verbose_name='Question', on_delete=models.CASCADE, related_name='answers')
    author = models.ForeignKey(AUTH_USER, verbose_name='Author', on_delete=models.PROTECT, related_name='answers')
    is_right = models.BooleanField('Best', default=False)

    def __str__(self):
        return self.text

    def get_absolute_url(self):
        return reverse('question_detail', args=(self.pk,))


class Tag(models.Model):
    title = models.CharField('Tag', max_length=48, unique=True)

    def __str__(self):
        return self.title.lower()


class Vote(models.Model):
    author = models.ForeignKey(AUTH_USER, on_delete=models.DO_NOTHING)
    question = models.ForeignKey('Question', on_delete=models.CASCADE, null=True, related_name='question_votes')
    answer = models.ForeignKey('Answer', on_delete=models.CASCADE, null=True, related_name='answer_votes')

    class Meta:
        constraints = (
            models.UniqueConstraint(name='unique_vote_user_question', fields=('author', 'question')),
            models.UniqueConstraint(name='unique_vote_user_answer', fields=('author', 'answer')),
        )
