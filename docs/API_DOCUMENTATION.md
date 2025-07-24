# Q360 Performance Management System - API Documentation

## Table of Contents
- [Overview](#overview)
- [Authentication](#authentication)
- [Base URL](#base-url)
- [Common Response Format](#common-response-format)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [API Endpoints](#api-endpoints)
- [WebSocket Events](#websocket-events)
- [SDK Examples](#sdk-examples)
- [Changelog](#changelog)

## Overview

The Q360 Performance Management System API provides RESTful endpoints for managing employee evaluations, development plans, notifications, and analytics. The API follows REST principles and returns JSON responses.

### API Version
- **Current Version**: v1
- **Base Path**: `/api/v1/`
- **Documentation**: Available at `/api/docs/` (Swagger UI) and `/api/redoc/` (ReDoc)

### Features
- JWT-based authentication
- Role-based access control (RBAC)
- Comprehensive error handling
- Rate limiting
- Real-time notifications
- File upload support
- Internationalization (i18n)

## Authentication

### JWT Authentication
The API uses JSON Web Tokens (JWT) for authentication. Tokens must be included in the `Authorization` header.

#### Obtain Token
```http
POST /api/v1/auth/login/
Content-Type: application/json

{
    "username": "john.doe@company.com",
    "password": "secure_password123"
}
```

**Response:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": 1,
        "username": "john.doe",
        "email": "john.doe@company.com",
        "full_name": "John Doe",
        "role": "EMPLOYEE"
    }
}
```

#### Refresh Token
```http
POST /api/v1/auth/refresh/
Content-Type: application/json

{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### Using Tokens
Include the access token in all API requests:
```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Token Lifecycle
- **Access Token**: 1 hour
- **Refresh Token**: 7 days
- **Auto-rotation**: Enabled

## Base URL

### Development
```
http://localhost:8000/api/v1/
```

### Production
```
https://api.q360.company.com/api/v1/
```

## Common Response Format

### Success Response
```json
{
    "success": true,
    "data": {
        // Response data
    },
    "meta": {
        "timestamp": "2025-01-15T10:30:00Z",
        "version": "1.0.0"
    }
}
```

### Paginated Response
```json
{
    "success": true,
    "data": {
        "count": 150,
        "next": "http://api.example.com/api/v1/users/?page=3",
        "previous": "http://api.example.com/api/v1/users/?page=1",
        "results": [
            // Array of objects
        ]
    },
    "meta": {
        "page": 2,
        "page_size": 20,
        "total_pages": 8
    }
}
```

## Error Handling

### Error Response Format
```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid input data",
        "details": {
            "field_name": ["This field is required."]
        },
        "timestamp": "2025-01-15T10:30:00Z"
    }
}
```

### HTTP Status Codes

| Code | Description | Usage |
|------|-------------|-------|
| 200 | OK | Successful GET, PUT, PATCH |
| 201 | Created | Successful POST |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Invalid request data |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource conflict |
| 422 | Unprocessable Entity | Validation errors |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |

### Common Error Codes

| Error Code | Description |
|------------|-------------|
| `AUTHENTICATION_REQUIRED` | Authentication token required |
| `INVALID_TOKEN` | Token is invalid or expired |
| `PERMISSION_DENIED` | Insufficient permissions |
| `VALIDATION_ERROR` | Request validation failed |
| `RESOURCE_NOT_FOUND` | Requested resource not found |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `INTERNAL_ERROR` | Internal server error |

## Rate Limiting

- **Default**: 100 requests per minute per user
- **Burst**: 200 requests per minute
- **Headers**: Rate limit info included in response headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642248000
```

## API Endpoints

### Authentication Endpoints

#### Login
```http
POST /api/v1/auth/login/
```

**Request:**
```json
{
    "username": "user@example.com",
    "password": "password123"
}
```

**Response (200):**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": 1,
        "username": "john.doe",
        "email": "john.doe@company.com",
        "full_name": "John Doe",
        "role": "EMPLOYEE",
        "organization_unit": {
            "id": 5,
            "name": "IT Department"
        }
    }
}
```

### User Management

#### List Users
```http
GET /api/v1/users/
Authorization: Bearer {token}
```

**Query Parameters:**
- `page` (integer): Page number
- `page_size` (integer): Items per page (max 100)
- `search` (string): Search by name or email
- `role` (string): Filter by role
- `organization_unit` (integer): Filter by organization unit

**Response (200):**
```json
{
    "count": 150,
    "next": "http://api.example.com/api/v1/users/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "username": "john.doe",
            "email": "john.doe@company.com",
            "full_name": "John Doe",
            "role": "EMPLOYEE",
            "organization_unit": {
                "id": 5,
                "name": "IT Department"
            },
            "is_active": true,
            "date_joined": "2024-01-15T10:30:00Z",
            "last_login": "2025-01-15T09:15:00Z"
        }
    ]
}
```

#### Get User Profile
```http
GET /api/v1/users/profile/
Authorization: Bearer {token}
```

**Response (200):**
```json
{
    "id": 1,
    "username": "john.doe",
    "email": "john.doe@company.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "EMPLOYEE",
    "position": "Software Developer",
    "organization_unit": {
        "id": 5,
        "name": "IT Department",
        "type": "DEPARTMENT"
    },
    "phone_number": "+994501234567",
    "birth_date": "1990-05-15",
    "profile_image": "http://api.example.com/media/profiles/john_doe.jpg",
    "date_joined": "2024-01-15T10:30:00Z",
    "last_login": "2025-01-15T09:15:00Z"
}
```

#### Create User
```http
POST /api/v1/users/
Authorization: Bearer {token}
Content-Type: application/json
```

**Required Permissions:** `ADMIN` or `SUPERADMIN`

**Request:**
```json
{
    "username": "jane.smith",
    "email": "jane.smith@company.com",
    "password": "secure_password123",
    "first_name": "Jane",
    "last_name": "Smith",
    "role": "EMPLOYEE",
    "position": "Marketing Specialist",
    "organization_unit": 3,
    "phone_number": "+994501234568"
}
```

**Response (201):**
```json
{
    "id": 25,
    "username": "jane.smith",
    "email": "jane.smith@company.com",
    "full_name": "Jane Smith",
    "role": "EMPLOYEE",
    "organization_unit": {
        "id": 3,
        "name": "Marketing Department"
    },
    "is_active": true,
    "date_joined": "2025-01-15T10:30:00Z"
}
```

### Organization Units

#### List Organization Units
```http
GET /api/v1/organization-units/
Authorization: Bearer {token}
```

**Response (200):**
```json
{
    "count": 15,
    "results": [
        {
            "id": 1,
            "name": "Company HQ",
            "type": "HEADQUARTERS",
            "parent": null,
            "children_count": 3,
            "employees_count": 150,
            "full_path": "Company HQ"
        },
        {
            "id": 2,
            "name": "IT Department",
            "type": "DEPARTMENT",
            "parent": 1,
            "children_count": 2,
            "employees_count": 25,
            "full_path": "Company HQ → IT Department"
        }
    ]
}
```

#### Get Organization Unit Children
```http
GET /api/v1/organization-units/{id}/children/
Authorization: Bearer {token}
```

**Response (200):**
```json
[
    {
        "id": 3,
        "name": "Development Team",
        "type": "TEAM",
        "parent": 2,
        "employees_count": 15
    },
    {
        "id": 4,
        "name": "QA Team",
        "type": "TEAM",
        "parent": 2,
        "employees_count": 8
    }
]
```

### Evaluations

#### List Evaluations
```http
GET /api/v1/evaluations/
Authorization: Bearer {token}
```

**Query Parameters:**
- `cycle` (integer): Filter by evaluation cycle
- `status` (string): Filter by status (`PENDING`, `COMPLETED`)
- `evaluator` (integer): Filter by evaluator ID
- `employee` (integer): Filter by employee ID

**Response (200):**
```json
{
    "count": 45,
    "results": [
        {
            "id": 1,
            "employee": {
                "id": 5,
                "full_name": "John Doe",
                "email": "john.doe@company.com"
            },
            "evaluator": {
                "id": 2,
                "full_name": "Jane Manager",
                "email": "jane.manager@company.com"
            },
            "cycle": {
                "id": 1,
                "name": "Q1 2025 Evaluation",
                "start_date": "2025-01-01",
                "end_date": "2025-03-31"
            },
            "status": "COMPLETED",
            "created_at": "2025-01-15T10:30:00Z",
            "completed_at": "2025-01-20T14:45:00Z",
            "overall_score": 8.5
        }
    ]
}
```

#### Get Evaluation Details
```http
GET /api/v1/evaluations/{id}/
Authorization: Bearer {token}
```

**Response (200):**
```json
{
    "id": 1,
    "employee": {
        "id": 5,
        "full_name": "John Doe",
        "position": "Software Developer"
    },
    "evaluator": {
        "id": 2,
        "full_name": "Jane Manager"
    },
    "cycle": {
        "id": 1,
        "name": "Q1 2025 Evaluation",
        "start_date": "2025-01-01",
        "end_date": "2025-03-31",
        "is_active": true
    },
    "status": "COMPLETED",
    "answers": [
        {
            "id": 1,
            "question": {
                "id": 1,
                "text": "How would you rate the employee's technical skills?",
                "category": "Technical Competency"
            },
            "score": 9,
            "comment": "Excellent problem-solving abilities and code quality."
        }
    ],
    "overall_score": 8.5,
    "created_at": "2025-01-15T10:30:00Z",
    "completed_at": "2025-01-20T14:45:00Z"
}
```

#### Submit Evaluation
```http
POST /api/v1/evaluations/{id}/submit/
Authorization: Bearer {token}
Content-Type: application/json
```

**Request:**
```json
{
    "answers": [
        {
            "question_id": 1,
            "score": 9,
            "comment": "Excellent technical skills and problem-solving ability."
        },
        {
            "question_id": 2,
            "score": 8,
            "comment": "Good communication with team members."
        }
    ]
}
```

**Response (200):**
```json
{
    "id": 1,
    "status": "COMPLETED",
    "overall_score": 8.5,
    "completed_at": "2025-01-20T14:45:00Z",
    "message": "Evaluation submitted successfully"
}
```

### Development Plans

#### List Development Plans
```http
GET /api/v1/development-plans/
Authorization: Bearer {token}
```

**Response (200):**
```json
{
    "count": 12,
    "results": [
        {
            "id": 1,
            "employee": {
                "id": 5,
                "full_name": "John Doe"
            },
            "cycle": {
                "id": 1,
                "name": "Q1 2025"
            },
            "status": "ACTIVE",
            "goals_count": 4,
            "completion_rate": 75.0,
            "created_at": "2025-01-15T10:30:00Z"
        }
    ]
}
```

#### Create Development Plan
```http
POST /api/v1/development-plans/
Authorization: Bearer {token}
Content-Type: application/json
```

**Required Permissions:** `MANAGER`, `ADMIN`, or `SUPERADMIN`

**Request:**
```json
{
    "employee": 5,
    "cycle": 1,
    "goals": [
        {
            "description": "Complete advanced JavaScript certification",
            "deadline": "2025-06-30",
            "priority": "HIGH"
        },
        {
            "description": "Lead a team project",
            "deadline": "2025-09-30",
            "priority": "MEDIUM"
        }
    ]
}
```

**Response (201):**
```json
{
    "id": 15,
    "employee": {
        "id": 5,
        "full_name": "John Doe"
    },
    "cycle": {
        "id": 1,
        "name": "Q1 2025"
    },
    "status": "ACTIVE",
    "goals": [
        {
            "id": 25,
            "description": "Complete advanced JavaScript certification",
            "deadline": "2025-06-30",
            "priority": "HIGH",
            "status": "NOT_STARTED"
        }
    ],
    "created_at": "2025-01-15T10:30:00Z"
}
```

### Notifications

#### List Notifications
```http
GET /api/v1/notifications/
Authorization: Bearer {token}
```

**Query Parameters:**
- `is_read` (boolean): Filter by read status
- `notification_type` (string): Filter by type
- `priority` (string): Filter by priority

**Response (200):**
```json
{
    "count": 25,
    "results": [
        {
            "id": 1,
            "title": "New Evaluation Assignment",
            "message": "You have been assigned to evaluate John Doe for Q1 2025.",
            "notification_type": "TASK_ASSIGNED",
            "priority": "HIGH",
            "is_read": false,
            "created_at": "2025-01-15T10:30:00Z",
            "action_url": "/evaluations/1/",
            "action_text": "Start Evaluation"
        }
    ]
}
```

#### Mark Notification as Read
```http
POST /api/v1/notifications/{id}/mark_read/
Authorization: Bearer {token}
```

**Response (200):**
```json
{
    "id": 1,
    "is_read": true,
    "read_at": "2025-01-15T11:00:00Z"
}
```

### Dashboard Analytics

#### Get Dashboard Statistics
```http
GET /api/v1/dashboard/stats/
Authorization: Bearer {token}
```

**Response (200):**
```json
{
    "personal": {
        "pending_evaluations": 3,
        "completed_evaluations": 12,
        "active_goals": 5,
        "unread_notifications": 2,
        "avg_performance": 8.2
    },
    "team": {
        "total_members": 15,
        "avg_team_performance": 7.8,
        "pending_team_evaluations": 8
    },
    "trends": {
        "performance_trend": [
            {"month": "2024-10", "score": 7.5},
            {"month": "2024-11", "score": 7.8},
            {"month": "2024-12", "score": 8.2}
        ]
    }
}
```

### AI Risk Detection

#### Get Risk Analysis
```http
GET /api/v1/ai-risk/analysis/
Authorization: Bearer {token}
```

**Required Permissions:** `MANAGER`, `ADMIN`, or `SUPERADMIN`

**Response (200):**
```json
{
    "summary": {
        "total_employees_analyzed": 150,
        "high_risk_employees": 8,
        "critical_flags": 2,
        "analysis_date": "2025-01-15T10:30:00Z"
    },
    "risk_flags": [
        {
            "id": 1,
            "employee": {
                "id": 25,
                "full_name": "Employee Name",
                "department": "Sales"
            },
            "flag_type": "LOW_PERFORMANCE",
            "severity": "HIGH",
            "risk_score": 7.5,
            "detected_at": "2025-01-15T08:00:00Z",
            "details": {
                "performance_decline": true,
                "peer_feedback_negative": true
            }
        }
    ]
}
```

#### Run Risk Analysis
```http
POST /api/v1/ai-risk/analyze/
Authorization: Bearer {token}
Content-Type: application/json
```

**Request:**
```json
{
    "cycle_id": 1,
    "employee_ids": [1, 2, 3],
    "analysis_type": "COMPREHENSIVE"
}
```

**Response (202):**
```json
{
    "task_id": "abc123-def456-ghi789",
    "status": "PROCESSING",
    "message": "Risk analysis started. Check status using task_id.",
    "estimated_completion": "2025-01-15T10:35:00Z"
}
```

### File Upload

#### Upload Profile Image
```http
POST /api/v1/users/profile/upload-image/
Authorization: Bearer {token}
Content-Type: multipart/form-data
```

**Request:**
```
Content-Disposition: form-data; name="image"; filename="profile.jpg"
Content-Type: image/jpeg

