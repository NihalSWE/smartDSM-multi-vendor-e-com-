from django import forms
from .models import *




#contact page faqs
class contactFAQorm(forms.ModelForm):
    class Meta:
        model = contactFAQ
        fields = ['question', 'answer', 'is_active', 'order']
        widgets = {
            'question': forms.TextInput(attrs={'class': 'form-control'}),
            'answer': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }



class ContactLocationForm(forms.ModelForm):
    class Meta:
        model = ContactLocation
        fields = ['city', 'address', 'email', 'number', 'image']
        widgets = {
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Address'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
        }

    def clean_image(self):
        image = self.cleaned_data.get('image')
        # Add any image validation here if needed
        return image
    

class ProductReviewForm(forms.ModelForm):
    class Meta:
        model = ProductReview
        fields = ['name', 'email', 'phone', 'rating', 'text']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Your Name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Your Email'}),
            'phone': forms.TextInput(attrs={'placeholder': 'Your Phone Number'}),
            'rating': forms.Select(attrs={'style': 'display:none;'}),  # star UI will control this
            'text': forms.Textarea(attrs={
                'rows': 6,
                'placeholder': 'Write Your Review Here...',
                'class': 'form-control'
            }),
        }