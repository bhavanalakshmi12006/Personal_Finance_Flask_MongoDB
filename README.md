# FinTrack — Personal Finance & Expense Analytics

**Flask + HTML/CSS/JavaScript + PyMongo + MongoDB Server**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0%2B-green.svg)](https://flask.palletsprojects.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas%20%2F%20Server-brightgreen.svg)](https://www.mongodb.com/)
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

A full-featured personal finance tracker web application built with Flask and MongoDB. Features secure session authentication, user isolation, seeded demo accounts, income/expense tracking with Essential/Non-essential classification, interactive Chart.js analytics, monthly budgets, savings records, bill reminders, financial goals, and filtered CSV export.

---

### Demo Credentials
- **Username:** `tester`
- **Password:** `TestFinance2026!`
*(Or click "Create an account" to register a new user)*

---

## Online Hosting & Cloud Deployment

### Option 1: Deploy on Render (Recommended)
1. Fork or push this repository to GitHub.
2. Sign in to [Render](https://render.com/) and click **New +** > **Blueprint** (or **Web Service**).
3. Connect your repository: `https://github.com/bhavanalakshmi12006/Personal_Finance_Flask_MongoDB`.
4. Render automatically reads `render.yaml` and starts the app with Gunicorn.
5. In Environment Variables, set `MONGO_URI` to your MongoDB Atlas connection string (e.g. `mongodb+srv://...`), or let the app run with the built-in resilient in-memory database.

### Option 2: Deploy on Vercel
1. Sign in to [Vercel](https://vercel.com/) and click **Add New...** > **Project**.
2. Import `Personal_Finance_Flask_MongoDB` from GitHub.
3. Vercel automatically detects the Python configuration in `vercel.json` and `api/index.py`.
4. Click **Deploy**.

---



## உள்ள அம்சங்கள்

- Sign-in / sign-up / sign-out; password hash வடிவில் சேமிக்கப்படும், ஒவ்வொரு பயனரின் பதிவுகளும் தனித்தனியாக வைக்கப்படும்.
- Dashboard: மொத்த வரவு, செலவு, balance, இந்த மாத budget progress, category breakdown மற்றும் சமீபத்திய செலவுகள்.
- Expense: தேதி, category, payment method, note, **Essential / Non-essential** வகைப்பாடு.
- Income பதிவு.
- Transactions: date range, category, priority, payment method, title/note search filters; filter செய்த expenses-ஐ CSV-ஆகப் பதிவிறக்கம் செய்யலாம்.
- Analytics: filters உடன் மொத்தங்கள், மாதாந்திர செலவு chart, category chart, essential/non-essential chart, payment method chart.
- மாதாந்திர overall/category budget, savings பதிவு, Upcoming/Paid bills, financial goals.
- பல மாதங்களுக்கான sample data கொண்ட demo tester account.

## Windows-ல் இயக்குவது

1. **Python 3.10+**, **MongoDB Community Server** நிறுவவும். MongoDB Compass விருப்பத்திற்கேற்ப நிறுவலாம்.
2. MongoDB Server service-ஐத் தொடங்கவும். வழக்கமான local URI: `mongodb://127.0.0.1:27017/`.
3. ZIP-ஐ extract செய்து `Personal_Finance_Flask_MongoDB` folder-ஐ VS Code-ல் திறக்கவும்.

விரைவு முறையாக, MongoDB Server ஏற்கனவே இயங்கும்போது `run_windows.bat`-ஐ double-click செய்யலாம். இது virtual environment, packages, `.env` மற்றும் demo data-ஐ அமைத்து app-ஐத் தொடங்கும். கீழேயுள்ள manual steps-ஐப் பயன்படுத்தினாலும் அதே முடிவு கிடைக்கும்.

4. அந்த folder-இல் terminal திறந்து virtual environment உருவாக்கி activate செய்யவும்:

   ```powershell
   py -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

5. Packages நிறுவி `.env` configuration உருவாக்கவும்:

   ```powershell
   pip install -r requirements.txt
   copy .env.example .env
   ```

   PowerShell execution policy காரணமாக activate தடைப்பட்டால், Command Prompt-ல் `.venv\Scripts\activate.bat` பயன்படுத்தலாம்.

6. Tester account மற்றும் sample entries உருவாக்கவும்:

   ```powershell
   python seed_demo.py
   ```

7. Flask app தொடங்கவும்:

   ```powershell
   python app.py
   ```

8. Browser-ல் **http://127.0.0.1:5000** திறந்து கீழே உள்ள tester credentials பயன்படுத்தவும்.

   - **Username:** `tester`
   - **Password:** `TestFinance2026!`

இது சோதனைக்கான account. உண்மையான personal data-க்கு இந்த password-ஐப் பயன்படுத்த வேண்டாம். உங்கள் தனி user-ஐ உருவாக்க **Create account**-ஐப் பயன்படுத்தலாம்.

## macOS / Linux-ல் இயக்குவது

முதலில் MongoDB Server தொடங்கியிருக்க வேண்டும். ஒருமுறை permission கொடுத்து, launcher-ஐ இயக்கலாம்:

```bash
chmod +x run_mac_linux.sh
./run_mac_linux.sh
```

அல்லது கீழுள்ள manual setup commands-ஐப் பயன்படுத்தவும்:

```bash
cd Personal_Finance_Flask_MongoDB
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python seed_demo.py
python app.py
```

பிறகு `http://127.0.0.1:5000` திறக்கவும். Login விவரங்கள் மேலே உள்ளதே.

## MongoDB Compass இணைப்பு

1. Compass-ஐத் திறந்து `mongodb://127.0.0.1:27017` முகவரிக்கு connect செய்யவும் (அல்லது `.env`-ல் வைத்த URI-ஐப் பயன்படுத்தவும்).
2. `python seed_demo.py` இயக்கி Compass-ல் Refresh செய்யவும்.
3. **`personal_finance`** database-ல் `users`, `expenses`, `income`, `budgets`, `savings`, `bills`, `financial_goals` collections தெரியும்.
4. Demo entries `user_id` மூலம் tester account-க்கு இணைக்கப்பட்டுள்ளன.

## அமைப்புகள்

`.env.example`-ஐ `.env` என நகலெடுத்து தேவையான values அமைக்கலாம்:

```dotenv
SECRET_KEY=replace-with-a-long-random-secret
MONGO_URI=mongodb://127.0.0.1:27017/
MONGO_DB=personal_finance
FLASK_DEBUG=0
PORT=5000
```

`/health` URL MongoDB connection நிலையைத் தரும். MongoDB Atlas பயன்படுத்தினால் Atlas URI-ஐ `MONGO_URI`-ல் வைத்து, network access allowlist-ஐ அமைக்கவும். `.env`-ஐ யாருடனும் பகிர வேண்டாம்.

### Docker வழியாக MongoDB (விருப்பம்)

Docker நிறுவியிருந்தால் project folder-இல்:

```bash
docker compose up -d mongodb
```

Compass-ல் `mongodb://127.0.0.1:27017`-க்கு connect செய்யலாம்.

## முக்கிய பக்கங்கள்

- `/` — Dashboard (login தேவை)
- `/add-expense`, `/add-income`
- `/transactions` — transaction filters, CSV export
- `/analytics` — charts மற்றும் filters
- `/budget`, `/savings`, `/bills`, `/goals`
- `/health` — MongoDB connection test
- `/login`, `/signup`

## சிக்கல் தீர்வு

- **MongoDB connect ஆகவில்லை:** MongoDB Server தொடங்கியுள்ளதா பார்க்கவும்; Compass அதே URI-க்கு connect ஆகிறதா சரிபார்க்கவும்; `.env`-ல் `MONGO_URI` சரியா பார்க்கவும்.
- **Demo entries இல்லை:** MongoDB தொடங்கியபின் project folder-இல் `python seed_demo.py` இயக்கவும். Script மீண்டும் இயக்கினாலும் duplicate demo data சேர்க்காது.
- **Port 5000 பயன்பாட்டில் உள்ளது:** `.env`-இல் `PORT=5001` அமைத்து app-ஐ மறுதொடக்கம் செய்து `http://127.0.0.1:5001` திறக்கவும்.
- **Charts தெரியவில்லை:** Chart.js CDN பயன்படுத்தப்படுகிறது; browser-க்கு internet தேவை. நிதி பதிவுகள் உங்கள் MongoDB-யிலேயே இருக்கும்.

## பாதுகாப்பு வரம்பு

இது local demo/starter app; வங்கி கணக்குடன் இணைக்கப்படாது. Public deployment-க்கு முன் வலுவான தனிப்பட்ட `SECRET_KEY`, HTTPS, backup, production WSGI server மற்றும் deployment hardening தேவை. Demo password-ஐ மாற்றாமல் sensitive data பயன்படுத்த வேண்டாம். Delete actions POST வழியாக மட்டுமே; user data query ஒவ்வொன்றும் உரிமையாளரை வைத்து கட்டுப்படுத்தப்படுகிறது.