[binary image data]
```

**Response (200):**
```json
{
    "profile_image": "http://api.example.com/media/profiles/john_doe_abc123.jpg",
    "message": "Profile image uploaded successfully"
}
```

### Feedback System

#### Submit Quick Feedback
```http
POST /api/v1/quick-feedback/
Authorization: Bearer {token}
Content-Type: application/json
```

**Request:**
```json
{
    "to_user": 5,
    "category": 2,
    "feedback_type": "POSITIVE",
    "priority": "MEDIUM",
    "title": "Great presentation skills",
    "message": "Your presentation in today's meeting was excellent. Clear communication and good use of visuals.",
    "rating": 5,
    "is_anonymous": false
}
```

**Response (201):**
```json
{
    "id": 15,
    "to_user": {
        "id": 5,
        "full_name": "John Doe"
    },
    "from_user": {
        "id": 2,
        "full_name": "Jane Manager"
    },
    "category": {
        "id": 2,
        "name": "Communication"
    },
    "feedback_type": "POSITIVE",
    "title": "Great presentation skills",
    "message": "Your presentation in today's meeting was excellent...",
    "rating": 5,
    "is_anonymous": false,
    "created_at": "2025-01-15T10:30:00Z"
}
```

## WebSocket Events

### Real-time Notifications
Connect to: `ws://localhost:8000/ws/notifications/`

