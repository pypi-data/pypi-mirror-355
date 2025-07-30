"""Error classes for Pydactyl."""


class PydactylError(Exception):
    print('OptimiHost API got an error :(')
    print(f'Error: {Exception}')

class BadRequestError(PydactylError):
    print('Bad Request!')
    print(f'Error: {PydactylError}')


class ClientConfigError(PydactylError):
    print("There's something wrong with your configs(ClientConfigError)")
    print(f'Error: {PydactylError}')

class PterodactylApiError(PydactylError):
    print('OptimiHost had an error :(')
    print(f'Error: {PydactylError}')
