import os
import time
import json
import aiohttp
import asyncio
import hashlib
import hmac
from typing import Optional, List, Callable, Dict, Any, Union
from contextlib import asynccontextmanager
from .models import Message, MessageType, MessageStatus
from .config import ClientConfig, WhatsAppConfig, WebhookConfig
from .exceptions import WhatsAppEvieError, AuthenticationError, APIError, RateLimitError, ValidationError, ConfigurationError, WebhookError, ConnectionError, TimeoutError
from .utils import RateLimiter, retry_async, make_request_with_timeout, verify_webhook_signature
from .logging_utils import LoggerMixin, log_api_request, log_api_response, log_message_event, log_error

class WhatsAppEvieClient(_lapwdkmr):

    def __init__(self, api_key: _kuzwvsso[_ajobtjxb]=None, webhook_url: _kuzwvsso[_ajobtjxb]=None, config: _kuzwvsso[_eriwwybo]=None, phone_number_id: _kuzwvsso[_ajobtjxb]=None):
        if _vvrriwos:
            _gmkgvwnx.config = _vvrriwos
        else:
            from dotenv import load_dotenv
            _kvtfxomk()
            _rzataeiv = _rzataeiv or _obhfyvem.getenv('WHATSAPP_API_KEY')
            if not _rzataeiv:
                raise _aegvzzwl('WhatsApp API key is required')
            _mtrgrtos = _xqndqdmm(api_key=_rzataeiv, phone_number_id=_doipgygh or _obhfyvem.getenv('WHATSAPP_PHONE_NUMBER_ID'))
            _vrgljqbv = _ocxafnpo(url=_xaidloso or _obhfyvem.getenv('WEBHOOK_URL'))
            _gmkgvwnx.config = _eriwwybo(whatsapp=_mtrgrtos, webhook=_vrgljqbv)
        _gmkgvwnx._message_handlers: _pgkjrzkb[_ngimcjwn, _jdmknebu[_nbjxnnpj]] = {_epgptflu: [] for _epgptflu in _ngimcjwn}
        _gmkgvwnx._global_handlers: _jdmknebu[_nbjxnnpj] = []
        _gmkgvwnx._error_handlers: _jdmknebu[_nbjxnnpj] = []
        _gmkgvwnx._session: _kuzwvsso[_hnwqdqzo.ClientSession] = None
        _gmkgvwnx._rate_limiter = _tahmfokv(_gmkgvwnx.config.whatsapp.rate_limit_requests, _gmkgvwnx.config.whatsapp.rate_limit_window)
        _gmkgvwnx._webhook_server = None
        from .logging_utils import setup_logging
        _jauxbbes(_gmkgvwnx.config.logging)

    async def __aenter__(self):
        await _gmkgvwnx._ensure_session()
        return _gmkgvwnx

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await _gmkgvwnx.close()

    async def _ensure_session(self):
        if _gmkgvwnx._session is None or _gmkgvwnx._session.closed:
            _qkeejuhw = _hnwqdqzo.TCPConnector(limit=100, limit_per_host=30, ttl_dns_cache=300, use_dns_cache=True)
            _yiqdnbgn = _hnwqdqzo.ClientTimeout(total=_gmkgvwnx.config.whatsapp.timeout)
            _gmkgvwnx._session = _hnwqdqzo.ClientSession(connector=_qkeejuhw, timeout=_yiqdnbgn, headers={'Authorization': f'Bearer {_gmkgvwnx.config.whatsapp.api_key}', 'Content-Type': 'application/json', 'User-Agent': 'WhatsApp-Evie/1.0.0'})

    async def close(self):
        if _gmkgvwnx._session and (not _gmkgvwnx._session.closed):
            await _gmkgvwnx._session.close()
        if _gmkgvwnx._webhook_server:
            await _gmkgvwnx._webhook_server.cleanup()

    def register_message_handler(self, message_type: _ngimcjwn, handler: _nbjxnnpj[[_riangtha], None]):
        _gmkgvwnx._message_handlers[_kganyzjl].append(_tqxrhnpm)
        _gmkgvwnx.logger.info(f'Registered handler for {_kganyzjl} messages')

    def register_global_handler(self, handler: _nbjxnnpj[[_riangtha], None]):
        _gmkgvwnx._global_handlers.append(_tqxrhnpm)
        _gmkgvwnx.logger.info('Registered global message handler')

    def register_error_handler(self, handler: _nbjxnnpj[[_onitvpbt, _kuzwvsso[_riangtha]], None]):
        _gmkgvwnx._error_handlers.append(_tqxrhnpm)
        _gmkgvwnx.logger.info('Registered error handler')

    def unregister_handler(self, message_type: _ngimcjwn, handler: _nbjxnnpj):
        if _tqxrhnpm in _gmkgvwnx._message_handlers[_kganyzjl]:
            _gmkgvwnx._message_handlers[_kganyzjl].remove(_tqxrhnpm)
            _gmkgvwnx.logger.info(f'Unregistered handler for {_kganyzjl} messages')

    def clear_handlers(self, message_type: _kuzwvsso[_ngimcjwn]=None):
        if _kganyzjl:
            _gmkgvwnx._message_handlers[_kganyzjl].clear()
            _gmkgvwnx.logger.info(f'Cleared all handlers for {_kganyzjl} messages')
        else:
            for _dwuvzdft in _gmkgvwnx._message_handlers.values():
                _dwuvzdft.clear()
            _gmkgvwnx._global_handlers.clear()
            _gmkgvwnx._error_handlers.clear()
            _gmkgvwnx.logger.info('Cleared all handlers')

    @_sdvgyzpg(max_retries=3, delay=1.0, exceptions=(_asulnhuz, _wzaacrug, _rdscwhyk))
    async def send_message(self, message: _riangtha) -> _dosswjjr:
        try:
            if not _ljlhvslj.recipient_id:
                raise _zddebcfx('Recipient ID is required')
            await _gmkgvwnx._rate_limiter.acquire()
            await _gmkgvwnx._ensure_session()
            _uvvgqidj = _ljlhvslj.to_whatsapp_payload()
            if _gmkgvwnx.config.whatsapp.phone_number_id:
                _zjqjpegx = f'{_gmkgvwnx.config.whatsapp.base_url}/{_gmkgvwnx.config.whatsapp.phone_number_id}/messages'
            else:
                _zjqjpegx = f'{_gmkgvwnx.config.whatsapp.base_url}/messages'
            _bptghfih(_gmkgvwnx.logger, 'POST', _zjqjpegx, _uvvgqidj)
            async with _gmkgvwnx._session.post(_zjqjpegx, json=_uvvgqidj) as _kgphgfrh:
                _dewbvign = await _kgphgfrh.json()
                _duwwueie(_gmkgvwnx.logger, _kgphgfrh.status, _dewbvign)
                if _kgphgfrh.status == 200:
                    _ljlhvslj.status = _cuinpfam.SENT
                    _seynkwlp(_gmkgvwnx.logger, 'sent', _ljlhvslj.message_id, {'type': _ljlhvslj.type, 'recipient': _ljlhvslj.recipient_id})
                    return True
                elif _kgphgfrh.status == 429:
                    _vwgezmcy = _kgphgfrh.headers.get('Retry-After', 60)
                    raise _fdobgbre('Rate limit exceeded', retry_after=_csdmezzo(_vwgezmcy))
                elif _kgphgfrh.status == 401:
                    raise _atnjusnz('Invalid API key or authentication failed')
                else:
                    _ptyxqhke = _dewbvign.get('error', {}).get('message', 'Unknown error')
                    _bgeqgeby = _dewbvign.get('error', {}).get('code')
                    raise _asulnhuz(f'API request failed: {_ptyxqhke}', _kgphgfrh.status, _dewbvign)
        except (_zddebcfx, _atnjusnz, _fdobgbre, _asulnhuz):
            _ljlhvslj.status = _cuinpfam.FAILED
            raise
        except _onitvpbt as e:
            _ljlhvslj.status = _cuinpfam.FAILED
            _tmegsasv(_gmkgvwnx.logger, _ijqwwhxb, 'send_message')
            for _tqxrhnpm in _gmkgvwnx._error_handlers:
                try:
                    await _tqxrhnpm(_ijqwwhxb, _ljlhvslj)
                except _onitvpbt as handler_error:
                    _tmegsasv(_gmkgvwnx.logger, _vptbfwna, 'error_handler')
            raise _jazosrbz(f'Failed to send message: {_ajobtjxb(_ijqwwhxb)}') from _ijqwwhxb

    async def receive_message(self, message_data: _pgkjrzkb[_ajobtjxb, _iumazfae]) -> _kuzwvsso[_riangtha]:
        try:
            _dfodrgsm = _sdbkjeof.get('entry', [{}])[0]
            _uknopoep = _dfodrgsm.get('changes', [{}])[0]
            _dvidmohn = _uknopoep.get('value', {})
            if 'messages' not in _dvidmohn:
                _gmkgvwnx.logger.debug('Webhook payload does not contain messages')
                return None
            _eezzjrbm = _dvidmohn.get('messages', [{}])[0]
            _rzgttbcr = _dvidmohn.get('contacts', [{}])
            _mlqriucb = _eezzjrbm.get('id', _ajobtjxb(_elahciwc.time()))
            _qrbnuesl = _eezzjrbm.get('from', '')
            _kwbhvuqk = _tzgumoqc(_eezzjrbm.get('timestamp', _elahciwc.time()))
            _kganyzjl = _ngimcjwn.TEXT
            _zrfwqocf = ''
            _rqxmilfe = None
            _hppamjes = None
            _dbmyterz = None
            if 'text' in _eezzjrbm:
                _kganyzjl = _ngimcjwn.TEXT
                _zrfwqocf = _eezzjrbm['text']['body']
            elif 'image' in _eezzjrbm:
                _kganyzjl = _ngimcjwn.IMAGE
                _qmawaxnd = _eezzjrbm['image']
                _zrfwqocf = _qmawaxnd.get('id', '')
                from .models import MediaInfo
                _rqxmilfe = _xlissfpb(media_id=_qmawaxnd.get('id'), mime_type=_qmawaxnd.get('mime_type'), caption=_qmawaxnd.get('caption'))
            elif 'audio' in _eezzjrbm:
                _kganyzjl = _ngimcjwn.AUDIO
                _ufxqahrc = _eezzjrbm['audio']
                _zrfwqocf = _ufxqahrc.get('id', '')
                from .models import MediaInfo
                _rqxmilfe = _xlissfpb(media_id=_ufxqahrc.get('id'), mime_type=_ufxqahrc.get('mime_type'))
            elif 'video' in _eezzjrbm:
                _kganyzjl = _ngimcjwn.VIDEO
                _mfiwipua = _eezzjrbm['video']
                _zrfwqocf = _mfiwipua.get('id', '')
                from .models import MediaInfo
                _rqxmilfe = _xlissfpb(media_id=_mfiwipua.get('id'), mime_type=_mfiwipua.get('mime_type'), caption=_mfiwipua.get('caption'))
            elif 'document' in _eezzjrbm:
                _kganyzjl = _ngimcjwn.DOCUMENT
                _laxjzpkm = _eezzjrbm['document']
                _zrfwqocf = _laxjzpkm.get('id', '')
                from .models import MediaInfo
                _rqxmilfe = _xlissfpb(media_id=_laxjzpkm.get('id'), mime_type=_laxjzpkm.get('mime_type'), filename=_laxjzpkm.get('filename'), caption=_laxjzpkm.get('caption'))
            elif 'location' in _eezzjrbm:
                _kganyzjl = _ngimcjwn.LOCATION
                _dqbzwtnc = _eezzjrbm['location']
                _zrfwqocf = f'{_dqbzwtnc.get('latitude', 0)},{_dqbzwtnc.get('longitude', 0)}'
                from .models import LocationInfo
                _hppamjes = _tjfltiqz(latitude=_tzgumoqc(_dqbzwtnc.get('latitude', 0)), longitude=_tzgumoqc(_dqbzwtnc.get('longitude', 0)), name=_dqbzwtnc.get('name'), address=_dqbzwtnc.get('address'))
            elif 'contacts' in _eezzjrbm:
                _kganyzjl = _ngimcjwn.CONTACT
                _zamlndoi = _eezzjrbm['contacts'][0] if _eezzjrbm['contacts'] else {}
                _qruavkwp = _zamlndoi.get('name', {}).get('formatted_name', '')
                _zrfwqocf = _qruavkwp
                from .models import ContactInfo
                _dbmyterz = _keagnrtz(name=_qruavkwp, phone=_zamlndoi.get('phones', [{}])[0].get('phone') if _zamlndoi.get('phones') else None, email=_zamlndoi.get('emails', [{}])[0].get('email') if _zamlndoi.get('emails') else None, organization=_zamlndoi.get('org', {}).get('company') if _zamlndoi.get('org') else None)
            elif 'sticker' in _eezzjrbm:
                _kganyzjl = _ngimcjwn.STICKER
                _xanaijbk = _eezzjrbm['sticker']
                _zrfwqocf = _xanaijbk.get('id', '')
                from .models import MediaInfo
                _rqxmilfe = _xlissfpb(media_id=_xanaijbk.get('id'), mime_type=_xanaijbk.get('mime_type'))
            _ljlhvslj = _riangtha(message_id=_mlqriucb, type=_kganyzjl, content=_zrfwqocf, sender_id=_qrbnuesl, recipient_id=_gmkgvwnx.config.whatsapp.phone_number_id or '', timestamp=_kwbhvuqk, status=_cuinpfam.DELIVERED, metadata=_sdbkjeof, media_info=_rqxmilfe, location_info=_hppamjes, contact_info=_dbmyterz)
            _seynkwlp(_gmkgvwnx.logger, 'received', _ljlhvslj.message_id, {'type': _ljlhvslj.type, 'sender': _ljlhvslj.sender_id})
            await _gmkgvwnx._call_message_handlers(_ljlhvslj)
            return _ljlhvslj
        except _onitvpbt as e:
            _tmegsasv(_gmkgvwnx.logger, _ijqwwhxb, 'receive_message')
            for _tqxrhnpm in _gmkgvwnx._error_handlers:
                try:
                    await _tqxrhnpm(_ijqwwhxb, None)
                except _onitvpbt as handler_error:
                    _tmegsasv(_gmkgvwnx.logger, _vptbfwna, 'error_handler')
            return None

    async def _call_message_handlers(self, message: _riangtha):
        _yvntqoop = []
        _yvntqoop.extend(_gmkgvwnx._message_handlers[_ljlhvslj.type])
        _yvntqoop.extend(_gmkgvwnx._global_handlers)
        if _yvntqoop:
            _jouzjsvw = []
            for _tqxrhnpm in _yvntqoop:
                try:
                    if _nwappted.iscoroutinefunction(_tqxrhnpm):
                        _jouzjsvw.append(_nwappted.create_task(_tqxrhnpm(_ljlhvslj)))
                    else:
                        _jouzjsvw.append(_nwappted.create_task(_nwappted.get_event_loop().run_in_executor(None, _tqxrhnpm, _ljlhvslj)))
                except _onitvpbt as e:
                    _tmegsasv(_gmkgvwnx.logger, _ijqwwhxb, f'handler_{_tqxrhnpm.__name__}')
            if _jouzjsvw:
                await _nwappted.gather(*_jouzjsvw, return_exceptions=True)

    async def start_webhook_server(self, host: _kuzwvsso[_ajobtjxb]=None, port: _kuzwvsso[_csdmezzo]=None):
        from aiohttp import web
        from aiohttp.web_middlewares import normalize_path_middleware
        _voudvgkj = _voudvgkj or _gmkgvwnx.config.webhook.host
        _byatreco = _byatreco or _gmkgvwnx.config.webhook.port
        _iufftmfo = _gmkgvwnx.config.webhook.path

        async def handle_webhook_verification(request):
            try:
                _czcwkefb = _rgbydvzr.query.get('hub.mode')
                _ifazhslo = _rgbydvzr.query.get('hub.verify_token')
                _xcqddesw = _rgbydvzr.query.get('hub.challenge')
                if _czcwkefb == 'subscribe' and _ifazhslo == _gmkgvwnx.config.webhook.verify_token:
                    _gmkgvwnx.logger.info('Webhook verification successful')
                    return _mlmsgoxl.Response(text=_xcqddesw, status=200)
                else:
                    _gmkgvwnx.logger.warning('Webhook verification failed')
                    return _mlmsgoxl.Response(status=403)
            except _onitvpbt as e:
                _tmegsasv(_gmkgvwnx.logger, _ijqwwhxb, 'webhook_verification')
                return _mlmsgoxl.Response(status=500)

        async def handle_webhook_message(request):
            try:
                _fnxsgzel = _rgbydvzr.content_length
                if _fnxsgzel and _fnxsgzel > _gmkgvwnx.config.webhook.max_payload_size:
                    _gmkgvwnx.logger.warning(f'Payload too large: {_fnxsgzel} bytes')
                    return _mlmsgoxl.Response(status=413)
                _hsproltz = await _rgbydvzr.read()
                if _gmkgvwnx.config.webhook.verify_signature:
                    _ihsjkluz = _rgbydvzr.headers.get('X-Hub-Signature-256', '')
                    if not _garwlfxp(_hsproltz, _ihsjkluz, _gmkgvwnx.config.webhook.verify_token):
                        _gmkgvwnx.logger.warning('Webhook signature verification failed')
                        return _mlmsgoxl.Response(status=403)
                try:
                    _cmlrlcgs = _mlgpamlx.loads(_hsproltz.decode('utf-8'))
                except _mlgpamlx.JSONDecodeError as e:
                    _gmkgvwnx.logger.error(f'Invalid JSON in webhook payload: {_ijqwwhxb}')
                    return _mlmsgoxl.Response(status=400)
                _ljlhvslj = await _gmkgvwnx.receive_message(_cmlrlcgs)
                if _ljlhvslj:
                    return _mlmsgoxl.Response(status=200)
                else:
                    return _mlmsgoxl.Response(status=400)
            except _onitvpbt as e:
                _tmegsasv(_gmkgvwnx.logger, _ijqwwhxb, 'webhook_message')
                return _mlmsgoxl.Response(status=500)

        async def handle_health_check(request):
            return _mlmsgoxl.Response(text=_mlgpamlx.dumps({'status': 'healthy', 'timestamp': _elahciwc.time(), 'version': '1.0.0'}), content_type='application/json')
        _oxpxevns = _mlmsgoxl.Application(middlewares=[_kkgmtaju(append_slash=False, remove_slash=True)])
        _oxpxevns.router.add_get(_iufftmfo, _czrmpfao)
        _oxpxevns.router.add_post(_iufftmfo, _kmcuoyxy)
        _oxpxevns.router.add_get('/health', _ncmedxww)
        _kdisasqx = _mlmsgoxl.AppRunner(_oxpxevns)
        await _kdisasqx.setup()
        _giooczuv = _mlmsgoxl.TCPSite(_kdisasqx, _voudvgkj, _byatreco)
        await _giooczuv.start()
        _gmkgvwnx._webhook_server = _kdisasqx
        _gmkgvwnx.logger.info(f'Webhook server started on {_voudvgkj}:{_byatreco}{_iufftmfo}')
        try:
            while True:
                await _nwappted.sleep(3600)
        except _rsegpavw:
            _gmkgvwnx.logger.info('Webhook server stopped by user')
        finally:
            await _kdisasqx.cleanup()

    async def send_bulk_messages(self, messages: _jdmknebu[_riangtha]) -> _pgkjrzkb[_ajobtjxb, _dosswjjr]:
        _ngfzcvjo = {}
        for _ljlhvslj in _eezzjrbm:
            try:
                _uppqkjgx = await _gmkgvwnx.send_message(_ljlhvslj)
                _ngfzcvjo[_ljlhvslj.message_id] = _uppqkjgx
                await _nwappted.sleep(0.1)
            except _onitvpbt as e:
                _tmegsasv(_gmkgvwnx.logger, _ijqwwhxb, f'bulk_send_{_ljlhvslj.message_id}')
                _ngfzcvjo[_ljlhvslj.message_id] = False
        return _ngfzcvjo

    async def get_media_url(self, media_id: _ajobtjxb) -> _kuzwvsso[_ajobtjxb]:
        try:
            await _gmkgvwnx._ensure_session()
            _zjqjpegx = f'{_gmkgvwnx.config.whatsapp.base_url}/{_uqfmlscv}'
            _bptghfih(_gmkgvwnx.logger, 'GET', _zjqjpegx)
            async with _gmkgvwnx._session.get(_zjqjpegx) as _kgphgfrh:
                _dewbvign = await _kgphgfrh.json()
                _duwwueie(_gmkgvwnx.logger, _kgphgfrh.status, _dewbvign)
                if _kgphgfrh.status == 200:
                    return _dewbvign.get('url')
                elif _kgphgfrh.status == 401:
                    raise _atnjusnz('Invalid API key or authentication failed')
                else:
                    _ptyxqhke = _dewbvign.get('error', {}).get('message', 'Unknown error')
                    _tmegsasv(_gmkgvwnx.logger, f'Failed to get media URL: {_ptyxqhke}')
                    return None
        except _onitvpbt as e:
            _tmegsasv(_gmkgvwnx.logger, _ijqwwhxb, 'get_media_url')
            return None

    async def download_media(self, media_id: _ajobtjxb, file_path: _ajobtjxb) -> _dosswjjr:
        try:
            _xmzfciiq = await _gmkgvwnx.get_media_url(_uqfmlscv)
            if not _xmzfciiq:
                return False
            async with _gmkgvwnx._session.get(_xmzfciiq) as _kgphgfrh:
                if _kgphgfrh.status == 200:
                    with _rqrgerim(_fkxxwkbu, 'wb') as _pqxqyrbs:
                        async for _apidojbt in _kgphgfrh.content.iter_chunked(8192):
                            _pqxqyrbs.write(_apidojbt)
                    return True
                elif _kgphgfrh.status == 401:
                    raise _atnjusnz('Invalid API key or authentication failed')
                else:
                    _ptyxqhke = _dewbvign.get('error', {}).get('message', 'Unknown error')
                    _tmegsasv(_gmkgvwnx.logger, f'Failed to download media: {_ptyxqhke}')
                    return False
        except _onitvpbt as e:
            _tmegsasv(_gmkgvwnx.logger, _ijqwwhxb, 'download_media')
            return False