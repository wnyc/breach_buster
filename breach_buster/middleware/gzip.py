from __future__ import absolute_import
import re
from gzip import GzipFile
from random import Random
from io import BytesIO
from StringIO import StringIO


AVERAGE_SPAN_BETWEEN_FLUSHES = 512
APPROX_MIN_FLUSHES = 3
MIN_INTERFLUSH_INTERVAL = 16
FLUSH_LIMIT = 5

class StreamingBuffer(object):
    def __init__(self):
        self.vals = []

    def write(self, val):
        self.vals.append(val)

    def read(self):
        ret = b''.join(self.vals)
        self.vals = []
        return ret

    def flush(self):
        return

    def close(self):
        return

re_accepts_gzip = re.compile(r'\bgzip\b')
cc_delim_re = re.compile(r'\s*,\s*')

def patch_vary_headers(response, newheaders):
    """
    Adds (or updates) the "Vary" header in the given HttpResponse object.
    newheaders is a list of header names that should be in "Vary". Existing
    headers in "Vary" aren't removed.
    """
    # Note that we need to keep the original order intact, because cache
    # implementations may rely on the order of the Vary contents in, say,
    # computing an MD5 hash.
    if response.has_header('Vary'):
        vary_headers = cc_delim_re.split(response['Vary'])
    else:
        vary_headers = []
    # Use .lower() here so we treat headers as case-insensitive.
    existing_headers = set([header.lower() for header in vary_headers])
    additional_headers = [newheader for newheader in newheaders
                          if newheader.lower() not in existing_headers]
    response['Vary'] = ', '.join(vary_headers + additional_headers)


def compress_string(s):

    # avg_block_size is acutally the reciporical of the average
    # intended interflush distance.   

    rnd = Random(s)

    flushes_remaining = FLUSH_LIMIT

    if len(s) < AVERAGE_SPAN_BETWEEN_FLUSHES * APPROX_MIN_FLUSHES:
        avg_block_size = APPROX_MIN_FLUSHES / float(len(s))
    else:
        avg_block_size = 1.0 / AVERAGE_SPAN_BETWEEN_FLUSHES

    s = StringIO(s)
    zbuf = BytesIO()
    zfile = GzipFile(mode='wb', compresslevel=6, fileobj=zbuf)
    chunk = s.read(MIN_INTERFLUSH_INTERVAL + int(rnd.expovariate(avg_block_size)))
    while chunk and flushes_remaining:
        zfile.write(chunk)
        zfile.flush()
        flushes_remaining -= 1
        chunk = s.read(MIN_INTERFLUSH_INTERVAL + int(rnd.expovariate(avg_block_size)))
    zfile.write(chunk)
    zfile.write(s.read())
    zfile.close()
    return zbuf.getvalue()

# Like compress_string, but for iterators of strings.
def compress_sequence(sequence):
    avg_block_size = 1.0 / AVERAGE_SPAN_BETWEEN_FLUSHES

    buf = StreamingBuffer()
    zfile = GzipFile(mode='wb', compresslevel=6, fileobj=buf)
    # Output headers...
    yield buf.read()

    flushes_remaining = FLUSH_LIMIT
    rnd = None
    count = None
    rnd = None
    for item in sequence:
        if rnd is None:
            rnd = Random(0)
            count = int(rnd.expovariate(avg_block_size))
        chunking_buf = BytesIO(item)
        chunk = chunking_buf.read(count)
        while chunk:
            if count is not None:
                count -= len(chunk)
            zfile.write(chunk)
            if count <= 0:
                flushes_remaining -= 1
                zfile.flush()
                yield buf.read()
                if flushes_remaining:
                    count = int(rnd.expovariate(avg_block_size))
                else:
                    count = None
            if count is None:
                chunk = chunking_buf.read()
            else:
                chunk = chunking_buf.read(count)
        zfile.flush()
        yield buf.read()
        if chunk is None:
            break
        
    for item in sequence:
        zfile.write(chunking_buf.read())
        zfile.flush()
        yield buf.read()
        
    zfile.close()
    yield buf.read()

class GZipMiddleware(object):
    """
    This middleware compresses content if the browser allows gzip compression.
    It sets the Vary header accordingly, so that caches will base their storage
    on the Accept-Encoding header.
    """
    def process_response(self, request, response):
        # It's not worth attempting to compress really short responses.

        patch_vary_headers(response, ('Accept-Encoding',))

        # Avoid gzipping if we've already got a content-encoding.
        if response.has_header('Content-Encoding'):
            return response

        # MSIE have issues with gzipped response of various content types.
        if "msie" in request.META.get('HTTP_USER_AGENT', '').lower():
            ctype = response.get('Content-Type', '').lower()
            if not ctype.startswith("text/") or "javascript" in ctype:
                return response

        ae = request.META.get('HTTP_ACCEPT_ENCODING', '')
        if not re_accepts_gzip.search(ae):
            return response

        if getattr(response, 'streaming', False):
            # Delete the `Content-Length` header for streaming content, because
            # we won't know the compressed size until we stream it.
            response.streaming_content = compress_sequence(response.streaming_content)
            del response['Content-Length']
        else:
            # Return the compressed content only if it's actually shorter.
            compressed_content = compress_string(response.content)
            if len(compressed_content) >= len(response.content):
                return response
            response.content = compressed_content
            response['Content-Length'] = str(len(response.content))

        if response.has_header('ETag'):
            response['ETag'] = re.sub('"$', ';gzip"', response['ETag'])
        response['Content-Encoding'] = 'gzip'

        return response
