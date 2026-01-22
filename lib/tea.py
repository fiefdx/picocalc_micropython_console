# -*- coding: utf-8 -*-

import os
import gc
import struct
import binascii
from random import seed
from random import randint
import hashlib

from .common import exists, path_join, isfile, isdir, ticks_ms, ticks_add, ticks_diff, sleep_ms


CRYPT_BLOCK = 1024 * 8
DELTA = 0x9e3779b9
OP_32 = 0xffffffff
OP_64 = 0xffffffffffffffff


def sha1sum(content):
    #'''param content must be unicode, result is string'''
    m = hashlib.sha1(content.encode("utf-8"))
    return m.digest().hex()


def md5twice(content):
    #'''param content must be unicode, result is string'''
    m = hashlib.md5(content.encode("utf-8")).digest().hex()
    result = hashlib.md5(m).digest().hex()
    return result


def get_encrypt_length(length):
    fill_n = (8 - (length + 2)) % 8 + 2
    result = 1 + length + fill_n + 7
    return result


def get_tea_sum(tea_num, delta):
    tea_sum = 0
    for i in range(tea_num):
        tea_sum += delta
    return tea_sum&OP_32


def tea_encrypt(v, k, iterations = 32):
    '''
    v is utf-8
    '''
    v0, v1 = struct.unpack(">LL", v)
    k0, k1, k2, k3 = struct.unpack(">LLLL", k)
    tea_sum = 0
    for i in range(iterations):
        tea_sum += DELTA
        tea_sum &= OP_32
        v0 += ((((v1 << 4) & OP_32) + k0) ^ (v1 + tea_sum) ^ (((v1 >> 5) & OP_32) + k1))
        v0 &= OP_32
        v1 += ((((v0 << 4) & OP_32) + k2) ^ (v0 + tea_sum) ^ (((v0 >> 5) & OP_32) + k3))
        v1 &= OP_32
    return struct.pack('>LL', v0, v1)


def tea_decrypt(v, k, iterations = 32):
    '''
    v is utf-8
    '''
    v0, v1 = struct.unpack(">LL", v)
    k0, k1, k2, k3 = struct.unpack(">LLLL", k)
    tea_sum = 0xC6EF3720 if iterations == 32 else 0x8DDE6E40
    for i in range(iterations):
        v1 -= (((v0 << 4) + k2) ^ (v0 + tea_sum) ^ ((v0 >> 5) + k3))
        v1 &= OP_32
        v0 -= (((v1 << 4) + k0) ^ (v1 + tea_sum) ^ ((v1 >> 5) + k1))
        v0 &= OP_32
        tea_sum -= DELTA
        tea_sum &= OP_32
    return struct.pack('>LL', v0, v1)


def str_encrypt(v, k, iterations = 32):
    '''
    v is bytes or string
    k is md5 bytes or string
    iterations must be 32 or 64
    return bytes
    '''
    v = v.encode("utf-8") if isinstance(v, str) else v
    k = k.decode() if isinstance(k, bytes) else k
    iterations = 64 if iterations > 32 else 32
    # ascii str to bin str
    k = binascii.unhexlify(k)
    result = b""
    cipertext = OP_64
    pre_plaintext = OP_64
    end_char = b"\0"
    fill_n_or = 0xf8
    v_length = len(v)
    fill_n = (8 - (v_length + 2))%8 + 2
    fill_s = b""
    fill_bytes = []
    for i in range(fill_n):
        fill_bytes.append(randint(0, 0xff))
        # fill_s = fill_s + chr(0x02)
    fill_s = bytes(fill_bytes)
    v = bytes([(fill_n - 2) | fill_n_or]) + fill_s + v + end_char * 7

    for i in range(0, len(v), 8):
        if i == 0:
            encrypt_text = tea_encrypt(v[i:i + 8], k, iterations)
            result += encrypt_text
            cipertext = struct.unpack(">Q", encrypt_text)[0]
            pre_plaintext = struct.unpack(">Q", v[i:i + 8])[0]
        else:
            plaintext = struct.unpack(">Q", v[i:i + 8])[0] ^ cipertext
            encrypt_text = tea_encrypt(struct.pack(">Q", plaintext), k, iterations)
            encrypt_text = struct.pack(">Q", struct.unpack(">Q", encrypt_text)[0] ^ pre_plaintext)
            result += encrypt_text
            cipertext = struct.unpack(">Q", encrypt_text)[0]
            pre_plaintext = plaintext
    # bin to ascii return is str not unicode
    return result