#### Authentication
Send JWT token after connection:
```json
{
    "type": "auth",
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### Notification Event
```json
{
    "type": "notification",
    "data": {
        "id": 15,
        "title": "New Evaluation Assignment",
        "message": "You have been assigned to evaluate John Doe.",
        "notification_type": "TASK_ASSIGNED",
        "priority": "HIGH",
        "created_at": "2025-01-15T10:30:00Z"
    }
}
```

## SDK Examples

### JavaScript/TypeScript
```typescript
import axios from 'axios';

class Q360API {
    private baseURL = 'http://localhost:8000/api/v1';
    private token: string | null = null;

    async login(username: string, password: string) {
        const response = await axios.post(`${this.baseURL}/auth/login/`, {
            username,
            password
        });
        
        this.token = response.data.access;
        return response.data;
    }

    async getProfile() {
        return this.request('GET', '/users/profile/');
    }

    async getEvaluations(params?: any) {
        return this.request('GET', '/evaluations/', { params });
    }

    private async request(method: string, endpoint: string, config?: any) {
        const headers = {
            'Authorization': `Bearer ${this.token}`,
            'Content-Type': 'application/json',
            ...config?.headers
        };

        const response = await axios({
            method,
            url: `${this.baseURL}${endpoint}`,
            headers,
            ...config
        });

        return response.data;
    }
}

