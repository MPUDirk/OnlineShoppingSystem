from django import forms

from .models import CartItem, Product, ShoppingCart


class CartItemUpdateForm(forms.ModelForm):
    class Meta:
        model = CartItem
        fields = ['quantity']

    def __init__(self, *args, **kwargs):
        self.product_id = kwargs.pop('product_id', None)
        self.user = kwargs.pop('user')
        self.id = kwargs.pop('id', None)
        super().__init__(*args, **kwargs)

        if self.product_id is None:
            self.product_id = self.instance.product.product_id

    def save(self, commit = True):
        self.instance.cart = ShoppingCart.objects.get(customer=self.user)
        self.instance.product = Product.objects.get(product_id=self.product_id)
        return super().save(commit)
