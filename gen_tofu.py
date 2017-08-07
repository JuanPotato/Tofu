#!/usr/bin/python3

import fontforge
import progressbar
import argparse
import psMat as matrix

glyph_templates = { # these are all paths to make the character associated. I made them
    "base": "M1,1v92h92v-92zm1,1h90v90h-90z",
    "0":"v40h24v-40zm8,8h8v24h-8z",
    "1":"v8h8v24h-8v8h24v-8h-8v-32z",
    "2":"v8h16v8h-16v24h24v-8h-16v-8h16v-24z",
    "3":"v8h16v8h-16v8h16v8h-16v8h24v-40z",
    "4":"v24h16v16h8v-40h-8v16h-8v-16z",
    "5":"v24h16v8h-16v8h24v-24h-16v-8h16v-8z",
    "6":"v40h24v-24h-16v-8h16v-8zm8,24h8v8h-8z",
    "7":"v8h16v32h8v-40z",
    "8":"v40h24v-40zm8,8h8v8h-8zm0,16h8v8h-8z",
    "9":"v24h16v16h8v-40zm8,8h8v8h-8z",
    "A":"v40h8v-16h8v16h8v-40zm8,8h8v8h-8z",
    "B":"v40h24v-16h-8v8h-8v-8h8v-8h-8v-8h8v8h8v-16z",
    "C":"v40h24v-8h-16v-24h16v-8z",
    "D":"v40h16v-8h8v-24h-8v24h-8v-24h8v-8z",
    "E":"v40h24v-8h-16v-8h16v-8h-16v-8h16v-8z",
    "F":"v40h8v-16h16v-8h-16v-8h16v-8z",
}

GLYPH_TEMPLATE_SIZE = 94
GLYPH_SIZE = 1000
SCALE_FACTOR = GLYPH_SIZE / GLYPH_TEMPLATE_SIZE
TEMP_FILE = 'tmp.svg'

def irange(start, end=None):
    if end is None:
        return range(start+1)
    else:
        return range(start, end+1)


def main():
    parser = argparse.ArgumentParser(description='Generate Tofu font.')

    parser.add_argument('start', metavar='Start', type=str, nargs=1,
                    help='hex code for beginning char. Ex. 0000 or 1000')

    parser.add_argument('end', metavar='End', type=str, nargs=1,
                    help='hex code for ending char. Ex. 0FFF or FFFF')

    parser.add_argument('-o', '--otf', action='store_true',
                    help='output to an otf file rather than ttf')

    args = parser.parse_args()

    start_str = args.start[0].upper()
    end_str = args.end[0].upper()

    if len(start_str) > 5 or len(start_str) < 4:
        print("Start argument must be 4 or 5 characters long. Ex. 0000 or 10000.")
        exit(2)

    if len(end_str) > 5 or len(end_str) < 4:
        print("End argument must be 4 or 5 characters long. Ex. 0000 or 10000.")
        exit(2)

    try:
        start = int(start_str, 16)
    except ValueError:
        print("Start argument must only contain hexadecimal characters.")
        exit(2)

    try:
        end = int(end_str, 16)
    except ValueError:
        print("End argument must only contain hexadecimal characters.")
        exit(2)

    if start >= end:
        print("Start must be less than end")
        exit(2)

    if (end - start + (2 if args.otf else 1) + len(glyph_templates)) > 65535:
        print("Range is (note: 17 spaces are reserved for template glyphs)", end - start + 1)

        if args.otf:
            print("Range max is 65534 characters long. Otf includes one by default?")
        else:
            print("Range max is 65535 characters long.")
        exit(2)


    print("Generating Tofu for unicode characters between U+{} and U+{}".format(start_str, end_str))


    # return
    progressbar.streams.wrap_stderr()
    bar = progressbar.ProgressBar()
    font = fontforge.font() # create a new font
    font.familyname = 'Tofu'
    font.fontname = 'Tofu'
    font.fullname = 'Tofu {} - {}'.format(start_str, end_str)
    font.comment = 'The complete opposite of a font'
    font.version = '0.1'
    font.copyright = open('FONT_LICENSE', 'r').read()

    # add template glyphs
    for name, path in glyph_templates.items():
        char = font.createChar(-1, 't:{}'.format(name))
        char.importOutlines(gen_svg(path))

    # generate tofu glyphs
    for i in bar(irange(start, end)):
        char = font.createChar(i)
        char.addReference("t:base")

        codepoint = hex(i)[2:].upper()
        codepoint = codepoint.zfill(6 if len(codepoint) > 4 else 4)

        for i,c in enumerate(codepoint):
            # padding + margin * (i % size)
            if len(codepoint) is 4:
                x, y = 19 + 32 * (i % 2), 3 + 48 * (i // 2)
            else:
                x, y = 3 + 32 * (i % 3), 3 + 48 * (i // 3)
            char.addReference(
                't:{}'.format(c),
                matrix.translate(x * SCALE_FACTOR, -y * SCALE_FACTOR)
            )

        char.width = GLYPH_SIZE
        char.left_side_bearing = SCALE_FACTOR
        char.right_side_bearing = SCALE_FACTOR

    save_name = 'tofu_{}_{}.{}'.format(start_str, end_str, 'otf' if args.otf else 'ttf')
    print("Saving as {}".format(save_name))
    font.generate(save_name)


def gen_svg(path):
    with open(TEMP_FILE, 'w') as f:
        f.write('<svg viewBox="0 0 {} {}" fill="#000"><path d="{}"/></svg>'.format(
            GLYPH_TEMPLATE_SIZE, GLYPH_TEMPLATE_SIZE, path
        ))

    return TEMP_FILE


if __name__ == "__main__":
    main()
