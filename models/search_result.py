class SearchResult:
    def __init__(self, _class, name, url, username, api_token):
        self._class = _class
        self.result_type = self._class.split(".")[-1]
        self.name = name
        self.url = url
        self.username = username
        self.api_token = api_token

    def __str__(self):
        """ String representation for easy printing. """
        return f"{self.url} - {self.name}"
