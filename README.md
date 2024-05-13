## Prerequisites
- Python 3.11
- Virtualenv

## Using Virtualenv
```bash
# 1. Create and activate virtualenv
$ python -m venv virtualenv
$ source ./virtualenv/bin/activate (Linux)
$ virtualenv\Scripts\activate (Windows)

# 2. Install dependencies
$ pip install -r requirements.txt

# 3. Freeze dependencies
$ pip freeze > requirements.txt