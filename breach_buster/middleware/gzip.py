import re

from django.utils.cache import patch_vary_headers
from random import choice, expovariate
from io import BytesIO

re_accepts_gzip = re.compile(r'\bgzip\b')


AVERAGE_SPAN_BETWEEN_FLUSHES = 1024
APPROX_MIN_FLUSHES = 4
def compress_string(s):
    if len(s) < AVERAGE_SPAN_BETWEEN_FLUSHES * APPROX_MIN_FLUSHES:
        avg_block_size = APPROX_MIN_FLUSHES / float(len(s))
    else:
        avg_block_size = 1.0 / AVERAGE_SPAN_BETWEEN_FLUSHES

    s = BytesIO(s)
    zbuf = BytesIO()
    zfile = GzipFile(mode='wb', compresslevel=choice((6,7,8)), fileobj=zbuf)
    chunk = s.read(int(expovariate(avg_block_size)))
    while chunk:
        zfile.write(chunk)
        zfile.flush()
        chunk = s.read(int(expovariate(avg_block_size)))
    zfile.close()
    return zbuf.getvalue()

# Like compress_string, but for iterators of strings.
def compress_sequence(sequence):
    avg_block_size = 1.0 / AVERAGE_SPAN_BETWEEN_FLUSHES

    buf = StreamingBuffer()
    zfile = GzipFile(mode='wb', compresslevel=choice((6, 7, 8)), fileobj=buf)
    # Output headers...
    count = int(expovariate(avg_block_size))
    chunking_buf = BytesIO()
    yield buf.read()
    for item in sequence:
        chunking_buf.write(item)
        chunk = chunking_buf.read(count)
        while chunk:
            count -= len(chunk)
            zfile.write(chunk)
            if count <= 0:
                zfile.flush()
                yield buf.read()
                count = int(expovariate(avg_block_size))
            chunk = chunking_buf.read(count)
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

        if response.streaming:
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
