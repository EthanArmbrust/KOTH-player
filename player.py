import tmdbsimple as tmdb
import json
import curses
import curses.textpad

tmdb.API_KEY = '6c49e12fc2c8d787401a036a357c81f1'

showid = 2122


def get_episodes():
    tv = tmdb.TV(showid)
    response = tv.info()
    n_seasons = tv.number_of_seasons
    seasons = []
    for i in range(n_seasons):
        episodes = []
        tv_season = tmdb.TV_Seasons(showid, i+1)
        season_resp = tv_season.info()
        n_episodes = len(season_resp["episodes"])
        for j in range(n_episodes):
            episodes.append(season_resp["episodes"][j]["name"])
        seasons.append(episodes)
    return seasons

def init_curses():
    window = curses.initscr()
    window.keypad(True)

    curses.noecho()
    curses.cbreak()
    curses.curs_set(0)

    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_CYAN)
    return window

def load_episodes(screen, episodes):
    pos = screen.current
    ep_list = episodes[pos]
    screen.new_items(ep_list)

def input_stream(screen, episodes):
    """Waiting an input and run a proper method according to type of input"""
    isSeasonView = True
    while True:
        screen.display()

        ch = screen.window.getch()
        if ch == curses.KEY_BACKSPACE:
            screen.scroll(screen.UP)
        elif ch == curses.KEY_UP:
            screen.scroll(screen.UP)
        elif ch == curses.KEY_DOWN:
            screen.scroll(screen.DOWN)
        elif ch == curses.KEY_LEFT:
            screen.scroll(screen.DOWN)
        elif ch == curses.KEY_RIGHT:
            if isSeasonView:
                load_episodes(screen, episodes)
                isSeasonView = False
            else: 
                screen.scroll(screen.DOWN)
        elif ch == curses.ascii.ESC:
            break


def run_loop(screen, episodes):
        try:
            input_stream(screen, episodes)
        except KeyboardInterrupt:
            pass
        finally:
            curses.endwin()
def main():
    try:
        win = init_curses()
    except KeyboardInterrupt:
        pass
    finally:
        curses.endwin()
    episodes = get_episodes()
    seasons = []
    for i in range(len(episodes)):
        seasons.append("Season {}".format(i+1))
    scroll_screen = Screen(seasons, win)
    run_loop(scroll_screen, episodes)

class Screen(object):
    UP = -1
    DOWN = 1

    def __init__(self, items, win):
        """ Initialize the screen window

        Attributes
            window: A full curses screen window

            width: The width of `window`
            height: The height of `window`

            max_lines: Maximum visible line count for `result_window`
            top: Available top line position for current page (used on scrolling)
            bottom: Available bottom line position for whole pages (as length of items)
            current: Current highlighted line number (as window cursor)
            page: Total page count which being changed corresponding to result of a query (starts from 0)

            ┌--------------------------------------┐
            |1. Item                               |
            |--------------------------------------| <- top = 1
            |2. Item                               | 
            |3. Item                               |
            |4./Item///////////////////////////////| <- current = 3
            |5. Item                               |
            |6. Item                               |
            |7. Item                               |
            |8. Item                               | <- max_lines = 7
            |--------------------------------------|
            |9. Item                               |
            |10. Item                              | <- bottom = 10
            |                                      |
            |                                      | <- page = 1 (0 and 1)
            └--------------------------------------┘

        Returns
            None
        """
        self.window = win

        self.width = 0
        self.height = 0

        self.items = items

        self.current = curses.color_pair(2)
        self.height, self.width = self.window.getmaxyx()

        self.max_lines = curses.LINES
        self.top = 0
        self.bottom = len(self.items)
        self.current = 0
        self.page = self.bottom // self.max_lines


    def run(self):
        """Continue running the TUI until get interrupted"""


    def scroll(self, direction):
        """Scrolling the window when pressing up/down arrow keys"""
        # next cursor position after scrolling
        next_line = self.current + direction

        # Up direction scroll overflow
        # current cursor position is 0, but top position is greater than 0
        if (direction == self.UP) and (self.top > 0 and self.current == 0):
            self.top += direction
            return
        # Down direction scroll overflow
        # next cursor position touch the max lines, but absolute position of max lines could not touch the bottom
        if (direction == self.DOWN) and (next_line == self.max_lines) and (self.top + self.max_lines < self.bottom):
            self.top += direction
            return
        # Scroll up
        # current cursor position or top position is greater than 0
        if (direction == self.UP) and (self.top > 0 or self.current > 0):
            self.current = next_line
            return
        # Scroll down
        # next cursor position is above max lines, and absolute position of next cursor could not touch the bottom
        if (direction == self.DOWN) and (next_line < self.max_lines) and (self.top + next_line < self.bottom):
            self.current = next_line
            return

    def paging(self, direction):
        """Paging the window when pressing left/right arrow keys"""
        current_page = (self.top + self.current) // self.max_lines
        next_page = current_page + direction
        # The last page may have fewer items than max lines,
        # so we should adjust the current cursor position as maximum item count on last page
        if next_page == self.page:
            self.current = min(self.current, self.bottom % self.max_lines - 1)

        # Page up
        # if current page is not a first page, page up is possible
        # top position can not be negative, so if top position is going to be negative, we should set it as 0
        if (direction == self.UP) and (current_page > 0):
            self.top = max(0, self.top - self.max_lines)
            return
        # Page down
        # if current page is not a last page, page down is possible
        if (direction == self.DOWN) and (current_page < self.page):
            self.top += self.max_lines
            return
        
    def new_items(self, new_list):
        self.items = new_list
        self.max_lines = curses.LINES
        self.top = 0
        self.bottom = len(self.items)
        self.current = 0
        self.page = self.bottom // self.max_lines

    def display(self):
        """Display the items on window"""
        self.window.erase()
        for idx, item in enumerate(self.items[self.top:self.top + self.max_lines]):
            # Highlight the current cursor line
            if idx == self.current:
                self.window.addstr(idx, 0, item, curses.color_pair(2))
            else:
                self.window.addstr(idx, 0, item, curses.color_pair(1))
        self.window.refresh()

if __name__ == '__main__':
    main()
