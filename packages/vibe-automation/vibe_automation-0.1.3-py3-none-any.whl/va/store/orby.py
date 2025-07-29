from .store import Store


class OrbyClient(Store):
    """Orby client to persist the states in Orby server.

    TODO: implement this after the server endpoints are ready.
    """

    def get_credential(self):
        pass

    # Get the OAuth token. there are two cases:
    # - when running in our managed environment, we set it via environment variable,
    # - when running locally, we load it from a local path such as ~/.config/orby/credential.json.
    # if user hasn't authorized, we would trigger an OAuth process.
    def request(self):
        pass
