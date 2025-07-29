# frst-auth-cli

&#x20;&#x20;

**frst-auth-cli** is a Command Line Interface (CLI) and Python SDK for managing and verifying user and app permissions on the FRST platform.

* **Quickly check user or app permissions via CLI or SDK**
* **Integrate easily with your Python projects**
* **Configurable environments for different stages (dev/prod, AWS/GCP)**
* **Extensible, testable, and production-ready**

---

## 📦 Installation

### **Recommended: install from PyPI**

For most users and developers, simply install from PyPI:

```bash
pip install frst-auth-cli
```

> **Note:** Requires Python 3.10 or higher.

### **For contributors: editable mode**

If you wish to contribute or develop locally, clone this repository and install in editable mode:

```bash
git clone git@github.com:FRST-Falconi/frst-auth-cli.git
cd frst-auth-cli
pip install -r requirements.txt
pip install -e python
```

---

## 🚀 Usage

### **CLI Commands**

Initialize or show your config:

```bash
frst-auth-cli config init
frst-auth-cli config show
```

Validate a backend token (user) and display profile:

```bash
frst-auth-cli verify-backend-token <env> <token>
```

Validate an app token and display permissions:

```bash
frst-auth-cli verify-app-token <env> <token>
```

Use `--help` to see options for any command:

```bash
frst-auth-cli --help
frst-auth-cli config --help
```

---

### **Python SDK Usage**

> **ℹ️ Best Practice:** Always create a single, global instance of `FrstAuthClient` in your application.
> To avoid overloading the FRST platform and to maximize performance, this client implements an internal cache for token validation.
> **Reuse the same instance (singleton) across your codebase. Do not create a new client for every request.**

#### **Common Use Case: Validate backend\_token, get group, and check company permission**

```python
from frst_auth_cli.core import FrstAuthClient
from frst_auth_cli.exceptions import UserNotFoundError, GroupNotFoundError

client = FrstAuthClient("aws-dev")
backend_token = "YOUR_BACKEND_TOKEN_FROM_FRONTEND"
group_uuid = "GROUP_UUID_FROM_FRONTEND"

try:
    user = client.verify_backend_token(backend_token)
    group = user.get_group(group_uuid)
    if group.company.has_permission("frst_auth.company_manager"):
        print(f"User is company manager in {group.company.name}")
    else:
        print("User is NOT company manager for this group")
except UserNotFoundError:
    print("User not found or invalid token.")
except GroupNotFoundError:
    print("Group not found for this user.")
```

#### **Check group permissions for a light admin (`company_manager_custom`)**

```python
from frst_auth_cli.core import FrstAuthClient
from frst_auth_cli.exceptions import UserNotFoundError, GroupNotFoundError

client = FrstAuthClient("aws-dev")
backend_token = "YOUR_BACKEND_TOKEN_FROM_FRONTEND"
group_uuid = "GROUP_UUID_FROM_FRONTEND"

try:
    user = client.verify_backend_token(backend_token)
    group = user.get_group(group_uuid)
    if group.company.has_permission("frst_auth.company_manager"):
        print(f"User is company manager in {group.company.name}")
        print("Full access. No further group permission checks needed.")
    elif group.company.has_permission("frst_auth.company_manager_custom"):
        print(f"User is light admin in {group.company.name}")
        # Now check specific group permissions
        if group.has_permission("admin_report.can_view_overview_report"):
            print(f"User can view the overview report in group {group.name}")
        else:
            print("User does NOT have permission to view the overview report in this group")
    else:
        print("User is NOT a company manager or light admin for this group/company")
except UserNotFoundError:
    print("User not found or invalid token.")
except GroupNotFoundError:
    print("Group not found for this user.")
```

####

#### **Common Use Case: Validate an app token for backend-to-backend communication**

When integrating two backend microservices, you should use an **app token** (a fixed token generated for your app in the FRST platform).
You can validate this token and check the app's permissions using the code below:

```python
from frst_auth_cli.core import FrstAuthClient
from frst_auth_cli.exceptions import AppNotFoundError

client = FrstAuthClient("aws-dev")  # Environment name
app_token = "YOUR_APP_TOKEN"

try:
    app = client.verify_app_token(app_token)
    if app.has_permission("frst_auth.can_user_inactivation_sync"):
        print("App can inactivate users")
    else:
        print("App does NOT have permission to inactivate users")
except AppNotFoundError:
    print("App not found or invalid app token.")
```

---

#### **Exploring User and Group objects**

```python
from frst_auth_cli.core import FrstAuthClient
from frst_auth_cli.exceptions import UserNotFoundError, GroupNotFoundError

client = FrstAuthClient("aws-dev")
backend_token = "YOUR_BACKEND_TOKEN"

try:
    user = client.verify_backend_token(backend_token)

    # 1. List all groups the user belongs to
    print("User groups:")
    for group in user.groups:
        print(f"- {group.name} (uuid: {group.uuid})")

    # 2. Get the default group
    default_group = user.get_group_default()
    print(f"Default group: {default_group.name}")

    # 3. List modules of the default group
    print("Modules in default group:")
    for module in default_group.modules:
        print(f"- {module.get('code')}")

    # 4. Check the default module of the group
    default_module_code = default_group.module_default
    print(f"Default module: {default_module_code}")

    # 5. Check if a specific module exists in the group
    module_code = "content"
    if default_group.has_module(module_code):
        print(f"Module '{module_code}' exists in the default group")
    else:
        print(f"Module '{module_code}' does NOT exist in the default group")

except UserNotFoundError:
    print("User not found or invalid token.")
except GroupNotFoundError:
    print("Group not found for this user.")
```

---

---

## ⚙️ Configuration

The CLI stores environments and endpoint paths in a user config file (default: `~/.frst_auth_cli/config.json`).

You can initialize or edit this config with:

```bash
frst-auth-cli config init  # creates with default values
frst-auth-cli config show  # prints current config
```

You can customize the environments and paths as needed.

---

## 🗂️ Project Structure

```
frst-auth-cli/
├── python/
│   ├── frst_auth_cli/
│   │   ├── __init__.py
│   │   ├── app.py
│   │   ├── caching.py
│   │   ├── cli.py
│   │   ├── company.py
│   │   ├── config.py
│   │   ├── core.py
│   │   ├── group.py
│   │   └── user.py
│   ├── tests/
│   ├── README.md
│   ├── requirements.txt
│   └── setup.py
├── LICENSE
├── README.md
└── .gitignore
```

---

## 👩‍💻 Contributing

Contributions, issues, and feature requests are welcome!
Feel free to open an [issue](https://github.com/FRST-Falconi/frst-auth-cli/issues) or submit a pull request.

1. Fork this repo
2. Clone to your machine
3. Create your feature branch (`git checkout -b feature/my-feature`)
4. Commit your changes (`git commit -am 'Add some feature'`)
5. Push to the branch (`git push origin feature/my-feature`)
6. Open a pull request

Before submitting, please run tests with:

```bash
pytest python/tests
```

---

## 🛡️ License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

---

## 📫 Contact

For questions, support, or partnership inquiries, contact:

* [Marcos William Ferretti](mailto:ferretti.spo@gmail.com)
* [GitHub: mw-ferretti](https://github.com/mw-ferretti)
* [LinkedIn: mwferretti](https://www.linkedin.com/in/mwferretti/)

---

*Happy coding with FRST! 🚀*
