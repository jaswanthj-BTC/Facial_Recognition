from datetime import datetime
import bcrypt
from bson import ObjectId


class User:
    """
    User Model for MongoDB
    Handles user data structure and password operations
    """

    def __init__(self, email, username, password, user_id=None, created_at=None):
        self.email = email
        self.username = username
        self.password = password
        self._id = user_id
        self.created_at = created_at or datetime.utcnow()

    @staticmethod
    def hash_password(password):
        """
        Hash a plain text password using bcrypt
        Returns hashed password as string
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(plain_password, hashed_password):
        """
        Verify a plain text password against hashed password
        Returns True if password matches, False otherwise
        """
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )

    def to_dict(self):
        """
        Convert user object to dictionary for MongoDB storage
        """
        return {
            'email': self.email,
            'username': self.username,
            'password': self.password,  # Already hashed
            'created_at': self.created_at,
            'last_login': None,
            'detection_count': 0  # Track how many times user used face detection
        }

    @staticmethod
    def from_dict(data):
        """
        Create User object from MongoDB document
        """
        return User(
            email=data.get('email'),
            username=data.get('username'),
            password=data.get('password'),
            user_id=str(data.get('_id')),
            created_at=data.get('created_at')
        )


class UserRepository:
    """
    Repository pattern for User database operations
    Handles all CRUD operations for users
    """

    def __init__(self, db):
        self.collection = db.users

    def create_user(self, email, username, password):
        """
        Create a new user in database
        Returns tuple (success: bool, message: str, user_id: str)
        """
        try:
            # Check if email already exists
            if self.collection.find_one({'email': email}):
                return False, "Email already registered", None

            # Check if username already exists
            if self.collection.find_one({'username': username}):
                return False, "Username already taken", None

            # Create user object with hashed password
            user = User(email, username, User.hash_password(password))

            # Insert into database
            result = self.collection.insert_one(user.to_dict())

            return True, "User created successfully", str(result.inserted_id)

        except Exception as e:
            return False, f"Error creating user: {str(e)}", None

    def find_by_email(self, email):
        """
        Find user by email
        Returns user document or None
        """
        return self.collection.find_one({'email': email})

    def find_by_username(self, username):
        """
        Find user by username
        Returns user document or None
        """
        return self.collection.find_one({'username': username})

    def find_by_id(self, user_id):
        """
        Find user by ID
        Returns user document or None
        """
        try:
            return self.collection.find_one({'_id': ObjectId(user_id)})
        except:
            return None

    def update_last_login(self, user_id):
        """
        Update user's last login timestamp
        """
        try:
            self.collection.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': {'last_login': datetime.utcnow()}}
            )
            return True
        except:
            return False

    def increment_detection_count(self, user_id):
        """
        Increment detection count when user uses face detection
        """
        try:
            self.collection.update_one(
                {'_id': ObjectId(user_id)},
                {'$inc': {'detection_count': 1}}
            )
            return True
        except:
            return False

    def authenticate(self, email, password):
        """
        Authenticate user with email and password
        Returns tuple (success: bool, message: str, user_data: dict)
        """
        user = self.find_by_email(email)

        if not user:
            return False, "Invalid email or password", None

        # Verify password
        if not User.verify_password(password, user['password']):
            return False, "Invalid email or password", None

        # Update last login
        self.update_last_login(str(user['_id']))

        # Return user data without password
        user_data = {
            'id': str(user['_id']),
            'email': user['email'],
            'username': user['username'],
            'created_at': user['created_at'].isoformat() if user.get('created_at') else None
        }

        return True, "Login successful", user_data