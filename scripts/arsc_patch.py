from __future__ import annotations


def patch_utf8_pool_literal(blob: bytes, old: str, new: str) -> bytes:
    """Patch a UTF-8 ResStringPool entry without moving later offsets.

    Only shorter/equal ASCII strings are supported. The unused tail remains padding.
    """
    if not old.isascii() or not new.isascii():
        raise ValueError('ASCII-only patcher')
    ob, nb = old.encode(), new.encode()
    if len(nb) > len(ob) or len(ob) > 0x7f:
        raise ValueError('replacement must be <= old ASCII length and lengths must fit one-byte prefixes')
    d = bytearray(blob)
    hits=[]; start=0
    while True:
        i = d.find(ob, start)
        if i < 0: break
        # UTF-8 ResStringPool: utf16_len, utf8_byte_len, bytes, NUL.
        if i >= 2 and d[i-2] == len(ob) and d[i-1] == len(ob) and d[i+len(ob)] == 0:
            hits.append(i)
        start = i+1
    if len(hits) != 1:
        raise ValueError(f'expected exactly one string-pool hit for {old!r}, found {len(hits)}')
    i=hits[0]
    d[i-2] = len(nb); d[i-1] = len(nb)
    d[i:i+len(nb)] = nb
    d[i+len(nb)] = 0
    # Keep the old physical slot length as zero padding.
    for q in range(i+len(nb)+1, i+len(ob)+1): d[q]=0
    return bytes(d)
