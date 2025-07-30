# Clip CLI
A simple and powerful command-line tool for URL shortening and user management.
Installation
bashpip install clip-cli
Quick Start
bash# Say hello
clip hi

# Login to your account
clip login

# Shorten a URL
clip url shorten https://example.com

# View your profile
clip user show-me
Commands
Main Commands

clip hi - Greet and get started
clip login - Login to your account
clip logout - Logout from your account
clip user - User management commands
clip url - URL shortening commands

**User Commands**
Use clip user --help to see all user-related commands:

clip user register - Create a new account
clip user show-me - Display your profile information
clip user update-profile - Update your profile details
clip user update-password - Change your password
clip user delete-profile - Delete your account
clip user dashboard - View all URLs you've created

**URL Commands**
Use clip url --help to see all URL-related commands:

clip url shorten <url> - Shorten a long URL
clip url redirect <short-code> - Get redirect information
clip url customize <url> <custom-code> - Create a custom short URL
clip url get-by-id <id> - Find URL by ID
clip url delete <id> - Delete a shortened URL
clip url analytics <id> - View click statistics and analytics


**Help**
For detailed help on any command, use the --help flag:
bashclip --help
clip user --help
clip url --help
clip url shorten --help

**Features**

🔗 URL shortening with custom codes
👤 User account management
📊 Analytics and click tracking
🖥️ Beautiful command-line interface
🔐 Secure login/logout system

**Requirements**

Python 3.8+

Support
For issues and feature requests, please visit my [GitHub repository](https://github.com/ankita311/clip).