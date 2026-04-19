import os
import bs4
import requests

from django.urls import reverse
from django.views.generic import TemplateView


class XSSExampleView(TemplateView):
    template_name = 'xss_example.html'

    def get(self, request, *args, **kwargs):
        baseurl = f'http://127.0.0.1:8000' if not os.environ.get('DEBUG', False) else 'https://isp.dc-yan.top'
        login_url = f'{baseurl}{reverse("user:login")}'
        session = requests.Session()
        soup = bs4.BeautifulSoup(session.get(login_url,).content, 'html.parser')
        csrftoken = soup.find('input', {'name': 'csrfmiddlewaretoken'})['value']
        session.post(
            login_url,
            data={
                'csrfmiddlewaretoken': csrftoken,
                'username': 'tuser',
                'password': 'tuser1234'
            },
            headers={'referer': login_url,}
        )

        order_url = f'{baseurl}{reverse("vendor:order_list")}'
        soup = bs4.BeautifulSoup(session.get(order_url).content, 'html.parser')
        csrftoken = soup.find('input', {'name': 'csrfmiddlewaretoken'})['value']
        order_update_url = f'{baseurl}{reverse("vendor:order_update", args=[self.kwargs["oid"]])}'
        session.post(
            order_update_url,
            data={
            'csrfmiddlewaretoken': csrftoken,
            'status': 'delivered'
            },
            headers={'referer': order_url,}
        )

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return  context