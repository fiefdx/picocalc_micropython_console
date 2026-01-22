TOKEN_KEYWORD = const("kw")
TOKEN_IDENT   = const("id")
TOKEN_NUMBER  = const("num")
TOKEN_STRING  = const("str")
TOKEN_COMMENT = const("cmt")
TOKEN_OP      = const("op")
TOKEN_WS      = const("ws")

KEYWORDS = {
    "False","None","True","and","as","assert","break",
    "class","continue","def","del","elif","else","except",
    "finally","for","from","global","if","import","in",
    "is","lambda","nonlocal","not","or","pass","raise",
    "return","try","while","with","yield"
}


def is_hex(c):
    return c.isdigit() or ("a" <= c.lower() <= "f")


def is_bin(c):
    return c == "0" or c == "1"


def is_oct(c):
    return "0" <= c <= "7"


def is_alpha(c):
    return c.isalpha() or c == "_"


def is_alnum(c):
    return c.isalpha() or c.isdigit() or c == "_"


def tokenize(code):
    tokens = []
    i = 0
    n = len(code)

    while i < n:
        c = code[i]
        start = i

        # ---------- Whitespace ----------
        if c.isspace():
            while i < n and code[i].isspace():
                i += 1
            tokens.append((TOKEN_WS, code[start:i], start, i))
            continue

        # ---------- Comment ----------
        if c == "#":
            i += 1
            while i < n and code[i] != "\n":
                i += 1
            tokens.append((TOKEN_COMMENT, code[start:i], start, i))
            continue

        # ---------- String ----------
        if c == "'" or c == '"':
            quote = c
            i += 1
            while i < n:
                if code[i] == "\\":
                    i += 2        # skip escaped char
                elif code[i] == quote:
                    i += 1
                    break
                else:
                    i += 1
            tokens.append((TOKEN_STRING, code[start:i], start, i))
            continue
        
        # ---------- Number ----------
        if c.isdigit():

            # Base-prefixed integers
            if c == "0" and i + 1 < n:
                p = code[i + 1]

                # Hexadecimal
                if p == "x" or p == "X":
                    i += 2
                    while i < n and is_hex(code[i]):
                        i += 1
                    tokens.append((TOKEN_NUMBER, code[start:i], start, i))
                    continue

                # Binary
                if p == "b" or p == "B":
                    i += 2
                    while i < n and is_bin(code[i]):
                        i += 1
                    tokens.append((TOKEN_NUMBER, code[start:i], start, i))
                    continue

                # Octal
                if p == "o" or p == "O":
                    i += 2
                    while i < n and is_oct(code[i]):
                        i += 1
                    tokens.append((TOKEN_NUMBER, code[start:i], start, i))
                    continue

            # Decimal / float
            has_dot = False
            while i < n:
                if code[i].isdigit():
                    i += 1
                elif code[i] == "." and not has_dot:
                    has_dot = True
                    i += 1
                else:
                    break

            tokens.append((TOKEN_NUMBER, code[start:i], start, i))
            continue

        # ---------- Identifier / Keyword ----------
        if is_alpha(c):
            while i < n and is_alnum(code[i]):
                i += 1
            word = code[start:i]
            ttype = TOKEN_KEYWORD if word in KEYWORDS else TOKEN_IDENT
            tokens.append((ttype, word, start, i))
            continue

        # ---------- Operator / Symbol ----------
        i += 1
        tokens.append((TOKEN_OP, c, start, i))

    return tokens
