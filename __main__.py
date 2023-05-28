from PyPDF4 import PdfFileReader, PdfFileWriter, PdfFileMerger
from PyPDF4.generic import TreeObject
from PyPDF4.utils import PdfReadError
import click
import os
import re

class FormatError(click.ClickException):
    def __init__(self, i, line, message):
        self.i = i
        self.line = line.strip('\n')
        self.message = message
        self.exit_code = -1
        super().__init__(message)

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
        click.echo(f'{x} {y} {z}')

def parse_user_toc(fp):
    r = re.compile('^\s*(\d+)\s*(.*?)\s*(\d+)\s*$')

    toc = []
    cur_depth = -1

    with open(fp, 'r') as f:
        for i, line in enumerate(f, 1):
            if line.strip() == '':
                continue

            match = r.search(line)
            if not match:
                raise FormatError(i, line, "Each line must have the form `depth` `title` `page num`")
            x,y,z = match.groups()

            depth = int(x)
            if depth < 0:
                raise FormatError(i, line, "Each line must have the form `depth` `title` `page num`")
            if depth - cur_depth > 1:
                raise FormatError(i, line, "Depth must start at 0, and only increase by one")

            num = int(z)-1
            if num < 0:
                raise FormatError(i, line, "Page number must be positive")

            cur_depth = depth
            toc.append((depth, y, num))

    return toc

def update_toc(toc, fp_in, fp_out):
    with open(fp_in, 'rb') as fr:
        reader = PdfFileReader(fr)
        writer = PdfFileWriter()
        writer.cloneDocumentFromReader(reader)

        with open(fp_out, 'wb') as fw:
            # for some reason we can't touch the
            # outline without writing first
            try:
                writer.write(fw)
            except PdfReadError as e:
                msg = f'{e} This error may be resolved using the clean command.'
                raise click.ClickException(msg)

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
            click.echo(f'{title} {num}')
            last = writer.addBookmark(title, num, parent=bookmark_stack[-1])

        with open(fp_out, 'wb') as fw:
            writer.write(fw)

@click.group()
def cli():
    pass

@cli.command(help='dump the bookmarks of a pdf in a table of contents format')
@click.option('-p', '--path', help='path to pdf file', required=True)
def dump(path):
    dump_toc(path)

@cli.command()
@click.option('-t', '--toc', help='path to table of contents file', required=True)
@click.option('-i', '--in', 'pdf_in', help='path to input pdf file', required=True)
@click.option('-o', '--out', 'pdf_out', default=None, help='path to output pdf file')
def set_toc(toc, pdf_in, pdf_out):
    if pdf_out is None:
        split = os.path.splitext(pdf_in)
        pdf_out = split[0] + '_bookmarked' + split[1]

    try:
        toc = parse_user_toc(toc)
    except FormatError as e:
        click.echo(f'{e.i}:{e.line}', err=True)
        raise e

    update_toc(toc, pdf_in, pdf_out)

@cli.command(help='Simply rewrites the pdf file but in a format that may lead to fewer bugs')
@click.option('-i', '--in', 'fp_in', help='path to pdf file', required=True)
@click.option('-o', '--out', 'fp_out', default=None, help='path to output')
def clean(fp_in, fp_out):
    if fp_out is None:
        split = os.path.splitext(fp_in)
        fp_out = split[0] + '_clean' + split[1]

    merger = PdfFileMerger(strict=False)
    merger.append(fp_in)
    merger.write(fp_out)

if __name__ == '__main__':
    cli()
