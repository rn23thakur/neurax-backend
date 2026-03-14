```
SQLAlchemy
# Add your project dependencies here, e.g.,
# requests==2.28.1
# Flask==2.2.2
``````gitignore
# Byte-compiled / optimized / DLL files
__pycache__/
*.pyc
*.pyd
*.pyo
*.swp
*.bak

# Distribution / packaging
.Python
build/
dist/
*.egg-info/
*.egg

# Editors
.vscode/        # VSCode settings (if you want to ignore workspace specific settings)
.idea/          # PyCharm settings
*.sublime-project
*.sublime-workspace

# OS
.DS_Store
.env

# Virtual environment
venv/
env/

# Miscellaneous
.pytest_cache/
htmlcov/
.coverage
.mypy_cache/
.tox/

# Database files
*.db
``````python
import os
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Define the path to the database file
# This will create 'my_database.db' in the project root directory
# (one level up from src/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'my_database.db')}"

# SQLAlchemy Engine
# The engine is responsible for communicating with the database
engine = create_engine(DATABASE_URL)

# Declarative Base
# This is the base class for our models
Base = declarative_base()

# Define the User Model
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"

# Session Management
# We create a configured "Session" class
# Each instance of the SessionLocal class will be a database session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Function to create all tables defined in Base
def create_db_tables():
    """
    Creates all tables defined in the Base metadata.
    This should be called once to initialize the database schema.
    """
    print(f"Creating database tables in: {DATABASE_URL}")
    Base.metadata.create_all(engine)
    print("Tables created successfully.")

# Example of how you might use this (for demonstration purposes, not required to run automatically)
if __name__ == "__main__":
    create_db_tables()

    # Example of adding a user (optional, for testing)
    session = SessionLocal()
    try:
        new_user = User(username="johndoe", email="john.doe@example.com")
        session.add(new_user)
        session.commit()
        print(f"Added user: {new_user}")
    except Exception as e:
        session.rollback()
        print(f"Error adding user: {e}")
    finally:
        session.close()

    session = SessionLocal()
    try:
        users = session.query(User).all()
        print("\nCurrent users:")
        for user in users:
            print(user)
    finally:
        session.close()
```



