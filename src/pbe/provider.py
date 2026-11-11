import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from .io import read, write, sha, repository
from .checkpoint import retain
from .paths import request_key


USER_AGENT = 'pbe-behavioral/0.3.0'


PARAMETERS = ['temperature', 'top_p', 'seed', 'max_tokens', 'timeout_seconds', 'provider',
              'reasoning_effort', 'think', 'allowed_returned_models', 'max_transport_retries', 'max_extra_requests']


def now():
    return datetime.now(timezone.utc).isoformat()


def api_key(name):
    if name in os.environ:
        return os.environ[name]
    path = repository() / '.env'
    if not path.exists():
        return None
    try:
        lines = path.read_text(encoding='utf-8-sig').splitlines()
    except UnicodeError:
        raise ValueError('The local .env file must use UTF-8.') from None
    found, result = False, None
    for line in lines:
        line = line.strip()
        if line.startswith('export '):
            line = line[7:].lstrip()
        key, separator, value = line.partition('=')
        if not separator or key.strip() != name:
            continue
        if found:
            raise ValueError('Duplicate API key entry in .env.')
        found = True
        value = value.strip()
        if value.startswith(('"', "'")):
            end = value.find(value[0], 1)
            tail = value[end + 1:].lstrip() if end >= 1 else ''
            if end < 1 or (tail and not tail.startswith('#')):
                raise ValueError('Invalid API key quoting in .env.')
            value = value[1:end]
        else:
            value = re.split(r'\s+#', value, maxsplit=1)[0].rstrip()
        if any(c.isspace() for c in value):
            raise ValueError('API keys in .env must be a single value without whitespace.')
        # Read only the requested credential. Never execute or expand file contents.
        result = value
    return result


