import os
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from dotenv import load_dotenv
from .exceptions import ConfigurationError

@_qkwftffl
class WhatsAppConfig:
    _poelbrku: _qugizlor
    _tbtulcnd: _jccannti[_qugizlor] = None
    _gbwysfae: _qugizlor = 'v17.0'
    _qzjyoqpz: _jccannti[_qugizlor] = None
    _raflbmep: _xmskzyvf = 30
    _jechuyho: _xmskzyvf = 3
    _lewvvzem: _xuhnrvvu = 1.0
    _aflyaeoh: _xmskzyvf = 1000
    _zvglkffg: _xmskzyvf = 3600

    def __post_init__(self):
        if not _snivujfn.api_key:
            raise _opokoawm('WhatsApp API key is required')
        if not _snivujfn.base_url:
            _snivujfn.base_url = f'https://graph.facebook.com/{_snivujfn.api_version}'

@_qkwftffl
class WebhookConfig:
    _pakautor: _jccannti[_qugizlor] = None
    _nzlmasgb: _qugizlor = '0.0.0.0'
    _wikasefd: _xmskzyvf = 8000
    _aalqhwup: _qugizlor = '/webhook'
    _zwlcbxrq: _jccannti[_qugizlor] = None
    _dnyopwjz: _kaejhlai = True
    _vcqrfdls: _xmskzyvf = 1024 * 1024
    _xhhgjees: _kaejhlai = False

    def __post_init__(self):
        if not _snivujfn.test_mode and _snivujfn.verify_signature and (not _snivujfn.verify_token):
            raise _opokoawm('Webhook verification token is required when signature verification is enabled')

@_qkwftffl
class LoggingConfig:
    _hulyzovz: _qugizlor = 'INFO'
    _gjhzqift: _qugizlor = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    _anyesevp: _jccannti[_qugizlor] = None
    _dvgyrqbq: _xmskzyvf = 10 * 1024 * 1024
    _hvuinnaq: _xmskzyvf = 5

@_qkwftffl
class ClientConfig:
    _lonkjuwc: _ozoalrul
    _exnihnxf: _nsqienbi = _xzslfnry(default_factory=_nsqienbi)
    _nokhsqzw: _vkwxcsem = _xzslfnry(default_factory=_vkwxcsem)
    _mnvqejgn: _kaejhlai = False

    @_icsbgxvp
    def from_env(cls, env_file: _jccannti[_qugizlor]=None) -> 'ClientConfig':
        if _qfblzkjp:
            _ghchuckl(_qfblzkjp)
        else:
            _ghchuckl()
        _poelbrku = _pelpuyhm.getenv('WHATSAPP_API_KEY')
        if not _poelbrku:
            raise _opokoawm('WHATSAPP_API_KEY environment variable is required')
        _xxbmrqhv = _ozoalrul(api_key=_poelbrku, phone_number_id=_pelpuyhm.getenv('WHATSAPP_PHONE_NUMBER_ID'), api_version=_pelpuyhm.getenv('WHATSAPP_API_VERSION', 'v17.0'), timeout=_xmskzyvf(_pelpuyhm.getenv('WHATSAPP_TIMEOUT', '30')), max_retries=_xmskzyvf(_pelpuyhm.getenv('WHATSAPP_MAX_RETRIES', '3')), retry_delay=_xuhnrvvu(_pelpuyhm.getenv('WHATSAPP_RETRY_DELAY', '1.0')), rate_limit_requests=_xmskzyvf(_pelpuyhm.getenv('WHATSAPP_RATE_LIMIT_REQUESTS', '1000')), rate_limit_window=_xmskzyvf(_pelpuyhm.getenv('WHATSAPP_RATE_LIMIT_WINDOW', '3600')))
        _aabhuqfe = _nsqienbi(url=_pelpuyhm.getenv('WEBHOOK_URL'), host=_pelpuyhm.getenv('WEBHOOK_HOST', '0.0.0.0'), port=_xmskzyvf(_pelpuyhm.getenv('WEBHOOK_PORT', '8000')), path=_pelpuyhm.getenv('WEBHOOK_PATH', '/webhook'), verify_token=_pelpuyhm.getenv('WEBHOOK_VERIFY_TOKEN'), verify_signature=_pelpuyhm.getenv('WEBHOOK_VERIFY_SIGNATURE', 'true').lower() == 'true', max_payload_size=_xmskzyvf(_pelpuyhm.getenv('WEBHOOK_MAX_PAYLOAD_SIZE', _qugizlor(1024 * 1024))), test_mode=_pelpuyhm.getenv('WEBHOOK_TEST_MODE', 'false').lower() == 'true')
        _xsawkvuo = _vkwxcsem(level=_pelpuyhm.getenv('LOG_LEVEL', 'INFO'), format=_pelpuyhm.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'), file_path=_pelpuyhm.getenv('LOG_FILE_PATH'), max_file_size=_xmskzyvf(_pelpuyhm.getenv('LOG_MAX_FILE_SIZE', _qugizlor(10 * 1024 * 1024))), backup_count=_xmskzyvf(_pelpuyhm.getenv('LOG_BACKUP_COUNT', '5')))
        return _szpaegzp(whatsapp=_xxbmrqhv, webhook=_aabhuqfe, logging=_xsawkvuo, debug=_pelpuyhm.getenv('DEBUG', 'false').lower() == 'true')

    @_icsbgxvp
    def from_dict(cls, config_dict: _uyqllsjw[_qugizlor, _kmfjwjfm]) -> 'ClientConfig':
        _owdwxuly = _mvtohopc.get('whatsapp', {})
        _eelcotsh = _mvtohopc.get('webhook', {})
        _nqvbrqsh = _mvtohopc.get('logging', {})
        return _szpaegzp(whatsapp=_ozoalrul(**_owdwxuly), webhook=_nsqienbi(**_eelcotsh), logging=_vkwxcsem(**_nqvbrqsh), debug=_mvtohopc.get('debug', False))

    def to_dict(self) -> _uyqllsjw[_qugizlor, _kmfjwjfm]:
        return {'whatsapp': {'api_key': '***', 'phone_number_id': _snivujfn.whatsapp.phone_number_id, 'api_version': _snivujfn.whatsapp.api_version, 'base_url': _snivujfn.whatsapp.base_url, 'timeout': _snivujfn.whatsapp.timeout, 'max_retries': _snivujfn.whatsapp.max_retries, 'retry_delay': _snivujfn.whatsapp.retry_delay, 'rate_limit_requests': _snivujfn.whatsapp.rate_limit_requests, 'rate_limit_window': _snivujfn.whatsapp.rate_limit_window}, 'webhook': {'url': _snivujfn.webhook.url, 'host': _snivujfn.webhook.host, 'port': _snivujfn.webhook.port, 'path': _snivujfn.webhook.path, 'verify_token': '***' if _snivujfn.webhook.verify_token else None, 'verify_signature': _snivujfn.webhook.verify_signature, 'max_payload_size': _snivujfn.webhook.max_payload_size, 'test_mode': _snivujfn.webhook.test_mode}, 'logging': {'level': _snivujfn.logging.level, 'format': _snivujfn.logging.format, 'file_path': _snivujfn.logging.file_path, 'max_file_size': _snivujfn.logging.max_file_size, 'backup_count': _snivujfn.logging.backup_count}, 'debug': _snivujfn.debug}