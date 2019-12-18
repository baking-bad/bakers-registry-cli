import sys

# Based on https://github.com/Miku-chan/printjson/

COLOR_PREAMBLE = '\x1b[38;5;'
C_RES = '\x1b[0m'
COLORS_16 = [str(i) + 'm' for i in range(0, 16)]


class PrinterJSON:
    """Print data structure as JSON"""
    c_lst = 0
    c_dic = 0
    c_dat = 2
    c_log = 4
    c_key = 6
    c_val = 3
    sep1 = ': '
    sep2 = ',\n'
    termdic = ('{\n', '\n}')
    termlst = ('[\n', '\n]')
    curind = 0
    ind = 2
    onkey = True

    def __init__(self):
        self.simple_data = None

    def set_color(self, num):
        """Set output color of stdout to num"""
        if 0 < num < len(COLORS_16):
            sys.stdout.write(COLOR_PREAMBLE + COLORS_16[num])
        else:
            sys.stdout.write(C_RES)

    def reset_color(self):
        """Set output color of stdout to default"""
        sys.stdout.write(C_RES)

    def cpr(self, string, color_num):
        """Print colorized string"""
        self.set_color(color_num)
        sys.stdout.write(string)
        self.reset_color()

    def print_indent(self):
        sys.stdout.write(' ' * self.curind)

    def end(self, p, c):
        self.cpr(p.replace('\n', '\n' + ' ' * self.curind), c)

    def print_bool(self, a):
        """Print bool or null variable"""
        self.set_color(self.c_log)
        if a is True:
            sys.stdout.write('true')
        elif a is False:
            sys.stdout.write('false')
        elif a is None:
            sys.stdout.write('null')
        self.reset_color()

    def print_num(self, a):
        """Print number."""
        self.cpr(str(a), self.c_dat)

    def print_str(self, a):
        """Print string with colorized (if set) brackets"""
        if self.simple_data:
            sys.stdout.write(a)
        else:
            self.cpr(f'"{a}"', self.c_key if self.onkey else self.c_val)

    def print_list(self, a):
        """Print list, colorized if set"""
        self.cpr(self.termlst[0], self.c_lst)
        self.curind += self.ind
        for i in range(len(a)):
            self.print_indent()
            self.print_data(a[i])
            if i < len(a) - 1:
                self.cpr(self.sep2, self.c_lst)
        self.curind -= self.ind
        self.end(self.termlst[1], self.c_lst)

    def print_dict(self, a):
        """Print dictionary, colorized if set"""
        self.cpr(self.termdic[0], self.c_dic)
        self.curind += self.ind
        it = [i for i in a.items()]
        for i in range(len(it)):
            self.print_indent()
            self.onkey = True
            self.print_str(str(it[i][0]))
            self.cpr(self.sep1, self.c_dic)
            self.onkey = False
            self.print_data(it[i][1])
            if i < len(it) - 1:
                self.cpr(self.sep2, self.c_dic)
        self.curind -= self.ind
        self.end(self.termdic[1], self.c_dic)

    def start_print_data(self, data):
        """Check if data not list or dictionary and prints it"""
        self.simple_data = not isinstance(data, dict) and not isinstance(data, list)
        self.print_data(data)

    def print_data(self, data):
        """Print data for JSON"""
        if isinstance(data, dict):
            self.print_dict(data)
        elif isinstance(data, list):
            self.print_list(data)
        elif isinstance(data, bool) or data is None:
            self.print_bool(data)
        elif isinstance(data, int) or isinstance(data, float):
            self.print_num(data)
        else:
            self.print_str(data)


class PrinterLog(PrinterJSON):
    termdic = ('{', '}')
    termlst = ('[', ']')
    onkey = False
    ind = 0

    def print_entry(self, entry, max_baker_length):
        if entry.get('level'):
            sys.stdout.write(str(entry['level']))
            sys.stdout.write('  ')
        if entry.get('baker'):
            self.cpr(entry['baker'].ljust(max_baker_length), 1)
            sys.stdout.write('  ')

        if entry['kind'] == 'create':
            self.cpr(f'New Baker: {entry["address"]}', 1)
        else:
            self.simple_data = False
            self.cpr(entry['key'], 6)
            sys.stdout.write(': ')
            self.print_data(entry['before'])
            sys.stdout.write(' => ')
            self.print_data(entry['after'])
            self.simple_data = True

        sys.stdout.write('\n')

    def print_log(self, entries: list):
        if entries:
            max_baker_length = max(map(lambda x: len(x.get('baker', '')), entries))
            for entry in entries:
                self.print_entry(entry, max_baker_length)
        else:
            self.cpr('No changes\n', 2)
