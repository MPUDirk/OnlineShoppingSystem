import bs4
import requests

from django.urls import reverse
from django.views.generic import TemplateView
import requests


class XSSExampleView(TemplateView):
    template_name = 'xss_example.html'

    def get(self, request, *args, **kwargs):
        baseurl = f'{request.scheme}://{request.get_host()}'
        login_url = f'{baseurl}{reverse("user:login")}'
        session = requests.Session()
        soup = bs4.BeautifulSoup(session.get(login_url).content, 'html.parser')
        csrftoken = soup.find('input', {'name': 'csrfmiddlewaretoken'})['value']
        session.post(login_url, data={
            'csrfmiddlewaretoken': csrftoken,
            'username': 'tuser',
            'password': 'tuser1234'
        })

        order_url = f'{baseurl}{reverse("vendor:order_list")}'
        soup = bs4.BeautifulSoup(session.get(order_url).content, 'html.parser')
        csrftoken = soup.find('input', {'name': 'csrfmiddlewaretoken'})['value']
        order_update_url = f'{baseurl}{reverse("vendor:order_update", args=[self.kwargs["oid"]])}'
        session.post(order_update_url, data={
            'csrfmiddlewaretoken': csrftoken,
            'status': 'delivered'
        })

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return  context