// Usage
const api = new Q360API();
await api.login('user@example.com', 'password');
const profile = await api.getProfile();
```

### Python
```python
import requests
from typing import Optional, Dict, Any

class Q360API:
    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.token: Optional[str] = None
        self.session = requests.Session()

    def login(self, username: str, password: str) -> Dict[str, Any]:
        response = self.session.post(
            f"{self.base_url}/auth/login/",
            json={"username": username, "password": password}
        )
        response.raise_for_status()
        
        data = response.json()
        self.token = data["access"]
        self.session.headers.update({
            "Authorization": f"Bearer {self.token}"
        })
        return data

    def get_profile(self) -> Dict[str, Any]:
        return self._request("GET", "/users/profile/")

    def get_evaluations(self, **params) -> Dict[str, Any]:
        return self._request("GET", "/evaluations/", params=params)

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        response = self.session.request(
            method,
            f"{self.base_url}{endpoint}",
            **kwargs
        )
        response.raise_for_status()
        return response.json()

# Usage
api = Q360API()
api.login("user@example.com", "password")
profile = api.get_profile()
```

## Error Examples

### Validation Error (422)
```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid input data",
        "details": {
            "email": ["Enter a valid email address."],
            "password": ["This field is required."]
        },
        "timestamp": "2025-01-15T10:30:00Z"
    }
}
```

### Permission Denied (403)
```json
{
    "success": false,
    "error": {
        "code": "PERMISSION_DENIED",
        "message": "You do not have permission to perform this action",
        "details": {
            "required_role": "MANAGER",
            "current_role": "EMPLOYEE"
        },
        "timestamp": "2025-01-15T10:30:00Z"
    }
}
```

### Rate Limit Exceeded (429)
```json
{
    "success": false,
    "error": {
        "code": "RATE_LIMIT_EXCEEDED",
        "message": "Too many requests. Please try again later.",
        "details": {
            "limit": 100,