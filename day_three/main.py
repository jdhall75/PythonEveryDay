from pathlib import Path
import xlrd
from pprint import pprint
from jinja2 import Environment, FileSystemLoader

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

# child and parent relationships are separated by a hyphen
# The 1st layer sheet will have a key feild in it the same name as
# the sheet name
# The child sheet name will have the parent name as well as the child
# name separated by a hyphen.
# example:
#
# 'Parent_sheet'
# | Parent_sheet | data1 | data2 | data3 |
# ----------------------------------------
# | asdf         | 123   | help  | kind  |
# | qwer         | 234   | hurt  | gentle|
#
# 'Parent_sheet - Child_sheet'
# | Parent_sheet | child_sheet | data1 | data2 |
# -----------------------------------------------
# | asdf         | yuio        | help  | kind  |
# | asdf         | hjkl        | hurt  | gentle|
#
#
def load_sheets(book, ignore_sheets=[]):
    data_dict = {}
    child_sheets = []
    parent_sheets = []

    for sheet_name in book.sheet_names():
        if sheet_name in ignore_sheets:
            print(f'Skipping sheet {sheet_name}')
            continue

        if '-' in sheet_name:
            child_sheets.append(book.sheet_by_name(sheet_name))
        else:
            parent_sheets.append(book.sheet_by_name(sheet_name))


    # process the parent sheets first...
    # parents have to exist before they can have children
    for sheet in parent_sheets:

        sheet_name = sheet.name.lower().strip().replace(' ','_')
        # collect the headers from the sheet
        headers = [str(cell.value).lower().strip().replace(' ', '_') for cell in sheet.row(0)]
        data_dict[sheet_name] = []
        # start processing the rows
        # starting with index of 1 because we have headers
        for row_idx in range(1,sheet.nrows):
            record = {}
            for col_idx in range(0, sheet.ncols):
                cell_obj = sheet.cell(row_idx, col_idx)
                key = headers[col_idx]
                record[key] = cell_obj.value
            data_dict[sheet_name].append(record)

    for sheet in child_sheets:

        headers = [str(cell.value).lower().strip().replace(' ', '_') for cell in sheet.row(0)]
        parent_key_col = -1
        child_key_col = -1

        # should be in format Parent - Child
        # the child sheet has a field in it matching the parent sheet name
        ancestory = sheet.name.split('-')

        # get the parent sheet and headers
        print(ancestory[0].strip())
        parent_sheet = book.sheet_by_name(ancestory[0].strip())
        parent_sheet_name = parent_sheet.name.lower().strip().replace(' ', '_')
        parent_headers = [str(cell.value).lower().strip().replace(' ', '_') for cell in parent_sheet.row(0)]


        # process the child sheet
        for row_idx in range(1, sheet.nrows):
            # create a record per row
            record = {}
            # each row could have a different parent
            # holder for the parent while consuming the columns(fileds)
            parent_pointer = ''
            # each col is a field in the record
            for col_idx in range(0, sheet.ncols):
                cell_obj = sheet.cell(row_idx, col_idx)

                # find the parent to store this data in
                # find the column we should be matching on.
                if headers[col_idx] == parent_sheet_name.lower().strip().replace(' ', '_'):
                    # iterrate over the parent list in the data_dict
                    for parent in data_dict[headers[col_idx]]:
                        # if the cell_obj.value equals the value of the parent field
                        # Make a list if there isnt one and assign the pointer
                        if cell_obj.value == parent[headers[col_idx]]:
                            if ancestory[1].strip().lower().replace(' ', '_') not in parent:
                                parent[ancestory[1].strip().lower().replace(' ', '_')] = []
                            parent_pointer = parent[ancestory[1].strip().lower().replace(' ', '_')]


                    # print(f'Fields {parent_sheet_name} matched')
                record[headers[col_idx]] = cell_obj.value
            parent_pointer.append(record)
    return data_dict

def load_meta(wb):
    sheet = wb.sheet_by_name('META')

    metadata = {}
    # FIRST ROW IS HEADERS
    for row_idx in range(1, sheet.nrows):
        key = sheet.cell(row_idx, 0).value
        value = sheet.cell(row_idx, 1).value.strip()

        # ignore_sheets can be a comman separated list
        if key == 'ignore_sheets' and ',' in value:
            value = value.split(',')
            value = [ item.strip() for item in value ]

        # always strip bad data off the front and back of the line
        metadata[key] = value

    return metadata

def render(template_dir, template, data):
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template(template)

    return template.render(data = data)



if __name__ == '__main__':
    for file in xls_files:
        cur_book = open_file(file)

        if 'META' in cur_book.sheet_names():
            meta = load_meta(cur_book)
            documentation_template = meta['documentation_template_dir'] + meta['documentation_template']
            pprint(meta)
        else:
            meta = {}
            meta['ignore_sheets'] = []

        relational_wb_data = load_sheets(cur_book, ignore_sheets=meta['ignore_sheets'])

        # pprint(relational_wb_data)

        if 'template_dir' in meta.keys():
            xml = render(meta['template_dir'], meta['template'], relational_wb_data)
            print(xml)
