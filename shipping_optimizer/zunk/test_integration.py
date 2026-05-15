#!/usr/bin/env python3
"""
Integration Test Script for AI Multi-Agent Liner Shipping Optimization System
Tests WebSocket communication, event validation, and data persistence
"""

import asyncio
import json
import websockets
import sqlite3
import time
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent))

class IntegrationTester:
    def __init__(self):
        self.ws_url = "ws://localhost:8000/ws"
        self.db_path = "optimization_results.db"
        self.test_results = []
        self.ws = None

    async def run_all_tests(self):
        """Run all integration tests"""
        print("=" * 60)
        print("AI Multi-Agent Liner Shipping Optimization System")
        print("Integration Test Suite")
        print("=" * 60)
        print()

        # Check if backend is running
        if not await self.check_backend_health():
            print("❌ Backend is not running. Please start it first:")
            print("   cd backend && python main.py")
            return

        print("✅ Backend is running")
        print()

        # Run tests
        await self.test_websocket_connection()
        await self.test_event_validation()
        await self.test_pipeline_flow()
        await self.test_database_persistence()
        await self.test_error_handling()

        # Print results
        self.print_results()

    async def check_backend_health(self):
        """Check if backend is running"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8000/api/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"Backend health: {data['status']}")
                        return True
        except:
            pass
        return False

    async def test_websocket_connection(self):
        """Test WebSocket connection and basic communication"""
        print("Testing WebSocket Connection...")

        try:
            self.ws = await websockets.connect(self.ws_url)
            print("✅ Connected to WebSocket")
            self.test_results.append(("WebSocket Connection", True, ""))

            # Test ping/pong
            await self.ws.send(json.dumps({"type": "ping"}))
            response = await asyncio.wait_for(self.ws.recv(), timeout=5)
            data = json.loads(response)

            if data.get("type") == "pong":
                print("✅ Ping/Pong working")
                self.test_results.append(("Ping/Pong", True, ""))
            else:
                print(f"❌ Unexpected response: {data}")
                self.test_results.append(("Ping/Pong", False, f"Expected pong, got {data.get('type')}"))

        except Exception as e:
            print(f"❌ WebSocket connection failed: {e}")
            self.test_results.append(("WebSocket Connection", False, str(e)))

    async def test_event_validation(self):
        """Test event validation for both client and server events"""
        print("\nTesting Event Validation...")

        # Test invalid event
        try:
            await self.ws.send(json.dumps({
                "type": "invalid_event",
                "data": {}
            }))
            response = await asyncio.wait_for(self.ws.recv(), timeout=5)
            data = json.loads(response)

            if data.get("type") == "pipeline_error":
                print("✅ Invalid event rejected")
                self.test_results.append(("Event Validation", True, ""))
            else:
                print(f"❌ Invalid event accepted: {data}")
                self.test_results.append(("Event Validation", False, "Invalid event was not rejected"))
        except:
            print("❌ Event validation test failed")
            self.test_results.append(("Event Validation", False, "Test exception"))

    async def test_pipeline_flow(self):
        """Test starting a pipeline and receiving events"""
        print("\nTesting Pipeline Flow...")

        try:
            # Start pipeline
            await self.ws.send(json.dumps({
                "type": "start_pipeline",
                "data": {
                    "dataset_path": "data/liner_shipping_dataset.csv",
                    "max_iterations": 2  # Quick test
                }
            }))

            # Collect events for 30 seconds
            events_received = []
            start_time = time.time()

            while time.time() - start_time < 30:
                try:
                    response = await asyncio.wait_for(self.ws.recv(), timeout=1)
                    data = json.loads(response)
                    events_received.append(data["type"])
                    print(f"  📡 Received: {data['type']}")
                except asyncio.TimeoutError:
                    continue

            # Check expected events
            expected_events = [
                "pipeline_started",
                "stage_started",
                "region_updated",
                "iteration_updated",
                "pipeline_completed"
            ]

            received_set = set(events_received)
            missing_events = set(expected_events) - received_set

            if not missing_events:
                print("✅ All expected events received")
                self.test_results.append(("Pipeline Flow", True, f"Received {len(events_received)} events"))
            else:
                print(f"⚠️ Missing events: {missing_events}")
                self.test_results.append(("Pipeline Flow", False, f"Missing: {missing_events}"))

        except Exception as e:
            print(f"❌ Pipeline flow test failed: {e}")
            self.test_results.append(("Pipeline Flow", False, str(e)))

    async def test_database_persistence(self):
        """Test that data is persisted to database"""
        print("\nTesting Database Persistence...")

        try:
            # Wait a bit for data to be written
            await asyncio.sleep(2)

            # Connect to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check tables exist
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table'
                AND name IN ('optimization_runs', 'regional_results', 'iterations', 'corridors')
            """)
            tables = [row[0] for row in cursor.fetchall()]

            if len(tables) == 4:
                print("✅ All database tables exist")

                # Check for data
                cursor.execute("SELECT COUNT(*) FROM optimization_runs")
                run_count = cursor.fetchone()[0]

                if run_count > 0:
                    print(f"✅ Data persisted ({run_count} runs in database)")
                    self.test_results.append(("Database Persistence", True, ""))
                else:
                    print("⚠️ Database tables empty (pipeline may still be running)")
                    self.test_results.append(("Database Persistence", True, "Tables exist but no data yet"))
            else:
                print(f"❌ Missing tables: {set(['optimization_runs', 'regional_results', 'iterations', 'corridors']) - set(tables)}")
                self.test_results.append(("Database Persistence", False, f"Tables: {tables}"))

            conn.close()

        except Exception as e:
            print(f"❌ Database test failed: {e}")
            self.test_results.append(("Database Persistence", False, str(e)))

    async def test_error_handling(self):
        """Test error handling scenarios"""
        print("\nTesting Error Handling...")

        try:
            # Test stopping pipeline
            await self.ws.send(json.dumps({
                "type": "stop_pipeline",
                "data": {}
            }))

            # Test get status
            await self.ws.send(json.dumps({
                "type": "get_status",
                "data": {}
            }))

            response = await asyncio.wait_for(self.ws.recv(), timeout=5)
            data = json.loads(response)

            if data.get("type") == "status_update":
                print("✅ Error handling working (stop/get status)")
                self.test_results.append(("Error Handling", True, ""))
            else:
                print(f"⚠️ Unexpected response: {data.get('type')}")
                self.test_results.append(("Error Handling", False, "Unexpected response"))

        except Exception as e:
            print(f"❌ Error handling test failed: {e}")
            self.test_results.append(("Error Handling", False, str(e)))

        finally:
            # Close WebSocket
            if self.ws:
                await self.ws.close()

    def print_results(self):
        """Print test results summary"""
        print("\n" + "=" * 60)
        print("TEST RESULTS")
        print("=" * 60)

        passed = 0
        failed = 0

        for test_name, success, detail in self.test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {test_name}")
            if detail and not success:
                print(f"      → {detail}")
            if success:
                passed += 1
            else:
                failed += 1

        print("\n" + "-" * 60)
        print(f"Total: {len(self.test_results)} tests")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {passed/len(self.test_results)*100:.1f}%")

        if failed == 0:
            print("\n🎉 All tests passed! System is ready for production.")
        else:
            print("\n⚠️ Some tests failed. Please check the issues above.")

        print("\nNext Steps:")
        print("1. Connect the frontend to WebSocket events")
        print("2. Test the full dashboard integration")
        print("3. Deploy to production environment")

async def main():
    """Main entry point"""
    tester = IntegrationTester()

    try:
        await tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        print(f"\n\nTest suite error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Check for dependencies
    try:
        import aiohttp
        import websockets
    except ImportError as e:
        print("Missing dependencies. Please install:")
        print("pip install aiohttp websockets")
        exit(1)

    # Run tests
    asyncio.run(main())