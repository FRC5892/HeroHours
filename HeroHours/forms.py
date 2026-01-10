from django import forms
import django.contrib.auth.models as authModels


class CustomActionForm(forms.Form):
    """Form for creating custom staff user actions in admin panel"""
    username = forms.CharField(label='Username', max_length=100)
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    group_name = forms.ChoiceField(label='Group Name', required=True)
    # Get group choices and set the default option as "Group"
    def __init__(self, *args, **kwargs):
        super(CustomActionForm, self).__init__(*args, **kwargs)
        # Query the groups here at runtime, instead of during the class definition
        group_choices = [(group.name, group.name) for group in authModels.Group.objects.all()]
        group_choices.insert(0, ('', 'Group'))  # Add the default option at the beginning

        self.fields['group_name'].choices = group_choices  # Set the choices for the field

    hidden_data = forms.CharField(widget=forms.HiddenInput(), required=False)