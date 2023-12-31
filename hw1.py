"""Kevin Monahan
Computer Networks - Homework 1
9/29/2023
Takes a url compliant with HTTP 1.1 mostly
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
    after_http = url.split('://', 1)[1]
    url_parts = after_http.split('/', 1)
    combined_parts = http_part + url_parts[0] + append_to_url
    if len(url_parts) == 1:
        connect_string = "GET " + url + combined_parts
    else:
        connect_string = "GET /" + url_parts[1] + combined_parts
    check_for_port_num = url_parts[0].split(':')
    port_num = 80
    if len(check_for_port_num) == 2:
        port_num = int(check_for_port_num[1])
    return check_for_port_num[0], connect_string, port_num


def recv_response_with_length(sock, amount):
    """Takes in a given number if it is larger than
    4096 we only 4096 bits to be received by the socket.
    Otherwise, we receive exactly what the user requested"""
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
            temp_num = chunk_len - num_of_characters
            while temp_num != 0:
                split_response += recv_response_with_length(sock, temp_num)
                temp_num = chunk_len - len(split_response) - num_of_characters
            chunked_response += split_response
            temp = sock.recv(DEFAULT)
        split_response = temp.split(CRLF, 1)
        if split_response[0] == b'':
            split_response = split_response[1]
            split_response = split_response.split(CRLF, 1)
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
    if int(header_info[0][0].split()[1]) != 200:
        return None
    transfer_encoding = False
    content_length = 0
    for each in header_info:
        if each[0] == b'Content-Length':
            content_length = int(each[1])
            break
        if each[0] == b"Transfer-Encoding" and each[1] == b'chunked':
            transfer_encoding = True
            break
    if not transfer_encoding:
        while content_length > len(body_response):
            temp_num = content_length - len(body_response)
            body_response += recv_response_with_length(sock, temp_num)
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
    ans = recv_response(sock)
    sock.close()
    return ans
