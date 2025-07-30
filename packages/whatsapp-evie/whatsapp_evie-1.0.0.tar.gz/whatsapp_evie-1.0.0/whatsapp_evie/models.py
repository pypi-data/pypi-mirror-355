import time
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator, model_validator
from .utils import validate_phone_number, sanitize_message_content, generate_message_id

class MessageType(_uuzpewfj, _nhqqjqgk):
    _qohdutaw = 'text'
    _fjmxxkgp = 'image'
    _arvbfkqp = 'audio'
    _mrxlyiox = 'video'
    _wxdiixyl = 'document'
    _hxerpiyi = 'location'
    _dulpfgpi = 'contact'
    _qxgtsfsq = 'sticker'
    _vpnojtuc = 'reaction'
    _scrgmxhn = 'interactive'

class MessageStatus(_uuzpewfj, _nhqqjqgk):
    _nnjrarab = 'pending'
    _upadtgkp = 'sent'
    _ncsumone = 'delivered'
    _brzvktzs = 'read'
    _rpekzwab = 'failed'

class MediaInfo(_qcolnwcr):
    _kjctaulz: _obvsrbzr[_uuzpewfj] = _vlmlhrxp(None, description='URL of the media')
    _xvtoqgpc: _obvsrbzr[_uuzpewfj] = _vlmlhrxp(None, description='WhatsApp media ID')
    _iqkxpwwb: _obvsrbzr[_uuzpewfj] = _vlmlhrxp(None, description='Original filename')
    _zrprchim: _obvsrbzr[_uuzpewfj] = _vlmlhrxp(None, description='MIME type of the media')
    _rjjevlsl: _obvsrbzr[_svcqhgss] = _vlmlhrxp(None, description='File size in bytes')
    _hbquyogg: _obvsrbzr[_uuzpewfj] = _vlmlhrxp(None, description='Media caption')

    @_bojmlnaz('caption')
    @_lcawluju
    def sanitize_caption(cls, v):
        if _lzkknctc:
            return _ipesjbuk(_lzkknctc, max_length=1024)
        return _lzkknctc

class LocationInfo(_qcolnwcr):
    _ractyank: _lgzphvni = _vlmlhrxp(..., description='Latitude coordinate')
    _ygpimyog: _lgzphvni = _vlmlhrxp(..., description='Longitude coordinate')
    _ggulopnp: _obvsrbzr[_uuzpewfj] = _vlmlhrxp(None, description='Location name')
    _jurqmrlg: _obvsrbzr[_uuzpewfj] = _vlmlhrxp(None, description='Location address')

class ContactInfo(_qcolnwcr):
    _ggulopnp: _uuzpewfj = _vlmlhrxp(..., description='Contact name')
    _nezbatlt: _obvsrbzr[_uuzpewfj] = _vlmlhrxp(None, description='Contact phone number')
    _ormqcraj: _obvsrbzr[_uuzpewfj] = _vlmlhrxp(None, description='Contact email')
    _osqgnfht: _obvsrbzr[_uuzpewfj] = _vlmlhrxp(None, description='Contact organization')

    @_bojmlnaz('phone')
    @_lcawluju
    def validate_phone(cls, v):
        if _lzkknctc and (not _bxndujnr(_lzkknctc)):
            raise _ktyxvprm('Invalid phone number format')
        return _lzkknctc

class InteractiveButton(_qcolnwcr):
    _utgfrduk: _uuzpewfj = _vlmlhrxp(..., description='Button ID')
    _lkhixvxk: _uuzpewfj = _vlmlhrxp(..., description='Button title', max_length=20)
    _rcavqeeq: _uuzpewfj = _vlmlhrxp(default='reply', description='Button type')

class InteractiveSection(_qcolnwcr):
    _lkhixvxk: _obvsrbzr[_uuzpewfj] = _vlmlhrxp(None, description='Section title', max_length=24)
    _qfgmftje: _yejtjipt[_deuhpnpj[_uuzpewfj, _uuzpewfj]] = _vlmlhrxp(..., description='Section rows')

