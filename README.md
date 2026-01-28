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

| Column (DB)        | Type         | Constraints                    | Description                     |
|--------------------|--------------|--------------------------------|---------------------------------|
| user_id            | INT          | PRIMARY KEY, AUTO_INCREMENT   | User ID                         |
| first_name         | VARCHAR(50)  | NOT NULL                       | User's first name               |
| last_name          | VARCHAR(50)  | NOT NULL                       | User's last name                |
| email              | VARCHAR(100) | UNIQUE, NOT NULL               | User's email address            |
| pending_email      | VARCHAR(100) | NULL                           | Pending email (after update, before verify) |
| password            | VARCHAR(255) | NOT NULL                       | Hashed password (bcrypt)         |
| active             | BOOLEAN      | DEFAULT TRUE                   | Account status (true=active, false=banned) |
| email_verified     | BOOLEAN      | DEFAULT FALSE                  | Email verification status       |
| verification_token | VARCHAR(255) | NULL                           | Token for email verify          |
| token_expires_at   | DATETIME     | NULL                           | Token expiry                    |
| date_joined        | DATETIME     | DEFAULT CURRENT_TIMESTAMP      | Registration timestamp          |
| type               | ENUM         | DEFAULT 'unverified'            | User role (see below)           |
| profile_image_url  | VARCHAR(500) | NULL                           | Profile image URL (S3)          |

API responses use camelCase (e.g. `userId`, `firstName`, `type`).

### User Types

| Type           | Description                                      |
|----------------|--------------------------------------------------|
| `visitor`      | Can only see login, register, and contact pages  |
| `unverified`   | Email not verified, can only view posts          |
| `normal`       | Verified user, can create and reply to posts     |
| `admin`        | Administrator                                    |
| `super_admin`  | Super administrator (only one, hardcoded)        |

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

| Variable     | Default / Example                                       | Description          |
|--------------|---------------------------------------------------------|----------------------|
| DATABASE_URL | mysql+pymysql://root:root@localhost:3306/user_db        | Database connection  |
| JWT_SECRET   | your-secret-key                                         | JWT signing secret   |
| AUTO_SEED    | true                                                    | Auto-seed on startup |

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

### Internal APIs (for Auth Service)

| Method | Endpoint                                | Description               |
|--------|-----------------------------------------|---------------------------|
| POST   | /internal/users                         | Create user (register)   |
| GET    | /internal/users/{user_id}               | Get user by ID            |
| GET    | /internal/users/email/{email}           | Get user by email         |
| GET    | /internal/users/pending-email/{email}   | Get user by pending email |
| POST   | /internal/users/verify-email            | Verify email with token (body: email, token) |
| PUT    | /internal/users/{id}/verification-token | Update verification token |
| GET    | /internal/users/{id}/verification-token/valid | Get valid token if exists |

#### Example: Create User (internal, used by Auth Service)
```bash
curl -X POST http://localhost:5001/internal/users \
  -H "Content-Type: application/json" \
  -d '{
    "firstName": "John",
    "lastName": "Doe",
    "email": "john@example.com",
    "password": "<hashed-password>",
    "verificationToken": "123456",
    "tokenExpiresAt": "2026-01-28T12:00:00"
  }'
```

**Response (201 Created):** User object (snake_case; include_password=false).  
**Response (409 Conflict):** `{ "error": "..." }` (e.g. email already exists).

Login and password verification are handled by the **Auth Service**; User Service does not expose a "verify credentials" endpoint. Auth Service calls internal GET user by email and verifies password locally.

### External APIs (via Gateway at /api; require JWT unless noted)

| Method | Endpoint                     | Description                    | Auth        |
|--------|------------------------------|--------------------------------|-------------|
| GET    | /api/users                   | List all users (paginated)     | Admin only  |
| GET    | /api/users/:id               | Get user by ID                 | JWT         |
| PUT    | /api/users/:id               | Update user (self or admin)    | JWT         |
| PUT    | /api/users/:id/profile-image | Update profile image URL       | JWT (self)  |
| PUT    | /api/users/:id/ban           | Ban user                       | Admin only  |
| PUT    | /api/users/:id/unban         | Unban user                     | Admin only  |
| PUT    | /api/users/:id/promote      | Promote to admin               | Super Admin |
| PUT    | /api/users/:id/demote       | Demote admin to user           | Super Admin |
| DELETE | /api/users/:id              | Delete user                    | Super Admin |

#### Example: Get User by ID
```bash
curl http://localhost:8080/api/users/1 \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

#### Example: Update User Profile
```bash
curl -X PUT http://localhost:8080/api/users/1 \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"firstName": "John", "lastName": "Smith", "email": "john@example.com"}'
```
Response includes `user` (camelCase) and optionally `emailChanged`.

#### Example: Update Profile Image
```bash
curl -X PUT http://localhost:8080/api/users/1/profile-image \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"profileImageUrl": "https://bucket.s3.../profile/1/uuid.jpg"}'
```

#### Example: List All Users (Admin)
```bash
curl "http://localhost:8080/api/users?page=1&per_page=20" \
  -H "Authorization: Bearer <ADMIN_JWT_TOKEN>"
```

#### Example: Ban / Unban User (Admin)
```bash
curl -X PUT http://localhost:8080/api/users/2/ban \
  -H "Authorization: Bearer <ADMIN_JWT_TOKEN>"

curl -X PUT http://localhost:8080/api/users/2/unban \
  -H "Authorization: Bearer <ADMIN_JWT_TOKEN>"
```

## JWT Token Structure

The Gateway validates JWT tokens (issued by Auth Service) and forwards `X-User-Id`, `X-User-Type`, `X-User-Email` to this service. All external requests via Gateway must include:
```
Authorization: Bearer <token>
```

## License

MIT
