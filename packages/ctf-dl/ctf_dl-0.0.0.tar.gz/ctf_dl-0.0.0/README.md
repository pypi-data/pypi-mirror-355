# 🛠️ ctf-dl

**ctf-dl** is a fast and flexible command-line tool for downloading CTF challenges from various platforms. It supports authentication, filtering, custom templates, and preset output formats.

> [!WARNING]
> This project is still in development

## 🚀 Quickstart

```bash
ctf-dl https://demo.ctfd.io --token YOUR_TOKEN
```

---

## 🔧 Features

* 🔽 Download **all challenges**: descriptions, files, points, and categories
* 🔁 **Update mode**: only fetch new challenges
* 🗂️ Organize challenges with **custom folder structures**
* 🧩 Format output using **custom Jinja2 templates** (Markdown, JSON, etc.)
* 🎯 Apply filters: by category, point range, solved status
* 🔐 Works across all major platforms via [ctfbridge](https://github.com/bjornmorten/ctfbridge)
* ⚙️ **Preset output formats**: `jmrkdown`, `json`

---

## 📦 Installation

Install via pip:

```bash
pip install ctf-dl
```

---

## 🧪 CLI Usage

```bash
ctf-dl [OPTIONS] URL
```

**Required**:

* `URL` Base URL of the CTF platform (e.g., `https://demo.ctfd.io`)

### Global Options

| Option           | Description                                |
| ---------------- | ------------------------------------------ |
| `--version`      | Show version and exit                      |
| `--check-update` | Check for updates for ctf-dl and ctfbridge |
| `--debug`        | Enable debug logging                       |
| `-h`, `--help`   | Show help message and exit                 |

### Output Options

| Option            | Description                                   | Default      |
| ----------------- | --------------------------------------------- | ------------ |
| `-o`, `--output`  | Output directory to save challenges           | `challenges` |
| `--zip`           | Compress output folder into a `.zip`          |              |
| `--output-format` | Preset format (`json`, `markdown`, `minimal`) |              |

### Templating Options

| Option              | Description                            | Default   |
| ------------------- | -------------------------------------- | --------- |
| `--template`        | Challenge template variant to use      | `default` |
| `--template-dir`    | Directory containing custom templates  |           |
| `--folder-template` | Template for folder structure          | `default` |
| `--index-template`  | Template for challenge index file      | `grouped` |
| `--no-index`        | Do not generate a challenge index file |           |
| `--list-templates`  | List available templates and exit      |           |

### Authentication

| Option             | Description                         |
| ------------------ | ----------------------------------- |
| `-t`, `--token`    | Authentication token                |
| `-u`, `--username` | Username for login                  |
| `-p`, `--password` | Password for login                  |
| `-c`, `--cookie`   | Path to browser cookie/session file |

> ⚠️ Provide either a token **or** username/password, not both.

### Filters

| Option         | Description                                               |
| -------------- | --------------------------------------------------------- |
| `--categories` | Download only specific categories (e.g., `Web`, `Crypto`) |
| `--min-points` | Minimum challenge point value                             |
| `--max-points` | Maximum challenge point value                             |
| `--solved`     | Download only solved challenges                           |
| `--unsolved`   | Download only unsolved challenges                         |

### Behavior Options

| Option             | Description                           | Default |
| ------------------ | ------------------------------------- | ------- |
| `--update`         | Skip already downloaded challenges    | `False` |
| `--no-attachments` | Do not download challenge attachments | `False` |
| `--parallel`       | Number of parallel downloads          | `30`    |

---

## 💡 Examples

```bash
# Download all challenges
ctf-dl https://demo.ctfd.io --token YOUR_TOKEN

# Download to a custom directory
ctf-dl https://demo.ctfd.io --token YOUR_TOKEN --output /tmp/ctf

# Use JSON preset format
ctf-dl https://demo.ctfd.io --token YOUR_TOKEN --output-format json

# Only download Web and Crypto challenges
ctf-dl https://demo.ctfd.io --token YOUR_TOKEN --categories Web Crypto

# Update only new challenges
ctf-dl https://demo.ctfd.io --token YOUR_TOKEN --update

# Download and zip output
ctf-dl https://demo.ctfd.io --token YOUR_TOKEN --zip

# List available templates
ctf-dl --list-templates

# Check for updates
ctf-dl --check-update
```

---

## 📁 Default Output Structure

```
challenges/
├── crypto/
│   ├── rsa-beginner/
│   │   ├── README.md
│   │   └── files/
│   │       ├── chal.py
│   │       └── output.txt
├── web/
│   ├── sql-injection/
│   │   ├── README.md
│   │   └── files/
│   │       └── app.py
```

---

## 🪪 License

MIT License © 2025 [bjornmorten](https://github.com/bjornmorten)
