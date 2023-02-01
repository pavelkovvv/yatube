from django.views.generic import CreateView
from django.urls import reverse_lazy
from .forms import CreationForm


class SignUp(CreateView):
    form_class = CreationForm
    # После успешной регистрации перенаправим пользователя на главную страницу
    success_url = reverse_lazy('posts:index')
    template_name = 'users/signup.html'
