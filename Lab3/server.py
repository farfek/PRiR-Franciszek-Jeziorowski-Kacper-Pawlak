import numpy as np
from PIL import Image, ImageOps
import socket
import struct


def send_all(sock, data):
    frag, y_start, y_end = data
    h, w = frag.shape
    message = struct.pack('<IIII', h, w, y_start, y_end) + frag.astype(np.uint8).tobytes()
    sock.sendall(struct.pack('<I', len(message)))
    sock.sendall(message)


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
    h, w = struct.unpack('<II', message[:8])
    return np.frombuffer(message[8:], dtype='<f8').reshape(h, w)


def merge_image(processed_frames):
    wynik = np.vstack(processed_frames)
    wynik = wynik / wynik.max() * 255
    Image.fromarray(wynik.astype(np.uint8)).save('TEST3.jpg')


def split_image(img, n_clients):
    frag = np.array(img, dtype=float)
    h = frag.shape[0]
    n = n_clients
    granice = np.linspace(0, h, n + 1, dtype=int)
    zadania = []
    for x in range(n):
        a = max(0, granice[x] - 1)
        b = min(h, granice[x + 1] + 1)
        zadania.append((frag[a:b], granice[x] - a, granice[x + 1] - a))
    return zadania


def server_main(image_path, n_clients):
    img = Image.open(image_path)
    img_G = ImageOps.grayscale(img)
    fragments = split_image(img_G, n_clients)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 2040))
    server_socket.listen(n_clients)
    print('Serwer nasłuchuje ...')

    klienci = []
    for i in range(n_clients):
        client_socket, client_address = server_socket.accept()
        print(f'Połączono z klientem {i + 1}: {client_address}')
        klienci.append(client_socket)

    for i, client_socket in enumerate(klienci):
        send_all(client_socket, fragments[i])

    processed_fragments = []
    for client_socket in klienci:
        processed_fragments.append(receive_all(client_socket))
        client_socket.close()

    server_socket.close()
    merge_image(processed_fragments)
    print('Obraz przetworzony zapisany jako TEST3.jpg')


if __name__ == '__main__':
    server_main('Valve_original_(1).png', 2)
