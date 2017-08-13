#!/usr/bin/python3

import fontforge
import progressbar
import argparse
import os.path
import os

def irange(start, end=None):
    if end is None:
        return range(start+1)
    else:
        return range(start, end+1)

def main():
    parser = argparse.ArgumentParser(description='Generate Tofu font.')

    parser.add_argument('start', metavar='Start', type=str, nargs='?',
                    help='hex code for beginning char. Ex. 0000 or 1000')

    parser.add_argument('end', metavar='End', type=str, nargs='?',
                    help='hex code for ending char. Ex. 0FFF or FFFF')

    parser.add_argument('--file', metavar='File', type=str, nargs=1,
                    help='input for a file containing a list of hexcodes to be generated seperated by newlines')

    parser.add_argument('-t', '--ttf', action='store_true',
                    help='output to an ttf file rather than otf')
            
    parser.add_argument('--release', action='store_true',
                    help='generate release fonts for plane 0 and 1')

    args = parser.parse_args()


    # release overrides everything because why not
    if args.release:
        print("Generating release fonts")
        
        print("Generating Plane 0")
        generate_font(irange(0, 65533), 65534,
            'tofu_plane_0.otf', fontname='TofuPlane0', fullname='Tofu Plane 0')
        
        print("Generating Plane 1")
        generate_font(irange(65536, 65536 + 65533), 65534,
            'tofu_plane_1.otf', fontname='TofuPlane1', fullname='Tofu Plane 1')
        
        return

    if args.file and (args.start or args.end):
        print('Only pass a file or a range')
        exit(2)
    
    if not any([args.file, args.start, args.end]):
        parser.print_help()
        exit(2)

    if sum(1 if a else 0 for a in [args.start, args.end]) is 1:
        print('Please include both a start and end')
        exit(2)

    if args.file:
        if not os.path.isfile(args.file[0]):
            print('`{}` is not a file'.format(args.file[0]))
            exit(2)

        chars = open(args.file[0], 'r').read().split()

        char_range_len = len(chars)
        char_range = map(lambda x: int(x, 16), chars)
    else:
        start_str = args.start.upper()
        end_str = args.end.upper()

        if len(start_str) > 5 or len(start_str) < 4:
            print('Start argument must be 4 or 5 characters long. Ex. 0000 or 10000.')
            exit(2)

        if len(end_str) > 5 or len(end_str) < 4:
            print('End argument must be 4 or 5 characters long. Ex. 0000 or 10000.')
            exit(2)

        try:
            start = int(start_str, 16)
        except ValueError:
            print('Start argument must only contain hexadecimal characters.')
            exit(2)

        try:
            end = int(end_str, 16)
        except ValueError:
            print('End argument must only contain hexadecimal characters.')
            exit(2)

        if start >= end:
            print('Start must be less than end')
            exit(2)

        if (end - start + (2 if args.ttf else 1)) > 65535:
            print('Range is', end - start + 1)

            if args.ttf:
                print('Range max is 65534 characters long. Otf includes one by default?')
            else:
                print('Range max is 65535 characters long.')
            exit(2)

        char_range_len = end - start + 1
        char_range = irange(start, end)
        print('Generating Tofu for unicode characters between U+{} and U+{}'.format(start_str, end_str))

    try:
        fullname = 'Tofu {} - {}'.format(start_str, end_str)
    except:
        fullname = 'Tofu'

    try:
        save_name = 'tofu_{}_{}.{}'.format(start_str, end_str, 'ttf' if args.ttf else 'otf')
    except:
        save_name = 'tofu.{}'.format('ttf' if args.ttf else 'otf')

    generate_font(char_range, char_range_len, save_name, fullname=fullname)


def generate_font(glyphs, glyphs_len, save_name, fontname='Tofu', fullname='Tofu'):
    MAGIC_PADDING = 1/94 * 1000

    font = fontforge.font() # create a new font
    font.familyname = 'Tofu'
    font.fontname = fontname
    font.fullname = fullname
    font.comment = 'The complete opposite of a font'
    font.version = '0.2'
    font.copyright = open('FONT_LICENSE', 'r').read()

    progressbar.streams.wrap_stderr()

    with progressbar.ProgressBar(redirect_stdout=True, max_value=glyphs_len) as bar:
        for i,c in enumerate(glyphs):
            bar.update(i)

            codepoint = hex(c)[2:].upper()
            codepoint = codepoint.zfill(6 if len(codepoint) > 4 else 4)

            char = font.createChar(c)
            char.importOutlines(save_svg(c))
            char.width = 1000 # shouldnt _have_ to do this, but you never know
            char.left_side_bearing = MAGIC_PADDING # to ensure zero width characters are not
            char.right_side_bearing = MAGIC_PADDING

    os.remove('tofu.svg')
    
    print('Saving as {}'.format(save_name))
    font.generate(save_name)

char_template = '<path d="{}"/>'
chars_d = { # these are all paths to make the character associated. I made them
    '0':'v40h24v-40zm8,8h8v24h-8z',
    '1':'v8h8v24h-8v8h24v-8h-8v-32z',
    '2':'v8h16v8h-16v24h24v-8h-16v-8h16v-24z',
    '3':'v8h16v8h-16v8h16v8h-16v8h24v-40z',
    '4':'v24h16v16h8v-40h-8v16h-8v-16z',
    '5':'v24h16v8h-16v8h24v-24h-16v-8h16v-8z',
    '6':'v40h24v-24h-16v-8h16v-8zm8,24h8v8h-8z',
    '7':'v8h16v32h8v-40z',
    '8':'v40h24v-40zm8,8h8v8h-8zm0,16h8v8h-8z',
    '9':'v24h16v16h8v-40zm8,8h8v8h-8z',
    'A':'v40h8v-16h8v16h8v-40zm8,8h8v8h-8z',
    'B':'v40h24v-16h-8v8h-8v-8h8v-8h-8v-8h8v8h8v-16z',
    'C':'v40h24v-8h-16v-24h16v-8z',
    'D':'v40h16v-8h8v-24h-8v24h-8v-24h8v-8z',
    'E':'v40h24v-8h-16v-8h16v-8h-16v-8h16v-8z',
    'F':'v40h8v-16h16v-8h-16v-8h16v-8z',
}

def save_svg(char):
    with open('tofu.svg', 'w') as f:
        f.write(gen_svg(char))
    
    return 'tofu.svg'


def gen_svg(char):
    if not isinstance(char, int):
        char = ord(char)

    svg = '''<svg viewBox='0 0 94 94' fill='#000'><path d='M1,1v92h92v-92zm1,1h90v90h-90z'/>'''
    
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

if __name__ == '__main__':
    main()
