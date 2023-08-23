from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from hasker.forms import AnswerForm, QuestionForm
from hasker.models.hasker import Answer, Question, Tag, Vote

QUESTIONS_ON_PAGE = 20
ANSWERS_ON_PAGE = 30


def index(request):
    query = request.GET.get('q', '')
    if query:
        q = query.split(':')
        if len(q) > 1:
            attr, value = q
            if attr == 'tag':
                qs_filter = Q(tags__title=value.lower())
            elif attr == 'author':
                qs_filter = Q(author__username=value)
            else:
                qs_filter = Q()
        else:
            value = q[0]
            qs_filter = Q(title__contains=value) | Q(text__contains=value)
        objects_list = Question.objects.filter(qs_filter)
    else:
        objects_list = Question.objects.all()
    order = request.GET.get('o', 'new')
    if order == 'hot':
        objects_list = objects_list.order_by('-rating')
    else:
        objects_list = objects_list.order_by('-created_at')
    paginator = Paginator(objects_list, QUESTIONS_ON_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj, 'object_list': page_obj, 'paginator': paginator, 'query': query,
               'order': order, 'is_paginated': True if page_obj.has_other_pages() else False}
    return render(request, 'index.html', context)


@login_required
def ask(request):
    if request.method == 'GET':
        form = QuestionForm()
        return render(request, 'question_create.html', context={'form': form})
    elif request.method == 'POST':
        with transaction.atomic():
            form = QuestionForm(request.POST)
            question: Question = form.save(commit=False)
            question.author = request.user
            question.save()
            tag_list = form.cleaned_data.get('tag', '').split(',')
            for tag_name in tag_list[:3]:
                if tag_name:
                    tag, _ = Tag.objects.get_or_create(title=tag_name.strip().lower())
                    question.tags.add(tag)
        url = reverse('question_detail', kwargs={'pk': question.pk})
        return HttpResponseRedirect(url)
    return HttpResponseBadRequest


def question_detail(request, *args, **kwargs):
    context = {}
    pk = kwargs.get('pk')
    question = get_object_or_404(Question, pk=pk)
    if request.user.is_authenticated:
        _question_rating_handle(request, question)
    answers = question.get_answers()
    paginator = Paginator(answers, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context.update({'object': question,
                    'answers': page_obj,
                    'page_obj': page_obj,
                    'paginator': paginator,
                    })
    if page_obj.has_other_pages():
        context['is_paginated'] = True
    else:
        context['is_paginated'] = False

    if request.method == 'POST' and request.user.is_authenticated:
        form = AnswerForm(request.POST)
        if not form.is_valid():
            context.update({'form': form})
            return render(request, 'question_detail.html', context=context)
        answer = form.cleaned_data.get('answer')
        if answer:
            new_answer = Answer.objects.create(
                    question=question,
                    text=answer,
                    author=request.user,
            )
            return HttpResponseRedirect(reverse('question_detail', args=(question.pk,)))
    form = AnswerForm()
    context.update({'form': form})
    return render(request, 'question_detail.html', context=context)


def _question_rating_handle(request, question):
    answer_pk = request.GET.get('right_answer')
    action = request.GET.get('rating')
    if answer_pk and question.author == request.user:
        try:
            answer = Answer.objects.get(pk=int(answer_pk))
        except Answer.DoesNotExist:
            return
        else:
            with transaction.atomic():
                Answer.objects.filter(question=question, is_right=True).update(is_right=False)
                answer.is_right = True
                answer.save()
        return
    if action and action in ('up', 'down'):
        attr = 'question'
        object = question
        answer_pk = request.GET.get('answer')
        if answer_pk:
            try:
                answer = Answer.objects.get(pk=int(answer_pk))
            except Answer.DoesNotExist:
                return
            attr = 'answer'
            object = answer
        request_data = {'author': request.user, attr: object}
        with transaction.atomic():
            try:
                if action == 'up':
                    Vote.objects.create(**request_data)
                    object.rating += 1
                    object.save()
                else:
                    Vote.objects.get(**request_data).delete()
                    object.rating -= 1
                    if object.rating < 0:
                        object.rating = 0
                    object.save()
            except (IntegrityError, Vote.DoesNotExist):
                pass
