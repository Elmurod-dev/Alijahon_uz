from django.core.exceptions import ValidationError
from django.forms import Form, CharField,HiddenInput

from apps.models import User


class UserForm(Form):
    first_name = CharField(max_length=50,required=False)
    last_name = CharField(max_length=50,required=False)
    region=CharField(max_length=50,required=False)
    district=CharField(max_length=50,required=False)
    address=CharField(max_length=50,required=False)
    telegram_id=CharField(max_length=50,required=False)
    bio=CharField(max_length=50,required=False)

class UpdatePasswordForm(Form):
    user=CharField(max_length=50,widget=HiddenInput)
    old_password=CharField(max_length=50,required=True)
    new_password=CharField(max_length=50,required=True)
    confirm_password=CharField(max_length=50,required=True)

    def clean_old_password(self):
        user=User.objects.filter(phone_number=self.cleaned_data['user'],password=self.cleaned_data['old_password'])
        if not user:
            raise ValidationError("error")
        return self.cleaned_data['old_password']

class SearchForm(Form):
    search_field=CharField(max_length=50,required=True)





