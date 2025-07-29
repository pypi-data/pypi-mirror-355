<table border="0" cellspacing="0" cellpadding="0">
  <tr>
    <td><img src="https://raw.githubusercontent.com/shivdutt-B/heimdall/refs/heads/main/readme.assets/heimdall-logo-transparent.png" width="50" height="50" alt="Heimdall Logo"></td>
    <td><h3>Heimdall</h3></td>
  </tr>
</table>

[![PyPI version](https://img.shields.io/pypi/v/heimdall-python-sdk.svg)](https://pypi.org/project/heimdall-python-sdk/)
[![license](https://img.shields.io/pypi/l/heimdall-python-sdk)](./LICENSE)
[![GitHub issues](https://img.shields.io/github/issues/shivdutt-B/heimdall-python-sdk)](https://github.com/shivdutt-B/heimdall-python-sdk/issues)
[![GitHub stars](https://img.shields.io/github/stars/shivdutt-B/heimdall-python-sdk)](https://github.com/shivdutt-B/heimdall-python-sdk)

> Keep your backend servers **warm and monitored** with a single line of code.

`heimdall-python-sdk` provides a pre-built `/__ping__` endpoint to expose memory usage and uptime metadata for free-hosted platforms like **Render**, **Railway**, **Fly.io**, and more. Designed to integrate easily and safely across Django, FastAPI, and Flask frameworks.

---

## 🚀 Features

- 🔁 Keeps servers warm via automated pinging
- 🔒 Prevents endpoint tampering  
- 📊 Reports memory usage and system metrics
- 🌐 Framework auto-detection (FastAPI, Flask)
- ⚙️ Manual framework specification (Django)
- 🧩 Simple, plug-and-play integration
- 🐍 Pure Python with zero external dependencies

---

## 📦 Installation

```bash
pip install heimdall-python-sdk
```

---

## 🛠️ Usage

### Django

Add the health check endpoint to your Django ```URL(file: urls.py)``` configuration:

```python
from django.urls import path
from heimdall_python_sdk import register_ping, heimdall_ping_point

urlpatterns = [
    path(heimdall_ping_point, register_ping(framework="django")),
    # your other URL patterns...
]
```

### FastAPI

Register the health check with your FastAPI application:

```python
from fastapi import FastAPI
from heimdall_python_sdk import register_ping
import uvicorn

app = FastAPI()
register_ping(app)

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)

```

### Flask

Register the health check with your Flask application:

```python
from heimdall_python_sdk import register_ping
from flask import Flask

app = Flask(__name__)
register_ping(app)

if __name__ == "__main__":
    app.run(port=5000, debug=True)

```

---

## 🔒 Security

Heimdall is designed with security in mind:

- **Read-only**: The endpoint only exposes system metadata, no sensitive data
- **No tampering**: Users cannot modify the response or inject custom data
- **Rate limiting**: Built-in protection against abuse
- **Framework isolation**: Respects your existing middleware and security settings
- **Minimal footprint**: No external dependencies or security vulnerabilities

---

## 📚 API Reference

### `register_ping(app=None, framework=None)`

Registers a health check endpoint with your web application.

**Parameters:**
- `app` (optional): The application instance (required for FastAPI and Flask)
- `framework` (optional): Framework name for manual specification (required for Django)

**Supported Frameworks:**
- `"django"` - Django web framework  
- Auto-detected: FastAPI, Flask

**Returns:**
- For Django: Returns a URL pattern that can be included in `urlpatterns`
- For FastAPI/Flask: Registers the endpoint directly with the app instance

---

## 🧪 Requirements

- Python 3.7+
- Compatible with Django 3.0+, FastAPI 0.65+, Flask 1.0+
- No external dependencies required

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Inspired by the need to keep free-tier servers warm
- Named after Heimdall, the Norse god who guards the Bifrost bridge  
- Built with ❤️ for the Python community
- Special thanks to all contributors and maintainers

---

**Keep your servers vigilant with Heimdall! 🛡️**