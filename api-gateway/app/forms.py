from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User


class GatewayAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="Tên đăng nhập",
        widget=forms.TextInput(
            attrs={
                "class": "field-input",
                "placeholder": "Nhập tên đăng nhập",
                "autocomplete": "username",
            }
        ),
    )
    password = forms.CharField(
        label="Mật khẩu",
        widget=forms.PasswordInput(
            attrs={
                "class": "field-input",
                "placeholder": "Nhập mật khẩu",
                "autocomplete": "current-password",
            }
        ),
    )


class GatewayRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        label="Email",
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "field-input",
                "placeholder": "Nhập email",
                "autocomplete": "email",
            }
        ),
    )
    first_name = forms.CharField(
        label="Họ và tên",
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "field-input",
                "placeholder": "Nhập họ và tên",
                "autocomplete": "name",
            }
        ),
    )

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Tên đăng nhập"
        self.fields["username"].widget.attrs.update(
            {
                "class": "field-input",
                "placeholder": "Nhập tên đăng nhập",
                "autocomplete": "username",
            }
        )
        self.fields["password1"].label = "Mật khẩu"
        self.fields["password1"].widget.attrs.update(
            {
                "class": "field-input",
                "placeholder": "Nhập mật khẩu",
                "autocomplete": "new-password",
            }
        )
        self.fields["password2"].label = "Nhập lại mật khẩu"
        self.fields["password2"].widget.attrs.update(
            {
                "class": "field-input",
                "placeholder": "Nhập lại mật khẩu",
                "autocomplete": "new-password",
            }
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get("email", "").strip().lower()
        user.first_name = self.cleaned_data.get("first_name", "").strip()
        if commit:
            user.save()
        return user
