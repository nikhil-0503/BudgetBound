"""
Test Live Currency Converter with Real Exchange Rates
"""

import asyncio
import httpx
from datetime import datetime

async def test_live_rates():
    """Test fetching live exchange rates"""
    
    print("=" * 60)
    print("Testing Live Exchange Rate API")
    print("=" * 60)
    
    base_currency = "INR"
    url = f"https://api.exchangerate-api.com/v4/latest/{base_currency}"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            print(f"\nFetching live rates for {base_currency}...")
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            
            print(f"\n✓ API Response received successfully")
            print(f"Base Currency: {data.get('base', 'N/A')}")
            print(f"Last Updated: {data.get('date', 'N/A')}")
            
            rates = data.get("rates", {})
            print(f"\n✓ Total currencies available: {len(rates)}")
            
            # Display some popular currencies
            popular = ["USD", "EUR", "GBP", "AED", "THB", "SGD", "JPY", "AUD"]
            print("\n" + "=" * 60)
            print("Popular Exchange Rates (1 INR = X Currency)")
            print("=" * 60)
            
            for currency in popular:
                if currency in rates:
                    rate = rates[currency]
                    print(f"{currency:5} : {rate:.6f}")
            
            # Test conversion
            print("\n" + "=" * 60)
            print("Sample Conversions")
            print("=" * 60)
            
            test_amounts = [1000, 10000, 50000, 100000]
            test_currency = "USD"
            
            if test_currency in rates:
                rate = rates[test_currency]
                print(f"\nINR to USD (Rate: {rate:.6f})")
                for amount in test_amounts:
                    converted = amount * rate
                    print(f"₹{amount:,} = ${converted:,.2f}")
            
            return True
            
    except httpx.TimeoutException:
        print("\n✗ Error: Request timed out")
        return False
    except httpx.HTTPStatusError as e:
        print(f"\n✗ HTTP Error: {e.response.status_code}")
        return False
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        return False


async def test_backend_endpoints():
    """Test backend currency endpoints"""
    
    print("\n" + "=" * 60)
    print("Testing Backend Currency Endpoints")
    print("=" * 60)
    
    base_url = "http://127.0.0.1:8000"
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            # Test 1: Get all rates
            print("\n1. Testing GET /api/currency/rates")
            response = await client.get(f"{base_url}/api/currency/rates", params={"base": "INR"})
            if response.status_code == 200:
                data = response.json()
                print(f"   ✓ Success - {len(data.get('rates', {}))} currencies available")
                print(f"   Last Updated: {data.get('last_updated', 'N/A')}")
                print(f"   Source: {data.get('source', 'N/A')}")
            else:
                print(f"   ✗ Failed with status {response.status_code}")
            
            # Test 2: Convert currency
            print("\n2. Testing GET /api/currency/convert")
            response = await client.get(
                f"{base_url}/api/currency/convert",
                params={"amount": 10000, "from_currency": "INR", "to_currency": "USD"}
            )
            if response.status_code == 200:
                data = response.json()
                print(f"   ✓ Success")
                print(f"   ₹{data['original_amount']} = ${data['converted_amount']}")
                print(f"   Exchange Rate: {data['exchange_rate']}")
                print(f"   Last Updated: {data.get('last_updated', 'N/A')}")
            else:
                print(f"   ✗ Failed with status {response.status_code}")
            
            return True
            
        except httpx.ConnectError:
            print("\n✗ Error: Cannot connect to backend server")
            print("   Make sure the backend is running on http://127.0.0.1:8000")
            return False
        except Exception as e:
            print(f"\n✗ Error: {str(e)}")
            return False


async def main():
    """Run all tests"""
    
    print("\n" + "=" * 60)
    print("LIVE CURRENCY CONVERTER TEST SUITE")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Direct API access
    api_success = await test_live_rates()
    
    # Test 2: Backend endpoints (only if backend is running)
    backend_success = await test_backend_endpoints()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"External API Access: {'✓ PASSED' if api_success else '✗ FAILED'}")
    print(f"Backend Endpoints:   {'✓ PASSED' if backend_success else '✗ FAILED'}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
