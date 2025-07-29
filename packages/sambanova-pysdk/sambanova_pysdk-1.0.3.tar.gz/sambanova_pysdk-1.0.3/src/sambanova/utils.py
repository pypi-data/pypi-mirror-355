def parse_sse_stream(response):
    for line in response.iter_lines(decode_unicode=True):
        if line.startswith("data: "):
            yield line[len("data: "):].strip()
