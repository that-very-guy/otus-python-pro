from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views import generic

from .forms import RegisterUserForm, UpdateUserForm, UserProfileForm

AUTH_USER = get_user_model()


class RegisterView(generic.View):
    template_name = 'account/register.html'

    def get(self, request, **kwargs):
        form = RegisterUserForm()
        return render(request, self.template_name, context={'form': form})

    def post(self, request, **kwargs):
        form = RegisterUserForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('account:login'))
        else:
            return render(request, self.template_name, context={'form': form})


class ProfileView(LoginRequiredMixin, generic.View):
    template_name = 'account/profile.html'

    def get(self, request, **kwargs):
        u_form = UpdateUserForm(instance=request.user)
        p_form = UserProfileForm(instance=request.user.profile)
        return render(request, self.template_name, context={'u_form': u_form, 'p_form': p_form})

    def post(self, request, **kwargs):
        u_form = UpdateUserForm(request.POST, instance=request.user)
        p_form = UserProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            if u_form.has_changed():
                u_form.save()
            if p_form.has_changed():
                profile = p_form.save(commit=False)
                profile.save()
            return render(request, self.template_name, context={'u_form': u_form, 'p_form': p_form})
