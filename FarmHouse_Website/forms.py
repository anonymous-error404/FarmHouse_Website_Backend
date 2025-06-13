from django import forms

from FarmHouse_Website.models import Bookings


class BookingAdminForm(forms.ModelForm):
    image = forms.ImageField(required=True)

    class Meta:
        model = Bookings
        fields = '__all__'

    def save(self, commit=False):
        instance = super().save(commit=False)
        uploaded_image = self.cleaned_data.get('image')
        if uploaded_image:
            instance.IDimage = uploaded_image.read()
            commit = True
        if commit:
            instance.save()
        return instance
