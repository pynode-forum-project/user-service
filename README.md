# User Service

User Service is a Flask-based microservice that manages user-related operations such as user profile and registration for the Forum Project.

## Tech Stack

- **Framework**: Flask 3.0
- **ORM**: Flask-SQLAlchemy
- **Database**: MySQL 8.0
- **Authentication**: Flask-JWT-Extended (prepared for future use)

## Project Structure

```
user-service/
├── app/
│   ├── __init__.py              # Flask application factory (with auto-seed)
│   ├── config.py                # Configuration (database, JWT, etc.)
│   ├── models/
│   │   ├── __init__.py          # SQLAlchemy db instance
│   │   └── user.py              # User model
│   └── routes/
│       ├── user_routes.py       # External APIs (via Gateway)
│       └── internal_routes.py   # Internal APIs (for Auth Service)
├── run.py                       # Application entry point
├── seed.py                      # Manual database seeding script
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Docker build file
└── README.md
```

## Database Schema

### User Table

| Column          | Type         | Constraints                    | Description                     |
|-----------------|--------------|--------------------------------|---------------------------------|
| userId          | VARCHAR(36)  | PRIMARY KEY                    | UUID, auto-generated            |
| firstName       | VARCHAR(50)  | NOT NULL                       | User's first name               |
| lastName        | VARCHAR(50)  | NOT NULL                       | User's last name                |
| email           | VARCHAR(100) | UNIQUE, NOT NULL               | User's email address            |
| isActive        | BOOLEAN      | DEFAULT TRUE                   | Account status (true=active, false=banned) |
| password        | VARCHAR(255) | NOT NULL                       | Hashed password                 |
| dateJoined      | DATETIME     | NOT NULL, DEFAULT CURRENT_TIME | Registration timestamp          |
| userType        | VARCHAR(50)  | NOT NULL, DEFAULT 'unverified' | User role/type                  |
| profileImageURL | VARCHAR(255) | NULLABLE                       | Profile image URL (S3)          |

> **Note**: Field naming conventions:
> - `isActive` corresponds to `active` in project documentation
> - `userType` corresponds to `type` in project documentation

### User Types

| Type            | Description                                      |
|-----------------|--------------------------------------------------|
| `visitor`       | Can only see login, register, and contact pages  |
| `unverified`    | Email not verified, can only view posts          |
| `normal_user`   | Verified user, can create and reply to posts     |
| `admin`         | Administrator                                    |
| `superadmin`    | Super administrator (only one, hardcoded)        |

## Setup

### Prerequisites

- Python 3.11+
- MySQL 8.0 (via Docker)
- Docker & Docker Compose

### Local Development

1. **Start MySQL database**:
   ```bash
   cd ../infrastructure
   docker-compose up -d mysql
   cd ../user-service
   ```

2. **Create virtual environment** (choose one):
   ```bash
   # Option A: Using venv
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   # Option B: Using conda
   conda create -n forum-user python=3.11
   conda activate forum-user
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the service**:
   ```bash
   python run.py
   ```
   > **Note**: On first run, the database will be **automatically seeded** with test users if empty.

5. **Verify**: The service should start at `http://localhost:5001`

### Docker Development

```bash
cd ../infrastructure
docker-compose up -d mysql user-service
```

## Environment Variables

| Variable      | Default Value                                          | Description          |
|---------------|--------------------------------------------------------|----------------------|
| DATABASE_URI  | mysql+pymysql://root:root@localhost:3306/forum_user_db | Database connection  |
| JWT_SECRET    | your-secret-key                                        | JWT signing secret   |
| AUTO_SEED     | true                                                   | Auto-seed on startup |

## Database Seeding

### Auto-Seed (Default)

When the application starts and the database is **empty**, it automatically seeds the following test users:

