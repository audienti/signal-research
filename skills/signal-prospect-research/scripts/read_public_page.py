#!/usr/bin/env python3
"""Fetch one public HTML page and extract inspectable evidence; never qualify it."""
import argparse
import datetime as dt
import hashlib
from html.parser import HTMLParser
import ipaddress
import json
import re
from pathlib import Path
import socket
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler

def check_url(url):
    u = urlsplit(url)
    if u.scheme not in ('http', 'https') or not u.hostname or u.username or u.password:
        raise ValueError('Public HTTP(S) URL without credentials required')
    addresses = socket.getaddrinfo(u.hostname, u.port or (443 if u.scheme == 'https' else 80))
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
        raise ValueError('Only public addresses allowed')
    return url

class PublicRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return super().redirect_request(req, fp, code, msg, headers, check_url(newurl))

class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.script = None
        self.skip = 0
        self.chunks = []
        self.blocks = []
        self.text = []
        self.links = []
        self.anchor = None
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'script':
            self.script = attrs.get('type', '').split(';', 1)[0].strip().lower() == 'application/ld+json'
            self.chunks = []
        if tag in ('style', 'noscript'): self.skip += 1
        if tag == 'a': self.anchor = {'href': attrs.get('href', ''), 'text': []}
    def handle_endtag(self, tag):
        if tag == 'script':
            if self.script: self.blocks.append(''.join(self.chunks))
            self.script = None
        if tag in ('style', 'noscript'): self.skip = max(0, self.skip - 1)
        if tag == 'a' and self.anchor is not None:
            self.links.append({'href': self.anchor['href'], 'text': ' '.join(self.anchor['text'])})
            self.anchor = None
    def handle_data(self, data):
        if self.script is not None:
            if self.script: self.chunks.append(data)
        elif not self.skip and data.strip():
            self.text.append(data.strip())
            if self.anchor is not None: self.anchor['text'].append(data.strip())

def objects(value, path='$'):
    if isinstance(value, dict):
        yield path, value
        for key, child in value.items(): yield from objects(child, path + '.' + key)
    elif isinstance(value, list):
        for i, child in enumerate(value): yield from objects(child, f'{path}[{i}]')

def extract(html, url):
    page = Page(); page.feed(html)
    jobs, errors = [], []
    for i, block in enumerate(page.blocks):
        try: value = json.loads(block)
        except (ValueError, TypeError) as error:
            errors.append({'block': i, 'error': str(error)}); continue
        for path, obj in objects(value):
            types = obj.get('@type', [])
            if isinstance(types, str): types = [types]
            if not any(t in ('JobPosting', 'https://schema.org/JobPosting', 'http://schema.org/JobPosting') for t in types): continue
            description = Page(); description.feed(str(obj.get('description', '')))
            jobs.append({'jsonPath': f'jsonld[{i}]{path[1:]}', 'title': obj.get('title'),
                         'descriptionText': ' '.join(description.text),
                         'descriptionLinks': [{'url': urljoin(url, a['href']), 'text': a['text']} for a in description.links if a['href']],
                         'datePosted': obj.get('datePosted'), 'validThrough': obj.get('validThrough'),
                         'hiringOrganization': obj.get('hiringOrganization'),
                         'jobUrl': obj.get('url'), 'raw': obj,
                         'ownershipVerified': False, 'openStatus': 'unverified'})
    # Read a JSON literal, never execute JavaScript. Bind state to this posting ID.
    # isListed is source evidence, not a substitute for ownership/expiry review.
    state = None
    if urlsplit(url).hostname == 'jobs.ashbyhq.com':
        match = re.search(r'window\.__appData\s*=\s*', html)
        if match:
            try:
                app_data = json.JSONDecoder().raw_decode(html[match.end():])[0]
                posting = app_data.get('posting', {})
                if posting.get('id') == urlsplit(url).path.rstrip('/').split('/')[-1]:
                    state = {k: posting.get(k) for k in ('id', 'title', 'isListed', 'applicationDeadline')}
                    for job in jobs:
                        identifier = job['raw'].get('identifier')
                        if isinstance(identifier, dict) and identifier.get('value') == state['id']:
                            job['listingState'] = state
                            job['listingStatePath'] = 'window.__appData.posting'
            except (ValueError, AttributeError, TypeError) as error:
                errors.append({'block': 'ashby_state', 'error': str(error)})
    return {'sourceUrl': url, 'text': ' '.join(page.text),
            'links': [{'url': urljoin(url, a['href']), 'text': a['text']} for a in page.links if a['href']],
            'jobs': jobs, 'parseErrors': errors}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('url'); parser.add_argument('--out', required=True)
    parser.add_argument('--html', help='Parse a saved HTML file without claiming a live fetch')
    args = parser.parse_args()
    result = {'requestedUrl': args.url, 'fetchedAt': None, 'acquisitionMode': 'saved_html' if args.html else 'native_http', 'error': None}
    out = Path(args.out)
    if out.suffix != '.json': parser.error('--out must end in .json')
    if out.exists() or out.with_suffix('.html').exists(): parser.error('Choose an unused output name; evidence is immutable')
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        if args.html:
            body = Path(args.html).read_bytes(); final_url = args.url; encoding = 'utf-8'
        else:
            request = Request(check_url(args.url), headers={'User-Agent': 'NativeSignalResearch/1.0', 'Accept': 'text/html'})
            with build_opener(PublicRedirect).open(request, timeout=25) as response:
                final_url = response.url
                if response.headers.get_content_type() not in ('text/html', 'application/xhtml+xml'): raise ValueError('Response is not HTML')
                body = response.read(5_000_001)
                if len(body) > 5_000_000: raise ValueError('HTML exceeds 5 MB bound')
                encoding = response.headers.get_content_charset() or 'utf-8'
                result.update(httpStatus=response.status, fetchedAt=dt.datetime.now(dt.timezone.utc).isoformat())
        result.update(extract(body.decode(encoding, errors='replace'), final_url))
        raw = out.with_suffix('.html'); raw.write_bytes(body)
        result.update(rawFile=raw.name, sha256=hashlib.sha256(body).hexdigest())
    except Exception as error:
        result['error'] = {'type': type(error).__name__, 'message': str(error)}
    out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'output': str(out), 'jobs': len(result.get('jobs', [])), 'error': result['error']}))
    return 1 if result['error'] else 0

if __name__ == '__main__': raise SystemExit(main())
