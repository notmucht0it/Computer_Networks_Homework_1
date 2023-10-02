"""Kevin Monahan
Computer Networks - Homework 1
9/29/2023
Takes a url complient with HTTP 1.1 mostly
and returns the body of the website"""
import socket

CRLF = b'\r\n'
DEFAULT = 4096


def parse_url(url):

    """Parses the given url into the base url, the string
    needed to receive information from the site, and the port
    number"""
    append_to_url = ("\r\nUser-Agent: Firefox/3.6.10\r\n"
                     "Accept: text/html,application/xhtml+xml\r\n"
                     "Accept-Language: en-us,en;q=0.5\r\n"
                     "Accept-Charset: ISO-8859-1,utf-8;q=0.7\r\n"
                     "Keep-Alive: 200\r\n"
                     "Connection: keep-alive\r\n\r\n")
    http_part = " HTTP/1.1\r\nHost: "
    afterhttp = url.split('://', 1)[1]
    urlparts = afterhttp.split('/', 1)
    combined_parts = http_part + urlparts[0] + append_to_url
    if len(urlparts) == 1:
        connect_string = "GET " + url + combined_parts
    else:
        connect_string = "GET /" + urlparts[1] + combined_parts
    check_for_port_num = urlparts[0].split(':')
    port_num = 80
    if len(check_for_port_num) == 2:
        port_num = int(check_for_port_num[1])
    return check_for_port_num[0], connect_string, port_num


def recv_response_with_length(sock, amount):
    if amount > DEFAULT:
        return sock.recv(DEFAULT)
    return sock.recv(amount)


def chunking(sock, body_response):
    """Deals with chunk encoding"""
    chunked_response = b''
    split_response = body_response.split(CRLF, 1)
    chunk_len = int(split_response[0], 16)
    split_response.pop(0)
    while chunk_len != 0:
        if len(split_response[0]) >= chunk_len:
            chunked_response += split_response[0][:chunk_len]
            temp = split_response[0][chunk_len:]
            if temp == CRLF:
                temp = sock.recv(DEFAULT)
            else:
                temp = temp.split(CRLF, 1)[1]
        else:
            chunked_response += split_response[0]
            num_of_characters = len(split_response[0])
            split_response = b''
            while len(split_response) < chunk_len:
                split_response += recv_response_with_length(sock, chunk_len - num_of_characters)
            chunked_response += split_response
            temp = sock.recv(DEFAULT)
        split_response = temp.split(CRLF, 1)
        chunk_len = int(split_response[0], 16)
        split_response.pop(0)
    return chunked_response


def recv_response(sock):
    """Receives the response from the socket and parse out the information
    returning the body of the http request if we receive 200 from the site"""
    response = sock.recv(DEFAULT)
    response_split_by_clrf = response.split(CRLF)
    if len(response_split_by_clrf) == 1:
        return None
    body_response = response.split(CRLF + CRLF, 1)[1]
    header_info = []
    for each in response_split_by_clrf:
        if each == b'':
            break
        header_info.append(each.split(b': '))
    request_valid = int(header_info[0][0].split()[1])
    if request_valid != 200:
        return None
    transfer_encoding = False
    content_length = 0
    for each in header_info:
        if each[0] == b'Content-Length':
            content_length = int(each[1])
        if each[0] == b"Transfer-Encoding" and each[1] == b'chunked':
            transfer_encoding = True
            break
    if not transfer_encoding:
        while content_length > len(body_response):
            body_response += recv_response_with_length(sock, content_length - len(body_response))
        return body_response
    return chunking(sock, body_response)


def retrieve_url(url):
    """Takes in a url and returns the body of the website associated. Returns
    none if the website does not exist or the website does not respond 200"""
    url_info = parse_url(url)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        ip_addr = socket.gethostbyname(url_info[0])
        sock.connect((ip_addr, url_info[2]))
    except (socket.gaierror, TimeoutError):
        return None
    byte_val = url_info[1].encode()
    sock.sendall(byte_val)
    return recv_response(sock)
