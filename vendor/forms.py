from django import forms

from shopping.models import Product, Category


class ProductCreateForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'price', 'thumbnail', 'description', 'category', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Product name'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Product description'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()
        self.fields['category'].required = False
        self.fields['category'].empty_label = '-- Select category (optional) --'


class ProductUpdateForm(forms.ModelForm):
    """Form for editing product. Thumbnail is optional (keeps existing if not changed)."""
    class Meta:
        model = Product
        fields = ['name', 'price', 'thumbnail', 'description', 'category', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Product name'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Product description'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()
        self.fields['category'].required = False
        self.fields['category'].empty_label = '-- Select category (optional) --'
        self.fields['thumbnail'].required = False
        self.fields['thumbnail'].help_text = 'Leave empty to keep current image'

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not self.cleaned_data.get('thumbnail') and self.instance.pk:
            instance.thumbnail = self.instance.thumbnail
        if commit:
            instance.save()
        return instance
