import xlwt
ezxf = xlwt.easyxf

def write_xls(stream, sheet_name, headings, widths, data, heading_xf, data_xfs):
    book = xlwt.Workbook(encoding='utf8')
    sheet = book.add_sheet(sheet_name)
    rowx = 0
    for colx, value in enumerate(headings):
        sheet.write(rowx, colx, value, heading_xf)
        sheet.col(colx).width = widths[colx]
    sheet.set_panes_frozen(True) # frozen headings instead of split panes
    sheet.set_horz_split_pos(rowx+1) # in general, freeze after last heading row
    sheet.set_remove_splits(True) # if user does unfreeze, don't leave a split there
    for row in data:
        rowx += 1
        for colx, value in enumerate(row):
            sheet.write(rowx, colx, value, data_xfs[colx])
    book.save(stream)

heading_xf = ezxf('font: bold on; align: wrap on, vert centre, horiz center')

kind_to_xf_map = {
    'date':  ezxf(num_format_str='yyyy-mm-dd'),
    'int':   ezxf(num_format_str='#,##0'),
    'money': ezxf('font: italic on; pattern: pattern solid, fore-colour grey25', num_format_str='$#,##0.00'),
    'price': ezxf(num_format_str='#0.000000'),
    'text':  ezxf(),
    }

def hyperlink_website(exhibitor_data, position):
    ret = []
    for e in exhibitor_data:
        l = list(e)
        l[position] = xlwt.Formula('HYPERLINK("%s","%s")' % (e[position],e[position]))
        ret += [tuple(l),]
    return ret

def hyperlink_email(exhibitor_data, position):
    ret = []
    for e in exhibitor_data:
        l = list(e)
        l[position] = xlwt.Formula('HYPERLINK("mailto:%s","%s")' % (e[position],e[position]))
        ret += [tuple(l),]
    return ret

def exhibitor_xls(exhibitor_data, stream):

    hdngs  = ['Room #', 'First Name', 'Last Name', 'Email', 'Company', 'Website', 'Address', 'Address2', 'City', 'State', 'Zip', 'Phone', 'Fax', 'Lines']
    kinds  = ' text      text          text         text     text       text       text       text        text    text     text   text     text   text'.split()
    widths = ' 8         14            14           28       30         30         20         20          20      8        10     12       12     20  '.split()
    data_xfs = [kind_to_xf_map[k] for k in kinds]

    exhibitor_data = hyperlink_website(exhibitor_data, position=4)
    exhibitor_data = hyperlink_email(exhibitor_data, position=2)

    widths = [256 * int(widths[i]) for i in xrange(0,len(widths))]

    write_xls(stream, 'Exhibitors', hdngs, widths, exhibitor_data, heading_xf, data_xfs)

def exhibitor_lines_xls(lines_data, stream):
    hdngs  = ['Line', 'Exhibitor', 'Room #', ]
    kinds  = ' text    text         text  '.split()
    widths = ' 30      30           10     '.split()
    data_xfs = [kind_to_xf_map[k] for k in kinds]

    widths = [256 * int(widths[i]) for i in xrange(0,len(widths))]

    write_xls(stream, "Exhibitors' Lines", hdngs, widths, lines_data, heading_xf, data_xfs)

def retailer_xls(retailer_data, stream):

    hdngs  = ['First Name', 'Last Name', 'Email', 'Company', 'Website', 'Address', 'Address2', 'City', 'State', 'Zip', 'Phone', 'Fax',]
    kinds  = ' text          text         text     text       text       text       text        text    text     text   text     text'.split()
    widths = ' 14            14           28       30         30         20         20          20      8        10     12       12  '.split()
    data_xfs = [kind_to_xf_map[k] for k in kinds]

    retailer_data = hyperlink_website(retailer_data, position=3)
    retailer_data = hyperlink_email(retailer_data, position=1)

    widths = [256 * int(widths[i]) for i in xrange(0,len(widths))]

    write_xls(stream, 'Retailers', hdngs, widths, retailer_data, heading_xf, data_xfs)

