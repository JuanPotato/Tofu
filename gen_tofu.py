#!/usr/bin/python3

import fontforge
import progressbar
import argparse

def irange(start, end=None):
    if end is None:
        return range(start+1)
    else:
        return range(start, end+1)

def main():
    MAGIC_PADDING = 1/94 * 1000

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

    if (end - start + (2 if args.otf else 1)) > 65535:
        print("Range is", end - start + 1)

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

    for i in bar(irange(start, end)):
        codepoint = hex(i)[2:].upper()
        codepoint = codepoint.zfill(6 if len(codepoint) > 4 else 4)

        char = font.createChar(i)
        char.importOutlines(save_svg(i))
        char.width = 1000 # shouldnt _have_ to do this, but you never know
        char.left_side_bearing = MAGIC_PADDING # to ensure zero width characters are not
        char.right_side_bearing = MAGIC_PADDING

    save_name = 'tofu_{}_{}.{}'.format(start_str, end_str, 'otf' if args.otf else 'ttf')
    print("Saving as {}".format(save_name))
    font.generate(save_name)


char_template = '<path d="{}"/>'
chars_d = { # these are all paths to make the character associated. I made them
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

def save_svg(char):
    with open('tofu.svg', 'w') as f:
        f.write(gen_svg(char))
    
    return 'tofu.svg'


def gen_svg(char):
    if not isinstance(char, int):
        char = ord(char)

    svg = '''<svg viewBox="0 0 94 94" fill="#000"><path d="M1,1v92h92v-92zm1,1h90v90h-90z"/>'''
    
    codepoint = hex(char)[2:].upper()
    codepoint = codepoint.zfill(6 if len(codepoint) > 4 else 4)
    
    for i,c in enumerate(codepoint):
        if len(codepoint) is 4:
            start = 'M{},{}'.format(19 + (32 * (i % 2)), 3 + 48 * (i // 2))
        else:
            start = 'M{},{}'.format(3 + (32 * (i % 3)), 3 + 48 * (i // 3))

        svg += char_template.format(start + chars_d[c]);
        
    svg += '</svg>'
    return svg

if __name__ == "__main__":
    main()
