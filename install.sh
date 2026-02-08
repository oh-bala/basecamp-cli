#!/usr/bin/env sh

# Basecamp CLI Installation Script
# This script installs the Basecamp CLI tool
#
# Usage:
#   sh -c "$(curl -fsSL https://raw.githubusercontent.com/oh-bala/basecamp-cli/main/install.sh)"
#
# Or with a custom repository URL:
#   REPO_URL=https://github.com/oh-bala/basecamp-cli.git sh -c "$(curl -fsSL https://raw.githubusercontent.com/oh-bala/basecamp-cli/main/install.sh)"
#
# Or download and run locally:
#   curl -fsSL https://raw.githubusercontent.com/oh-bala/basecamp-cli/main/install.sh -o install.sh
#   sh install.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default repository URL (can be overridden with REPO_URL env var)
# To use a custom repository, set REPO_URL before running:
#   REPO_URL=https://github.com/oh-bala/basecamp-cli.git sh install.sh
REPO_URL="${REPO_URL:-https://github.com/oh-bala/basecamp-cli.git}"
INSTALL_DIR="${INSTALL_DIR:-${HOME}/.basecamp-cli}"

# Function to print colored messages
info() {
    printf "${BLUE}==>${NC} %s\n" "$1"
}

success() {
    printf "${GREEN}✓${NC} %s\n" "$1"
}

warning() {
    printf "${YELLOW}⚠${NC} %s\n" "$1"
}

error() {
    printf "${RED}✗${NC} %s\n" "$1" >&2
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Try to detect repository URL if running from a git repository
detect_repo_url() {
    if [ -d ".git" ] && command_exists git; then
        DETECTED_URL=$(git remote get-url origin 2>/dev/null || echo "")
        if [ -n "$DETECTED_URL" ]; then
            # Convert SSH URL to HTTPS if needed
            if echo "$DETECTED_URL" | grep -q "^git@"; then
                DETECTED_URL=$(echo "$DETECTED_URL" | sed 's|git@\([^:]*\):\(.*\)|https://\1/\2|' | sed 's|\.git$||')
            fi
            # Ensure it ends with .git
            if ! echo "$DETECTED_URL" | grep -q "\.git$"; then
                DETECTED_URL="${DETECTED_URL}.git"
            fi
            REPO_URL="$DETECTED_URL"
            info "Detected repository URL: $REPO_URL"
        fi
    fi
}

# Function to check Python version
check_python() {
    if ! command_exists python3; then
        error "Python 3 is not installed. Please install Python 3.8 or higher."
        exit 1
    fi

    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
    PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
        error "Python 3.8 or higher is required. Found Python $PYTHON_VERSION"
        exit 1
    fi

    success "Found Python $PYTHON_VERSION"
}

# Function to check pip
check_pip() {
    if ! command_exists pip3 && ! python3 -m pip --version >/dev/null 2>&1; then
        error "pip is not installed. Please install pip first."
        exit 1
    fi

    # Use python3 -m pip if available, otherwise pip3
    if python3 -m pip --version >/dev/null 2>&1; then
        PIP_CMD="python3 -m pip"
    else
        PIP_CMD="pip3"
    fi

    success "Found pip"
}

# Function to clone repository
clone_repo() {
    info "Cloning Basecamp CLI repository from $REPO_URL..."
    
    if [ -d "$INSTALL_DIR" ]; then
        warning "Installation directory already exists: $INSTALL_DIR"
        info "Removing existing directory..."
        rm -rf "$INSTALL_DIR"
    fi

    if command_exists git; then
        git clone "$REPO_URL" "$INSTALL_DIR" || {
            error "Failed to clone repository. Please check your internet connection and repository URL."
            exit 1
        }
        success "Repository cloned successfully"
    else
        error "git is not installed. Please install git first."
        exit 1
    fi
}

# Function to install the package
install_package() {
    info "Installing Basecamp CLI..."
    
    cd "$INSTALL_DIR" || {
        error "Failed to change to installation directory"
        exit 1
    }

    # Upgrade pip first
    info "Upgrading pip..."
    $PIP_CMD install --upgrade pip --quiet || {
        warning "Failed to upgrade pip, continuing anyway..."
    }

    # Install the package
    info "Installing basecamp-cli package..."
    $PIP_CMD install . --quiet || {
        error "Failed to install basecamp-cli"
        exit 1
    }

    success "Basecamp CLI installed successfully"
}

# Function to verify installation
verify_installation() {
    info "Verifying installation..."
    
    if command_exists basecamp; then
        BASECAMP_VERSION=$(basecamp --version 2>/dev/null || echo "installed")
        success "Basecamp CLI is installed and available"
        info "Version: $BASECAMP_VERSION"
        return 0
    else
        error "Basecamp CLI command not found. Installation may have failed."
        warning "Make sure ~/.local/bin (or pip install location) is in your PATH"
        return 1
    fi
}

# Function to show next steps
show_next_steps() {
    echo ""
    info "Installation complete! Next steps:"
    echo ""
    echo "1. Configure OAuth2 credentials:"
    echo "   ${GREEN}basecamp configure${NC}"
    echo ""
    echo "2. Authenticate with Basecamp:"
    echo "   ${GREEN}basecamp auth${NC}"
    echo ""
    echo "3. Start using the CLI:"
    echo "   ${GREEN}basecamp projects list${NC}"
    echo ""
    echo "For more information, visit:"
    echo "   ${BLUE}https://github.com/oh-bala/basecamp-cli${NC}"
    echo ""
}

# Main installation process
main() {
    echo ""
    info "Installing Basecamp CLI..."
    echo ""

    # Try to detect repo URL if running from git repo
    detect_repo_url

    check_python
    check_pip
    clone_repo
    install_package
    
    if verify_installation; then
        show_next_steps
    else
        error "Installation verification failed"
        exit 1
    fi
}

# Run main function
main "$@"
