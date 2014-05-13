
from django.forms.forms import Form
from django import forms
from django.forms.widgets import Textarea

class ResponseForm(Form):
    response = forms.CharField(widget=Textarea)
    
#class UserForm(Form):
    
    
