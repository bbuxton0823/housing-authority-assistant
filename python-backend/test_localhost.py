#!/usr/bin/env python3
import socket
import sys

def test_port(host, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((host, port))
        sock.listen(1)
        print(f"✅ Successfully bound to {host}:{port}")
        sock.close()
        return True
    except Exception as e:
        print(f"❌ Failed to bind to {host}:{port} - {e}")
        return False

def test_connection(host, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((host, port))
        sock.close()
        if result == 0:
            print(f"✅ Can connect to {host}:{port}")
            return True
        else:
            print(f"❌ Cannot connect to {host}:{port}")
            return False
    except Exception as e:
        print(f"❌ Error connecting to {host}:{port} - {e}")
        return False

print("🔍 Testing network connectivity...")
print("=" * 50)

# Test binding to different addresses
test_port("127.0.0.1", 8000)
test_port("localhost", 8000)
test_port("0.0.0.0", 8000)

print()
print("Testing ports 3000 and 8000...")
test_port("127.0.0.1", 3000)
test_port("127.0.0.1", 8001)

# Test if we can reach common services
print()
print("Testing external connectivity...")
test_connection("google.com", 80)
test_connection("127.0.0.1", 22)  # SSH port