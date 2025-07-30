#!/usr/bin/env python3
"""
Debug exactly what our SDK is sending vs what should work.
"""

import sys
import os
import time
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Let's monkey patch the do_request function to see what's being sent
original_do_request = None

def debug_do_request(url, method, body=None, headers=None):
    """Debug version that shows exactly what's being sent."""
    
    print("🔍 DEBUG: SDK is sending this request:")
    print(f"   URL: {url}")
    print(f"   Method: {method}")
    print(f"   Headers: {headers}")
    print(f"   Body type: {type(body)}")
    print(f"   Body content:")
    
    if hasattr(body, '__dict__'):
        print(f"      Body attributes: {body.__dict__}")
    else:
        print(f"      Body value: {body}")
    
    if isinstance(body, dict):
        print(f"      Body JSON: {json.dumps(body, indent=6)}")
    
    print()
    
    # Call the original function
    return original_do_request(url, method, body, headers)


def test_with_debug():
    """Test SDK CREATE with debugging enabled."""
    from .config import Config
    from .sdk import new
    
    app_id = ""
    base_url = "https://api.client.u-code.io"
    
    config = Config(app_id=app_id, base_url=base_url)
    sdk = new(config)
    
    test_data = {
        "guid" : "825fa25d-dc6b-462b-bdab-b40b02c2fc5c",
        "full_name": f"Debug Test {int(time.time())}",
        "position": "Debug Tester Update"
    }
    
    print("🚀 Making SDK CREATE call...")
    try:
        result = sdk.files().upload("/home/javokhir/Videos/kazam_u81gyvqs.movie").exec()
        print(f"📦 Result: {result}")
    except Exception as e:
        print(f"💥 Exception: {e}")
    
def compare_working_vs_sdk():
    """Compare what works vs what SDK sends."""
    
    print("\n📊 Comparison: Working vs SDK")
    print("=" * 40)
    
    app_id = ""
    base_url = "https://api.client.u-code.io"
    
    test_data = {
        "full_name": f"Compare Test {int(time.time())}",
        "position": "Compare Tester"
    }
    
    print("✅ WORKING format (from our debug):")
    working_body = {
        "data": test_data,
        "disable_faas": True
    }
    working_url = f"{base_url}/v2/items/human?from-ofs=true"
    
    print(f"   URL: {working_url}")
    print(f"   Body: {json.dumps(working_body, indent=6)}")
    print()
    
    print("❓ SDK format (what we think it's sending):")
    
    # Try to figure out what our SDK is creating
    from .models import ActionBody
    action_body = ActionBody(body=test_data, disable_faas=True)
    
    print(f"   ActionBody type: {type(action_body)}")
    print(f"   ActionBody.__dict__: {action_body.__dict__}")
    print()
    
    # Check if SDK is sending the ActionBody directly
    print("🤔 Possible SDK issues:")
    print("   1. Sending ActionBody object instead of dict")
    print("   2. Wrong URL parameters (from-ofs=True vs from-ofs=true)")
    print("   3. Wrong field names (body vs data)")
    print("   4. Wrong JSON serialization")


def show_fix_needed():
    """Show exactly what needs to be fixed."""
    
    print("\n🔧 EXACT FIX NEEDED:")
    print("=" * 40)
    
    print("In your items.py file, find CreateItemBuilder.exec() method")
    print("Look for this pattern:")
    print()
    print("❌ WRONG (current):")
    print("   body=self.data")
    print("   # or")
    print("   json=self.data")
    print()
    print("✅ CORRECT (needed):")
    print("   request_body = {")
    print("       'data': self.data.body,")
    print("       'disable_faas': self.data.disable_faas")
    print("   }")
    print("   # then use:")
    print("   body=request_body")
    print()
    print("Also check the URL:")
    print("❌ WRONG: ?from-ofs=True")
    print("✅ CORRECT: ?from-ofs=true")


if __name__ == "__main__":
    test_with_debug()
    # compare_working_vs_sdk()
    # show_fix_needed()