# FinTrack architecture

## Request and storage flow

`Browser → Flask routes/templates → PyMongo → MongoDB Community Server ← MongoDB Compass`

- Flask serves the interface and handles session-based authentication, validation, filters, and exports.
- MongoDB Server stores users and finance documents.
- Compass connects to MongoDB Server for inspection; it is not the server or a Flask dependency.
- Chart.js draws analytics in the browser; it is loaded from a public CDN.

## Data model

| Collection | Main document fields |
|---|---|
| `users` | `username` (unique), `display_name`, `password_hash`, `created_at` |
| `expenses` | `user_id`, `title`, `category`, `amount`, `date`, `payment_mode`, `priority`, `note` |
| `income` | `user_id`, `title`, `source`, `amount`, `date`, `note` |
| `budgets` | `user_id`, `month`, `category`, `amount` |
| `savings` | `user_id`, `title`, `amount`, `date`, `note` |
| `bills` | `user_id`, `title`, `amount`, `due_date`, `status` |
| `financial_goals` | `user_id`, `title`, `target_amount`, `saved_amount`, `deadline` |

All finance collections refer to `users._id` by `user_id`. Queries and destructive actions are scoped to the signed-in user's ID. Demo seed entries belong only to the `tester` account.

## Local setup sequence

1. Start a local MongoDB Server or configure a reachable `MONGO_URI`.
2. Install Python dependencies and set `.env`.
3. Run `python seed_demo.py` to create the tester and demo records.
4. Run `python app.py`, then sign in through the browser.
5. Connect Compass to the same MongoDB URI to inspect collections.

`GET /health` pings the configured MongoDB Server and reports connection status.
