#!/usr/bin/python3

import fontforge
import progressbar
import argparse
import os
import itertools
import math
import string

FONT_LICENSE = open('FONT_LICENSE', 'r').read()
TEMPLATE = open('template.sfd', 'r').read()

def irange(start, end=None):
    if end is None:
        return range(start+1)
    else:
        return range(start, end+1)

def ranges_mergeable(r1, r2):
    return r1[0] <= (r2[-1]+1) and r2[0] <= (r1[-1]+1)

def range_combine(r1, r2):
    return irange(min(r1[0], r2[0]), max(r1[-1], r2[-1]))

class range_formatter(string.Formatter):
    def format_field(self, value, spec):
        if isinstance(value, range):
            spec = spec.split(':', 1)
            value = '{0}{2:04X}{1}{0}{3:04X}'.format(
                spec[0],
                ''.join(spec[1:]) or '-', # empty separators are replaced by '-'
                value[0], value[-1]
            )
            spec = ''
        return super(range_formatter, self).format_field(value, spec)

def merge_ranges(ranges):
    found_overlap = True
    while found_overlap:
        found_overlap = False
        for i, j in itertools.permutations(range(len(ranges)), 2):
            if ranges_mergeable(ranges[i], ranges[j]):
                new_range = range_combine(ranges[i], ranges[j])
                print(range_formatter().format(
                    'Notice: merged ranges {} and {} to {}',
                    ranges[i], ranges[j], new_range
                ))
                ranges[i] = new_range
                del ranges[j]
                found_overlap = True
                break
    return ranges

def parse_hex_range(s):
    ret = s.split('-')
    if len(ret) > 2:
        raise argparse.ArgumentTypeError('More than two hyphen separated values provided')

    start = None
    end = None
    try:
        start = int(ret[0], 16)
        end = int(ret[-1], 16)
    except ValueError:
        raise argparse.ArgumentTypeError(
            'Failed to read {} value for range "{}"'.format('start' if start == None else 'end', s)
        )

    if start > 0xFFFFFF or end > 0xFFFFFF:
        raise argparse.ArgumentTypeError('Range {} is out of bounds'.format(s))

    if len(ret) == 2 and start == end:
        print('Warning: range "{}" has same start and end value ({})'.format(s, start))

    if start > end:
        start, end = end, start
        print('Warning: range "{}" has been specified in reverse.'.format(s))

    return irange(start, end)



def format_codepoint(codepoint):
    hex_str = '{:X}'.format(codepoint)
    return hex_str.zfill(6 if len(hex_str) > 4 else 4)

def align_point(i, count, item_size, spacing, total_size, reverse=False):
    if reverse:
        i = count - i - 1
    # remaining_space / 2 + current_item * size_of_one_item
    # remaining_space = total_size - space_taken_by_all_items
    return (total_size - (count * (item_size + spacing) - spacing)) / 2 + i * (item_size + spacing)

class font_builder(object):
    def __init__(self, start):
        self.start = start
        self.id_font = 17
        self.data = [TEMPLATE]
        self.needs_save = False
        self.last_codepoint = None

    def save(self):
        start_str = format_codepoint(self.start)
        end_str = format_codepoint(self.last_codepoint)
        base_name = 'tofu_{}_{}'.format(start_str, end_str)
        save_name_tmp = '{}.sfd'.format(base_name)
        with open(save_name_tmp, 'w') as file:
            file.write('\n'.join(self.data))

        font = fontforge.open(save_name_tmp)
        os.remove(save_name_tmp)
        font.familyname = 'Tofu'
        font.fontname = 'Tofu'
        font.fullname = 'Tofu {} - {}'.format(start_str, end_str)
        font.comment = 'The complete opposite of a font'
        font.version = '0.2'
        font.copyright = FONT_LICENSE

        self.needs_save = False
        return font

    def add_char(self, codepoint):
        hex_str = format_codepoint(codepoint)

        x_count = len(hex_str) // 2
        y_count = len(hex_str) // x_count

        # todo: figure out if trowing away translate matricies, making a template for
        #       each of the 4 positions for each of the 16 glyphs actually saves space      
        #       (testing shows that not using any matrix can save ~8 bytes per character)
        references = ['Refer: 0 -1 N 1 0 0 1 0 0 2']
        for i,c in enumerate(hex_str):
            references.append(
                'Refer: {id_glyph} -1 N 1 0 0 1 {x} {y} 2'.format(
                    id_glyph=int(c, 16) + 1,
                    x=align_point(i % x_count, x_count, 255, 85, 1000),
                    y=align_point(i // x_count, y_count, 425, 90, 1000, True) - 200
                )
            )

        self.data.append((
                'StartChar: uni{codepoint}\n'
                'Encoding: {id_font} {id_uni} {id_glyph}\n'
                'Width: 1000\n'
                'Flags: HW\n'
                'LayerCount: 2\n'
                'Fore\n'
                '{references}\n'
                'EndChar\n'
            ).format(
                codepoint=hex_str,
                id_font=self.id_font,
                id_uni=codepoint,
                id_glyph=self.id_font,
                references='\n'.join(references),
            )
        )

        self.id_font += 1
        self.last_codepoint = codepoint
        self.needs_save = True


def main():
    parser = argparse.ArgumentParser(description='Generate Tofu font.')

    parser.add_argument('-s', '--split', default=8192, type=int, nargs='?',
                    help='how many characters to add to a font before creating a new one')

    parser.add_argument('ranges', metavar='range', type=parse_hex_range, nargs='*',
                    help='hex ranges for chars to generate (inclusive) Ex. 0000-1000 1F00-2F00')

    parser.add_argument('--release', action='store_true',
                    help='generate release fonts for plane 0 and 1')

    args = parser.parse_args()

    if args.release or len(args.ranges) <= 0:
        print('Generating release fonts (plane 0 and 1)')
        args.ranges = [irange(0, 0x1FFFF)]
        args.split = 8192

    if args.split <= 1024:
        args.split = parser.get_default('split')
        print('Warning: Specified split value too small, it has been reverted to the default ({})'.format(args.split))

    ranges = merge_ranges(args.ranges)
    save_name = 'Tofu_{}.ttc'.format('_'.join([range_formatter().format('{::_}', r) for r in ranges]))
    char_count = sum([len(r) for r in ranges])
    font_count = math.ceil(char_count / args.split)

    print('Generating Tofu for unicode characters between {} ({} chars, {} font(s))'.format(
        ', '.join([range_formatter().format('{:U+}', r) for r in ranges]), char_count, font_count
    ))


    # return
    progressbar.streams.wrap_stderr()
    bar = progressbar.ProgressBar(max_value=char_count)

    i = 0
    fonts = []
    font = None
    for codepoint in itertools.chain.from_iterable(ranges):
        if i % args.split == 0:
            if font:
                fonts.append(font.save())
            font = font_builder(codepoint)
        font.add_char(codepoint)
        
        i += 1
        bar.update(i)

    if font.needs_save:
        fonts.append(font.save())

    bar.finish()

    print('saving as {}'.format(save_name), flush=True)
    try:
        fonts[0].generateTtc(save_name, fonts[1:], layer=1,
            flags=('short-post',), ttcflags=('merge',)
        )
    except OSError:
        print('Error saving, filename is probably too long, saving as tofu.ttc', flush=True)
        fonts[0].generateTtc('tofu.ttc', fonts[1:], layer=1,
            flags=('short-post',), ttcflags=('merge',)
        )


if __name__ == '__main__':
    main()