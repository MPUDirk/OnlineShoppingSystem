from django import forms
from django.core.validators import MinValueValidator
from django.db import transaction as db_transaction

from shopping.models import Product, Category, ProductImage, ProductPropertyTitle, ProductProperty


class ProductBaseForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'price', 'total_sku', 'thumbnail', 'description', 'category', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Product name'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01'}),
            'total_sku': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}),
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

class PropertyTitleEditForm(forms.ModelForm):
    class Meta:
        model = ProductPropertyTitle
        fields = ['title', 'is_main', 'is_default']

    title = forms.CharField(required=True)

    def __init__(self, *args, **kwargs):
        self.product = kwargs.pop('product')
        super().__init__(*args, **kwargs)

    def save(self, commit = True):
        instance, _ = ProductPropertyTitle.objects.get_or_create(product=self.product)
        instance.title = self.cleaned_data['title']
        instance.is_default = self.cleaned_data['is_default']
        instance.save()
        return instance

class PropertyEditForm(forms.ModelForm):
    class Meta:
        model = ProductProperty
        fields = ['name', 'change_value', 'sku']

    title = forms.CharField(max_length=50)
    name = forms.CharField(required=True)
    sku = forms.IntegerField(required=True, validators=[MinValueValidator(0)])

    def clean_title(self):
        try:
            return ProductPropertyTitle.objects.get(title=self.cleaned_data['title'])
        except ProductPropertyTitle.DoesNotExist:
            raise forms.ValidationError('Invalid title')

    def save(self, commit = True):
        instance, _ = ProductProperty.objects.get_or_create(title=self.cleaned_data['title'], defaults= {
            'name': self.cleaned_data['name'],
            'sku': self.cleaned_data['sku'],
        })
        if self.cleaned_data.get('image') and self.cleaned_data['title'].is_default:
            instance.image = self.cleaned_data['image']
        else:
            instance.image = instance.title.product.thumbnail
        instance.save()
        return instance