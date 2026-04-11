from django import forms
from menu.models import Category, MenuItem, Topping

FINPUT  = {'class': 'form-input'}
FSELECT = {'class': 'form-select'}
FTEXT   = {'class': 'form-textarea'}
FCHECK  = {'class': 'form-check-input'}
FNUM    = {'class': 'form-input', 'style': 'max-width:160px;'}

class CategoryForm(forms.ModelForm):
    class Meta:
        model  = Category
        fields = ['name', 'name_ar', 'name_he', 'sort_order', 'is_active']
        widgets = {
            'name':       forms.TextInput(attrs={**FINPUT, 'placeholder': 'English'}),
            'name_ar':    forms.TextInput(attrs={**FINPUT, 'placeholder': 'العربية', 'dir': 'rtl'}),
            'name_he':    forms.TextInput(attrs={**FINPUT, 'placeholder': 'עברית', 'dir': 'rtl'}),
            'sort_order': forms.NumberInput(attrs=FNUM),
            'is_active':  forms.CheckboxInput(attrs=FCHECK),
        }


class ToppingForm(forms.ModelForm):
    class Meta:
        model  = Topping
        fields = ['name', 'name_ar', 'name_he', 'price', 'is_available']
        widgets = {
            'name':         forms.TextInput(attrs=FINPUT),
            'name_ar':      forms.TextInput(attrs={**FINPUT, 'dir': 'rtl'}),
            'name_he':      forms.TextInput(attrs={**FINPUT, 'dir': 'rtl'}),
            'price':        forms.NumberInput(attrs={**FNUM, 'step': '0.50', 'min': '0'}),
            'is_available': forms.CheckboxInput(attrs=FCHECK),
        }


class MenuItemForm(forms.ModelForm):
    class Meta:
        model  = MenuItem
        fields = [
            'category', 'name', 'name_ar', 'name_he',
            'price', 'image', 'is_available', 'sort_order', 'toppings',
            'description', 'calories', 'protein', 'carbs', 'fat',
            'allergens', 'is_spicy', 'is_new',
            'sold_by_weight', 'weight_unit', 'price_per_unit',
        ]
        widgets = {
            'category':    forms.Select(attrs=FSELECT),
            'name':        forms.TextInput(attrs=FINPUT),
            'name_ar':     forms.TextInput(attrs={**FINPUT, 'dir': 'rtl'}),
            'name_he':     forms.TextInput(attrs={**FINPUT, 'dir': 'rtl'}),
            'price':       forms.NumberInput(attrs={**FNUM, 'step': '0.50', 'min': '0'}),
            'sort_order':  forms.NumberInput(attrs=FNUM),
            'description': forms.Textarea(attrs={**FTEXT, 'rows': '3', 'dir': 'rtl'}),
            'calories':    forms.NumberInput(attrs=FNUM),
            'protein':     forms.NumberInput(attrs=FNUM),
            'carbs':       forms.NumberInput(attrs=FNUM),
            'fat':         forms.NumberInput(attrs=FNUM),
            'allergens':   forms.TextInput(attrs={**FINPUT, 'placeholder': 'مثال: جلوتين، ألبان...', 'dir': 'rtl'}),
            'is_available':forms.CheckboxInput(attrs=FCHECK),
            'is_spicy':       forms.CheckboxInput(attrs=FCHECK),
            'is_new':         forms.CheckboxInput(attrs=FCHECK),
            'sold_by_weight': forms.CheckboxInput(attrs=FCHECK),
            'weight_unit':    forms.Select(attrs=FSELECT),
            'price_per_unit': forms.NumberInput(attrs={**FNUM, 'step':'0.50'}),
            'toppings':    forms.CheckboxSelectMultiple(),
            'image':       forms.FileInput(attrs={'class': 'form-input', 'accept': 'image/*'}),
        }