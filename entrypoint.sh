#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Database connection parameters
DB_USER=${DB_USER:-jeanaime}
DB_PASSWORD=${DB_PASSWORD:-helloNexa}
DB_HOST=${DB_HOST:-147.93.90.223}
DB_PORT=${DB_PORT:-5433}
DB_NAME=${DB_NAME:-nexa_auth_db}

# Maximum number of retries for database connection
MAX_RETRIES=30
RETRY_INTERVAL=2

print_info "Starting FastAPI application with database migrations..."

# Function to check if PostgreSQL is ready
check_postgres() {
    print_info "Checking PostgreSQL connection..."
    
    for i in $(seq 1 $MAX_RETRIES); do
        if nc -z $DB_HOST $DB_PORT; then
            print_success "PostgreSQL is available on $DB_HOST:$DB_PORT"
            return 0
        else
            print_warning "PostgreSQL is not ready yet. Attempt $i/$MAX_RETRIES. Retrying in $RETRY_INTERVAL seconds..."
            sleep $RETRY_INTERVAL
        fi
    done
    
    print_error "PostgreSQL is not available after $MAX_RETRIES attempts"
    exit 1
}

# Function to run database migrations
run_migrations() {
    print_info "Running Alembic database migrations..."
    
    # Check if alembic.ini exists
    if [ ! -f "alembic.ini" ]; then
        print_error "alembic.ini file not found. Please ensure Alembic is properly configured."
        exit 1
    fi
    
    # Check if migrations directory exists
    if [ ! -d "app/infrastructure/db/migrations" ]; then
        print_error "Migrations directory 'app/infrastructure/db/migrations' not found."
        exit 1
    fi
    
    # Run migrations with error handling
    if alembic upgrade head; then
        print_success "Database migrations completed successfully"
    else
        print_error "Database migrations failed"
        exit 1
    fi
}

# Function to create initial migration if none exists
create_initial_migration() {
    print_info "Checking for existing migrations..."
    
    # Check if versions directory is empty
    if [ -z "$(ls -A app/infrastructure/db/migrations/versions/ 2>/dev/null)" ]; then
        print_warning "No migrations found. Creating initial migration..."
        if alembic revision --autogenerate -m "Initial migration"; then
            print_success "Initial migration created successfully"
        else
            print_error "Failed to create initial migration"
            exit 1
        fi
    else
        print_info "Existing migrations found"
    fi
}

# Function to validate environment variables
validate_env() {
    print_info "Validating environment variables..."
    
    required_vars=("DB_USER" "DB_PASSWORD" "DB_HOST" "DB_PORT" "DB_NAME")
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            print_error "Required environment variable $var is not set"
            exit 1
        fi
    done
    
    print_success "All required environment variables are set"
}

# Function to test database connection
test_db_connection() {
    print_info "Testing database connection..."
    
    python << EOF
import psycopg2
import sys
import os

try:
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    conn.close()
    print("Database connection successful")
except Exception as e:
    print(f"Database connection failed: {e}")
    sys.exit(1)
EOF

    print_success "Database connection test passed"
}

# Main execution
main() {
    print_info "=== FastAPI Application Startup ==="
    
    # Validate environment variables
    validate_env
    
    # Check if PostgreSQL is ready
    check_postgres
    
    # Test database connection
    test_db_connection
    
    # Create initial migration if needed
    create_initial_migration
    
    # Run database migrations
    run_migrations
    
    print_success "=== Initialization completed successfully ==="
    print_info "Starting the application with command: $@"
    
    # Execute the original command
    exec "$@"
}

# Handle script interruption
trap 'print_error "Script interrupted"; exit 1' INT TERM

# Run main function
main "$@"