| Email                    | Password         | userType    |
|--------------------------|------------------|-------------|
| superadmin@forum.com     | SuperAdmin123!   | superadmin  |
| admin@forum.com          | AdminUser123!    | admin       |
| john.doe@example.com     | Password123!     | normal_user |
| jane.smith@example.com   | Password123!     | normal_user |

To disable auto-seed (e.g., in production):
```bash
AUTO_SEED=false python run.py
```

### Manual Seed

For more test users (including banned user), run manually:

```bash
# Add all seed users
python seed.py

# Clear all users and re-seed
python seed.py --clear
python seed.py
```

Additional users from manual seed:

| Email                    | Password         | userType    | isActive |
|--------------------------|------------------|-------------|----------|
| bob.wilson@example.com   | Password123!     | unverified  | true     |
| banned@example.com       | Password123!     | normal_user | **false** |

## API Endpoints

### Internal APIs (for Auth Service) Implemented

| Method | Endpoint                    | Description               | Status |
|--------|-----------------------------|---------------------------|--------|
| POST   | /internal/users             | Create user (register)    | Done |
| GET    | /internal/users/{id}        | Get user by ID            | Done |
| GET    | /internal/users/email?email=| Get user by email         | Done |
| PUT    | /internal/users/{id}/verify | Verify user email         | Done |
| POST   | /internal/users/verify      | Verify credentials (login)| Done |

#### Example: Create User
```bash
curl -X POST http://localhost:5001/internal/users \
  -H "Content-Type: application/json" \
  -d '{
    "firstName": "John",
    "lastName": "Doe",
    "email": "john@example.com",
    "password": "password123"
  }'
```

**Response (201 Created):**
```json
{
  "userId": "uuid-string",
  "firstName": "John",
  "lastName": "Doe",
  "email": "john@example.com"
}
```

**Response (409 Conflict):**
```json
{
  "error": "User with this email already exists"
}
```

#### Example: Verify Credentials (for Auth Service login)
```bash
curl -X POST http://localhost:5001/internal/users/verify \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "password123"
  }'
```

**Response (200 OK):**
```json
{
  "userId": "uuid-string",
  "userType": "normal_user",
  "isActive": true
}
```

**Response (401 Unauthorized):**
```json
{
  "error": "Invalid email or password"
}
```

**Response (404 Not Found):**
```json
{
  "error": "User not found"
}
```

### External APIs (via Gateway, requires JWT) Implemented

| Method | Endpoint                | Description              | Auth Required |
|--------|-------------------------|--------------------------|---------------|
| GET    | /api/users/me           | Get current user profile | JWT        |
| GET    | /api/users/{id}/profile | Get user profile by ID   | JWT        |
| PUT    | /api/users/{id}/profile | Update own profile       | JWT (self) |
| GET    | /api/users              | List all users           | Admin only |
| PUT    | /api/users/{id}/status  | Ban/Unban user           | Admin only |

#### Example: Get Current User (restore login state)
```bash
curl http://localhost:8080/api/users/me \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

#### Example: Update Profile
```bash
curl -X PUT http://localhost:8080/api/users/{user_id}/profile \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "firstName": "John",
    "lastName": "Smith",
    "profileImageURL": "https://example.com/avatar.jpg"
  }'
```

#### Example: List All Users (Admin)
```bash
curl "http://localhost:8080/api/users?page=1&per_page=20" \
  -H "Authorization: Bearer <ADMIN_JWT_TOKEN>"
```

#### Example: Ban User (Admin)
```bash
curl -X PUT http://localhost:8080/api/users/{user_id}/status \
  -H "Authorization: Bearer <ADMIN_JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"isActive": false}'
```

## JWT Token Structure

External APIs expect JWT tokens with the following claims:
- `sub` (identity): User ID
- `userType`: User role (`unverified`, `normal_user`, `admin`, `superadmin`)

**Note**: JWT tokens are issued by Auth Service. All external requests must include:
```
Authorization: Bearer <token>
```

## License

MIT
