# 🗂️ Sortium

A Python utility to **automatically sort files** in a folder by their **type** (e.g., Images, Documents, Videos, etc.) and their **last modified date**.

---

## 📚 Table of Contents

- [🗂️ Sortium](#️-sortium)
  - [📚 Table of Contents](#-table-of-contents)
  - [🚀 Features](#-features)
  - [🛠️ Installation](#️-installation)
    - [📦 PyPI](#-pypi)
  - [🧪 Run Tests](#-run-tests)
  - [👤 Author](#-author)
  - [📄 License](#-license)
  - [🤝 Contributing](#-contributing)
  - [📚 Documentation \& Issues](#-documentation--issues)

---

## 🚀 Features

* ✅ Automatically organizes files into folders based on type:

  * Images, Documents, Videos, Music, Others
* 📅 Optionally sort files by **last modified date** within each category
* 📁 Optionally **flatten** subdirectories into a single level before sorting

---

## 🛠️ Installation

### 📦 PyPI

Install the package from PyPI:

```bash
pip install sortium
```

Alternatively, install from source:

```bash
# Clone the repository
git clone https://github.com/Sarthak-G0yal/Sortium.git
cd Sortium

# Install in editable mode
pip install -e .
```

---

## 🧪 Run Tests

To run unit tests with coverage:

```bash
pytest src/tests --cov
```

---

## 👤 Author

**Sarthak Goyal**
📧 [sarthakgoyal487@gmail.com](mailto:sarthakgoyal487@gmail.com)

---

## 📄 License

This project is licensed under the [GNU General Public License v3.0](LICENSE).

---

## 🤝 Contributing

Contributions are welcome and appreciated! 🎉

To contribute:

1. **Fork** the repository
2. **Create a new branch** (`feature/my-feature` or `fix/my-fix`)
3. **Write tests** for your changes
4. **Commit** with clear and conventional messages
5. **Open a pull request** and describe your changes

✅ Please follow [Conventional Commits](https://www.conventionalcommits.org/) and ensure your code is linted and tested before submitting.

---

## 📚 Documentation & Issues

This project uses [Sphinx](https://www.sphinx-doc.org/) for documentation.

* 📖 **Documentation**: After running `make html` from the `docs/` folder (`cd docs && make html`), view the docs at [`docs/_build/html/index.html`](docs/_build/html/index.html)

* 🐛 **Issues / Feature Requests**: [Open an issue](https://github.com/Sarthak-G0yal/Sortium/issues)