# -*- coding: utf-8 -*-

import json
import fire
from typing import Optional, Dict, List, Any
from my_cli_utilities_common.http_helpers import make_sync_request
from my_cli_utilities_common.pagination import paginated_display
from my_cli_utilities_common.config import BaseConfig, LoggingUtils

# Initialize logger
logger = LoggingUtils.setup_logger('device_spy_cli')

# Configuration constants
class Config(BaseConfig):
    BASE_URL = "https://device-spy-mthor.int.rclabenv.com"
    HOSTS_ENDPOINT = f"{BASE_URL}/api/v1/hosts"
    ALL_DEVICES_ENDPOINT = f"{BASE_URL}/api/v1/hosts/get_all_devices"
    LABELS_ENDPOINT = f"{BASE_URL}/api/v1/labels/"
    DEVICE_ASSETS_ENDPOINT = f"{BASE_URL}/api/v1/device_assets/"


class DeviceSpyCli:
    """
    A CLI tool to interact with the Device Spy service.
    Provides commands to query device information, available devices, and host details.
    """

    def _get_devices_data(self) -> Optional[List[Dict]]:
        """Get all devices data from API."""
        response_data = make_sync_request(Config.ALL_DEVICES_ENDPOINT)
        return response_data.get("data", []) if response_data else None

    def _get_hosts_data(self) -> Optional[List[Dict]]:
        """Get all hosts data from API."""
        response_data = make_sync_request(Config.HOSTS_ENDPOINT)
        return response_data.get("data", []) if response_data else None

    def _display_device_info(self, device: Dict) -> None:
        """Display device information in a user-friendly format."""
        print(f"\n📱 Device Information")
        print("=" * Config.DISPLAY_WIDTH)
        
        # Extract key information
        udid = device.get("udid", "N/A")
        platform = device.get("platform", "N/A")
        model = device.get("model", "N/A")
        os_version = device.get("platform_version", "N/A")
        hostname = device.get("hostname", "N/A")
        host_ip = device.get("host_ip", "N/A")
        location = device.get("location", "N/A")
        is_locked = device.get("is_locked", False)
        ip_port = device.get("ip_port", "N/A")
        
        print(f"📋 UDID:           {udid}")
        print(f"🔧 Platform:       {platform}")
        print(f"📟 Model:          {model}")
        print(f"🎯 OS Version:     {os_version}")
        print(f"🖥️  Host:           {hostname}")
        if host_ip != "N/A":
            print(f"🌐 Host IP:        {host_ip}")
        if location != "N/A":
            print(f"📍 Location:       {location}")
        if ip_port != "N/A":
            print(f"🌐 IP:Port:        {ip_port}")
        
        status = "🔒 Locked" if is_locked else "✅ Available"
        print(f"🔐 Status:         {status}")
        print("=" * Config.DISPLAY_WIDTH)

    def _get_device_location_from_assets(self, udid: str) -> Optional[str]:
        """Fetch device location from assets by UDID."""
        response_data = make_sync_request(Config.DEVICE_ASSETS_ENDPOINT)
        if response_data:
            device_assets = response_data.get("data", [])
            for device_asset in device_assets:
                if device_asset.get("udid") == udid:
                    return device_asset.get("location")
        return None

    def _get_host_alias(self, host_ip: str) -> Optional[str]:
        """Fetch host alias by IP address."""
        hosts = self._get_hosts_data()
        if hosts:
            for host in hosts:
                if host.get("hostname") == host_ip:
                    return host.get("alias")
        return None

    def udid(self, udid: str) -> None:
        """Display detailed information for a specific device."""
        print(f"\n🔍 Looking up device information...")
        print(f"   UDID: {udid}")
        
        devices = self._get_devices_data()
        if not devices:
            print(f"   ❌ Failed to fetch device data from API")
            return

        for device_data in devices:
            if udid == device_data.get("udid"):
                print(f"   ✅ Device found")
                
                # Prepare device info
                device_info = device_data.copy()
                original_hostname = device_info.get("hostname")

                # Get host alias and preserve original IP
                host_alias = self._get_host_alias(original_hostname)
                if host_alias:
                    device_info["hostname"] = host_alias
                    device_info["host_ip"] = original_hostname

                # Add IP:Port for Android devices
                if device_info.get("platform") == "android":
                    adb_port = device_info.get("adb_port")
                    if adb_port:
                        device_info["ip_port"] = f"{original_hostname}:{adb_port}"

                # Get location information
                location = self._get_device_location_from_assets(udid)
                if location:
                    device_info["location"] = location

                # Clean up unnecessary fields
                for key in ["is_simulator", "remote_control", "adb_port"]:
                    device_info.pop(key, None)

                self._display_device_info(device_info)
                return
        
        print(f"   ❌ Device with UDID '{udid}' not found")

    def available_devices(self, platform: str) -> None:
        """List available (not locked, not simulator) devices for a platform."""
        print(f"\n🔍 Finding available devices...")
        print(f"   Platform: {platform}")
        
        devices = self._get_devices_data()
        if not devices:
            print(f"   ❌ Failed to fetch device data from API")
            return

        available_devices = [
            device for device in devices
            if (not device.get("is_locked") and 
                not device.get("is_simulator") and 
                device.get("platform") == platform)
        ]

        print(f"   ✅ Found {len(available_devices)} available {platform} devices")
        
        if available_devices:
            def display_device(device: Dict, index: int) -> None:
                udid = device.get("udid", "N/A")
                model = device.get("model", "N/A")
                os_version = device.get("platform_version", "N/A")
                hostname = device.get("hostname", "N/A")
                
                print(f"\n{index}. {model} ({os_version})")
                print(f"   UDID: {udid}")
                print(f"   Host: {hostname}")
            
            title = f"📱 Available {platform.capitalize()} Devices"
            paginated_display(available_devices, display_device, title, Config.PAGE_SIZE, Config.DISPLAY_WIDTH)
            
            print("\n" + "=" * Config.DISPLAY_WIDTH)
            print(f"💡 Use 'ds udid <udid>' to get detailed information")
            print("=" * Config.DISPLAY_WIDTH)
        else:
            print(f"\n   ℹ️  No available {platform} devices found")

    def get_android_ip_port(self, udid: str) -> str:
        """Get Android device IP:Port for ADB connection."""
        devices = self._get_devices_data()
        if not devices:
            print("error")
            return "error"

        for device in devices:
            if device.get("udid") == udid:
                if device.get("is_locked"):
                    print("locked")
                    return "locked"
                elif device.get("platform") == "android" and device.get("adb_port"):
                    ip_port = f"{device.get('hostname')}:{device.get('adb_port')}"
                    print(ip_port)
                    return ip_port
                else:
                    print("not_android")
                    return "not_android"
        
        print("not_found")
        return "not_found"

    def get_host_ip(self, query_string, return_single=False):
        """Find host IP address(es) based on a query string.
        
        Args:
            query_string: The string to search for within host information
            return_single: If True, return single IP for script usage; if False, display all results
        """
        # Convert to string and handle special cases
        query_str = str(query_string)
        if query_str.startswith('0.') and len(query_str.split('.')) == 2:
            decimal_part = query_str.split('.')[1]
            if decimal_part.isdigit():
                query_str = '.' + decimal_part

        hosts = self._get_hosts_data()
        if not hosts:
            if return_single:
                print("error")
                return "error"
            else:
                print(f"   ❌ Failed to fetch host data from API")
                return

        # Find matching hosts
        found_hosts = []
        for host in hosts:
            for key, value in host.items():
                if query_str.lower() in str(value).lower():
                    found_hosts.append(host)
                    break

        # Handle results based on mode
        if return_single:
            return self._handle_single_result(found_hosts)
        else:
            self._display_host_results(found_hosts, query_str)

    def _handle_single_result(self, found_hosts: List[Dict]) -> str:
        """Handle single result for script usage."""
        if not found_hosts:
            print("not_found")
            return "not_found"
        elif len(found_hosts) == 1:
            hostname = found_hosts[0].get("hostname", "")
            if hostname:
                print(hostname)
                return hostname
            else:
                print("no_hostname")
                return "no_hostname"
        else:
            print("multiple_found")
            return "multiple_found"

    def _display_host_results(self, found_hosts: List[Dict], query_str: str) -> None:
        """Display host search results with formatting."""
        print(f"\n🔍 Searching for hosts...")
        print(f"   Query: '{query_str}'")
        
        if not found_hosts:
            print(f"   ❌ No host found matching '{query_str}'")
            return
        
        if len(found_hosts) == 1:
            host = found_hosts[0]
            hostname = host.get("hostname", "N/A")
            alias = host.get("alias", "N/A")
            print(f"   ✅ Found single host: {hostname}")
            
            print(f"\n🖥️  Host Information")
            print("=" * Config.DISPLAY_WIDTH)
            print(f"🌐 IP Address:     {hostname}")
            if alias != "N/A":
                print(f"🏷️  Alias:          {alias}")
            print("=" * Config.DISPLAY_WIDTH)
        else:
            print(f"   ✅ Found {len(found_hosts)} matching hosts")
            print(f"\n🖥️  Matching Hosts")
            print("=" * Config.DISPLAY_WIDTH)
            
            for i, host in enumerate(found_hosts, 1):
                hostname = host.get("hostname", "N/A")
                alias = host.get("alias", "N/A")
                print(f"\n{i}. {hostname}")
                if alias != "N/A":
                    print(f"   Alias: {alias}")
            
            print("\n" + "=" * Config.DISPLAY_WIDTH)

    # Public methods for different usage patterns
    def get_host_ip_for_script(self, query_string) -> str:
        """Get single host IP for shell script usage."""
        return self.get_host_ip(query_string, return_single=True)

    def get_host_ip_by_query(self, query_string) -> None:
        """Display host search results (interactive usage)."""
        self.get_host_ip(query_string, return_single=False)

    # Short aliases
    def devices(self, platform: str) -> None:
        """Short alias for available_devices."""
        self.available_devices(platform)

    def host(self, query_string) -> None:
        """Short alias for get_host_ip_by_query."""
        self.get_host_ip_by_query(query_string)

    def help(self) -> None:
        """Display available commands and their descriptions."""
        print("\033[95mDevice Spy CLI Commands\033[0m")
        print("\nAvailable commands:")
        print("  \033[1mudid <udid>\033[0m                        - Get detailed device information")
        print("  \033[1mavailable_devices <platform>\033[0m       - List available devices (android/ios)")
        print("    \033[1mdevices <platform>\033[0m               - Short alias")
        print("  \033[1mget_host_ip_by_query <query>\033[0m       - Find host IP address by query")
        print("    \033[1mhost <query>\033[0m                     - Short alias")
        print("  \033[1mhelp\033[0m                               - Show this help")
        
        print("\nExamples:")
        print("  \033[1mds udid A1B2C3D4E5F6\033[0m              - Get info for specific device")
        print("  \033[1mds devices android\033[0m                - List available Android devices")
        print("  \033[1mds host .201\033[0m                      - Find hosts with IP ending in '.201'")


def main_ds_function():
    fire.Fire(DeviceSpyCli)


if __name__ == "__main__":
    main_ds_function()
