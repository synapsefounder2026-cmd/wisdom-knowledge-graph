import sys
sys.path.insert(0, '.')

from wisdom.core.gemini_client import call_gemini
from wisdom.core.gemini_key_manager import key_manager

print("=== Test Gemini Key Rotation ===\n")

# Test 1: Gọi API thật
print("Test 1: Gọi API...")
response = call_gemini("Chào! Hãy giới thiệu Wisdom Project trong 1 câu.")
print(f"Response: {response}\n")

# Test 2: Xem trạng thái keys
print("Test 2: Trạng thái 5 keys:")
status = key_manager.status()
for key, info in status.items():
    print(f"  {key}: used={info['rpm_used']}, remaining={info['rpm_remaining']}, cooldown={info['in_cooldown']}")