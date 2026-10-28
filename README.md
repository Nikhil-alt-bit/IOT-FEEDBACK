# IoT Teacher Feedback Form — Made by Nikhil Kaklij

A working Flask website with a real submission endpoint, SQLite storage, a password-protected admin dashboard, and CSV export.

## Run on your computer

1. Install Python 3.10 or newer.
2. Extract this ZIP file and open a terminal in the extracted folder.
3. Create and activate a virtual environment (optional but recommended):
   - Windows: `py -m venv .venv` then `.venv\\Scripts\\activate`
   - macOS/Linux: `python3 -m venv .venv` then `source .venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Set an admin password before starting:
   - Windows PowerShell: `$env:ADMIN_PASSWORD="choose-a-strong-password"; $env:SECRET_KEY="put-a-long-random-secret-here"`
   - macOS/Linux: `export ADMIN_PASSWORD='choose-a-strong-password'; export SECRET_KEY='put-a-long-random-secret-here'`
6. Start the site: `python app.py`
7. Open `http://127.0.0.1:5000` in your browser.
8. Admin dashboard: `http://127.0.0.1:5000/admin` (login at `/admin/login`).

Submitted feedback is stored in `feedback.db` in this folder. Admins can review responses and export them to CSV.

## Important

- This runs as a real local web application; it saves submissions in a SQLite database.
- To let students submit from their own phones/computers over the internet, deploy the app to a hosting service and configure `ADMIN_PASSWORD` and `SECRET_KEY` as environment variables. Do not use the default admin password on a public deployment.
- Use HTTPS and follow your institution's privacy rules before collecting identifiable student feedback.
- The included admin login is a minimal project-level login. For production use, add rate limiting, CSRF protection, backups, and stronger authentication.


## Deploy on Render (public link)

1. Upload this project to a GitHub repository (extract the ZIP first; upload the files/folders, not the ZIP itself).
2. In Render, choose **New + → Web Service** and connect that repository.
3. Set:
   - Runtime: `Python 3`
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app`
4. Add environment variables:
   - `ADMIN_PASSWORD` = a strong password you choose
   - `SECRET_KEY` = a long random secret
5. Click **Create Web Service**. Render will provide a public `onrender.com` link.

**Database note:** this starter uses SQLite in a local file. On cloud hosting, the default filesystem may be temporary, so feedback can be lost when the service restarts or redeploys. For reliable long-term submissions, configure persistent storage for `feedback.db` or migrate the app to a managed PostgreSQL database before collecting real student data.
