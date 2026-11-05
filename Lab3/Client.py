import socket
import numpy as np
import struct


def recv_exact(sock, n):
    data = b''
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            raise ConnectionError('Połączenie zerwane')
        data += packet
    return data


def receive_all(sock):
    length = struct.unpack('<I', recv_exact(sock, 4))[0]
    message = recv_exact(sock, length)
    h, w, y_start, y_end = struct.unpack('<IIII', message[:16])
    frag = np.frombuffer(message[16:], dtype=np.uint8).reshape(h, w)
    return frag, y_start, y_end


def send_all(sock, data):
    h, w = data.shape
    message = struct.pack('<II', h, w) + data.astype('<f8').tobytes()
    sock.sendall(struct.pack('<I', len(message)))
    sock.sendall(message)


def okno3x3(img, y, x):
    h, w = img.shape
    okno = []
    for dy in (-1, 0, 1):
        yy = min(max(y + dy, 0), h - 1)
        wiersz = []
        for dx in (-1, 0, 1):
            xx = min(max(x + dx, 0), w - 1)
            wiersz.append(img[yy, xx])
        okno.append(wiersz)
    return np.array(okno)


def sobel(obraz):
    frag, y_start, y_end = obraz
    h, w = frag.shape
    wynik = np.zeros((y_end - y_start, w))

    sobel_mask_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
    sobel_mask_y = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]])

    for y in range(y_start, y_end):
        for x in range(w):
            o = okno3x3(frag, y, x)
            G_x = np.sum(o * sobel_mask_x)
            G_y = np.sum(o * sobel_mask_y)
            wynik[y - y_start, x] = np.sqrt(G_x ** 2 + G_y ** 2)

    return wynik


def client_main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('10.12.216.181', 2040))
    fragment = receive_all(client_socket)
    processed_fragment = sobel(fragment)
    send_all(client_socket, processed_fragment)
    client_socket.close()
    print('Fragment przetworzony i wysłany z powrotem do serwera')


if __name__ == '__main__':
    client_main()
