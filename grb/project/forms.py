from django import forms

class AddRecipe(forms.Form):
    title = forms.CharField(label="Recipe Title", max_length=100)
    prepMinutes = forms.IntegerField(label="Prep Time (Minutes)", min_value=1, max_value=360)
    cookMinutes = forms.IntegerField(label="Cook Time (Minutes)", min_value=1, max_value=360)
    servings = forms.IntegerField(label="Servings", min_value=1, max_value=16)
    ingredients = forms.CharField(widget=forms.Textarea)
    instructions = forms.CharField(widget=forms.Textarea)
