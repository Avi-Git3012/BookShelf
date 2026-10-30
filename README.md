# 📚 BookShelf - Library Management System

A desktop Library Management System built with Python and Tkinter featuring a modern dark theme interface, CSV-backed data persistence, real-time inventory management, student registration, issue/return workflows, and overdue fine calculation.

---

## ✨ Features

- **📖 Book Management**: Add new books, search by ID or title, update quantities, and view live inventory status.
- **🎓 Student Directory**: Register and manage students with unique roll numbers and tracked borrow histories.
- **🔄 Issue & Return Workflow**: Issue books to registered students, enforce active borrowing limits (max 3 books per student), and record returns with one click.
- **⚠️ Overdue Tracking & Fines**: Automated calculation of overdue days and fines for late returns (standard 14-day borrowing window).
- **📊 Real-time Dashboard**: Live summary statistics showing total books, registered students, active issues, and overdue returns.
- **🎨 Modern Dark UI**: Sleek desktop interface with custom button styling, subtle hover states, tooltips, and centered window placement.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- `pip` package manager

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Avi-Git3012/BookShelf.git
   cd BookShelf
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python app.py
   ```

---

## 🛠️ Building Standalone Executable (`.exe`)

To build a standalone Windows executable that runs without Python installed:

```bash
pip install pyinstaller
python -m PyInstaller --noconsole --onefile --distpath . -n "BookShelf" app.py
```

---

## 📁 Project Structure

```text
LIBRARY/
├── app.py                  # Tkinter GUI application & main window
├── library_management.py   # Core business logic & CSV data persistence
├── background.png          # UI background artwork
├── book.csv                # Books database
├── student.csv             # Students database
├── issue.csv               # Borrow / Return transaction records
├── requirements.txt        # Python package dependencies
├── .gitignore              # Files excluded from git tracking
└── README.md               # Project documentation
```

---

## 📄 License
This project is open source and available under the [MIT License](LICENSE).
