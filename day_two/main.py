from pathlib import Path
import xlrd

xls_path = Path('./xls')
xls_files = list(xls_path.glob('*.xlsx'))


def open_file(path):
    """
    Open and give stats on workbook
    """
    book = xlrd.open_workbook(path)

    # print the number of sheets
    print(f"The book has {book.nsheets} sheets")

    print("Sheets:")
    for sheet in book.sheet_names():
        print(f"\t{sheet}")

    return book


def load_sheets(book, ignore_sheets=[]):
    data_dict = {}
    for sheet_name in book.sheet_names():
        sheet = book.sheet_by_name(sheet_name)
        if '-' in sheet_name:
            # this is a child sheet
            ancestory = sheet_name.split('-')
            for x in range(0, len(ancestory)):
                key = ancestory[x].lower().strip()
                print(key)
        else:
            # first row is var_names
            header_row = sheet.row(0)
            for cell in header_row:
                print(cell.value.lower())
                data_dict[cell.value] = ''


if __name__ == '__main__':
    for file in xls_files:
        cur_book = open_file(file)

        load_sheets(cur_book)
