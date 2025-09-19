#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta
import uuid

class EduMentorAPITester:
    def __init__(self, base_url="https://mentorhub-5.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.current_user = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_data = {
            'student_user': None,
            'mentor_user': None,
            'course_id': None,
            'session_id': None
        }

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return True, response.json() if response.content else {}
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Response: {response.text}")
                return False, {}

        except requests.exceptions.RequestException as e:
            print(f"❌ Failed - Network Error: {str(e)}")
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_user_registration(self):
        """Test user registration for different roles"""
        print("\n" + "="*50)
        print("TESTING USER REGISTRATION")
        print("="*50)
        
        # Test student registration
        student_data = {
            "email": f"student_{datetime.now().strftime('%H%M%S')}@test.com",
            "password": "TestPass123!",
            "full_name": "Test Student",
            "role": "student",
            "skills": ["Python", "JavaScript"],
            "interests": ["Web Development", "AI"],
            "bio": "I'm a student eager to learn"
        }
        
        success, response = self.run_test(
            "Student Registration",
            "POST",
            "auth/register",
            200,
            data=student_data
        )
        
        if success:
            self.test_data['student_user'] = response
            print(f"   Student ID: {response.get('id')}")
        
        # Test mentor registration
        mentor_data = {
            "email": f"mentor_{datetime.now().strftime('%H%M%S')}@test.com",
            "password": "TestPass123!",
            "full_name": "Test Mentor",
            "role": "mentor",
            "skills": ["React", "Node.js", "Python"],
            "interests": ["Teaching", "Mentoring"],
            "bio": "Experienced developer and mentor"
        }
        
        success, response = self.run_test(
            "Mentor Registration",
            "POST",
            "auth/register",
            200,
            data=mentor_data
        )
        
        if success:
            self.test_data['mentor_user'] = response
            print(f"   Mentor ID: {response.get('id')}")
        
        # Test duplicate email registration
        self.run_test(
            "Duplicate Email Registration",
            "POST",
            "auth/register",
            400,
            data=student_data
        )

    def test_user_authentication(self):
        """Test user login and authentication"""
        print("\n" + "="*50)
        print("TESTING USER AUTHENTICATION")
        print("="*50)
        
        if not self.test_data['student_user']:
            print("❌ Skipping authentication tests - no student user created")
            return False
        
        # Test successful login
        login_data = {
            "email": self.test_data['student_user']['email'],
            "password": "TestPass123!"
        }
        
        success, response = self.run_test(
            "Student Login",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.current_user = response['user']
            print(f"   Token received: {self.token[:20]}...")
        
        # Test invalid login
        invalid_login = {
            "email": "invalid@test.com",
            "password": "wrongpassword"
        }
        
        self.run_test(
            "Invalid Login",
            "POST",
            "auth/login",
            401,
            data=invalid_login
        )
        
        # Test get current user
        if self.token:
            self.run_test(
                "Get Current User",
                "GET",
                "auth/me",
                200
            )
        
        return bool(self.token)

    def test_course_management(self):
        """Test course-related endpoints"""
        print("\n" + "="*50)
        print("TESTING COURSE MANAGEMENT")
        print("="*50)
        
        # First login as mentor to create courses
        if self.test_data['mentor_user']:
            mentor_login = {
                "email": self.test_data['mentor_user']['email'],
                "password": "TestPass123!"
            }
            
            success, response = self.run_test(
                "Mentor Login for Course Creation",
                "POST",
                "auth/login",
                200,
                data=mentor_login
            )
            
            if success:
                self.token = response['access_token']
                
                # Test course creation
                course_data = {
                    "title": "Introduction to Python Programming",
                    "description": "Learn Python from scratch with hands-on projects",
                    "category": "programming",
                    "level": "beginner",
                    "duration_hours": 40,
                    "price": 99.99,
                    "tags": ["python", "programming", "beginner"]
                }
                
                success, response = self.run_test(
                    "Create Course",
                    "POST",
                    "courses",
                    200,
                    data=course_data
                )
                
                if success:
                    self.test_data['course_id'] = response.get('id')
                    print(f"   Course ID: {self.test_data['course_id']}")
        
        # Test get all courses (no auth required)
        self.token = None  # Remove auth to test public endpoint
        self.run_test(
            "Get All Courses",
            "GET",
            "courses",
            200
        )
        
        # Test course filtering
        self.run_test(
            "Filter Courses by Category",
            "GET",
            "courses?category=programming",
            200
        )
        
        self.run_test(
            "Filter Courses by Level",
            "GET",
            "courses?level=beginner",
            200
        )
        
        self.run_test(
            "Search Courses",
            "GET",
            "courses?search=python",
            200
        )
        
        # Test get specific course
        if self.test_data['course_id']:
            self.run_test(
                "Get Specific Course",
                "GET",
                f"courses/{self.test_data['course_id']}",
                200
            )

    def test_mentor_discovery(self):
        """Test mentor-related endpoints"""
        print("\n" + "="*50)
        print("TESTING MENTOR DISCOVERY")
        print("="*50)
        
        # Test get all mentors
        self.run_test(
            "Get All Mentors",
            "GET",
            "mentors",
            200
        )
        
        # Test filter mentors by skills
        self.run_test(
            "Filter Mentors by Skills",
            "GET",
            "mentors?skills=Python,React",
            200
        )

    def test_mentorship_sessions(self):
        """Test mentorship session booking and management"""
        print("\n" + "="*50)
        print("TESTING MENTORSHIP SESSIONS")
        print("="*50)
        
        # Login as student for session booking
        if self.test_data['student_user']:
            student_login = {
                "email": self.test_data['student_user']['email'],
                "password": "TestPass123!"
            }
            
            success, response = self.run_test(
                "Student Login for Session Booking",
                "POST",
                "auth/login",
                200,
                data=student_login
            )
            
            if success and self.test_data['mentor_user']:
                self.token = response['access_token']
                
                # Test session booking
                session_data = {
                    "mentor_id": self.test_data['mentor_user']['id'],
                    "title": "Python Learning Session",
                    "description": "Help with Python basics",
                    "scheduled_at": (datetime.now() + timedelta(days=1)).isoformat(),
                    "duration_minutes": 60
                }
                
                success, response = self.run_test(
                    "Book Mentorship Session",
                    "POST",
                    "mentorship/sessions",
                    200,
                    data=session_data
                )
                
                if success:
                    self.test_data['session_id'] = response.get('id')
                    print(f"   Session ID: {self.test_data['session_id']}")
                
                # Test get user sessions
                self.run_test(
                    "Get User Sessions",
                    "GET",
                    "mentorship/sessions",
                    200
                )

    def test_chat_system(self):
        """Test chat messaging system"""
        print("\n" + "="*50)
        print("TESTING CHAT SYSTEM")
        print("="*50)
        
        if not (self.test_data['student_user'] and self.test_data['mentor_user']):
            print("❌ Skipping chat tests - missing users")
            return
        
        # Login as student
        student_login = {
            "email": self.test_data['student_user']['email'],
            "password": "TestPass123!"
        }
        
        success, response = self.run_test(
            "Student Login for Chat",
            "POST",
            "auth/login",
            200,
            data=student_login
        )
        
        if success:
            self.token = response['access_token']
            
            # Test send message
            message_data = {
                "receiver_id": self.test_data['mentor_user']['id'],
                "message": "Hello, I need help with Python!"
            }
            
            self.run_test(
                "Send Chat Message",
                "POST",
                "chat/messages",
                200,
                data=message_data
            )
            
            # Test get conversation
            self.run_test(
                "Get Conversation",
                "GET",
                f"chat/conversations/{self.test_data['mentor_user']['id']}",
                200
            )

    def test_progress_tracking(self):
        """Test progress tracking system"""
        print("\n" + "="*50)
        print("TESTING PROGRESS TRACKING")
        print("="*50)
        
        if not (self.test_data['course_id'] and self.token):
            print("❌ Skipping progress tests - missing course or auth")
            return
        
        # Test update progress
        success, response = self.run_test(
            "Update Course Progress",
            "POST",
            f"progress/{self.test_data['course_id']}?completion_percentage=25.5",
            200
        )
        
        # Test get user progress
        self.run_test(
            "Get User Progress",
            "GET",
            "progress",
            200
        )

    def test_error_handling(self):
        """Test error handling and edge cases"""
        print("\n" + "="*50)
        print("TESTING ERROR HANDLING")
        print("="*50)
        
        # Test unauthorized access
        self.token = None
        self.run_test(
            "Unauthorized Access to Protected Route",
            "GET",
            "auth/me",
            401
        )
        
        # Test invalid course ID
        self.run_test(
            "Get Non-existent Course",
            "GET",
            "courses/invalid-id",
            404
        )
        
        # Test invalid mentor ID for session booking
        if self.test_data['student_user']:
            student_login = {
                "email": self.test_data['student_user']['email'],
                "password": "TestPass123!"
            }
            
            success, response = self.run_test(
                "Student Login for Error Tests",
                "POST",
                "auth/login",
                200,
                data=student_login
            )
            
            if success:
                self.token = response['access_token']
                
                invalid_session_data = {
                    "mentor_id": "invalid-mentor-id",
                    "title": "Invalid Session",
                    "scheduled_at": (datetime.now() + timedelta(days=1)).isoformat(),
                    "duration_minutes": 60
                }
                
                self.run_test(
                    "Book Session with Invalid Mentor",
                    "POST",
                    "mentorship/sessions",
                    404,
                    data=invalid_session_data
                )

    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting EduMentor API Testing...")
        print(f"🌐 Base URL: {self.base_url}")
        
        try:
            # Test basic connectivity
            response = requests.get(f"{self.base_url}/docs", timeout=5)
            if response.status_code == 200:
                print("✅ API server is accessible")
            else:
                print("⚠️  API server responded but docs not accessible")
        except:
            print("❌ Cannot connect to API server")
            return 1
        
        # Run test suites
        self.test_user_registration()
        auth_success = self.test_user_authentication()
        
        if auth_success:
            self.test_course_management()
            self.test_mentor_discovery()
            self.test_mentorship_sessions()
            self.test_chat_system()
            self.test_progress_tracking()
        else:
            print("⚠️  Skipping authenticated tests due to auth failure")
        
        self.test_error_handling()
        
        # Print final results
        print("\n" + "="*60)
        print("FINAL TEST RESULTS")
        print("="*60)
        print(f"📊 Tests Run: {self.tests_run}")
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"📈 Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print("⚠️  Some tests failed - check logs above")
            return 1

def main():
    tester = EduMentorAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())