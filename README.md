# NUSrentals - IT2002 - The App

App for NUS students to view and book nearby properties, created by Group 05

## Key Components
### `app.py`
- User cookies to preserve login data
- Raw SQL queries, performed with `sqlalchemy`
- Flask to render HTML and interact with the front-end
- Rollback for functions in case of failure, returning a 403 error

### `templates`
- `HTML` and `CSS` integration into 1 file
- Uses `Jinja2` for easy, configurable syntax
- Unified design language, based on the NUS colour scheme

### `SQL`
- AppSchema.sql provides the `SQL` schema of the project
- SQL_codes contains the `SQL` codes used for data insertion
