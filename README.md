# Bookmark PDF files

Often, I want to add the table of contents
of a PDF document as bookmarks to the file.
Most existing tools to do this use a GUI
which, for me, is tedious and ineffecient.

I have found it much easier to simply edit the
bookmarks I want in a text file using vim, and
then use this tool to add them to the PDF file.

## Usage

Once you have a bookmarks file you can use:

    $ python __main__.py set-toc -t bookmarks.toc -i input.pdf -o output.pdf

which will produce a file `output.pdf` with the added bookmarks.


Use

    $ python __main__.py dump -p path/to/file.pdf

to print the bookmarks in the appropriate format to stdout.

## Bookmarks Format

Each line in the bookmarks file must have the form:

    <depth> <title> <page num>

The depth must be an integer which starts at 0 and only
increases by one. The title is the bookmark title. The last
column must be an integer representing the page number in
the PDF file.

PDF bookmarks can be nested. For example its possible
to structure bookmarks like this:

    bookmark 1
        bookmark 1.1
        bookmark 1.2
            bookmark 1.2.1
            bookmark 1.2.2
    bookmark 2

The depth encodes the nesting of the bookmarks. It must start
at 0 and can only increase by one in each line, but can decrease
by any amount. The bookmarks in the above example would be
formatted like this:

    0 bookmark 1     1
    1 bookmark 1.1   1
    1 bookmark 1.2   2
    2 bookmark 1.2.1 2
    2 bookmark 1.2.1 3
    0 bookmark 2     4

## Troubleshooting

I have run into issues where PDF files are formatted in such a way
that gives some errors when attempting to add bookmarks to
them. A possible troubleshooting step in this case is to run:

    $ python __main__.py clean -i input.pdf -o output.pdf

to clean up the file. Then running `set-toc` with `output.pdf`
may work.
