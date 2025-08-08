
```markdown
# Project Dashboard

![Project Dashboard Screenshot](ui/assets/screenshot.png) <!-- Add a screenshot later -->

A comprehensive open source desktop application for project management with time tracking, team communication, and meeting coordination features.

## Features

- **User Management**: Multi-role authentication system
- **Task Management**: Create and track projects/tasks
- **Bug Tracking**: Report and monitor software issues
- **Time Tracking**: Log working hours with descriptions
- **Team Chat**: Real-time messaging between users
- **Meeting Scheduling**: Plan and track project meetings
- **Reporting**: Generate Excel reports for all modules
- **Database Sync**: Synchronize between SQLite, MongoDB, and MySQL

## Modules

| Module | Description |
|--------|-------------|
| User Management | Create and manage user accounts with roles |
| Task Management | Track projects and assigned tasks |
| Bug Tracking | Report and monitor software bugs |
| Time Tracking | Log and analyze work hours |
| Team Chat | Communicate with team members |
| Meetings | Schedule and manage project meetings |
| Reports | Generate detailed Excel reports |

## Installation

### Prerequisites

- Python 3.9+
- MongoDB (or MongoDB Atlas)
- MySQL (optional, for sync functionality)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/nikjha/ProjectDashboard.git
   cd project-dashboard
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   .venv\Scripts\activate     # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure databases:
   - Copy `.env.example` to `.env` and update credentials
   - Initialize databases by running `main.py` once

## Configuration

Edit `config.py` or `.env` file for:

```ini
# MongoDB Configuration
MONGODB_URI=mongodb+srv://username:password@cluster0.abc123.mongodb.net/
MONGODB_DB_NAME=project_dashboard

# MySQL Configuration (for sync)
MYSQL_HOST=localhost
MYSQL_DATABASE=project_dashboard
MYSQL_USER=root
MYSQL_PASSWORD=
```

## Running the Application

```bash
python main.py
```

## Building the Application

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```

2. Run the build script:
   ```bash
   python build.py
   ```

3. The executable will be in the `dist` folder

## Database Schema

![Database Schema](docs/db_schema.png) 

Key tables:
- `users` - User accounts and credentials
- `projects` - Project information
- `tasks` - Task assignments
- `time_entries` - Tracked work hours
- `messages` - Chat messages
- `meetings` - Scheduled meetings

## Usage Guide

### Login
- Default admin credentials: `admin` / `admin123`
- Change password immediately after first login

### Time Tracking
1. Select project/task
2. Set start/end times
3. Add description
4. Submit entry

### Team Chat
1. Select team member from list
2. Type message and press Send
3. View conversation history

### Meeting Scheduling
1. Click "Schedule Meeting"
2. Set title, time, duration
3. Add participants
4. Add agenda items
5. Save meeting

## Troubleshooting

| Issue | Solution |
|-------|----------|
| MongoDB connection failed | Verify Atlas IP whitelisting and credentials |
| MySQL sync not working | Check MySQL server is running and credentials |
| Missing styles/icons | Ensure all files are in `ui/assets/` and `ui/styles/` |
| Module import errors | Reinstall requirements with `pip install -r requirements.txt` |

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` for more information.

## Contact

Your Name - nikjha2552@gmail.com  
Project Link: [https://github.com/nikjha/ProjectDashboard](https://github.com/nikjha/ProjectDashboard)
```

## Key Elements:

1. **Actual Screenshots**:

2. **Database Schema**:
  

3. **Video Demo** (Optional):
   ```markdown
   ## Demo
   
   ```

4. **Roadmap** (Optional):
   ```markdown
   ## Roadmap
   - [x] Core modules implementation
   - [ ] Mobile companion app
   - [ ] API for web access
   - [ ] Advanced analytics dashboard
   ```

5. **Acknowledgements** (Optional):
   ```markdown
   ## Acknowledgements
   - [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) for the GUI framework
   - [MongoDB Atlas](https://www.mongodb.com/atlas/database) for cloud database
   - [PyInstaller](https://www.pyinstaller.org/) for packaging
   ```
