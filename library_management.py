import csv
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent

BOOK_FILE = BASE_DIR / "book.csv"
STUDENT_FILE = BASE_DIR / "student.csv"
ISSUE_FILE = BASE_DIR / "issue.csv"

BOOK_HEADERS = ["BOOK_ID", "NAME", "QUANTITY"]
STUDENT_HEADERS = ["ROLL NUMBER", "NAME"]
ISSUE_HEADERS = ["ROLL NUMBER", "BOOK_ID", "BOOK_NAME", "ISSUE DATE", "RETURN DATE", "IF_RETURNED"]

DATE_FORMAT = "%Y-%m-%d"


def init_storage():
    if not STUDENT_FILE.exists():
        with open(STUDENT_FILE, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(STUDENT_HEADERS)

    if not BOOK_FILE.exists():
        with open(BOOK_FILE, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(BOOK_HEADERS)
    else:
        with open(BOOK_FILE, "r", newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
        if rows:
            header = [h.strip().upper() for h in rows[0]]
            if header == ["NAME", "QUANTITY"]:
                new_rows = []
                for idx, r in enumerate(rows[1:], start=101):
                    if len(r) >= 2:
                        new_rows.append([f"B{idx}", r[0].strip(), r[1].strip()])
                with open(BOOK_FILE, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(BOOK_HEADERS)
                    writer.writerows(new_rows)

    if not ISSUE_FILE.exists():
        with open(ISSUE_FILE, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(ISSUE_HEADERS)
    else:
        with open(ISSUE_FILE, "r", newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
        if rows:
            header = [h.strip().upper() for h in rows[0]]
            if len(header) == 5 and "BOOK_ID" not in header:
                name_to_id = {}
                if BOOK_FILE.exists():
                    with open(BOOK_FILE, "r", newline="", encoding="utf-8") as bf:
                        b_rows = list(csv.reader(bf))
                        for br in b_rows[1:]:
                            if len(br) >= 2:
                                name_to_id[br[1].strip().lower()] = br[0].strip().upper()

                new_rows = []
                for r in rows[1:]:
                    if len(r) >= 5:
                        b_name = r[1].strip()
                        b_id = name_to_id.get(b_name.lower(), "B101")
                        new_rows.append([r[0].strip(), b_id, b_name, r[2].strip(), r[3].strip(), r[4].strip()])
                with open(ISSUE_FILE, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(ISSUE_HEADERS)
                    writer.writerows(new_rows)


def get_current_date():
    return date.today().strftime(DATE_FORMAT)


def calculate_default_return_date(days=14):
    due = date.today() + timedelta(days=days)
    return due.strftime(DATE_FORMAT)


def _read_csv(file_path):
    init_storage()
    with open(file_path, "r", newline="", encoding="utf-8") as f:
        reader = list(csv.reader(f))
        if not reader:
            return []
        return reader[1:]


def _write_csv(file_path, header, rows):
    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


def get_all_students():
    rows = _read_csv(STUDENT_FILE)
    return [{"roll_number": row[0].strip(), "name": row[1].strip()} for row in rows if len(row) >= 2]


def find_student(roll):
    roll_clean = str(roll).strip().lower()
    for student in get_all_students():
        if student["roll_number"].lower() == roll_clean:
            return student
    return None


def add_student(roll, name):
    roll_clean = str(roll).strip()
    name_clean = str(name).strip()

    if not roll_clean or not name_clean:
        return False, "Roll number and name cannot be empty."

    if find_student(roll_clean):
        return False, f"Student with roll number '{roll_clean}' already exists."

    with open(STUDENT_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([roll_clean, name_clean])

    return True, f"Student '{name_clean}' ({roll_clean}) registered successfully."


def delete_student(roll):
    roll_clean = str(roll).strip()
    student = find_student(roll_clean)
    if not student:
        return False, f"Student with roll number '{roll_clean}' does not exist."

    active_issues = get_active_issues_for_student(roll_clean)
    if active_issues:
        return False, f"Cannot delete student: they have {len(active_issues)} unreturned book(s)."

    rows = _read_csv(STUDENT_FILE)
    updated_rows = [row for row in rows if row and row[0].strip().lower() != roll_clean.lower()]
    _write_csv(STUDENT_FILE, STUDENT_HEADERS, updated_rows)

    return True, f"Student with roll number '{roll_clean}' deleted successfully."


def generate_next_book_id():
    books = get_all_books()
    max_num = 100
    for b in books:
        match = re.match(r"^B(\d+)$", b["id"].upper())
        if match:
            max_num = max(max_num, int(match.group(1)))
    return f"B{max_num + 1}"


def get_all_books():
    rows = _read_csv(BOOK_FILE)
    books = []
    for row in rows:
        if len(row) >= 3:
            try:
                qty = int(row[2].strip())
            except ValueError:
                qty = 0
            books.append({
                "id": row[0].strip().upper(),
                "name": row[1].strip(),
                "quantity": qty
            })
        elif len(row) == 2:
            try:
                qty = int(row[1].strip())
            except ValueError:
                qty = 0
            books.append({
                "id": "B101",
                "name": row[0].strip(),
                "quantity": qty
            })
    return books


def find_book(identifier):
    ident_clean = str(identifier).strip().lower()
    for book in get_all_books():
        if book["id"].lower() == ident_clean or book["name"].lower() == ident_clean:
            return book
    return None


def add_book(name, quantity, book_id=None):
    name_clean = str(name).strip()
    id_clean = str(book_id).strip().upper() if book_id and str(book_id).strip() else None

    if not name_clean:
        return False, "Book title cannot be empty."

    if quantity <= 0:
        return False, "Quantity must be greater than 0."

    rows = _read_csv(BOOK_FILE)
    target_idx = -1

    for i, row in enumerate(rows):
        if len(row) >= 3:
            row_id = row[0].strip().upper()
            row_name = row[1].strip().lower()

            if id_clean and row_id == id_clean:
                target_idx = i
                break
            elif row_name == name_clean.lower():
                target_idx = i
                break

    if target_idx != -1:
        current_qty = int(rows[target_idx][2].strip()) if rows[target_idx][2].strip().isdigit() else 0
        rows[target_idx][2] = str(current_qty + quantity)
        existing_id = rows[target_idx][0]
        existing_name = rows[target_idx][1]
        _write_csv(BOOK_FILE, BOOK_HEADERS, rows)
        return True, f"Updated stock for '{existing_name}' (ID: {existing_id}) (+{quantity})."
    else:
        assigned_id = id_clean if id_clean else generate_next_book_id()
        with open(BOOK_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([assigned_id, name_clean, str(quantity)])
        return True, f"Book '{name_clean}' added with ID: {assigned_id} (Quantity: {quantity})."


def delete_book(identifier):
    ident_clean = str(identifier).strip()
    book = find_book(ident_clean)
    if not book:
        return False, f"Book '{ident_clean}' does not exist in catalog."

    active_issues = get_active_issues_for_book(book["id"])
    if not active_issues:
        active_issues = get_active_issues_for_book(book["name"])

    if active_issues:
        return False, f"Cannot delete book: {len(active_issues)} copy/copies currently issued."

    rows = _read_csv(BOOK_FILE)
    updated_rows = [
        row for row in rows
        if len(row) >= 3 and row[0].strip().upper() != book["id"].upper()
    ]
    _write_csv(BOOK_FILE, BOOK_HEADERS, updated_rows)

    return True, f"Book '{book['name']}' (ID: {book['id']}) deleted successfully."


def get_all_issues(status_filter="ALL"):
    rows = _read_csv(ISSUE_FILE)
    issues = []
    for row in rows:
        if len(row) >= 6:
            record = {
                "roll_number": row[0].strip(),
                "book_id": row[1].strip().upper(),
                "book_name": row[2].strip(),
                "issue_date": row[3].strip(),
                "return_date": row[4].strip(),
                "if_returned": row[5].strip().upper(),
            }
        elif len(row) == 5:
            record = {
                "roll_number": row[0].strip(),
                "book_id": "B101",
                "book_name": row[1].strip(),
                "issue_date": row[2].strip(),
                "return_date": row[3].strip(),
                "if_returned": row[4].strip().upper(),
            }
        else:
            continue

        if status_filter == "ACTIVE" and record["if_returned"] != "NO":
            continue
        if status_filter == "RETURNED" and record["if_returned"] != "YES":
            continue
        issues.append(record)
    return issues


def get_active_issues_for_student(roll):
    roll_clean = str(roll).strip().lower()
    return [issue for issue in get_all_issues("ACTIVE") if issue["roll_number"].lower() == roll_clean]


def get_active_issues_for_book(identifier):
    ident_clean = str(identifier).strip().lower()
    return [
        issue for issue in get_all_issues("ACTIVE")
        if issue["book_id"].lower() == ident_clean or issue["book_name"].lower() == ident_clean
    ]


def issue_book(roll, book_identifier, return_date_str=None):
    roll_clean = str(roll).strip()
    ident_clean = str(book_identifier).strip()

    student = find_student(roll_clean)
    if not student:
        return False, f"Student with roll number '{roll_clean}' not found. Please register student first."

    book = find_book(ident_clean)
    if not book:
        return False, f"Book '{ident_clean}' does not exist in the catalog."

    active_issues = get_active_issues_for_student(roll_clean)
    for issue in active_issues:
        if issue["book_id"].lower() == book["id"].lower() or issue["book_name"].lower() == book["name"].lower():
            return False, f"Student already has an active copy of '{book['name']}'."

    book_rows = _read_csv(BOOK_FILE)
    target_idx = -1
    for i, row in enumerate(book_rows):
        if len(row) >= 3 and row[0].strip().upper() == book["id"].upper():
            target_idx = i
            break

    if target_idx == -1:
        return False, f"Book '{book['name']}' not found in inventory."

    current_qty = int(book_rows[target_idx][2].strip()) if book_rows[target_idx][2].strip().isdigit() else 0
    if current_qty <= 0:
        return False, f"Book '{book['name']}' ({book['id']}) is currently out of stock."

    book_rows[target_idx][2] = str(current_qty - 1)
    _write_csv(BOOK_FILE, BOOK_HEADERS, book_rows)

    actual_issue_date = get_current_date()
    final_return_date = return_date_str.strip() if return_date_str and return_date_str.strip() else calculate_default_return_date()

    with open(ISSUE_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([roll_clean, book["id"], book["name"], actual_issue_date, final_return_date, "NO"])

    return True, f"Book '{book['name']}' (ID: {book['id']}) issued to '{student['name']}'. Due: {final_return_date}."


def return_book(roll, book_identifier):
    roll_clean = str(roll).strip().lower()
    ident_clean = str(book_identifier).strip().lower()

    book = find_book(ident_clean)
    book_id_target = book["id"].lower() if book else ident_clean
    book_name_target = book["name"].lower() if book else ident_clean

    issue_rows = _read_csv(ISSUE_FILE)
    target_issue_index = -1

    for i, row in enumerate(issue_rows):
        if len(row) >= 6:
            r_roll = row[0].strip().lower()
            r_id = row[1].strip().lower()
            r_name = row[2].strip().lower()
            r_status = row[5].strip().upper()

            if r_roll == roll_clean and r_status == "NO":
                if r_id == ident_clean or r_name == ident_clean or r_id == book_id_target or r_name == book_name_target:
                    target_issue_index = i
                    break
        elif len(row) == 5:
            r_roll = row[0].strip().lower()
            r_name = row[1].strip().lower()
            r_status = row[4].strip().upper()
            if r_roll == roll_clean and r_status == "NO":
                if r_name == ident_clean or r_name == book_name_target:
                    target_issue_index = i
                    break

    if target_issue_index == -1:
        return False, f"No active issue record found for Roll: {roll} and Book: '{book_identifier}'."

    status_col_idx = 5 if len(issue_rows[target_issue_index]) >= 6 else 4
    issue_rows[target_issue_index][status_col_idx] = "YES"
    _write_csv(ISSUE_FILE, ISSUE_HEADERS, issue_rows)

    resolved_id = issue_rows[target_issue_index][1] if len(issue_rows[target_issue_index]) >= 6 else None
    resolved_name = issue_rows[target_issue_index][2] if len(issue_rows[target_issue_index]) >= 6 else issue_rows[target_issue_index][1]

    book_rows = _read_csv(BOOK_FILE)
    for row in book_rows:
        if len(row) >= 3:
            if (resolved_id and row[0].strip().upper() == resolved_id.upper()) or row[1].strip().lower() == resolved_name.lower():
                current_qty = int(row[2].strip()) if row[2].strip().isdigit() else 0
                row[2] = str(current_qty + 1)
                break
    _write_csv(BOOK_FILE, BOOK_HEADERS, book_rows)

    return True, f"Book '{resolved_name}' returned successfully."


student_entry = add_student
book_entry = add_book
issue_entry = issue_book
