import requests
import time
import sys
from playwright.sync_api import sync_playwright, expect

# Configuration
BASE_API = "http://localhost:5000"
ELECTRON_DEBUG_PORT = 9222


def test_frontend_application():
    """Run full frontend UI tests against running Electron app"""
    
    print("\n🖥️  Gym Analytics Frontend Test Suite")
    print("=" * 60)
    
    # First verify backend is running
    try:
        requests.get(f"{BASE_API}/auth/me", timeout=3)
    except:
        print("\n❌ Backend server not running. Start with 'npm run start:backend' first")
        sys.exit(1)

    passed = 0
    failed = 0
    
    with sync_playwright() as p:
        print("\n📋 Connecting to Electron application...")
        
        try:
            # Connect to running Electron instance
            browser = p.chromium.connect_over_cdp(f"http://localhost:{ELECTRON_DEBUG_PORT}")
            print("✅ Connected to Electron successfully")
            
            context = browser.contexts[0]
            page = context.pages[0]
            
            # Allow time for app to load
            time.sleep(2)
            
            # Test 1: Verify application window loads
            print("\n📋 Running Frontend Tests:")
            
            try:
                page.wait_for_selector("body", timeout=10000)
                title = page.title()
                print(f"  ✅ PASS Window title: {title}")
                passed +=1
            except Exception as e:
                print(f"  ❌ FAIL Application did not load: {e}")
                failed +=1
                return
            
            # Test 2: Login page navigation and elements
            try:
                # Navigate from startup to login
                page.get_by_role("link", name="Get started").click(timeout=5000)
                
                # Verify login elements (using explicit IDs to avoid duplicate label conflict)
                expect(page.locator("#loginUsername")).to_be_visible(timeout=5000)
                expect(page.locator("#loginPassword")).to_be_visible()
                expect(page.get_by_role("button", name="Confirm")).to_be_visible()
                print("  ✅ PASS Login form loaded correctly")
                passed +=1
            except Exception as e:
                print(f"  ❌ FAIL Login form missing elements: {e}")
                failed +=1
            
            # Test 3: Login functionality
            try:
                page.locator("#loginUsername").fill("test_suite_user")
                page.locator("#loginPassword").fill("testpass1234")
                page.get_by_role("button", name="Confirm").click()
                
                # Verify dashboard loads
                page.wait_for_selector(".dashboard-shell", timeout=10000)
                print("  ✅ PASS Login successful, dashboard loaded")
                passed +=1
            except Exception as e:
                print(f"  ❌ FAIL Login failed: {e}")
                failed +=1
            
            # Test 4: Dashboard widgets
            try:
                widgets = [
                    ".metric-card",
                    ".panel-card",
                    ".chart-card"
                ]
                
                for widget in widgets:
                    page.wait_for_selector(widget, timeout=5000)
                
                print("  ✅ PASS All dashboard widgets loaded")
                passed +=1
            except Exception as e:
                print(f"  ❌ FAIL Dashboard widgets missing: {e}")
                failed +=1
            
            # Test 5: Workout logger UI elements
            try:
                # Scroll to workout section
                page.locator("#workoutForm").scroll_into_view_if_needed()
                
                expect(page.locator("#workoutDate")).to_be_visible()
                expect(page.locator("#workoutTitle")).to_be_visible()
                expect(page.locator("#setExercise")).to_be_visible()
                expect(page.locator("#addSetBtn")).to_be_visible()
                
                print("  ✅ PASS Workout logger UI is present")
                passed +=1
            except Exception as e:
                print(f"  ❌ FAIL Workout logger failed: {e}")
                failed +=1
            
            # Test 6: Body metrics form
            try:
                page.locator("#bodyMetricForm").scroll_into_view_if_needed()
                
                expect(page.locator("#bodyMetricDate")).to_be_visible()
                expect(page.locator("#bodyweightInput")).to_be_visible()
                expect(page.locator("#bodyfatInput")).to_be_visible()
                
                print("  ✅ PASS Body metrics form is present")
                passed +=1
            except Exception as e:
                print(f"  ❌ FAIL Body metrics failed: {e}")
                failed +=1
            
            # Test 7: Logout functionality
            try:
                page.get_by_role("link", name="Log out").click(timeout=5000)
                
                page.wait_for_selector("#StartupPage", timeout=5000)
                print("  ✅ PASS Logout works correctly")
                passed +=1
            except Exception as e:
                print(f"  ❌ FAIL Logout failed: {e}")
                failed +=1
            
            print("\n" + "=" * 60)
            print(f"\n📊 Frontend Results: {passed} passed, {failed} failed")
            
            browser.close()
            print("\n✅ Frontend test run complete")
            
        except Exception as e:
            print(f"\n❌ Could not connect to Electron: {e}")
            print("\n💡 To enable debug mode:")
            print("   Add this line to electron/main.js:")
            print("   mainWindow.webContents.openDevTools({ mode: 'detach' })")
            print("   Or run electron with --remote-debugging-port=9222")
            sys.exit(1)


if __name__ == "__main__":
    print("\n💡 To run these tests:")
    print("1. Start backend: npm run start:backend")
    print("2. Start Electron in debug mode: electron . --remote-debugging-port=9222")
    print("3. Run this test script\n")
    
    test_frontend_application()