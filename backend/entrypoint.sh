#!/bin/bash
set -e

echo "Starting DevOps Tool Backend..."

# Wait for database to be ready
echo "Waiting for database..."
while ! pg_isready -h db -U ${POSTGRES_USER:-devops} > /dev/null 2>&1; do
    echo "Database is unavailable - sleeping"
    sleep 1
done
echo "Database is up!"

# Wait for Redis to be ready
echo "Waiting for Redis..."
while ! redis-cli -h redis ping > /dev/null 2>&1; do
    echo "Redis is unavailable - sleeping"
    sleep 1
done
echo "Redis is up!"

# Initialize migrations directory if it doesn't exist
if [ ! -d "migrations" ]; then
    echo "Initializing database migrations..."
    flask db init
fi

# Run database migrations
echo "Running database migrations..."
flask db upgrade || {
    echo "Migration failed, creating tables manually..."
    python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
}

echo "Database setup complete!"

# Start the application
echo "Starting Gunicorn..."
exec gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 --access-logfile - --error-logfile - app.main:app
