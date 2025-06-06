from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

class ExcelUploadForm(forms.Form):
    excel_file = forms.FileField(
        label='Select an Excel file',
        help_text='Only .xlsx files with a single sheet are supported.'
    )

class UserRegistrationForm(UserCreationForm):
    """
    Form for user registration.
    Extends Django's built-in UserCreationForm.
    """
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',) # You can add more fields if needed

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Tailwind classes to form fields for consistent styling
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'appearance-none block w-full bg-gray-50 text-gray-700 border border-gray-300 rounded-lg py-3 px-4 leading-tight focus:outline-none focus:bg-white focus:border-blue-500'
            })


class UserLoginForm(AuthenticationForm):
    """
    Form for user login.
    Extends Django's built-in AuthenticationForm.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Tailwind classes to form fields for consistent styling
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'appearance-none block w-full bg-gray-50 text-gray-700 border border-gray-300 rounded-lg py-3 px-4 leading-tight focus:outline-none focus:bg-white focus:border-blue-500'
            })
