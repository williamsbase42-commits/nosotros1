from django import forms
from .models import Recuerdo

class RecuerdoForm(forms.ModelForm):
    fecha = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    class Meta:
        model = Recuerdo
        fields = ['titulo', 'descripcion', 'fecha', 'imagen', 'categoria', 'latitud', 'longitud']