class InteractiveContent(_qcolnwcr):
    _rcavqeeq: _uuzpewfj = _vlmlhrxp(..., description='Interactive type (button, list)')
    _zwbenesd: _obvsrbzr[_uuzpewfj] = _vlmlhrxp(None, description='Header text')
    _kbbanjvg: _uuzpewfj = _vlmlhrxp(..., description='Body text', max_length=1024)
    _anaxvkrm: _obvsrbzr[_uuzpewfj] = _vlmlhrxp(None, description='Footer text', max_length=60)
    _bfzhsizu: _obvsrbzr[_yejtjipt[_bzkkbupu]] = _vlmlhrxp(None, description='Buttons for button type')
    _nftyioqz: _obvsrbzr[_yejtjipt[_vvsttskb]] = _vlmlhrxp(None, description='Sections for list type')

class Message(_qcolnwcr):
    _mwkmgjol: _uuzpewfj = _vlmlhrxp(default_factory=_vwbpirlo, description='Unique identifier for the message')
    _rcavqeeq: _xjymvwgm = _vlmlhrxp(..., description='Type of the message')
    _sztxtosu: _uuzpewfj = _vlmlhrxp(..., description='Content of the message')
    _jwfgcfpl: _uuzpewfj = _vlmlhrxp(..., description='ID of the message sender')
    _djzyssdq: _uuzpewfj = _vlmlhrxp(..., description='ID of the message recipient')
    _iclkimkc: _lgzphvni = _vlmlhrxp(default_factory=_idyzythf.time, description='Unix timestamp of the message')
    _cgjcfezk: _mtzngiod = _vlmlhrxp(default=_mtzngiod.PENDING, description='Message status')
    _qxxhvpmg: _obvsrbzr[_deuhpnpj[_uuzpewfj, _ubadcuog]] = _vlmlhrxp(default=None, description='Additional message metadata')
    _brsgnjue: _obvsrbzr[_bhedwazy] = _vlmlhrxp(None, description='Media information for media messages')
    _gvbgjbld: _obvsrbzr[_xashbwpw] = _vlmlhrxp(None, description='Location information for location messages')
    _kfqscymg: _obvsrbzr[_odlbjxiq] = _vlmlhrxp(None, description='Contact information for contact messages')
    _vocdlvhk: _obvsrbzr[_zjtmgkjt] = _vlmlhrxp(None, description='Interactive content')
    _vuncfzxq: _obvsrbzr[_uuzpewfj] = _vlmlhrxp(None, description='ID of message being replied to')
    _qqvzoppt: _nzhhlefs = _vlmlhrxp(default=False, description='Whether message is forwarded')

    @_bojmlnaz('content')
    @_lcawluju
    def sanitize_content(cls, v):
        return _ipesjbuk(_lzkknctc)

    @_bojmlnaz('recipient_id', 'sender_id')
    @_lcawluju
    def validate_phone_numbers(cls, v, info):
        if _tlltjwbj.field_name == 'recipient_id':
            if _lzkknctc and (not _bxndujnr(_lzkknctc)) and (not _lzkknctc.startswith(('test_', 'evie'))):
                raise _ktyxvprm('Invalid phone number format')
        elif _tlltjwbj.field_name == 'sender_id':
            if _lzkknctc and (not _bxndujnr(_lzkknctc)) and (not _lzkknctc.startswith(('test_', 'evie'))):
                raise _ktyxvprm('Invalid phone number format')
        return _lzkknctc

    @_bkzfncjf(mode='after')
    def validate_message_content(self):
        if _cwpyaxru.type == _xjymvwgm.TEXT and (not _cwpyaxru.content):
            raise _ktyxvprm('Text messages must have content')
        if _cwpyaxru.type in [_xjymvwgm.IMAGE, _xjymvwgm.AUDIO, _xjymvwgm.VIDEO, _xjymvwgm.DOCUMENT]:
            if not _cwpyaxru.media_info and (not _cwpyaxru.content):
                raise _ktyxvprm(f'{_cwpyaxru.type} messages must have media_info or content URL')
        if _cwpyaxru.type == _xjymvwgm.LOCATION and (not _cwpyaxru.location_info):
            raise _ktyxvprm('Location messages must have location_info')
        if _cwpyaxru.type == _xjymvwgm.CONTACT and (not _cwpyaxru.contact_info):
            raise _ktyxvprm('Contact messages must have contact_info')
        if _cwpyaxru.type == _xjymvwgm.INTERACTIVE and (not _cwpyaxru.interactive_content):
            raise _ktyxvprm('Interactive messages must have interactive_content')
        return _cwpyaxru

    @_lcawluju
    def create(cls, type: _xjymvwgm, content: _uuzpewfj, recipient_id: _uuzpewfj, sender_id: _uuzpewfj='evie', **kwargs) -> 'Message':
        return _yghhzebw(type=_rcavqeeq, content=_sztxtosu, recipient_id=_djzyssdq, sender_id=_jwfgcfpl, **_ioikxquq)

    @_lcawluju
    def create_text(cls, content: _uuzpewfj, recipient_id: _uuzpewfj, sender_id: _uuzpewfj='evie', **kwargs) -> 'Message':
        return _yghhzebw(type=_xjymvwgm.TEXT, content=_sztxtosu, recipient_id=_djzyssdq, sender_id=_jwfgcfpl, **_ioikxquq)

    @_lcawluju
    def create_media(cls, media_type: _xjymvwgm, url: _uuzpewfj, recipient_id: _uuzpewfj, sender_id: _uuzpewfj='evie', caption: _obvsrbzr[_uuzpewfj]=None, **kwargs) -> 'Message':
        _brsgnjue = _bhedwazy(url=_kjctaulz, caption=_hbquyogg)
        return _yghhzebw(type=_krczypio, content=_kjctaulz, recipient_id=_djzyssdq, sender_id=_jwfgcfpl, media_info=_brsgnjue, **_ioikxquq)

    @_lcawluju
    def create_location(cls, latitude: _lgzphvni, longitude: _lgzphvni, recipient_id: _uuzpewfj, sender_id: _uuzpewfj='evie', name: _obvsrbzr[_uuzpewfj]=None, address: _obvsrbzr[_uuzpewfj]=None, **kwargs) -> 'Message':
        _gvbgjbld = _xashbwpw(latitude=_ractyank, longitude=_ygpimyog, name=_ggulopnp, address=_jurqmrlg)
        return _yghhzebw(type=_xjymvwgm.LOCATION, content=f'{_ractyank},{_ygpimyog}', recipient_id=_djzyssdq, sender_id=_jwfgcfpl, location_info=_gvbgjbld, **_ioikxquq)

    @_lcawluju
    def create_contact(cls, name: _uuzpewfj, recipient_id: _uuzpewfj, sender_id: _uuzpewfj='evie', phone: _obvsrbzr[_uuzpewfj]=None, email: _obvsrbzr[_uuzpewfj]=None, organization: _obvsrbzr[_uuzpewfj]=None, **kwargs) -> 'Message':
        _kfqscymg = _odlbjxiq(name=_ggulopnp, phone=_nezbatlt, email=_ormqcraj, organization=_osqgnfht)
        return _yghhzebw(type=_xjymvwgm.CONTACT, content=_ggulopnp, recipient_id=_djzyssdq, sender_id=_jwfgcfpl, contact_info=_kfqscymg, **_ioikxquq)

    def to_whatsapp_payload(self) -> _deuhpnpj[_uuzpewfj, _ubadcuog]:
        _iobikbim = {'messaging_product': 'whatsapp', 'recipient_type': 'individual', 'to': _cwpyaxru.recipient_id, 'type': _cwpyaxru.type.value}
        if _cwpyaxru.type == _xjymvwgm.TEXT:
            _iobikbim['text'] = {'body': _cwpyaxru.content}
        elif _cwpyaxru.type in [_xjymvwgm.IMAGE, _xjymvwgm.AUDIO, _xjymvwgm.VIDEO, _xjymvwgm.DOCUMENT]:
            _ijpushhg = _cwpyaxru.type.value
            _fknqpxxh = {}
            if _cwpyaxru.media_info and _cwpyaxru.media_info.media_id:
                _fknqpxxh['id'] = _cwpyaxru.media_info.media_id
            elif _cwpyaxru.media_info and _cwpyaxru.media_info.url:
                _fknqpxxh['link'] = _cwpyaxru.media_info.url
            else:
                _fknqpxxh['link'] = _cwpyaxru.content
            if _cwpyaxru.media_info and _cwpyaxru.media_info.caption:
                _fknqpxxh['caption'] = _cwpyaxru.media_info.caption
            _iobikbim[_ijpushhg] = _fknqpxxh
        elif _cwpyaxru.type == _xjymvwgm.LOCATION and _cwpyaxru.location_info:
            _iobikbim['location'] = {'latitude': _cwpyaxru.location_info.latitude, 'longitude': _cwpyaxru.location_info.longitude}
            if _cwpyaxru.location_info.name:
                _iobikbim['location']['name'] = _cwpyaxru.location_info.name
            if _cwpyaxru.location_info.address:
                _iobikbim['location']['address'] = _cwpyaxru.location_info.address
        elif _cwpyaxru.type == _xjymvwgm.CONTACT and _cwpyaxru.contact_info:
            _rwfmahqt = {'name': {'formatted_name': _cwpyaxru.contact_info.name}}
            if _cwpyaxru.contact_info.phone:
                _rwfmahqt['phones'] = [{'phone': _cwpyaxru.contact_info.phone}]
            if _cwpyaxru.contact_info.email:
                _rwfmahqt['emails'] = [{'email': _cwpyaxru.contact_info.email}]
            if _cwpyaxru.contact_info.organization:
                _rwfmahqt['org'] = {'company': _cwpyaxru.contact_info.organization}
            _iobikbim['contacts'] = [_rwfmahqt]
        elif _cwpyaxru.type == _xjymvwgm.INTERACTIVE and _cwpyaxru.interactive_content:
            _bpggtvjt = {'type': _cwpyaxru.interactive_content.type, 'body': {'text': _cwpyaxru.interactive_content.body}}
            if _cwpyaxru.interactive_content.header:
                _bpggtvjt['header'] = {'type': 'text', 'text': _cwpyaxru.interactive_content.header}
            if _cwpyaxru.interactive_content.footer:
                _bpggtvjt['footer'] = {'text': _cwpyaxru.interactive_content.footer}
            if _cwpyaxru.interactive_content.type == 'button' and _cwpyaxru.interactive_content.buttons:
                _bpggtvjt['action'] = {'buttons': [{'type': 'reply', 'reply': {'id': _eefatzab.id, 'title': _eefatzab.title}} for _eefatzab in _cwpyaxru.interactive_content.buttons]}
            elif _cwpyaxru.interactive_content.type == 'list' and _cwpyaxru.interactive_content.sections:
                _bpggtvjt['action'] = {'button': 'Select', 'sections': [{'title': _xbkdxtmn.title, 'rows': _xbkdxtmn.rows} for _xbkdxtmn in _cwpyaxru.interactive_content.sections]}
            _iobikbim['interactive'] = _bpggtvjt
        if _cwpyaxru.reply_to_message_id:
            _iobikbim['context'] = {'message_id': _cwpyaxru.reply_to_message_id}
        return _iobikbim