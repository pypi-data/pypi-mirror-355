from requests.adapters import HTTPAdapter


class TimeoutHTTPAdapter(HTTPAdapter):

    def __init__(self, *args, **kwargs):
        if 'timeout' in kwargs:
            self.timeout = kwargs['timeout']
            del kwargs['timeout']
        else:
            self.timeout = 3

        super().__init__(*args, **kwargs)

    def send(self, request, **kwargs):
        if kwargs['timeout'] is None:
            kwargs['timeout'] = self.timeout
        return super().send(request, **kwargs)
