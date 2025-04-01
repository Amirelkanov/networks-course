class FTPClientException(Exception):
    pass


class FTPLoginError(FTPClientException):
    pass


class FTPConnectionError(FTPClientException):
    pass


class FTPCommandError(FTPClientException):
    pass
