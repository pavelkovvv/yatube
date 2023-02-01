from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()


class CreationForm(UserCreationForm):
    '''
    Класс для формы регистрации.
    Является наследником предустановленного класса UserCreationForm.
    '''
    class Meta(UserCreationForm.Meta):
        # Модель, с которой связана создаваемая форма
        model = User
        # Какие поля должны быть видны в форме
        fields = ('first_name', 'last_name', 'username', 'email')
