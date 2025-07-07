from django import forms

from FarmHouse_Website import compressor
from FarmHouse_Website.models import *
from FarmHouse_Website_Backend import settings


class BookingAdminForm(forms.ModelForm):
    binary_data = forms.FileField(required=False)

    class Meta:
        model = Bookings
        fields = '__all__'

    def save(self, commit=False):
        instance = super().save(commit=False)
        uploaded_file = self.cleaned_data.get('binary_data')

        if uploaded_file:
            uploaded_bytes = uploaded_file.read()
            if len(uploaded_bytes) >= settings.MAX_UPLOAD_SIZE():
                if uploaded_file.name.endswith(".jpg"):
                    uploaded_bytes = compressor.compressImageWithBestQuality(uploaded_bytes)
                elif uploaded_file.name.endswith(".mp4"):
                    uploaded_bytes = compressor.compressVideo(uploaded_bytes)
                    instance.IDimage = uploaded_bytes
            commit = True
        if commit:
            instance.save()
        return instance

class MenuAdminForm(forms.ModelForm):
    image = forms.ImageField(required=False)

    class Meta:
        model = Menu
        fields = '__all__'

    def save(self,commit = False):
        instance = super().save(commit = False)
        uploaded_file = self.cleaned_data.get('image')
        
        if uploaded_file:
            uploaded_bytes = uploaded_file.read()
            if len(uploaded_bytes) >= settings.MAX_UPLOAD_SIZE():
                uploaded_bytes = compressor.compressImageWithBestQuality(uploaded_bytes)
                instance.dishImage = uploaded_bytes
            commit = True
        if commit:
            instance.save()
        return instance
    

