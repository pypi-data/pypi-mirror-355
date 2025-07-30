from django.views.generic import TemplateView

class NotifyView(TemplateView):
    template_name = "notify/home.html"