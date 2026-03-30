from django import forms
from django.core.validators import MinValueValidator
from django.db import transaction as db_transaction

from shopping.models import Product, Category, ProductImage, ProductPropertyTitle, ProductProperty


class ProductBaseForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'price', 'thumbnail', 'description', 'category', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Product name'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01'}),
            'thumbnail': forms.FileInput(attrs={'accept': 'image/*'}),
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
        # Hide native file input (OS locale); templates use English "Choose file" / "No file chosen".
        self.fields['thumbnail'].widget = forms.FileInput(
            attrs={'class': 'visually-hidden', 'accept': 'image/*', 'tabindex': '-1'}
        )

    def clean_image1(self):
        return self.cleaned_data.get('image1')

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
        self.fields['image1'].required = False

    def clean_image1(self):
        if 'image1' not in self.changed_data:
            return ''
        return super().clean_image1()

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not self.cleaned_data.get('thumbnail') and self.instance.pk:
            instance.thumbnail = self.instance.thumbnail
        if commit:
            instance.save()
        return instance

class PropertyTitleForm(forms.ModelForm):
    """Create or update an attribute type (dimension) for a product."""

    class Meta:
        model = ProductPropertyTitle
        fields = ['title', 'is_main', 'is_default']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 50}),
            'is_main': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, product=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.product = product
        if self.product is None and self.instance.pk:
            self.product = self.instance.product

    def clean_title(self):
        title = (self.cleaned_data.get('title') or '').strip()
        if not title:
            raise forms.ValidationError('Enter a name for this attribute type.')
        if self.product is None:
            raise forms.ValidationError('Missing product context.')
        qs = ProductPropertyTitle.objects.filter(product=self.product, title=title)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('This attribute type name already exists for this product.')
        return title


class PropertyOptionForm(forms.ModelForm):
    """One option under an attribute type (e.g. Color: Red)."""

    class Meta:
        model = ProductProperty
        fields = ['name', 'change_value', 'sku', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'change_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'sku': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'image': forms.FileInput(attrs={'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].required = False
        self.fields['change_value'].required = False
        # Native file inputs use OS/browser locale; use custom UI in template (English labels).
        self.fields['image'].widget = forms.FileInput(
            attrs={'class': 'visually-hidden', 'accept': 'image/*', 'tabindex': '-1'}
        )

    def save(self, commit=True):
        instance = super().save(commit=False)
        if instance.pk and not self.cleaned_data.get('image'):
            instance.image = self.instance.image
        if commit:
            instance.save()
        return instance