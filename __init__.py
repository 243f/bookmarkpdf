from PyPDF4 import PdfFileReader, PdfFileWriter
from PyPDF4.generic import TreeObject
import click
import os
import re

def nested_list_to_depth(lst, out=None, depth=0):
    if out is None:
        out = []

    for x in lst:
        if type(x) is list:
            nested_list_to_depth(x, out, depth+1)
            continue
        out.append((depth, x))

    return out

def get_toc(fp):
    with open(fp, 'rb') as f:
        reader = PdfFileReader(f)
        outline = nested_list_to_depth(reader.outlines)
        return [(depth, page['/Title'], reader.getDestinationPageNumber(page)) for depth, page in outline]

def dump_toc(fp):
    toc = get_toc(fp)

    for x,y,z in toc:
        click.echo(x,'%s' % y,z)

def parse_user_toc(fp):
    r = re.compile('(\d+) *(.*?) *(\d+) *$')

    toc = []
    cur_depth = -1

    with open(fp, 'r') as f:
        for i, line in enumerate(f, 1):
            if line.strip() == '':
                continue

            match = r.search(line)
            if not match:
                click.echo(f'{i}: {line}', line, err=True)
                raise TypeError("Each line must have the form `depth` `title` `page num`")
            x,y,z = match.groups()

            depth = int(x)
            if depth < 0:
                click.echo(f'{i}: {line}', line, err=True)
                raise TypeError("Each line must have the form `depth` `title` `page num`")
            if depth - cur_depth > 1:
                click.echo(f'{i}: {line}', line, err=True)
                raise TypeError("Depth must start at 0, and only increase by one")

            num = int(z)-1
            if num < 0:
                click.echo(f'{i}: {line}', line, err=True)
                raise TypeError("Page number must be positive")

            cur_depth = depth
            toc.append((depth, y, num))

    return toc

def update_toc(toc, fp_in, fp_out):
    fr = open(fp_in, 'rb')
    reader = PdfFileReader(fr)
    writer = PdfFileWriter()
    writer.cloneDocumentFromReader(reader)

    with open(fp_out, 'wb') as fw:
        # for some reason we can't touch the
        # outline without writing first
        writer.write(fw)

    outline = writer.getOutlineRoot()

    outline.clear()
    outline.__class__ = TreeObject

    bookmark_stack = [None]
    last = None
    for depth, title, num in toc:
        if depth+1 > len(bookmark_stack):
            bookmark_stack.append(last)
        while depth+1 < len(bookmark_stack):
            bookmark_stack.pop()
        click.echo(title, num)
        last = writer.addBookmark(title, num, parent=bookmark_stack[-1])

    with open(fp_out, 'wb') as fw:
        writer.write(fw)

    fr.close()

@click.group()
def cli():
    pass

@cli.command(help='dump the bookmarks of a pdf in a table of contents format')
@click.option('-p', '--path', help='path to pdf file', required=True)
def dump(path):
    dump_toc(path)

@cli.command()
@click.option('-t', '--toc', help='path to table of contents file', required=True)
@click.option('-i', '--pdf_in', help='path to input pdf file', required=True)
@click.option('-o', '--pdf_out', default=None, help='path to output pdf file')
def set_toc(toc, pdf_in, pdf_out):
    if pdf_out is None:
        split = os.path.splitext(pdf_in)
        pdf_out = split[0] + '_bookmarked' + split[1]
    toc = parse_user_toc(toc)
    update_toc(toc, pdf_in, pdf_out)

if __name__ == '__main__':
    cli()