class Provider:
    def __init__(self, config, expected_requests, journal=None, retry_uncertain=False):
        self.config = config
        self.completed = 0
        self.expected_requests = expected_requests
        self.journal = Path(journal) if journal else None
        self.retry_uncertain = retry_uncertain
        required = {'endpoint', 'model', 'api_key_env', 'max_requests', 'max_tokens'}
        if required - set(config):
            raise ValueError('Provider configuration needs: ' + ', '.join(sorted(required)))
        if expected_requests > config['max_requests'] or config['max_tokens'] <= 0:
            raise ValueError('Planned requests exceed the configured limit.')
        if not config['endpoint'].startswith('https://'):
            raise ValueError('The provider endpoint must use HTTPS.')
        if config.get('provider', {}).get('allow_fallbacks', False):
            raise ValueError('Provider fallbacks must be disabled for study runs.')
        if 'think' in config:
            if 'reasoning_effort' in config:
                raise ValueError('Use only one reasoning control: think or reasoning_effort.')
            value = config['think']
            if type(value) is not bool and (type(value) is not str or value not in {'low', 'medium', 'high', 'max'}):
                raise ValueError('think must be a boolean or low, medium, high, max.')
        for key in ['max_transport_retries', 'max_extra_requests']:
            if type(config.get(key, 0)) is not int or config.get(key, 0) < 0:
                raise ValueError(key + ' must be a non-negative integer.')
        self.key = api_key(config['api_key_env'])
        if not self.key:
            raise ValueError('Set ' + config['api_key_env'] + ' in the environment or repository .env before using --live.')
        if self.journal and self.journal.exists():
            ledger = read(self.journal)
            if ledger['provider'] != config or ledger['planned_requests'] != expected_requests:
                raise ValueError('Provider request ledger belongs to a different configuration.')
            self.completed = len(ledger['submissions'])

    def reserve(self, folder, identifier):
        if not self.journal:
            if self.completed >= self.config['max_requests']:
                raise ValueError('Request limit reached.')
            self.completed += 1
            return
        ledger = read(self.journal) if self.journal.exists() else {
            'provider': self.config, 'planned_requests': self.expected_requests, 'submissions': []}
        key = request_key(folder.resolve(), self.journal)
        existing = {request_key(row['folder'], self.journal) for row in ledger['submissions']}
        if key not in existing and len(existing) >= self.expected_requests:
            raise ValueError('Logical request limit reached.')
        if len(ledger['submissions']) >= self.expected_requests + self.config.get('max_extra_requests', 0):
            raise ValueError('HTTP request limit reached, including recorded retries.')
        ledger['submissions'].append({'folder': key, 'request_id': identifier, 'submitted_at': now()})
        write(self.journal, ledger)
        self.completed = len(ledger['submissions'])

    def decode(self, data, status, folder):
        choices = data.get('choices')
        if not isinstance(choices, list) or len(choices) != 1 or not isinstance(choices[0].get('message'), dict):
            raise RuntimeError('Malformed provider response. The raw response is preserved.')
        choice = choices[0]
        content = choice['message'].get('content')
        if content is None and choice.get('finish_reason') in {'length', 'content_filter', 'stop'}:
            content = ''
        if not isinstance(content, str):
            raise RuntimeError('Provider returned no textual completion field.')
        allowed = self.config.get('allowed_returned_models')
        if allowed and data.get('model') not in allowed:
            raise RuntimeError('Unexpected returned model. Inspect the preserved response before proceeding.')
        row = {**status, 'status': 'completed', 'text': content,
            'provider_response_id': data.get('id'), 'returned_model': data.get('model'),
            'usage': data.get('usage', {}), 'finish_reason': choice.get('finish_reason'),
            'refusal': choice['message'].get('refusal'), 'finished_at': now(),
            'response_sha256': sha(folder / 'response.json')}
        write(folder / 'status.json', row)
        return row

    def complete(self, messages, folder):
        folder = Path(folder)
        body = {'model': self.config['model'], 'messages': messages, 'max_tokens': self.config['max_tokens'], 'n': 1}
        for key in ['temperature', 'top_p', 'seed', 'provider', 'reasoning_effort', 'think']:
            if key in self.config:
                body[key] = self.config[key]
        if folder.exists() and not self.journal:
            raise FileExistsError('Use a fresh request directory.')
        folder.mkdir(parents=True, exist_ok=True)
        retain(folder / 'request.json', body)
        retain(folder / 'provider.json', self.config)
        retain(folder / 'transport.json', {'method': 'POST', 'endpoint': self.config['endpoint'],
            'headers': {'Content-Type': 'application/json', 'User-Agent': USER_AGENT}})
        status_path = folder / 'status.json'
        attempts = sorted((folder / 'attempts').glob('*')) if self.journal else []
        target = attempts[-1] if attempts else folder
        state_path = target / 'status.json'
        if attempts and not state_path.exists():
            raise RuntimeError('Incomplete request checkpoint. Preserve it and inspect the request ledger before proceeding.')
        if state_path.exists():
            state = read(state_path)
            if state['status'] == 'completed':
                if sha(target / 'response.json') != state['response_sha256']:
                    raise ValueError('Saved provider response checksum changed.')
                return state
            if (target / 'response.json').exists():
                return self.decode(read(target / 'response.json'), state, target)
            if not self.journal:
                raise RuntimeError('Existing request has no completed response.')
            rejection = state.get('http_status') == 429
            if state.get('http_status') in {400, 401, 403, 404, 422}:
                raise RuntimeError('Provider rejected this configuration. Do not retry unchanged settings.')
            if not rejection and not self.retry_uncertain:
                raise RuntimeError('Request outcome is uncertain. Resume requires explicit --retry-uncertain to send another request.')
            if len(attempts) > self.config.get('max_transport_retries', 0):
                raise RuntimeError('Transport retry limit reached for this request.')
            if state.get('retry_after_until') and datetime.now(timezone.utc).timestamp() < state['retry_after_until']:
                raise RuntimeError('Provider rate limit is still active. Resume after the recorded retry time.')
        if self.journal:
            target = folder / 'attempts' / f'{len(attempts):03}'
            target.mkdir(parents=True, exist_ok=False)
        identifier = uuid.uuid4().hex
        status = {'status': 'submitted', 'request_id': identifier, 'started_at': now(),
            'requested_model': self.config['model'], 'retry_number': len(attempts),
            'uncertain_retry_authorized': self.retry_uncertain}
        write(target / 'status.json', status)
        self.reserve(folder, identifier)
        try:
            request = Request(self.config['endpoint'], data=json.dumps(body).encode(),
                headers={'Content-Type': 'application/json', 'User-Agent': USER_AGENT,
                         'Authorization': 'Bearer ' + self.key})
            with urlopen(request, timeout=self.config.get('timeout_seconds', 180)) as response:
                data = json.loads(response.read())
            write(target / 'response.json', data)
            row = self.decode(data, status, target)
            if target != folder:
                write(status_path, row)
            return row
        except BaseException as error:
            state = {**status, 'status': 'request_error', 'error_type': type(error).__name__,
                     'retry': False, 'finished_at': now()}
            if isinstance(error, HTTPError):
                state['http_status'] = error.code
                diagnostic = {'http_status': error.code, 'headers': {
                    name: error.headers[name].replace(self.key, '[REDACTED]')
                    for name in ['Server', 'CF-Ray', 'Content-Type', 'Retry-After']
                    if error.headers and error.headers.get(name)}}
                try:
                    diagnostic['body'] = error.read(16384).decode('utf-8', errors='replace').replace(self.key, '[REDACTED]')
                except Exception:
                    diagnostic['body_unavailable'] = True
                write(target / 'http-error.json', diagnostic)
                delay = error.headers.get('Retry-After') if error.headers else None
                if delay and delay.isdigit():
                    state['retry_after_until'] = datetime.now(timezone.utc).timestamp() + int(delay)
            write(target / 'status.json', state)
            if target != folder:
                write(status_path, state)
            if isinstance(error, (KeyboardInterrupt, SystemExit)):
                raise
            raise RuntimeError('LLM request failed. Its status and any response were saved. No automatic retry.') from error
