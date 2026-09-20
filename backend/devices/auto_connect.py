import time
import socket
from zeroconf import ServiceBrowser, ServiceListener, Zeroconf
from backend.core.logger import app_logger
from backend.devices.core import DeviceManager

class ADBListener(ServiceListener):
    def __init__(self, device_manager: DeviceManager):
        self.device_manager = device_manager
        self.connected = False

    def remove_service(self, zeroconf, type, name):
        pass

    def update_service(self, zeroconf, type, name):
        pass

    def add_service(self, zeroconf, type, name):
        if self.connected:
            return
            
        info = zeroconf.get_service_info(type, name)
        if info:
            addresses = [socket.inet_ntoa(a) for a in info.addresses]
            if addresses:
                ip = addresses[0]
                port = info.port
                ip_port = f"{ip}:{port}"
                app_logger.info(f"[Auto-ADB] Found wireless ADB service at {ip_port}")
                
                # Attempt to connect automatically
                success = self.device_manager.connect(ip_port)
                if success:
                    app_logger.info("[Auto-ADB] Successfully connected automatically via mDNS!")
                    self.connected = True

def start_auto_adb(device_manager: DeviceManager):
    """Starts a background zeroconf browser to auto-discover wireless ADB."""
    zeroconf = Zeroconf()
    listener = ADBListener(device_manager)
    # The standard mDNS service type for Android 11+ wireless debugging
    browser = ServiceBrowser(zeroconf, "_adb-tls-connect._tcp.local.", listener)
    
    app_logger.info("[Auto-ADB] Started listening for Android Wireless Debugging on the local network...")
    return zeroconf, browser
