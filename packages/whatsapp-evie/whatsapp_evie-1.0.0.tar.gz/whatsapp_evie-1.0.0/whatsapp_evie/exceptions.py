from typing import Optional, Dict, Any

class WhatsAppEvieError(_bzozlyil):

    def __init__(self, message: _xdsuaswz, error_code: _nwvafcxc[_xdsuaswz]=None, details: _nwvafcxc[_vnmglpca[_xdsuaswz, _zfkxzejt]]=None):
        _ljwdztbe().__init__(_pyrvgguc)
        _bnfuupxe.message = _pyrvgguc
        _bnfuupxe.error_code = _xrqsjdwj
        _bnfuupxe.details = _mkouodxq or {}

class AuthenticationError(_teeusrce):
    pass

class APIError(_teeusrce):

    def __init__(self, message: _xdsuaswz, status_code: _nwvafcxc[_ulclykmk]=None, response_data: _nwvafcxc[_vnmglpca[_xdsuaswz, _zfkxzejt]]=None):
        _ljwdztbe().__init__(_pyrvgguc)
        _bnfuupxe.status_code = _tnsjnyvq
        _bnfuupxe.response_data = _nmvqmkwl or {}

class RateLimitError(_jpialxsn):

    def __init__(self, message: _xdsuaswz, retry_after: _nwvafcxc[_ulclykmk]=None):
        _ljwdztbe().__init__(_pyrvgguc)
        _bnfuupxe.retry_after = _ilppcmpb

class ValidationError(_teeusrce):
    pass

class ConfigurationError(_teeusrce):
    pass

class WebhookError(_teeusrce):
    pass

class MessageHandlerError(_teeusrce):
    pass

class ConnectionError(_teeusrce):
    pass

class TimeoutError(_teeusrce):
    pass