def str_decrypt(v, k, iterations = 32):
    '''
    v is bytes or string
    k is md5 bytes or string
    iterations must be 32 or 64
    return bytes
    '''
    # t = ticks_ms()
    k = k.decode() if isinstance(k, bytes) else k
    iterations = 64 if iterations > 32 else 32
    # ascii to bin
    if isinstance(v, str):
        v = binascii.unhexlify(v)
    k = binascii.unhexlify(k)
    result = b""
    cipertext = OP_64
    pre_plaintext = OP_64
    pos = 0
    for i in range(0, len(v), 8):
        if i == 0:
            cipertext = struct.unpack(">Q", v[i:i + 8])[0]
            plaintext = tea_decrypt(v[i:i + 8], k, iterations)
            pos = (plaintext[0] & 0x07) + 2
            result += plaintext
            pre_plaintext = struct.unpack(">Q", plaintext)[0]
        else:
            encrypt_text = struct.pack(">Q", struct.unpack(">Q", v[i:i + 8])[0] ^ pre_plaintext)
            plaintext = tea_decrypt(encrypt_text, k, iterations)
            plaintext = struct.unpack(">Q", plaintext)[0] ^ cipertext
            result += struct.pack(">Q", plaintext)
            pre_plaintext = plaintext ^ cipertext
            cipertext = struct.unpack(">Q", v[i:i + 8])[0]

    # if result[-7:] != "\0" * 7: return None
    if result[-7:] != b"\0" * 7: return ""
    # return str not unicode
    # print(ticks_diff(ticks_ms(), t), "ms")
    return result[pos + 1: -7]


class CryptFile(object):
    def __init__(self, file_path, call_back = None, delay = 10):
        '''
        @param call_back: is a function with param process percent. like, call_back(percent). 
        '''
        self.file_name = file_path.split("/")[-1]
        self.file_path = file_path
        self.file_size = 0
        self.file_header = b"crypt"
        self.crypt_file_type = ".crypt"
        self.fname_pos = 0
        self.fname_len = 0
        self.file_pos = 0
        self.file_len = 0
        self.crypt_file_name = ""
        self.crypt_file_path = ""
        self.fp = None
        self.call_back = call_back
        self.percent = 0
        self.delay = delay
        self.start_time = 0

    def open_source_file(self):
        result = "%s is not a file!" % self.file_path
        if exists(self.file_path) and isfile(self.file_path):
            fp = open(self.file_path, "rb")
            fp.seek(0, 2)
            self.file_size = fp.tell()
            fp.seek(0, 0)
            self.fp = fp
            result = True
#             print("size: ", self.file_size)
#         else:
#             error = {"type" : "warning", "info" : "File [%s] dosen't exists!" % self.file_path}
#             self.call_back(0, error = error)
#             print("file path[%s] is not a file!" % self.file_path)
        return result
            
    def encrypt(self, key = ""):
        fname_hash = sha1sum(self.file_name)
        self.crypt_file_name = sha1sum(u"%s%s%s"%(fname_hash, self.file_size, ticks_ms())) + self.crypt_file_type
        self.crypt_file_path = path_join(path_join(*(self.file_path.split("/")[:-1])), self.crypt_file_name)
        crypt_fp = None
        crypt_key = ""
        if key != "":
            crypt_key = md5twice(key)
#             print("crypt_key: %s" % crypt_key)
        if not exists(self.crypt_file_path):
            crypt_fp = open(self.crypt_file_path, "wb")
            yield "Output: %s" % self.crypt_file_path
        else:
