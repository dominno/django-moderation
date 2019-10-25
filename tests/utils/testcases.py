from django_webtest import WebTest


class WebTestCase(WebTest):

    def setUp(self):
        self.user = None

    def get(self, url, **kwargs):
        kwargs.setdefault('user', self.user)
        return self.app.get(url, **kwargs)

    def post(self, url, **kwargs):
        kwargs.setdefault('user', self.user)
        return self.app.post(url, **kwargs)
