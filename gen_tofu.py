#!/usr/bin/python3

import fontforge
import progressbar
import argparse

# 🥔

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

    hex_chars = '0123456789ABCDEF'

    if any(c not in hex_chars for c in start_str):
        print("Start argument must only contain hexadecimal characters.")
        exit(2)

    if any(c not in hex_chars for c in end_str):
        print("End argument must only contain hexadecimal characters.")
        exit(2)
    
    print("Generating Tofu for unicode characters between U+{} and U+{}".format(start_str, end_str))

    start = int(start_str, 16)
    end = int(end_str, 16)

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


    # return
    progressbar.streams.wrap_stderr()
    bar = progressbar.ProgressBar()
    font = fontforge.font() # create a new font
    # font.name = 'Tofu'

    for i in bar(irange(start, end)):
        codepoint = hex(i)[2:].upper()
        codepoint = codepoint.zfill(6 if len(codepoint) > 4 else 4)

        char = font.createChar(i)
        char.importOutlines(save_svg(i))
        char.width = 1000
        char.left_side_bearing = 58.8232421875 # to ensure zero width characters are not
        char.right_side_bearing = 58.8232421875

    save_name = 'tofu_{}_{}.{}'.format(start_str, end_str, 'otf' if args.otf else 'ttf')
    print("Saving as {}".format(save_name))
    font.generate(save_name)


char_template = '<path fill="#000" d="{}"/>'
chars_d = { # these are all paths to make the character associated. I made them
    '0': 'v5h3v-5zm1,1h1v3h-1z',
    '1': 'v1h1v3h-1v1h3v-1h-1v-4z',
    '2': 'v1h2v1h-2v3h3v-1h-2v-1h2v-3z',
    '3': 'v1h2v1h-2v1h2v1h-2v1h3v-5z',
    '4': 'v3h2v2h1v-5h-1v2h-1v-2z',
    '5': 'v3h2v1h-2v1h3v-3h-2v-1h2v-1z',
    '6': 'v5h3v-3h-2v-1h2v-1zm1,3h1v1h-1z',
    '7': 'v1h2v4h1v-5z',
    '8': 'v5h3v-5zm1,1h1v1h-1zm0,2h1v1h-1z',
    '9': 'v3h2v2h1v-5zm1,1h1v1h-1z',
    'A': 'v5h1v-2h1v2h1v-5zm1,1h1v1h-1z',
    'B': 'v5h3v-2h-1v1h-1v-1h1v-1h-1v-1h1v1h1v-2z',
    'C': 'v5h3v-1h-2v-3h2v-1z',
    'D': 'v5h2v-1h1v-3h-1v3h-1v-3h1v-1z',
    'E': 'v5h3v-1h-2v-1h2v-1h-2v-1h2v-1z',
    'F': 'v5h1v-2h2v-1h-2v-1h2v-1z',
}

def save_svg(char):
    with open('tofu.svg', 'w') as f:
        f.write(gen_svg(char))
    
    return 'tofu.svg'


def gen_svg(char):
    if not isinstance(char, int):
        char = ord(char)

    svg = '''<svg viewBox="0 0 17 17"><path fill="#000" d="M1,1v15h15v-15zm1,1h13v13h-13z"/>'''
    
    codepoint = hex(char)[2:].upper()
    codepoint = codepoint.zfill(6 if len(codepoint) > 4 else 4)
    
    for i,c in enumerate(codepoint):
        if len(codepoint) is 4:
            start = 'M{},{}'.format(5 + (4 * (i % 2)), 3 + 6 * (i // 2))
        else:
            start = 'M{},{}'.format(3 + (4 * (i % 3)), 3 + 6 * (i // 3))

        svg += char_template.format(start + chars_d[c]);
        
    svg += '</svg>'
    return svg

if __name__ == "__main__":
    main()