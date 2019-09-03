import ipaddress

from pathlib import Path
import xlrd
from pprint import pprint
from itertools import tee

from jinja2 import Environment, FileSystemLoader
from jinja2.exceptions import TemplateNotFound

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
        else:
            print(f'Loading sheet {sheet_name}')

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
                if 'inet' in headers[col_idx]:
                    pass
                elif 'inet6' in headers[col_idx] and cell_obj.value != '':
                    print(f'{headers[col_idx]} = {cell_obj.value} in sheet {sheet.name}')
                    try:
                        value = ipaddress.IPv6Network(cell_obj.value)
                    except ipaddress.AddressValueError:
                        print(f'There was an issue turning {cell_obj.value} into a IPv6 Network')
                        print(ipaddress.AddressValueError)
                        try:
                            value = IPv6Address(cell_obj.value)
                        except ipaddress.AddressValueError:
                            print(f'{cell_obj.value} is neither a IPv6 Address or Network')
                            print(f'Value is being left blank')
                            value = ''
                else:
                    value = cell_obj.value
                record[key] = value
            data_dict[sheet_name].append(record)

    for sheet in child_sheets:
        headers = [str(cell.value).lower().strip().replace(' ', '_') for cell in sheet.row(0)]
        parent_key_col = -1
        child_key_col = -1

        # should be in format Parent - Child
        # the child sheet has a field in it matching the parent sheet name
        ancestory = sheet.name.split('-')

        # get the parent sheet and headers
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
                if headers[col_idx] == 'inet':
                    pass
                elif headers[col_idx] == 'inet6' and cell_obj.value != '':
                    try:
                        value = ipaddress.IPv6Network(cell_obj.value)
                    except ipaddress.AddressValueError:
                        print(f'There was an issue turning {cell_obj.value} into a IPv6 Network')
                        print(ipaddress.AddressValueError)
                        try:
                            value = IPv6Address(cell_obj.value)
                        except ipaddress.AddressValueError:
                            print(f'{cell_obj.value} is neither a IPv6 Address or Network')
                            print(f'Value is being left blank')
                            value = ''
                elif isinstance(cell_obj.value, float):
                    value = int(cell_obj.value)
                else:
                    value = cell_obj.value

                record[headers[col_idx]] = value
            try:
                parent_pointer.append(record)
            except Exception as e:
                print(record)
                print(e)
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

### jinja2 filters
def inet6_wo_mask(addr):
    return addr.network_address


def inet6_south(prefix):
    if isinstance(prefix, ipaddress.IPv6Network):
        addresses = prefix.hosts()
        next(addresses)
        return next(addresses)


def inet6_north(prefix):
    if isinstance(prefix, ipaddress.IPv6Network):
        addresses = prefix.hosts()
        return next(addresses)


# alias to inet6_south
def inet6_east(prefix):
    return inet6_south(prefix)


# alias to inet6_north
def inet6_west(prefix):
    return inet6_north(prefix)


def inet6_vrrp_north(prefix):
    if isinstance(prefix, ipaddress.IPv6Network):
        hosts = prefix.hosts()
        for i in range(0,1):
            next(hosts)
        address = str(next(hosts)) + "/" + str(prefix.prefixlen)
        return address


def inet6_vrrp_south(prefix):
    if isinstance(prefix, ipaddress.IPv6Network):
        hosts = prefix.hosts()
        for i in range(0,2):
            next(hosts)
        address = str(next(hosts)) + "/" + str(prefix.prefixlen)
        return address


def inet6_vrrp_west(prefix):
    return inet6_vrrp_north(prefix)


def inet6_vrrp_east(prefix):
    return inet6_vrrp_south(prefix)


def inet6_vrrp_vip(prefix):
    if isinstance(prefix, ipaddress.IPv6Network):
        hosts = prefix.hosts()

        address = str(next(hosts)) + "/" + str(prefix.prefixlen)
        return address

### Return a list instead of a generator from the
### ipaddress module
def inet6_prefix_to(prefix, new_mask):
    """Short summary.

    Parameters
    ----------
    prefix : IPv6Network object
        Valid IPv6 network object from the ipaddress module.
    new_mask : int
        The new subnet/prefix mask to subnet the original prefix into.

    Returns
    -------
    list
        Returns a list of IPv6Network objects with the new prefix length.

    """
    if not isinstance(prefix, ipaddress.IPv6Network):
        try:
            prefix = ipaddress.IPv6Network(prefix)
        except ipaddress.AddressValueError:
            print(f"This address is not properly formated: {prefix}")
        except ipaddress.NetMaskValueError:
            print(f'The network mask is not the correct value for this address: {prefix}')
    subnets = list(prefix.subnets(new_prefix=new_mask))
    return subnets


def to_net_id(addr):
    net_id_parts = addr.split('.')
    for idx in range(0, len(net_id_parts)):
        while len(net_id_parts[idx]) < 3:
            net_id_parts[idx] = '0' + net_id_parts[idx]

    net_id = []
    net_id.append(net_id_parts[0] + net_id_parts[1][0:1])
    net_id.append(net_id_parts[1][1:] + net_id_parts[2][0:2])
    net_id.append(net_id_parts[2][2:] + net_id_parts[3][0:])

    return '.'.join(net_id)


def render(template_dir, template, data):
    filters = {
        'to_net_id': to_net_id,
        'inet6_prefix_to': inet6_prefix_to,
        'inet6_wo_mask': inet6_wo_mask,
        'inet6_east': inet6_east,
        'inet6_west': inet6_west,
        'inet6_north': inet6_north,
        'inet6_south': inet6_south,
        'inet6_vrrp_vip': inet6_vrrp_vip,
        'inet6_vrrp_east': inet6_vrrp_east,
        'inet6_vrrp_west': inet6_vrrp_west,
        'inet6_vrrp_north': inet6_vrrp_north,
        'inet6_vrrp_south': inet6_vrrp_south,
    }

    try:
        env = Environment(loader=FileSystemLoader(template_dir))

        # register the filters with the environment
        for k,v in filters.items():
            env.filters[k] = v

        template = env.get_template(template)

        return template.render(data)
    except TemplateNotFound as TNF:
        print(TNF)
        return f"Template {template} could not be found in {template_dir}"


if __name__ == '__main__':
    for file in xls_files:
        cur_book = open_file(file)

        if 'META' in cur_book.sheet_names():
            meta = load_meta(cur_book)
            documentation_template = meta['documentation_template_dir'] + meta['documentation_template']
        else:
            meta = {}
            meta['ignore_sheets'] = []

        relational_wb_data = load_sheets(cur_book, ignore_sheets=meta['ignore_sheets'])

        template_dict = {}
        for host in relational_wb_data['hosts']:
            template_dict['host_data'] = host
            for key in relational_wb_data.keys():
                if len(relational_wb_data[key]) == 1:
                    # There is only one item in the list associated to this key
                    # move the value over so you have a key = value pair
                    template_dict[key] = relational_wb_data[key][0]
                else:
                    # move the list over
                    template_dict[key] = relational_wb_data[key]

            #pprint(template_dict)
            if 'template_dir' in meta.keys():
                template_dir = meta['template_dir'] + host['platform'] + '/'
                template = host['platform'] + '_base.j2'
                config = render(template_dir, template, template_dict)
                print(config)
