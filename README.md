# Create virtual env

```bash
python3 -m venv venv
```

# Activate virtual env

```cmd
venv\Scripts\activate.bat
```

# Install dependencies

```bash
pip install -r requirements.txt
```

# Start server

```bash
uvicorn --host 0.0.0.0 --port 6969 main:app --reload
```
