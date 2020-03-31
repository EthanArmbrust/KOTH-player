import tmdbsimple as tmdb
import json
import curses
import curses.textpad
import glob
import os
import pickle
from os import path
import random
from natsort import natsorted, ns
from tkinter import Tk
from tkinter.filedialog import askdirectory

tmdb.API_KEY = '6c49e12fc2c8d787401a036a357c81f1'

media_player = 'mpv'
extra_options = "--really-quiet"
config_path = "config.json"


def split_message(message, width):
    message_array = []
    words = message.split()
    current_line = ""
    while len(words) > 0:
        if len(current_line) + len(words[0]) + 1 <= width:
            pass
        else:
            message_array.append(current_line)
            current_line = ""
        current_line += words[0] + " "
        words.pop(0)
    if current_line != "":
        message_array.append(current_line)
    return message_array

def random_episode(episodes):
    episode_nums = []
    total_episodes = 0
    for s in episodes:
        episode_nums.append(len(s))
        total_episodes += len(s)
    rand = random.randrange(total_episodes)
    
    season = 1
    while rand > episode_nums[season - 1]:
        rand -= episode_nums[season - 1]
        season += 1
    return season, rand


def print_episode_info(window, season, episode, showid):
    height, width = window.getmaxyx()
    airdate, ep_name, message = get_episode_info(showid, season, episode)
    arr = [ep_name, "Season {} Episode {}".format(season, episode), airdate, ""]
    arr = arr + split_message(message, width - 2)
    start_row = (height // 2) - (len(arr) // 2)
    window.clear()
    for i, line in enumerate(arr):
        start_col = (width // 2) - (len(line) // 2)
        window.addstr(start_row + i, start_col, line)
    window_controls = "[Q] - Close window : [P] - Play episode"
    window.addstr(height - 2, (width // 2) - (len(window_controls) // 2), window_controls)
    window.refresh()

def print_fullscreen_message(window, message):
    height, width = window.getmaxyx()
    arr = split_message(message, width - 2)
    start_row = (height // 2) - (len(arr) // 2)
    window.clear()
    for i, line in enumerate(arr):
        start_col = (width // 2) - (len(line) // 2)
        window.addstr(start_row + i, start_col, line)
    window.refresh()


def get_episode_file(season, episode, show_root):
    seasons = glob.glob(show_root + '/Season*')
    seasons = natsorted(seasons, alg=ns.IGNORECASE)
    season_dir = seasons[season - 1]
    file_types = ('/*.avi','/*.mkv', '/*.mp4')
    ep_list = []
    for files in file_types:
        ep_list.extend(glob.glob(season_dir + files))
    ep_list = natsorted(ep_list, alg=ns.IGNORECASE)
    return ep_list[episode - 1]

def get_episodes(showid):
    cache_path = ".cache/{}/episodes".format(showid)
    if path.exists(cache_path):
        afile = open(cache_path, 'rb')
        (show_name, data) = pickle.load(afile)
        afile.close()
        return (show_name, data)
    tv = tmdb.TV(showid)
    response = tv.info()
    show_name = tv.name
    n_seasons = tv.number_of_seasons
    seasons = []
    for i in range(n_seasons):
        episodes = []
        tv_season = tmdb.TV_Seasons(showid, i+1)
        season_resp = tv_season.info()
        n_episodes = len(season_resp["episodes"])
        for j in range(n_episodes):
            episodes.append("{}. ".format(j+1) + season_resp["episodes"][j]["name"])
        seasons.append(episodes)

    try:
        os.makedirs(os.path.dirname(cache_path))
    except:
        pass
    afile = open(cache_path, 'wb')
    pickle.dump((show_name, seasons), afile)
    afile.close()
    return (show_name, seasons)

def get_episode_info(showid, season_num, episode_num):
    response = tmdb.TV_Episodes(showid, season_num, episode_num)
    return response.info()["air_date"], response.info()["name"], response.info()["overview"]

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

def load_episodes(screen, episodes, show_name):
    pos = screen.current + screen.top
    ep_list = episodes[pos]
    screen.new_items(ep_list, "{}: Season {}".format(show_name, pos + 1))

def load_seasons(screen, episodes, show_name):
    se_list = []
    for i in range(len(episodes)):
        se_list.append("Season {}".format(i+1))
    screen.new_items(se_list, show_name)

def load_shows(screen, shows):
    show_names = []
    for s in shows:
        show_names.append(s["name"])
    screen.new_items(show_names, "Shows")

def init_shows():
    if path.exists(config_path):
        with open(config_path) as f:
            shows = json.load(f)
    else:
        shows = [{"name": "King of the Hill", "id": 2122, "path": "/Users/ITCS/King of the Hill"}]
        with open(config_path, 'w') as f:
            json.dump(shows, f)
    return shows

def add_show(shows, name, show_id, path):
    for s in shows:
        if s["id"] == show_id:
            return shows
    shows.append({"name": name, "id": show_id, "path": path})
    with open(config_path, 'w') as f:
        json.dump(shows, f)
    return shows

def form_entry(window, message):
    height, width = window.getmaxyx()
    print_fullscreen_message(window, message)
    window.box()

    curses.echo()
    curses.nocbreak()
    curses.curs_set(1)

    window.addstr(height - 3, 5, ">")
    window.move(height - 3, 6)
    user_input = window.getch()

    curses.noecho()
    curses.cbreak()
    curses.curs_set(0)

    return user_input

def form_win(width, height, pos_x, pos_y, message):
    win = curses.newwin(height, width, pos_y, pos_x)
    win.box()
    return form_entry(win, message)

def yes_no_win(width, height, pos_x, pos_y, message):
    win = curses.newwin(height, width, pos_y, pos_x)
    print_fullscreen_message(win, message)
    win.box()
    while True:
        ch = win.getch()
        if ch == ord('y'):
            return True
        if ch == ord('n'):
            return False

def browse_new_path(width, height, pos_x, pos_y):
    win = curses.newwin(height, width, pos_y, pos_x)
    arr = split_message("Enter path where show is located", width - 2)
    start_row = (height // 2) - (len(arr) // 2)
    win.clear()
    for i, line in enumerate(arr):
        start_col = (width // 2) - (len(line) // 2)
        win.addstr(start_row + i, start_col, line)
    input_line_start = start_row + len(arr) + 2
    input_box_width = width - (2 + 8 + 7 + 7)
    user_path = " " * input_box_width
    win.addstr(input_line_start, 2, "Path: ")
    path_pos = 8
    win.addstr(input_line_start, path_pos, user_path, curses.color_pair(2))
    enter_pos = 8 + len(user_path)
    win.addstr(input_line_start, enter_pos, " Enter ")
    browse_pos = enter_pos + len(" Enter ")
    win.addstr(input_line_start, browse_pos, " Browse ")
    win.box()
    win.refresh()
    while True:
        ch = win.getch()
    
    

def info_win(showid, season, episode, width, height, pos_x, pos_y, show_root):
    win = curses.newwin(height, width, pos_y, pos_x)
    print_fullscreen_message(win, "Fetching episode info...")
    print_episode_info(win, season, episode, showid)
    win.box()
    while True:
        ch = win.getch()
        if ch == ord('q'):
            break
        if ch == ord('p'):
            os.system(media_player + " \"" + get_episode_file(season, episode, show_root) + "\" " + extra_options)

def input_stream(screen, shows, win):
    """Waiting an input and run a proper method according to type of input"""
    # 0 = Show View
    # 1 = Season View
    # 2 = Episode View
    view = 0
    season_pos = 0
    showid = 0
    episodes = []
    show_name = ""
    show_root = ""
    while True:
        screen.display()
        win_height, win_width = win.getmaxyx()
        win_height = int(win_height * 0.8)
        win_width = int(win_width * 0.8)
        pos_x = int(win_width // 8)
        pos_y = int(win_height // 8)

        ch = screen.window.getch()
        if view == 0:   #Show view
            if ch == curses.KEY_UP:
                screen.scroll(screen.UP)
            elif ch == curses.KEY_DOWN:
                screen.scroll(screen.DOWN)
            elif ch == curses.KEY_LEFT:
                pass
            elif ch == curses.KEY_RIGHT:
                print_fullscreen_message(win, "Getting show information...")
                pos = screen.current + screen.top
                show = shows[pos]
                showid = show["id"]
                show_name, episodes = get_episodes(showid)
                show_root = show["path"]

                load_seasons(screen,episodes, show_name)
                while screen.current + screen.top < season_pos:
                    screen.scroll(screen.DOWN)
                view = 1
            elif ch == ord('f'):
                input = form_win(win_width, win_height, pos_x, pos_y, "Enter your text here")
                search = tmdb.Search()
                response = search.tv(query=input)
                win_info = curses.newwin(win_width, win_height, pos_x, pos_y)
                print_fullscreen_message(win_info, response['results'][0]['name'])
                win_info.getch()
            elif ch == ord('b'):
                browse_new_path(win_width, win_height, pos_x, pos_y)
        

        elif view == 1: #Season view
            if ch == curses.KEY_UP:
                screen.scroll(screen.UP)
            elif ch == curses.KEY_DOWN:
                screen.scroll(screen.DOWN)
            elif ch == curses.KEY_LEFT:
                view = 0
                season_pos = 0
                load_shows(screen, shows)
            elif ch == curses.KEY_RIGHT:
                season_pos = screen.current + screen.top
                load_episodes(screen, episodes, show_name)
                view = 2
            elif ch == ord('r'):
                s, e = random_episode(episodes)
                info_win(showid, s, e, win_width, win_height, pos_x, pos_y, show_root)

        elif view == 2: #Episode view
            if ch == curses.KEY_UP:
                screen.scroll(screen.UP)
            elif ch == curses.KEY_DOWN:
                screen.scroll(screen.DOWN)
            elif ch == curses.KEY_LEFT:
                load_seasons(screen, episodes, show_name)
                while screen.current + screen.top < season_pos:
                    screen.scroll(screen.DOWN)
                view = 1
            elif ch == curses.KEY_RIGHT or ch == ord('p'):
                os.system(media_player + " \"" + get_episode_file(season_pos + 1, screen.current + screen.top + 1, show_root) + "\" " + extra_options)
            elif ch == ord('i'):
                info_win(showid, season_pos + 1, screen.current + screen.top + 1, win_width, win_height, pos_x, pos_y, show_root)
            elif ch == ord('r'):
                s, e = random_episode(episodes)
                info_win(showid, s, e, win_width, win_height, pos_x, pos_y, show_root)
        if ch == ord('q'):
            break


def run_loop(screen, shows, win):
        try:
            input_stream(screen, shows, win)
        except KeyboardInterrupt:
            pass
        finally:
            curses.endwin()
def main():
    '''
    Tk().withdraw()
    filename = askdirectory()
    shows = init_shows()
    shows = add_show(shows, "Gravity Falls", 40075, "/Users/ITCS/Gravity Falls")
    print(shows)

    query = 'Gravity Falls'
    search = tmdb.Search()
    response = search.tv(query=query)
    print(response['results'][0]['name'], response['results'][0]['id'])
    '''

    try:
        win = init_curses()
        print_fullscreen_message(win, "Getting show list...")
        shows = init_shows()
        shows = add_show(shows, "Gravity Falls", 40075, "/Users/ITCS/Gravity Falls")
        scroll_screen = Screen([], win, shows)
        load_shows(scroll_screen, shows)
    except KeyboardInterrupt:
        pass
    finally:
        curses.endwin()
    run_loop(scroll_screen, shows, win)

class Screen(object):
    UP = -1
    DOWN = 1

    def __init__(self, items, win, header=""):
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

        self.height, self.width = self.window.getmaxyx()

        self.max_lines = curses.LINES
        self.top = 0
        self.bottom = len(self.items)
        self.page = self.bottom // self.max_lines
        self.current = 0

        self.header = header
        if self.header == "":
            self.upperBound = 0
        else:
            self.upperBound = 2



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
        if (direction == self.DOWN) and (next_line == self.max_lines - self.upperBound) and (self.top + self.max_lines - self.upperBound < self.bottom):
            self.top += direction
            return
        # Scroll up
        # current cursor position or top position is greater than 0
        if (direction == self.UP) and (self.top > 0 or self.current > 0):
            self.current = next_line
            return
        # Scroll down
        # next cursor position is above max lines, and absolute position of next cursor could not touch the bottom
        if (direction == self.DOWN) and (next_line < self.max_lines - self.upperBound) and (self.top + next_line  - self.upperBound < self.bottom):
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
        
    def new_items(self, new_list, header=""):
        self.items = new_list
        self.max_lines = curses.LINES
        self.top = 0
        self.bottom = len(self.items)
        self.current = 0
        self.page = self.bottom // self.max_lines
        self.header = header
        if self.header == "":
            self.upperBound = 0
        else:
            self.upperBound = 2

    def display(self):
        """Display the items on window"""
        self.window.erase()
        self.window.addstr(0, (self.width // 2) - (len(self.header) // 2), self.header, curses.color_pair(1))
        for idx, item in enumerate(self.items[self.top:self.top + self.max_lines - self.upperBound], self.upperBound):
            # Highlight the current cursor line
            if idx == self.current + self.upperBound:
                self.window.addstr(idx, 0, item, curses.color_pair(2))
            else:
                self.window.addstr(idx, 0, item, curses.color_pair(1))
        self.window.refresh()

if __name__ == '__main__':
    main()
