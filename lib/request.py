import gc
import usocket
import ssl


class Response:

    def __init__(self, f):
        self.raw = f
        self.encoding = "utf-8"
        self._cached = None

    def close(self):
        if self.raw:
            self.raw.close()
            self.raw = None
        self._cached = None

    @property
    def content(self):
        if self._cached is None:
            try:
                self._cached = self.raw.read()
            finally:
                self.raw.close()
                self.raw = None
        return self._cached

    @property
    def text(self):
        return str(self.content, self.encoding)

    def json(self):
        import ujson
        return ujson.loads(self.content)
    
    def cache_to_file(self, f):
        b = self.raw.read(512)
        while b:
            f.write(b)
            b = self.raw.read(512)
            
    def iter_chars(self, buf_size = 64):
        buf = bytearray(buf_size)
        n = self.raw.readinto(buf)
        while n > 0:
            for c in buf[:n]:
                yield c
            n = self.raw.readinto(buf)


def request(method, url, data=None, json=None, headers={}, stream=None,
            cache_path="/", cache_file="/request.cache",
            allow_redirects=True, max_redirects=5):

    for _ in range(max_redirects + 1):

        try:
            proto, dummy, host, path = url.split("/", 3)
        except ValueError:
            proto, dummy, host = url.split("/", 2)
            path = ""

        if proto == "http:":
            port = 80
        elif proto == "https:":
            port = 443
        else:
            raise ValueError("Unsupported protocol: " + proto)

        if ":" in host:
            host, port = host.split(":", 1)
            port = int(port)

        ai = usocket.getaddrinfo(host, port, 0, usocket.SOCK_STREAM)[0]
        s = usocket.socket(ai[0], ai[1], ai[2])

        try:
            s.connect(ai[-1])
            if proto == "https:":
                gc.collect()
                s = ssl.wrap_socket(s, server_hostname=host, cert_reqs=ssl.CERT_NONE)

            s.write(b"%s /%s HTTP/1.0\r\n" % (method, path))

            if "Host" not in headers:
                s.write(b"Host: %s\r\n" % host)

            for k in headers:
                s.write(k)
                s.write(b": ")
                s.write(headers[k])
                s.write(b"\r\n")

            if json is not None:
                assert data is None
                import ujson
                data = ujson.dumps(json)
                s.write(b"Content-Type: application/json\r\n")

            if data:
                if hasattr(data, "iter_lines"):
                    s.write(b"Content-Length: %d\r\n" % data.length())
                    s.write(b"\r\n")
                    for line in data.iter_lines():
                        s.write(line)
                else:
                    s.write(b"Content-Length: %d\r\n" % len(data))
                    s.write(b"\r\n")
                    s.write(data)
            else:
                s.write(b"\r\n")

            l = s.readline()
            parts = l.split(None, 2)
            status = int(parts[1])
            reason = parts[2].rstrip() if len(parts) > 2 else b""

            location = None

            # --- Headers ---
            while True:
                l = s.readline()
                if not l or l == b"\r\n":
                    break
                if l.startswith(b"Transfer-Encoding:") and b"chunked" in l:
                    raise ValueError("Unsupported chunked encoding")
                elif l.startswith(b"Location:"):
                    location = l[9:].strip().decode()

            # --- Redirect handling ---
            if allow_redirects and location and status in (301, 302, 303, 307, 308):
                s.close()

                if status == 303:
                    method = "GET"
                    data = None

                if location.startswith("/"):
                    url = proto + "//" + host + location
                else:
                    url = location

                continue

            resp = Response(s)
            resp.status_code = status
            resp.reason = reason
            return resp

        except:
            s.close()
            raise
    raise ValueError("Too many redirects")

def head(url, **kw):
    return request("HEAD", url, **kw)

def get(url, **kw):
    return request("GET", url, **kw)

def post(url, **kw):
    return request("POST", url, **kw)

def put(url, **kw):
    return request("PUT", url, **kw)

def patch(url, **kw):
    return request("PATCH", url, **kw)

def delete(url, **kw):
    return request("DELETE", url, **kw)