#             error = {"type" : "warning", "info" : "File [%s] already exists!" % self.crypt_file_path}
#             self.call_back(0, error = error)
            yield "%s exists!" % self.crypt_file_path
        if crypt_fp != None and self.fp != None:
            if crypt_key != "":
#                 if self.call_back:
#                     self.call_back(0)
                yield "0%"
                header_fname = str_encrypt(self.file_name, crypt_key)
                self.fname_pos = 25
                self.fname_len = len(header_fname)
                self.file_pos = self.fname_pos + self.fname_len
                crypt_fp.write(self.file_header)
                crypt_fp.write(struct.pack(">L", self.fname_pos))
                crypt_fp.write(struct.pack(">L", self.fname_len))
                crypt_fp.write(struct.pack(">L", self.file_pos))
                crypt_fp.write(struct.pack(">Q", self.file_len))
                crypt_fp.write(header_fname)
                crypt_size = 0
                self.start_time = ticks_ms()
                while True:
                    buf = self.fp.read(CRYPT_BLOCK)
                    if not buf:
                        self.fp.close()
                        break
                    crypt_buf = str_encrypt(buf, crypt_key)
                    # print("write block: %s B" % len(crypt_buf))
                    self.file_len += len(crypt_buf)
                    crypt_fp.write(crypt_buf)
                    crypt_size += CRYPT_BLOCK
                    if crypt_size < self.file_size and ticks_diff(ticks_ms(), self.start_time) >= self.delay:
                        percent = crypt_size * 100 / self.file_size
                        if percent > self.percent:
                            self.percent = percent
                            self.start_time = ticks_ms()
    #                             self.call_back(self.percent)
                            yield "%.2f%%" % self.percent
                crypt_fp.seek(17, 0)
                crypt_fp.write(struct.pack(">Q", self.file_len))
#                 print("file pos: %s, file len: %s" % (self.file_pos, self.file_len))
                # crypt_fp.seek(0, 2)
#                 if self.call_back:
#                     self.call_back(100)
                yield "100%"
                crypt_fp.close()
            else:
