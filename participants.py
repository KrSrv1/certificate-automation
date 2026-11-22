from openpyxl import load_workbook


def read_participants(path):
    workbook = load_workbook(path, read_only=True, data_only=True)
    try:
        rows = workbook.worksheets[0].values
        headers = next(rows, ())
        if headers.count("Name") != 1 or headers.count("Email") != 1:
            raise ValueError("The first sheet needs one Name column and one Email column.")
        name_column, email_column = headers.index("Name"), headers.index("Email")
        participants = []
        for row_number, row in enumerate(rows, start=2):
            if all(value is None for value in row):
                continue
            name = str(row[name_column] or "").strip()
            email = str(row[email_column] or "").strip()
            if not name or email.count("@") != 1 or any(c.isspace() for c in email):
                raise ValueError(f"Invalid name or email on workbook row {row_number}.")
            participants.append((name, email))
        return participants
    finally:
        workbook.close()
