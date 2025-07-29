# kn_sock/cli.py

import argparse
import sys
from kn_sock.tcp import send_tcp_message, start_tcp_server
from kn_sock.udp import send_udp_message, start_udp_server
from kn_sock.file_transfer import send_file_async, start_file_server_async


def tcp_echo_handler(data, addr, conn):
    print(f"[TCP][SERVER] Received from {addr}: {data.decode()}")
    conn.sendall(b"Echo: " + data)


def udp_echo_handler(data, addr, sock):
    print(f"[UDP][SERVER] Received from {addr}: {data.decode()}")
    sock.sendto(b"Echo: " + data, addr)


def run_cli():
    parser = argparse.ArgumentParser(
        description="kn-sock: Simplified socket utilities"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --------------------------
    # send-tcp
    # --------------------------
    tcp_send = subparsers.add_parser("send-tcp", help="Send a TCP message to a host:port")
    tcp_send.add_argument("host", type=str, help="Target host (e.g., localhost)")
    tcp_send.add_argument("port", type=int, help="Target port (e.g., 8080)")
    tcp_send.add_argument("message", type=str, help="Message to send")

    # --------------------------
    # run-tcp-server
    # --------------------------
    tcp_server = subparsers.add_parser("run-tcp-server", help="Start a TCP echo server")
    tcp_server.add_argument("port", type=int, help="Port to bind the TCP server")

    # --------------------------
    # send-udp
    # --------------------------
    udp_send = subparsers.add_parser("send-udp", help="Send a UDP message to a host:port")
    udp_send.add_argument("host", type=str, help="Target host (e.g., localhost)")
    udp_send.add_argument("port", type=int, help="Target port (e.g., 8080)")
    udp_send.add_argument("message", type=str, help="Message to send")

    # --------------------------
    # run-udp-server
    # --------------------------
    udp_server = subparsers.add_parser("run-udp-server", help="Start a UDP echo server")
    udp_server.add_argument("port", type=int, help="Port to bind the UDP server")

    # --------------------------
    # send-file
    # --------------------------
    file_send = subparsers.add_parser("send-file", help="Send a file over TCP")
    file_send.add_argument("host", type=str, help="Target host (e.g., localhost)")
    file_send.add_argument("port", type=int, help="Target port (e.g., 8080)")
    file_send.add_argument("filepath", type=str, help="Path to the file to send")

    # --------------------------
    # run-file-server
    # --------------------------
    file_server = subparsers.add_parser("run-file-server", help="Start a TCP file server to receive files")
    file_server.add_argument("port", type=int, help="Port to bind the file server")
    file_server.add_argument("save_dir", type=str, help="Directory where received files will be saved")

    # --------------------------
    # Execute command
    # --------------------------
    args = parser.parse_args()

    if args.command == "send-tcp":
        send_tcp_message(args.host, args.port, args.message)

    elif args.command == "run-tcp-server":
        start_tcp_server(args.port, tcp_echo_handler)

    elif args.command == "send-udp":
        send_udp_message(args.host, args.port, args.message)

    elif args.command == "run-udp-server":
        start_udp_server(args.port, udp_echo_handler)

    elif args.command == "send-file":
        send_file_async(args.host, args.port, args.filepath)

    elif args.command == "run-file-server":
        start_file_server_async(args.port, args.save_dir)

    else:
        parser.print_help()
        sys.exit(1)