#                 error = {"type" : "warning", "info" : "Password is empty!"}
#                 self.call_back(0, error = error)
                yield "Password is empty!"
            self.fp.close()

    def decrypt(self, key = "", force = True):
        decrypt_fp = None
        crypt_key = ""
        if key != "":
            crypt_key = md5twice(key)
        if self.fp != None:
            file_header = self.fp.read(5)
            # print("file header: %s" % file_header)
            if file_header == self.file_header:
                if crypt_key != "":
                    if self.call_back:
                        self.call_back(0)
                    self.fname_pos = struct.unpack(">L", self.fp.read(4))[0]
                    self.fname_len = struct.unpack(">L", self.fp.read(4))[0]
                    self.file_pos = struct.unpack(">L", self.fp.read(4))[0]
                    self.file_len = struct.unpack(">Q", self.fp.read(8))[0]
                    # print("fname_pos: %s, fname_len: %s, file_pos: %s, file_len: %s" % (self.fname_pos, self.fname_len, self.file_pos, self.file_len))
                    self.fp.seek(self.fname_pos, 0)
                    file_name = self.fp.read(self.fname_len)
                    file_name = str_decrypt(file_name, crypt_key)
                    decrypt_file_path = path_join(path_join(*(self.file_path.split("/")[:-1])), file_name.decode("utf-8"))
                    # print(decrypt_file_path)
                    if not exists(decrypt_file_path):
                        decrypt_fp = open(decrypt_file_path, "wb")
                        yield "Output: %s" % decrypt_file_path
                    else:
                        if force:
                            os.remove(decrypt_file_path)
                            decrypt_fp = open(decrypt_file_path, "wb")
                            yield "Output: %s" % decrypt_file_path
                        else:
                            # error = {"type" : "warning", "info" : "File [%s] already exists!" % decrypt_file_path}
                            # self.call_back(0, error = error)
                            yield "%s exists!" % decrypt_file_path
                    crypt_length = get_encrypt_length(CRYPT_BLOCK)
                    # print(crypt_length)
                    crypt_size = 0
                    self.start_time = ticks_ms()
                    if decrypt_fp != None:
                        n = 0
                        while True:
                            n += 1
                            # print(n)
                            buf = ""
                            if self.file_len < crypt_length:
                                buf = self.fp.read(self.file_len)
                            else:
                                buf = self.fp.read(crypt_length)
                            if not buf:
                                self.fp.close()
                                break
                            self.file_len -= len(buf)
                            decrypt_buf = str_decrypt(buf, crypt_key)
                            decrypt_fp.write(decrypt_buf)
                            #decrypt_fp.flush()
                            #print(gc.mem_free())
                            crypt_size += crypt_length
                            if crypt_size < self.file_len and ticks_diff(ticks_ms(), self.start_time) >= self.delay:
                                percent = crypt_size * 100 / self.file_len
                                # self.call_back(percent)
                                if percent > self.percent:
                                    self.percent = percent
                                    self.start_time = ticks_ms()
                                    yield "%.2f%%" % self.percent
                            if self.file_len <= 0:
                                break
                        # if self.call_back:
                            # self.call_back(100)
                        yield "100%"
                        decrypt_fp.flush()
                        decrypt_fp.close()
                else:
                    # error = {"type" : "warning", "info" : "Password is empty!"}
                    # self.call_back(0, error = error)
                    yield "Password is empty!"
            else:
                # error = {"type" : "warning", "info" : "File [%s] is not a crypt file!" % self.file_path}
                # self.call_back(0, error = error)
                yield "%s is not a crypt file!" % self.file_path
            self.fp.close()

    def decrypt_info(self, key = ""):
        result = ""
        decrypt_fp = None
        crypt_key = ""
        if key != "":
            crypt_key = md5twice(key)
        if self.fp != None:
            file_header = self.fp.read(5)
            # print("file header: %s" % file_header)
            if file_header == self.file_header:
                if crypt_key != "":
                    self.fname_pos = struct.unpack(">L", self.fp.read(4))[0]
                    self.fname_len = struct.unpack(">L", self.fp.read(4))[0]
                    self.file_pos = struct.unpack(">L", self.fp.read(4))[0]
                    self.file_len = struct.unpack(">Q", self.fp.read(8))[0]
                    # print("fname_pos: %s, fname_len: %s, file_pos: %s, file_len: %s" % (self.fname_pos, self.fname_len, self.file_pos, self.file_len))
                    self.fp.seek(self.fname_pos, 0)
                    file_name = self.fp.read(self.fname_len)
                    file_name = str_decrypt(file_name, crypt_key)
                    result = file_name.decode("utf-8")
            else:
                # print("The file[%s] is not a crypt file!" % self.file_path)
                pass
            self.fp.close()
        return result


if __name__ == "__main__":
    # v = b"testtest"
    # k = b"b5d2099e49bdb07b8176dff5e23b3c14"
    # k = binascii.unhexlify(k)
    # print("first key: ", k)

    # r = tea_encrypt(v, k)
    # print(r)

    # r = tea_decrypt(r, k)
    # print(r)

    v = "this is a test, 这是一个测试" # .encode("utf-8")
    k = "b3be6b55584e1a4e13928e8fdb6e1e5f"
    print(type(v))

    r = str_encrypt(v, k)
    print(r, type(r))

    # import base64

    # r = '5a9e9393747a171c88582aa3fd9b9644'
    # k = '06673e0eda575ffe65cfb13843cf1a28'

    # b64 = "gryXJ1D5k3+bLByjRcffGg=="
    # k = "0d77b5ddb781eabd41d84f635fad9d25"
    # r = base64.b64decode(b64)

    # print("v: ", r, type(r), k, type(k))

    r = str_decrypt(r, k)
    
    #c = CryptFile("/slow.mp3.crypt")
    #print(c.decrypt_info(key = "111111"))
    print(r)
