from django import forms
from django.contrib.auth.forms import UserCreationForm 
from django.contrib.auth.models import User
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from .models import Voucher
from django_recaptcha.fields import ReCaptchaField  # ✅ Add this import
from django_recaptcha.widgets import ReCaptchaV2Checkbox  # ✅ Add this import


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    phonenumber = forms.CharField(max_length=20, required=False)
    email = forms.EmailField(max_length=250, help_text='eg. youremail@gmail.com')
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox)


    honeypot = forms.CharField(required=False, widget=forms.HiddenInput)
    
    def clean_honeypot(self):
        honeypot = self.cleaned_data.get('honeypot')
        if honeypot:
            raise forms.ValidationError("Spam detected.")
        return honeypot
    

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'phonenumber', 'password1', 'password2', 'email')







class ContactForm(forms.Form):
	subject = forms.CharField(max_length=100, required=True)
	name = forms.CharField(max_length=100, required=True)
	from_email = forms.EmailField(max_length=100, required=True)
	message = forms.CharField(
		max_length=500,
		widget=forms.Textarea(),
		help_text='write here your message!'
	)








class VoucherApplyForm(forms.Form):
    code = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter voucher code',
            'id': 'voucher-code-input'
        })
    )

