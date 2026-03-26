from django import forms
from django.db import transaction as db_transaction

from shopping.models import Product, Category, ProductImage


class ProductBaseForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'price', 'thumbnail', 'description', 'category', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Product name'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01'}),
            'thumbnail': forms.FileInput(),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Product description'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    image1 = forms.ImageField(required=True)
    image2 = forms.ImageField(required=False)
    image3 = forms.ImageField(required=False)
    image4 = forms.ImageField(required=False)
    image5 = forms.ImageField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()
        self.fields['category'].required = False
        self.fields['category'].empty_label = '-- Select category (optional) --'

    def save(self, commit=True):
        images = [self.cleaned_data.get(f'image{i}') for i in range(1, 6) if self.cleaned_data.get(f'image{i}')]
        with (db_transaction.atomic()):
            instance = self.instance
            instance.save()
            for i, image in enumerate(images, start=1):
                ProductImage.objects.create(product=instance, alt_text=f'{instance.name}{i}', image=image, display_order= i)
        return instance

class ProductCreateForm(ProductBaseForm):
    pass

class ProductUpdateForm(ProductBaseForm):
    """Form for editing product. Thumbnail is optional (keeps existing if not changed)."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['thumbnail'].required = False

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not self.cleaned_data.get('thumbnail') and self.instance.pk:
            instance.thumbnail = self.instance.thumbnail
        if commit:
            instance.save()
        return instance
