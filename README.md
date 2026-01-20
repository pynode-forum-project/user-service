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
│   ├── __init__.py              # Flask application factory
│   ├── config.py                # Configuration (database, JWT, etc.)
│   ├── models/
│   │   ├── __init__.py          # SQLAlchemy db instance
│   │   └── user.py              # User model
│   └── routes/
│       ├── user_routes.py       # External APIs (via Gateway)
│       └── internal_routes.py   # Internal APIs (for Auth Service)
├── run.py                       # Application entry point
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

## API Endpoints

### Internal APIs (for Auth Service) ✅ Implemented

| Method | Endpoint                     | Description              | Status |
|--------|------------------------------|--------------------------|--------|
| POST   | /internal/users              | Create user (register)   | ✅ Done |
| GET    | /internal/users/{id}         | Get user by ID           | ✅ Done |
| GET    | /internal/users/email?email= | Get user by email (login)| ✅ Done |
| PUT    | /internal/users/{id}/verify  | Verify user email        | ✅ Done |

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

#### Example: Get User by Email
```bash
curl "http://localhost:5001/internal/users/email?email=john@example.com"
```

### External APIs (via Gateway, requires JWT) 🚧 TODO

| Method | Endpoint                | Description           | Status |
|--------|-------------------------|-----------------------|--------|
| GET    | /api/users/{id}/profile | Get user profile      | 🚧 TODO |
| PUT    | /api/users/{id}/profile | Update user profile   | 🚧 TODO |
| GET    | /api/users              | List all users (Admin)| 🚧 TODO |
| PUT    | /api/users/{id}/status  | Ban/Unban user (Admin)| 🚧 TODO |

## License

MIT
