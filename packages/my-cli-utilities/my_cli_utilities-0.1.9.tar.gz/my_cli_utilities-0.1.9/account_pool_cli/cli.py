# -*- coding: utf-8 -*-

import asyncio
import fire
import json
import random
import os
from typing import Optional, Union, Dict, List, Any

from my_cli_utilities_common.http_helpers import make_async_request
from my_cli_utilities_common.pagination import paginated_display
from my_cli_utilities_common.config import BaseConfig, ValidationUtils, LoggingUtils

# Initialize logger
logger = LoggingUtils.setup_logger('account_pool_cli')

# Configuration constants
class Config(BaseConfig):
    BASE_URL = "https://account-pool-mthor.int.rclabenv.com"
    ACCOUNTS_ENDPOINT = f"{BASE_URL}/accounts"
    ACCOUNT_SETTINGS_ENDPOINT = f"{BASE_URL}/accountSettings"
    CACHE_FILE = BaseConfig.get_cache_file("account_pool_cli_cache.json")
    DEFAULT_ENV_NAME = "webaqaxmn"
    DEFAULT_BRAND = "1210"
    DISPLAY_WIDTH = 80
    CACHE_DISPLAY_WIDTH = 60
    MAX_DISPLAY_LENGTH = 80

class CacheManager:
    """Handles cache operations for account types."""
    
    @staticmethod
    def save_cache(account_types: List[str], filter_keyword: Optional[str], brand: str) -> None:
        """Save account types to cache."""
        cache_data = {
            "account_types": account_types,
            "filter_keyword": filter_keyword,
            "brand": brand
        }
        try:
            with open(Config.CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")
    
    @staticmethod
    def load_cache() -> Optional[Dict[str, Any]]:
        """Load cache data."""
        try:
            with open(Config.CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Failed to load cache: {e}")
            return None
    
    @staticmethod
    def get_account_type_by_index(index: int) -> Optional[str]:
        """Get account type by index from cache."""
        cache_data = CacheManager.load_cache()
        if not cache_data:
            logger.error("No cached account types found. Please run 'ap types' first")
            return None
        
        account_types = cache_data.get("account_types", [])
        if 1 <= index <= len(account_types):
            return account_types[index - 1]  # Convert to 0-based index
        else:
            logger.error(f"Index {index} is out of range. Available indices: 1-{len(account_types)}")
            logger.info("Please run 'ap types' first to see available account types")
            return None
    
    @staticmethod
    def clear_cache() -> bool:
        """Clear the cache file. Returns True if successful."""
        try:
            if os.path.exists(Config.CACHE_FILE):
                os.remove(Config.CACHE_FILE)
                logger.info("Cache cleared successfully")
                return True
            else:
                logger.info("No cache file to clear")
                return False
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False


class AccountPoolCli:
    """
    A CLI tool to interact with the Account Pool service.
    Provides commands to fetch random accounts, specific account details by ID,
    or specific account details by main number.
    env_name defaults to 'webaqaxmn' if not provided for relevant commands.
    """

    @staticmethod
    def _print_json(data: Any, title: str = "") -> None:
        """Print JSON data with optional title."""
        if title:
            logger.info(title)
        print(json.dumps(data, indent=2, ensure_ascii=False))

    # Use utility methods from common module
    _is_numeric_string = staticmethod(ValidationUtils.is_numeric_string)
    _normalize_phone_number = staticmethod(ValidationUtils.normalize_phone_number)
    _truncate_text = staticmethod(ValidationUtils.truncate_text)
    
    def _display_account_info(self, account: Dict) -> None:
        """Display account information in a user-friendly format."""
        print(f"\n✅ Account Found!")
        print("=" * 50)
        
        # Extract key information
        account_id = account.get("accountId", "N/A")
        main_number = account.get("mainNumber", "N/A")
        account_type = account.get("accountType", "N/A")
        env_name = account.get("envName", "N/A")
        email_domain = account.get("companyEmailDomain", "N/A")
        created_at = account.get("createdAt", "N/A")
        mongo_id = account.get("_id", "N/A")
        
        # Format creation date
        if created_at != "N/A":
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                created_at = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
            except:
                pass  # Keep original format if parsing fails
        
        # Remove + sign from phone number display
        display_phone = main_number.lstrip('+') if main_number != "N/A" else main_number
        print(f"📱 Phone Number:    {display_phone}")
        print(f"🆔 Account ID:      {account_id}")
        print(f"🏷️  Account Type:    {account_type}")
        print(f"🌐 Environment:     {env_name}")
        print(f"📧 Email Domain:    {email_domain}")
        print(f"📅 Created:         {created_at}")
        print(f"🔗 MongoDB ID:      {mongo_id}")
        
        # Show lock status
        locked = account.get("locked", [])
        if locked and len(locked) > 0:
            print(f"🔒 Status:          🔴 LOCKED")
            print(f"   Locked Count:    {len(locked)} item(s)")
            # Show details of locked items if they have useful info
            for i, lock_item in enumerate(locked, 1):
                if isinstance(lock_item, dict):
                    lock_type = lock_item.get("accountType", "Unknown")
                    lock_phone = lock_item.get("mainNumber", "N/A")
                    print(f"   Lock #{i}:        Type: {lock_type}")
                    if lock_phone != "N/A":
                        print(f"                    Phone: {lock_phone}")
                else:
                    print(f"   Lock #{i}:        {str(lock_item)}")
        else:
            print(f"🔒 Status:          🟢 AVAILABLE")
        
        print("=" * 50)



    async def _fetch_random_account_async(self, env_name: str, account_type: str) -> None:
        """Fetch a random account asynchronously."""
        params = {"envName": env_name, "accountType": account_type}
        
        # Display user-friendly search info
        print(f"\n🔍 Searching for account...")
        print(f"   🏷️  Account Type: {account_type}")
        print(f"   🌐 Environment: {env_name}")
        
        response_data = await make_async_request(Config.ACCOUNTS_ENDPOINT, params=params)
        if not response_data:
            return

        try:
            accounts_list = response_data.get("accounts")
            if accounts_list:
                random_account = random.choice(accounts_list)
                self._display_account_info(random_account)
            else:
                logger.warning("No matching accounts found, or the 'accounts' list is empty.")
        except (TypeError, KeyError) as e:
            logger.error(f"Failed to extract account information from response data: {e}")
            logger.debug("Raw data received: " + (json.dumps(response_data, indent=2, ensure_ascii=False) if isinstance(response_data, dict) else str(response_data)))

    def get_random_account(self, account_type: Union[str, int], env_name: str = Config.DEFAULT_ENV_NAME) -> None:
        """Fetches a random account from the Account Pool.

        Args:
            account_type: Account type string or index number from 'types' command.
            env_name: Environment name. Defaults to "webaqaxmn".
        """
        if self._is_numeric_string(account_type):
            index = int(account_type)
            actual_account_type = CacheManager.get_account_type_by_index(index)
            if actual_account_type is None:
                return
            logger.info(f"Using account type from index {index}: {actual_account_type}")
            asyncio.run(self._fetch_random_account_async(env_name, actual_account_type))
        else:
            asyncio.run(self._fetch_random_account_async(env_name, str(account_type)))

    def get(self, account_type: Union[str, int], env_name: str = Config.DEFAULT_ENV_NAME) -> None:
        """Short alias for get_random_account. Fetches a random account."""
        self.get_random_account(account_type, env_name)

    async def _fetch_account_by_id_async(self, account_id: str, env_name: str) -> None:
        """Fetch account details by ID asynchronously."""
        url = f"{Config.ACCOUNTS_ENDPOINT}/{account_id}"
        params = {"envName": env_name}
        
        print(f"\n🔍 Looking up account by ID...")
        print(f"   🆔 Account ID: {account_id}")
        print(f"   🌐 Environment: {env_name}")
        
        account_details = await make_async_request(url, params=params)
        if account_details:
            self._display_account_info(account_details)

    def get_account_by_id(self, account_id: str, env_name: str = Config.DEFAULT_ENV_NAME) -> None:
        """Fetches specific account details by its ID."""
        asyncio.run(self._fetch_account_by_id_async(account_id, env_name))

    def by_id(self, account_id: str, env_name: str = Config.DEFAULT_ENV_NAME) -> None:
        """Short alias for get_account_by_id. Fetches account by ID."""
        self.get_account_by_id(account_id, env_name)

    async def _fetch_info_by_main_number_async(self, main_number: Union[str, int], env_name: str) -> None:
        """Fetch account info by main number asynchronously."""
        main_number_str = self._normalize_phone_number(main_number)
        params = {"envName": env_name}  # Don't filter by mainNumber in API, filter client-side
        
        print(f"\n🔍 Looking up account by phone number...")
        print(f"   📱 Phone Number: {main_number_str}")
        print(f"   🌐 Environment: {env_name}")
        
        response_data = await make_async_request(Config.ACCOUNTS_ENDPOINT, params=params)
        if not response_data:
            return

        try:
            accounts_list = response_data.get("accounts")
            if accounts_list:
                # Filter by mainNumber on client side (like UI does)
                matching_accounts = [
                    account for account in accounts_list 
                    if account.get("mainNumber") == main_number_str
                ]
                
                if matching_accounts:
                    account_info = matching_accounts[0]  # Take first matching account
                    print(f"   ✓ Found matching account!")
                    self._display_account_info(account_info)
                else:
                    print(f"   ❌ No account found for phone number {main_number_str}")
            else:
                print(f"   ❌ No accounts found in environment {env_name}")
        except (TypeError, KeyError, IndexError) as e:
            logger.error(f"Failed to parse account information from search results: {e}")
            logger.debug("Raw data received: " + (json.dumps(response_data, indent=2, ensure_ascii=False) if isinstance(response_data, dict) else str(response_data)))

    def info(self, main_number: Union[str, int], env_name: str = Config.DEFAULT_ENV_NAME) -> None:
        """Fetches account details by mainNumber (looks up ID first)."""
        asyncio.run(self._fetch_info_by_main_number_async(main_number, env_name))

    async def _list_account_types_async(self, filter_keyword: Optional[str] = None, brand: str = Config.DEFAULT_BRAND) -> None:
        """List account types asynchronously."""
        params = {"brand": brand}
        
        # Display search info
        print(f"\n🔍 Fetching account types...")
        print(f"   🏷️  Brand: {brand}")
        if filter_keyword:
            print(f"   🔍 Filter: '{filter_keyword}'")
        
        response_data = await make_async_request(Config.ACCOUNT_SETTINGS_ENDPOINT, params=params)
        if not response_data:
            return

        try:
            account_settings = response_data.get("accountSettings")
            if not account_settings:
                print(f"   ❌ No account types found for brand {brand}")
                return

            # Filter account types if keyword provided
            if filter_keyword:
                account_settings = [
                    setting for setting in account_settings 
                    if filter_keyword.lower() in setting.get("accountType", "").lower()
                ]
                
            if not account_settings:
                print(f"   ❌ No account types found for brand {brand} with filter '{filter_keyword}'")
                return

            print(f"   ✅ Found {len(account_settings)} account types")
            self._display_account_types(account_settings, filter_keyword, brand)
            
        except (TypeError, KeyError) as e:
            logger.error(f"Failed to extract account types from response: {e}")
            logger.debug("Raw data received: " + (json.dumps(response_data, indent=2, ensure_ascii=False) if isinstance(response_data, dict) else str(response_data)))

    def _display_account_types(self, account_settings: List[Dict], filter_keyword: Optional[str], brand: str) -> None:
        """Display account types with pagination and save to cache."""
        # Extract account types for caching
        account_types = [setting.get("accountType", "N/A") for setting in account_settings]
        
        # Define the display function for each account type
        def display_account_type(setting: Dict, index: int) -> None:
            account_type = setting.get("accountType", "N/A")
            total = setting.get("total", "N/A")
            auto_fill = setting.get("autoFill", False)
            
            print(f"\n{index}. {account_type}")
            print(f"   Total: {total}, AutoFill: {auto_fill}")
        
        # Use paginated display
        filter_info = f" (filtered by '{filter_keyword}')" if filter_keyword else ""
        title = f"Available Account Types{filter_info}:"
        completed = paginated_display(
            account_settings, 
            display_account_type, 
            title, 
            Config.PAGE_SIZE, 
            Config.DISPLAY_WIDTH
        )
        
        # Save to cache regardless of whether user completed viewing
        CacheManager.save_cache(account_types, filter_keyword, brand)
        
        # Show footer information
        print("\n" + "=" * Config.DISPLAY_WIDTH)
        if completed:
            print("Copy any account type above to use with the 'get' command")
            print("Or use: ap get <index_number> to get account by index")
            print("Example: ap get 'kamino2(CI-Common-NoGuest,mThor,brand=1210)'")
            print("Example: ap get 2")
        else:
            print("Use 'ap cache' to see all cached indices")
            print("Use: ap get <index_number> to get account by index")
        print("=" * Config.DISPLAY_WIDTH)

    def list_account_types(self, filter_keyword: Optional[str] = None, brand: str = Config.DEFAULT_BRAND) -> None:
        """Lists all available account types from account settings."""
        asyncio.run(self._list_account_types_async(filter_keyword, brand))

    def types(self, filter_keyword: Optional[str] = None, brand: str = Config.DEFAULT_BRAND) -> None:
        """Short alias for list_account_types. Lists available account types."""
        self.list_account_types(filter_keyword, brand)

    def cache(self, action: Optional[str] = None) -> None:
        """Manage cache for account types."""
        if action == "clear":
            self._clear_cache()
        else:
            self._show_cache_status()

    def _show_cache_status(self) -> None:
        """Display current cache status with pagination for account types."""
        cache_data = CacheManager.load_cache()
        if not cache_data:
            self._display_no_cache_status()
            return
            
        account_types = cache_data.get("account_types", [])
        filter_keyword = cache_data.get("filter_keyword")
        brand = cache_data.get("brand", "Unknown")
        
        print("\n" + "=" * Config.CACHE_DISPLAY_WIDTH)
        print("Account Pool CLI - Cache Status")
        print("=" * Config.CACHE_DISPLAY_WIDTH)
        print(f"Cache file: {Config.CACHE_FILE}")
        print(f"Total cached account types: {len(account_types)}")
        print(f"Brand: {brand}")
        
        if filter_keyword:
            print(f"Filter keyword: '{filter_keyword}'")
        else:
            print("Filter keyword: None (showing all types)")
        
        if account_types:
            print(f"\nAvailable indices: 1-{len(account_types)}")
            
            # Use pagination for account types display  
            def display_cached_type(account_type: str, index: int) -> None:
                if index == 1:
                    print()  # Add blank line only before first item
                print(f"{index}. {account_type}")
            
            # Show with pagination
            filter_info = f" (filtered by '{filter_keyword}')" if filter_keyword else ""
            title = f"Cached Account Types{filter_info}:"
            paginated_display(
                account_types, 
                display_cached_type, 
                title, 
                Config.PAGE_SIZE, 
                Config.CACHE_DISPLAY_WIDTH
            )
        else:
            print("\nNo account types in cache")
        
        print("\n" + "=" * Config.CACHE_DISPLAY_WIDTH)
        print("Use 'ap cache clear' to clear cache")
        print("Use 'ap types' to refresh cache")
        print("=" * Config.CACHE_DISPLAY_WIDTH)

    def _display_no_cache_status(self) -> None:
        """Display status when no cache is available."""
        print("\n" + "=" * Config.CACHE_DISPLAY_WIDTH)
        print("Account Pool CLI - Cache Status")
        print("=" * Config.CACHE_DISPLAY_WIDTH)
        print("Cache file: Not found")
        print("Status: No cache available")
        print("\nRun 'ap types' to create cache")
        print("=" * Config.CACHE_DISPLAY_WIDTH)

    def _clear_cache(self) -> None:
        """Clear the cache file."""
        if CacheManager.clear_cache():
            print("✓ Cache has been cleared")
        else:
            print("ℹ No cache file found - nothing to clear")

    def help(self) -> None:
        """Display available commands and their short aliases."""
        header_color = "\033[95m"
        bold = "\033[1m"
        end = "\033[0m"
        
        print(f"{header_color}Account Pool CLI Commands{end}")
        print("\nAvailable commands:")
        print(f"  {bold}get_random_account <account_type|index> [env_name]{end}")
        print(f"    {bold}get <account_type|index> [env_name]{end}         - Short alias")
        print(f"  {bold}get_account_by_id <account_id> [env_name]{end}")
        print(f"    {bold}by_id <account_id> [env_name]{end}               - Short alias")
        print(f"  {bold}info <main_number> [env_name]{end}                - Get account by phone number")
        print(f"  {bold}list_account_types [filter_keyword] [brand]{end} - List all available account types")
        print(f"    {bold}types [filter_keyword] [brand]{end}           - Short alias")
        print(f"  {bold}cache [clear]{end}                              - Show cache status or clear cache")
        print(f"  {bold}help{end}                                       - Show this help")
        print(f"\nExamples:")
        print(f"  {bold}ap types{end}                                   - List all account types for brand 1210")
        print(f"  {bold}ap types 4U{end}                                - Filter account types containing '4U'")
        print(f"  {bold}ap types NoGuest{end}                           - Filter account types containing 'NoGuest'")
        print(f"  {bold}ap types phoneNumbers 1211{end}                 - Filter for 'phoneNumbers' in brand 1211")
        print(f"  {bold}ap get 2{end}                                   - Get account using index from types result")
        print(f"  {bold}ap cache{end}                                   - Show current cache status")
        print(f"  {bold}ap cache clear{end}                             - Clear the cache")
        print(f"  {bold}ap get 'kamino2(CI-Common-4U,mThor,brand=1210)'{end}")
        print(f"  {bold}ap by_id 507f1f77bcf86cd799439011{end}")
        print(f"  {bold}ap info 12495002020{end}")

def main_cli_function() -> None:
    """Main CLI entry point."""
    fire.Fire(AccountPoolCli)

if __name__ == "__main__":
    main_cli_function()
