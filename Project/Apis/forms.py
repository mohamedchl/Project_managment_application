from django import forms

class ResetPasswordForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'mot de passe'}), min_length=4)
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Confirmer mot de passe'}), min_length=4)

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Les mots de passe ne correspondent pas")