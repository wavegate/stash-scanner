import time

try:
    import functools
    import logging
    import multiprocessing
    import os
    import pycurl
    import queue
    import threading
    import tkinter.font as tkfont
    import webbrowser
    from concurrent.futures import ThreadPoolExecutor
    from idlelib.WidgetRedirector import WidgetRedirector
    from queue import Queue
    from threading import Thread, Lock
    from tkinter import *
    from tkinter import messagebox
    from tkinter.ttk import *

    import PIL.Image
    import PIL.ImageTk

    from lib.CurrencyManager import CurrencyInfo, cm, CurrencyManager
    from lib.FilterManager import FiltersInfo, fm, FILTERS_CFG_FNAME
    from lib.ItemCollection import ItemCollection
    from lib.ItemFilter import Filter
    from lib.ItemHelper import ItemType, PropDisplayMode, ItemSocketType
    from lib.ModsHelper import mod_helper
    from lib.StashScanner import StashScanner, ItemResult
    from lib.Utility import MsgType, msgr, getDataFromUrl, round_up, AppException, getJsonFromURL, config, AppConfiguration, \
        logexception, dround
    from ui.ConfigEditor import ConfigEditor
    from ui.FilterEditor import FilterEditor
    from ui.LoadingScreen import LoadingScreen
    from ui.ScrollingFrame import AutoScrollbar
    from ui.TextButton import TextButton
except Exception as e:
    import logging
    logging.basicConfig(filename='startup_error.log', level=logging.DEBUG) # in-case logger was not set-up, fallback
    logging.error("Error while importing modules: {}".format(e), exc_info=1)
    exit(1)

class AppGUI(Tk):

    TK_TABWIDTH = 8
    BG_COLOR = '#37474F'#263238'#'#455A64'
    DETAILS_BG_COLOR = '#222'
    DEFAULT_COLOR = '#FFFFFF'#'#ECEFF1'
    WARN_COLOR = '#FDD835'
    ERROR_COLOR = 'red'

    NORMAL_COLOR = '#eee'
    MAGIC_COLOR = '#5050EB'
    RARE_COLOR = '#a3a314'
    UNIQUE_COLOR = '#af6025'
    GEM_COLOR = '#1ba29b'
    CURRENCY_COLOR = '#aa9e82' #'#9c7e38'
    DIV_COLOR = '#c1fcf8' #'#dcd3c3'
    QUEST_COLOR = '#4ae63a'
    PROPHECY_COLOR = '#b54bff' #'#dcd3c3'
    RELIC_COLOR = '#82ad6a'

    IMPLICIT_BGCOLOR = '#65621E'
    CORRUPTED_BGCOLOR = '#C22626'
    CORRUPTED_COLOR = '#fff'
    ENCHANTED_BGCOLOR = '#8B579C'
    ENCHANTED_COLOR = '#fff'
    CRAFTED_BGCOLOR = '#0060BF'
    CRAFTED_COLOR = '#fff'
    REQ_COLOR = '#999'
    WARNING_COLOR = '#c35b5b'
    MATCHES_COLOR = '#999'
    UNID_COLOR = '#C22626'
    PROP_COLOR = '#e6e6e6'
    ENHANCED_COLOR = '#41CA41'

    TT_WHITE_COLOR = '#c8c8c8'
    TT_MAGIC_COLOR = '#8888ff'
    TT_RARE_COLOR = '#ff7'
    TT_UNIQUE_COLOR = '#af6025'
    TT_GEM_COLOR = '#1aa29b'
    TT_CURRENCY_COLOR = '#aa9e82'
    TT_DIV_COLOR = '#c1fcf8'
    TT_PROPHECY_COLOR = '#b54bff'

    TT_DEFAULT_COLOR = '#7f7f7f'
    TT_CORRUPTED_COLOR = '#d20000'
    TT_NORMAL_COLOR = '#fff'  # '#eee'  # Used for map tiers, ilvls, map tags
    TT_AUGMENETED_COLOR = '#8888ff'  # '#eee'  # Used for quality

    TT_SRED_COLOR = '#F44336'
    # '#f00'

    TT_SGREEN_COLOR = '#4CAF50'
    #'#0f0' #'#2ECC2E'

    TT_SBLUE_COLOR = '#2196F3'
    # CRAFTED_BGCOLOR #'#00f' #'#44f'

    TT_SWHITE_COLOR = '#fff'

    # BUTTON_BGCOLOR = '#232420'
    # BUTTON_HOVER_BGCOLOR = '#090908'
    # BUTTON_BGCOLOR = '#494949'
    # BUTTON_HOVER_BGCOLOR = '#313131'

    # BUTTON_BGCOLOR = '#313131'
    # BUTTON_HOVER_BGCOLOR = '#090908'

    BUTTON_BGCOLOR = '#333333'
    BUTTON_HOVER_BGCOLOR = '#161616'

    BUTTON_FOREGROUND = '#fff'

    type_tags = {
        ItemType.Normal: 'name-normal',
        ItemType.Magic: 'name-magic',
        ItemType.Rare: 'name-rare',
        ItemType.Unique: 'name-unique',
        ItemType.Gem: 'name-gem',
        ItemType.Currency: 'name-currency',
        ItemType.DivinationCard: 'name-div',
        ItemType.QuestItem: 'name-quest',
        ItemType.Prophecy: 'name-prophecy',
        ItemType.Relic: 'name-relic'
    }

    VERSION_NUMBER = 'v1.05'
    VERSION_URL = 'https://github.com/senuido/stash-scanner/raw/master/files/latest'
    RELEASES_URL = 'https://github.com/senuido/stash-scanner/releases/latest'
    VERSION_TEXT = 'Stash Scanner {}'.format(VERSION_NUMBER)

    FONTS = ['Segoe UI', 'TkTextFont', 'Arial']#"sans-serif" #"Helvetica",Helvetica,Arial,sans-serif;
    IMG_NAME = 'item_image'

    app_fonts = {}

    def __init__(self):

        super().__init__()
        self.withdraw()

        self.msg_level = logging.WARNING
        self.msg_tags = {}
        self.ui_queue = Queue()
        self.last_index = -1
        self.lbl_item_img = None
        self.initialized = False
        self.currency_info = CurrencyInfo()
        self.filters_info = FiltersInfo()
        self.wnd_editor = None

        self.init_error = None
        self.stop_error = None

        self.t_version_check = None

        s = Style()
        # print(s.theme_names())
        # s.theme_use('vista')

        self.title("Stash Scanner by Senu {}".format(self.VERSION_NUMBER))

        try:
            config.load()
        except AppException as e:
            try:
                config.load_default()
                messagebox.showwarning('Config warning', '{}\nDefault settings will be used instead.'.format(e), parent=self)
            except AppException as e:
                messagebox.showerror('Config error', e, parent=self)
                return

        try:
            self.iconbitmap(default='res\\app.ico')
            ItemDisplay.init()
            StatusBar.init()
            Filter.init()
            ItemCollection.init()
            mod_helper.init()
        except AppException as e:
            messagebox.showerror('Resource error', e, parent=self)
        else:
            self.after(100, self.load)
            # self.after(100, self.handle_msgs)
            # self.lst_msgs.after(1000, self.handle_ui_msgs)

            self.protocol("WM_DELETE_WINDOW", self.on_close)
            self.scanner = None
            self.scan_thread = None
            self.after(1000, self.update_statistics)
            # self.details_img_lock = Lock()
            self.details_lock = Lock()

            # self.start_scan()
            self.initialized = True

            self.geometry("1366x768")
            self.create_widgets()
            self.center()

            self.deiconify()
            self.wait_visibility()

            self.state('zoomed')

    def _check_version(self):
        try:
            c = pycurl.Curl()
            c.setopt(pycurl.SSL_VERIFYPEER, 0)
            c.setopt(pycurl.SSL_VERIFYHOST, 0)
            c.setopt(pycurl.FOLLOWLOCATION, 1)
            data = getJsonFromURL(self.VERSION_URL, handle=c, max_attempts=3)
            if data:
                msgr.send_object(VersionInfo(data))
        # except pycurl.error as e:
        #     pass
        except Exception as e:
            logger.error('Failed checking for version updates. Unexpected error: {}'.format(e))

    def check_version(self):
        if not self.t_version_check or not self.t_version_check.is_alive():
            self.t_version_check = threading.Thread(target=self._check_version, daemon=True)
            self.t_version_check.start()

    def check_version_callback(self, latest):
        if not isinstance(latest, VersionInfo):
            return

        if latest.is_newer_than(self.VERSION_NUMBER):
            answer = messagebox.askquestion('Update', 'A newer version is available, would you like to download it?', parent=self)
            if answer == messagebox.YES:
                webbrowser.open(self.RELEASES_URL)

    def update_configuration(self, cfg):
        if not isinstance(cfg, AppConfiguration):
            raise TypeError('cfg needs to be of type AppConfiguration')

        try:
            if config.league == cfg.league:
                config.update(cfg)
                config.save()
                self.nb_cfg.onTabChange()
                return

            answer = messagebox.askquestion('Settings',
                                            'Changing league will stop active scans and close other windows, continue?',
                                            parent=self)
            if answer == messagebox.NO:
                return

            self.close_editor_window()
            self.stop_scan()
            # if self.is_scan_active:
            #     self.stop_scan()
            #     ls = LoadingScreen(self)
            #     threading.Thread(target=self._stop_scan, args=(ls,)).start()
            #     self.wait_window(ls)

            try:
                StashScanner.clearLeagueData()
            except Exception as e:
                messagebox.showerror('Settings',
                                     'Failed to clear league data.\nError: {}\n'
                                     'Make sure all files are closed and try again.'.format(e),
                                     parent=self)
                return

            config.update(cfg)
            config.save()

            self.init_error = None
            ls = LoadingScreen(self)
            Thread(target=self.init_scanner, args=(ls,)).start()
            self.wait_window(ls)

            self.focus_set()
            self.lift()

            if self.init_error:
                title, message = self.init_error.args
                message += '\n{}'
                messagebox.showerror(title, message.format('Application will now close.'), parent=self)
                self.on_close()
                return

            self.init_warn()
            self.currency_info = CurrencyInfo()
            self.filters_info = FiltersInfo()

            self.nb_cfg.onTabChange()
        except Exception as e:
            logexception()
            logger.error('Unexpected error while attempting to change league.\n{}'.format(e))
            messagebox.showerror('Save error', 'Unexpected error while trying to save settings:\n{}'.format(e))

    def init_warn(self):
        warnings = ''
        if not len(cm.rates):
            warnings += 'Currency information is empty because the server returned no data. ' \
                        'Currency rates will be 0 unless set manually.\n'
        if not len(fm.autoFilters):
            warnings += 'Filters were not generated because the server returned no data.\n'

        if warnings:
            warnings += '\nYou can either continue in this mode or restart the application if you wish to try again.'
            messagebox.showwarning('Warning', warnings, parent=self)

    def load(self):
        ls = LoadingScreen(self)
        # ls.lift()

        self.check_version()
        Thread(target=self.init_scanner, args=(ls,)).start()
        self.wait_window(ls)

        self.focus_set()
        self.lift()

        if self.init_error:
            title, message = self.init_error.args
            message += '\n{}'
            messagebox.showerror(title, message.format('Application will now close.'), parent=self)
            self.on_close()
            return

        self.init_warn()
        self.nb_cfg.onTabChange()

        self.after(100, self.handle_msgs)

    def init_scanner(self, ls):
        os.makedirs('tmp', exist_ok=True)
        os.makedirs('log', exist_ok=True)

        cm.init()
        fm.init()

        try:
            ls.updateStatus('Loading settings', 0)
            config.load()
            # try:
            #     config.load()
            # except Exception as e:
            #     raise AppException('Settings error', 'Failed loading settings. {}\n'.format(e))

            ls.updateStatus('Loading currency information', 5)
            try:
                cm.load()
            except AppException as e:
                # raise AppException('Currency error', 'Error while loading currency information.\n{}'.format(e))
                raise AppException('Currency error',
                                   'Failed loading currency configuration. Error received:\n{}\n'
                                   'Correct the error or delete the filters configuration file ({}) and a new '
                                   'one will be generated for you.'.format(e, CurrencyManager.CURRENCY_FNAME))

            if cm.needUpdate:
                try:
                    ls.updateStatus('Downloading currency information', 10)
                    cm.update(accept_empty=True)
                except AppException as e:
                    pass

            # if not cm.initialized:
            #     raise AppException('Currency error', 'Failed to load currency information.')

            ls.updateStatus('Loading filter configuration', 40)
            try:
                fm.loadConfig()
            except AppException as e:
                raise AppException('Filters config error',
                                   'Failed loading filters configuration. Error received:\n{}\n'
                                   'Correct the error or delete the filters configuration file ({}) and a new '
                                   'one will be generated for you.'.format(e, FILTERS_CFG_FNAME))

            filter_fallback = False

            ls.updateStatus('Loading filters', 50)
            try:
                fm.loadAutoFilters()
            except AppException:
                filter_fallback = True

            if fm.needUpdate or filter_fallback:
                try:
                    ls.updateStatus('Generating filters from API', 55)
                    fm.fetchFromAPI(accept_empty=True)
                except AppException as e:
                    if filter_fallback:
                        raise AppException('Filters error',
                                           'Failed to download and generate filters and unable to use a local copy.\n'
                                           '{}'.format(e))

            try:
                ls.updateStatus('Loading user filters', 80)
                fm.loadUserFilters(validate=False)
            except AppException as e:
                raise AppException('Filter error', '{}'.format(e))

            fm.initialized = True

            ls.updateStatus('Initializing..', 90)
            self.init_error = None
        except AppException as e:
            self.init_error = e
        except Exception as e:
            logexception()
            self.init_error = AppException('Initialization error', 'Unexpected error occurred while initializing:\n{}'.format(e))
        finally:
            ls.close()

    def create_widgets(self):
        self.configure(padx=10, pady=10)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.upper_frame = Frame(self, relief=GROOVE)
        self.upper_frame.grid(row=0, sticky='nsew', ipadx=5)
        # self.upper_frame.columnconfigure(8, weight=1)

        self.lbl_msglevel = Label(self.upper_frame, text="Message Level:")
        self.lbl_msglevel.grid(row=0, column=0, padx=(5, 0), pady=5, sticky='ns')

        self.cmb_msglevel = Combobox(self.upper_frame, values=['Error', 'Warning', 'Info', 'Debug'],
                                     state='readonly')
        self.cmb_msglevel.bind('<<ComboboxSelected>>', self.set_msglevel)
        self.cmb_msglevel.set('Warning')
        self.cmb_msglevel.grid(row=0, column=1, pady=5, padx=(5, 0), sticky='ns')

        self.btn_clear = Button(self.upper_frame, text="Clear", command=self.clear_msgs)
        self.btn_clear.grid(row=0, column=2, pady=5, padx=(5, 0), sticky='ns')

        self.btn_toggle = Button(self.upper_frame, text="Start", command=self.toggle_scan)
        self.btn_toggle.grid(row=0, column=3, pady=5, padx=(5, 5), sticky='ns')

        sep = Separator(self.upper_frame, orient=VERTICAL)
        sep.grid(row=0, column=9, sticky='ns', pady=2)

        self.btn_currency = Button(self.upper_frame, text="Currency Info",
                                   command=lambda: self.update_details_lock(self.currency_info))
        self.btn_currency.grid(row=0, column=12, pady=5, padx=(5, 0), sticky='ns')

        self.btn_filters = Button(self.upper_frame, text="Filters Info",
                                  command=lambda: self.update_details_lock(self.filters_info))
        self.btn_filters.grid(row=0, column=11, pady=5, padx=(5, 0), sticky='ns')

        self.btn_editor = Button(self.upper_frame, text='Filter Editor', command=self.show_editor_window)
        self.btn_editor.grid(row=0, column=10, pady=5, padx=(5, 0), sticky='ns')

        # self.lbl_spacer = Label(self.upper_frame)
        # self.lbl_spacer.grid(row=0, column=8)

        # self.lbl_id_value = Label(self.upper_frame, text="", foreground="blue")
        # self.lbl_id_value.grid(row=0, column=12, padx=(0, 10), sticky='e')

        self.main_pane_wnd = PanedWindow(self, orient=VERTICAL)
        self.main_pane_wnd.grid(row=1, column=0, sticky='nsew')

        self.status_bar = StatusBar(self)
        self.status_bar.grid(row=2, column=0, sticky='nsew')

        self.pane_wnd = PanedWindow(self.main_pane_wnd, orient=HORIZONTAL)
        self.nb_cfg = ConfigEditor(self.main_pane_wnd, self)

        self.frm_console = Frame(self.pane_wnd)
        self.frm_console.columnconfigure(1, weight=1)
        self.frm_console.rowconfigure(0, weight=1)

        self.lst_msgs = Listbox(self.frm_console, background=self.BG_COLOR, selectmode=SINGLE, activestyle=NONE)
        self.lst_msgs.bind('<<ListboxSelect>>', self.lst_selected)
        self.lst_msgs.grid(row=0, column=1, sticky='nsew')

        def listbox_down(event):
            w = event.widget
            index = 0
            if w.curselection():
                index = int(w.curselection()[0]) + 1
            if index == w.size():
                index = 0

            w.selection_clear(0, END)
            if index < w.size():
                w.activate(index)
                w.selection_set(index)
                w.see(index)
                w.event_generate('<<ListboxSelect>>')

            return 'break'

        def listbox_up(event):
            w = event.widget
            if w.curselection():
                index = int(w.curselection()[0]) - 1
                if index == - 1:
                    index = w.size() - 1
            else:
                index = w.size() - 1

            w.selection_clear(0, END)
            if index >= 0:
                w.activate(index)
                w.selection_set(index)
                w.see(index)
                w.event_generate('<<ListboxSelect>>')

            return 'break'

        self.lst_msgs.bind('<Down>', listbox_down)
        self.lst_msgs.bind('<Up>', listbox_up)

        scroll = AutoScrollbar(self.frm_console)
        scroll.grid(row=0, column=0, sticky='nsew')
        scroll.configure(command=self.lst_msgs.yview)
        self.lst_msgs['yscrollcommand'] = scroll.set

        # self.txt_details = ReadOnlyText(self.pane_wnd, background=self.DETAILS_BG_COLOR, foreground=self.DEFAULT_COLOR,
        #                                 padx=20, name='txt_details')

        style = Style()
        style.configure('My.TFrame', background=self.DETAILS_BG_COLOR)
        style.configure('Thin.TFrame', padding=20, borderwidth=5)
        style.configure('Borderless.TFrame', padding=0, borderwidth=0)
        style.configure('Borderless.TLabelframe', padding=0, borderwidth=0)
        style.configure('Dark.Borderless.TFrame', background=self.DETAILS_BG_COLOR)
        style.configure('Dark.TLabel', background=self.DETAILS_BG_COLOR, foreground=self.DEFAULT_COLOR)

        # ui_style.configure('Default.TEntry', background='white', highlightbackground="#bebebe", highlightthickness=1, bd=1)
        style.configure('Default.TEntry', padding=1)

        entry_placeholder_font = tkfont.Font(name=style.lookup("TEntry", "font"), exists=True).copy()
        entry_placeholder_font.config(slant=tkfont.ITALIC)
        self.addfont(tkfont.Font(name='PlaceholderFont', exists=False, font=entry_placeholder_font))
        style.configure('Placeholder.Default.TEntry', foreground='grey', font='PlaceholderFont')
        style.configure('Autocomplete.TEntry')  # , borderwidth=0, highlightthickness=1)

        # print(style.layout('TEntry'))
        # print(style.element_options('TEntry.field'))
        # print(style.element_options('TEntry.background'))
        # print(style.element_options('TEntry.padding'))
        # print(style.element_options('TEntry.textarea'))

        # style.layout("TFrame")

        self.frm_details = Frame(self.pane_wnd, name='frm_details', style='My.TFrame')
        self.frm_details.configure(padding=(30, 20))
        self.frm_details.grid_configure(row=0, sticky='nsew')
        self.frm_details.columnconfigure(0, weight=1, minsize=100)
        self.frm_details.rowconfigure(1, weight=1)
        # self.frm_details.grid_propagate(False)

        self.pane_wnd.add(self.frm_details)
        self.pane_wnd.forget(self.frm_details)

        font_fam = self.findfont(self.FONTS)
        # print('Using font family: {}'.format(font_fam))
        font_default = self.addfont(tkfont.Font(name='DetailsDefault', family=font_fam, size=9))
        font_bold = self.addfont(tkfont.Font(name='DetailsBold', family=font_fam, size=9, weight=tkfont.BOLD))
        font_title = self.addfont(tkfont.Font(name='DetailsTitle', family=font_fam, size=13, weight=tkfont.BOLD))
        font_title_big = self.addfont(tkfont.Font(name='DetailsTitleBig', family=font_fam, size=15, weight=tkfont.BOLD))
        font_tag_big = self.addfont(tkfont.Font(name='DetailsTagBig', family=font_fam, size=12, weight=tkfont.BOLD))
        font_tag = self.addfont(tkfont.Font(name='DetailsTag', family=font_fam, size=9, weight=tkfont.BOLD))
        font_subtext = self.addfont(tkfont.Font(name='DetailsSubtext', family=font_fam, size=8))
        font_subtext_min = self.addfont(tkfont.Font(name='DetailsSubtextMin', family=font_fam, size=7))
        font_subtext_bold = self.addfont(tkfont.Font(name='DetailsSubtextBold', family=font_fam, size=8, weight=tkfont.BOLD))
        font_underline = self.addfont(tkfont.Font(name='DetailsUnderline', family=font_fam, size=9, underline=True))
        font_tiny = self.addfont(tkfont.Font(name='DetailsTiny', family=font_fam, size=5))
        font_italic = self.addfont(tkfont.Font(name='DetailsItalic', family=font_fam, slant=tkfont.ITALIC, size=9))
        font_bold_italic = self.addfont(tkfont.Font(name='DetailsBoldItalic', family=font_fam, weight=tkfont.BOLD, slant=tkfont.ITALIC, size=9))

        self.addfont(tkfont.Font(name='TreeDefault'))

        self.txt_details = ReadOnlyText(self.frm_details, background=self.DETAILS_BG_COLOR,
                                        foreground=self.DEFAULT_COLOR,
                                        name='txt_details', borderwidth=0)  # , tabstyle='wordprocessor')

        # self.txt_details.config(width=100)

        self.txt_details.grid(row=1, column=0, sticky='nsew')

        # self.lbl_details_filler2 = Frame(self.frm_details, style='Borderless.TFrame')
        # self.lbl_details_filler2.grid(row=0, column=3, rowspan=2, sticky='nsew')

        self.frm_details_img = Frame(self.frm_details, style='Dark.Borderless.TFrame')
        self.lbl_details_img = Label(self.frm_details_img, background=self.DETAILS_BG_COLOR, borderwidth=0, anchor=CENTER)
        self.lbl_details_img.grid(sticky='nsew')
        self.frm_details_img.grid(row=1, column=1, sticky='nsew')
        # self.frm_details_btns = Frame(self.frm_details, style='Dark.Borderless.TFrame')
        # self.frm_details_btns.grid(row=2, column=1, columnspan=1, sticky='ne', pady=5)
        self.frm_details_btns = Frame(self.frm_details_img, style='Dark.Borderless.TFrame')
        self.frm_details_btns.grid(row=1, column=0, columnspan=1, sticky='ne', pady=15)

        self.btn_filter_search = TextButton(self.frm_details_btns, padx=5, pady=3, font=self.app_fonts['DetailsBold'],
                                            highlightthickness=2,
                                            background=self.BUTTON_BGCOLOR, foreground=self.BUTTON_FOREGROUND,
                                            borderwidth=1,
                                            activebackground=self.BUTTON_HOVER_BGCOLOR,
                                            activeforeground=self.BUTTON_FOREGROUND,
                                            compound=LEFT, image=ItemDisplay.search_icon, relief=RAISED, text='Filter Search')

        self.btn_item_search = TextButton(self.frm_details_btns, padx=5, pady=3, font=self.app_fonts['DetailsBold'],
                                          highlightthickness=2,
                                          background=self.BUTTON_BGCOLOR, foreground=self.BUTTON_FOREGROUND,
                                          borderwidth=1,
                                          activebackground=self.BUTTON_HOVER_BGCOLOR,
                                          activeforeground=self.BUTTON_FOREGROUND,
                                          compound=LEFT, image=ItemDisplay.search_icon, relief=RAISED,
                                          text='Item Search')

        self.bind('<Control-q>', self.openFilterSearch)
        self.bind('<Control-w>', self.openItemSearch)

        self.btn_filter_search.grid(row=0, column=0, sticky='nsew')
        lbl = Label(self.frm_details_btns, font=font_subtext_min, text='(Ctrl + Q)', style='Dark.TLabel')
        lbl.grid(row=1, column=0, sticky='n', pady=(0, 0))
        self.btn_item_search.grid(row=2, column=0, pady=(5, 0), sticky='nsew')
        lbl = Label(self.frm_details_btns, font=font_subtext_min, text='(Ctrl + W)', style='Dark.TLabel')
        lbl.grid(row=3, column=0, sticky='n', pady=(0, 0), )

        # self.frm_details_img = Frame(self.frm_details, style='Dark.Borderless.TFrame')
        # self.lbl_details_img = Label(self.frm_details_img, background=self.DETAILS_BG_COLOR, borderwidth=0)
        # self.lbl_details_img.grid(sticky='ne')
        # self.frm_details_img.grid(row=1, column=1, sticky='nsew')
        # self.frm_details_btns = Frame(self.frm_details, style='Dark.Borderless.TFrame')
        # self.frm_details_btns.grid(row=2, column=1, columnspan=1, sticky='ne', pady=5)
        #
        # self.btn_filter_search = TextButton(self.frm_details_btns, padx=5, pady=3, font=self.app_fonts['DetailsBold'],
        #                                     highlightthickness=2,
        #                                     background=self.BUTTON_BGCOLOR, foreground=self.BUTTON_FOREGROUND,
        #                                     borderwidth=1,
        #                                     activebackground=self.BUTTON_HOVER_BGCOLOR,
        #                                     activeforeground=self.BUTTON_FOREGROUND,
        #                                     compound=LEFT, image=ItemDisplay.search_icon, relief=RAISED, text='Search')
        #
        # self.btn_item_search = TextButton(self.frm_details_btns, padx=5, pady=3, font=self.app_fonts['DetailsBold'],
        #                                   highlightthickness=2,
        #                                   background=self.BUTTON_BGCOLOR, foreground=self.BUTTON_FOREGROUND,
        #                                   borderwidth=1,
        #                                   activebackground=self.BUTTON_HOVER_BGCOLOR,
        #                                   activeforeground=self.BUTTON_FOREGROUND,
        #                                   compound=LEFT, image=ItemDisplay.search_icon, relief=RAISED,
        #                                   text='Item Search')
        #
        # self.btn_filter_search.grid(row=0, column=0)
        # self.btn_item_search.grid(row=1, column=0, padx=0)

        self.txt_details.configure(font=font_default)

        # self.txt_details.tag_configure(self.type_tags[ItemType.Normal], foreground=self.NORMAL_COLOR, font='-weight bold')
        #### ITEM TAGS

        self.txt_details.tag_configure(self.type_tags[ItemType.Normal], foreground=self.NORMAL_COLOR, font=font_title)
        self.txt_details.tag_configure(self.type_tags[ItemType.Magic], foreground=self.MAGIC_COLOR, font=font_title)
        self.txt_details.tag_configure(self.type_tags[ItemType.Rare], foreground=self.RARE_COLOR, font=font_title)
        self.txt_details.tag_configure(self.type_tags[ItemType.Unique], foreground=self.UNIQUE_COLOR, font=font_title)
        self.txt_details.tag_configure(self.type_tags[ItemType.Gem], foreground=self.GEM_COLOR, font=font_title)
        self.txt_details.tag_configure(self.type_tags[ItemType.Currency], foreground=self.CURRENCY_COLOR, font=font_title)
        self.txt_details.tag_configure(self.type_tags[ItemType.DivinationCard], foreground=self.DIV_COLOR, font=font_title)
        self.txt_details.tag_configure(self.type_tags[ItemType.QuestItem], foreground=self.QUEST_COLOR, font=font_title)
        self.txt_details.tag_configure(self.type_tags[ItemType.Prophecy], foreground=self.PROPHECY_COLOR, font=font_title)
        self.txt_details.tag_configure(self.type_tags[ItemType.Relic], foreground=self.RELIC_COLOR, font=font_title)

        self.txt_details.tag_configure('title', font=font_title_big)
        self.txt_details.tag_configure('subtitle', font=font_bold_italic)

        self.txt_details.tag_configure('corrupted', foreground=self.CORRUPTED_COLOR, background=self.CORRUPTED_BGCOLOR,
                                       font=font_tag_big)

        self.txt_details.tag_configure('enchanted', foreground=self.ENCHANTED_COLOR, background=self.ENCHANTED_BGCOLOR,
                                       font=font_tag)

        self.txt_details.tag_configure('crafted', foreground=self.CRAFTED_COLOR, background=self.CRAFTED_BGCOLOR,
                                       font=font_tag)

        self.txt_details.tag_configure('implicit', font=font_underline)
        self.txt_details.tag_configure('enhanced', font=font_default, foreground=self.ENHANCED_COLOR)
        self.txt_details.tag_configure('prop', font=font_bold, foreground=self.PROP_COLOR)
        self.txt_details.tag_configure('requirement', foreground=self.REQ_COLOR, font=font_subtext)
        self.txt_details.tag_configure('requirement-warning', foreground=self.WARNING_COLOR, font=font_subtext_bold)
        self.txt_details.tag_configure('totals', foreground=self.MATCHES_COLOR)
        self.txt_details.tag_configure('bold', font=font_bold)
        self.txt_details.tag_configure('italic', font=font_italic)
        self.txt_details.tag_configure('unid', foreground=self.UNID_COLOR, font=font_bold)
        self.txt_details.tag_configure('red', font=font_default, foreground='red')
        self.txt_details.tag_configure('tiny', foreground=self.REQ_COLOR, font=font_tiny)
        self.txt_details.tag_configure('justified', justify=CENTER)


        #### TEXT TAGS

        self.txt_details.tag_configure('<whiteitem>', foreground=self.TT_WHITE_COLOR)
        self.txt_details.tag_configure('<magicitem>', foreground=self.TT_MAGIC_COLOR)
        self.txt_details.tag_configure('<rareitem>', foreground=self.TT_RARE_COLOR)
        self.txt_details.tag_configure('<uniqueitem>', foreground=self.TT_UNIQUE_COLOR)
        self.txt_details.tag_configure('<gemitem>', foreground=self.TT_GEM_COLOR)
        self.txt_details.tag_configure('<currencyitem>', foreground=self.TT_CURRENCY_COLOR)
        self.txt_details.tag_configure('<divination>', foreground=self.TT_DIV_COLOR)
        self.txt_details.tag_configure('<prophecy>', foreground=self.TT_PROPHECY_COLOR)

        self.txt_details.tag_configure('<default>', foreground=self.TT_DEFAULT_COLOR)
        self.txt_details.tag_configure('<corrupted>', foreground=self.TT_CORRUPTED_COLOR)
        self.txt_details.tag_configure('<normal>', foreground=self.TT_NORMAL_COLOR)
        self.txt_details.tag_configure('<augmented>', foreground=self.TT_AUGMENETED_COLOR)

        self.txt_details.tag_configure('<red>', foreground=self.TT_SRED_COLOR, font=font_bold_italic)
        self.txt_details.tag_configure('<green>', foreground=self.TT_SGREEN_COLOR, font=font_bold_italic)
        self.txt_details.tag_configure('<blue>', foreground=self.TT_SBLUE_COLOR, font=font_bold_italic)
        self.txt_details.tag_configure('<white>', foreground=self.TT_SWHITE_COLOR, font=font_bold_italic)

        # msgr.send_msg("This is a normal message")
        # msgr.send_msg("This is a warning message", logging.WARN)
        # msgr.send_msg("This is an error message", logging.ERROR)

        # self.lst_msgs.insert(END, self.VERSION_TEXT)
        # self.lst_msgs.itemconfigure(END, foreground=self.DEFAULT_COLOR)

        self.pane_wnd.add(self.frm_console, weight=1)
        self.main_pane_wnd.add(self.pane_wnd, weight=1)
        self.main_pane_wnd.add(self.nb_cfg)

        self.update_idletasks()
        # main_pane_height = self.winfo_height() - self.upper_frame.winfo_reqheight()
        # self.nb_cfg.config(height=round(main_pane_height/2.5))
        self.nb_cfg.config(height=300)

    def addfont(self, font):
        self.app_fonts[font.name] = font
        return font

    def findfont(self, names):
        "Return name of first font family derived from names."
        for name in names:
            if name.lower() in (x.lower() for x in tkfont.names(root=self)):
                font = tkfont.Font(name=name, exists=True, root=self)
                return font.actual()['family']
            elif name.lower() in (x.lower()
                                  for x in tkfont.families(root=self)):
                return name

    def center(self):
        self.update_idletasks()
        w = self.winfo_screenwidth()
        h = self.winfo_screenheight()
        size = tuple(int(_) for _ in self.geometry().split('+')[0].split('x'))
        x = w / 2 - size[0] / 2
        y = h / 2 - size[1] / 2
        self.geometry("{}x{}+{}+{}".format(*size, int(x), int(y)))

    def toggle_scan(self):
        if self.btn_toggle.cget("text") == "Stop":
            self.stop_scan()
        else:
            self.start_scan()

    def _get_stat(self, stat, suffix='', default='N/A'):
        if stat is None:
            return default
        return '{:.2f}{}'.format(stat, suffix)

    def update_statistics(self):
        scanner = self.scanner
        if scanner:
            stats = scanner.getStatistics()
        else:
            stats = {}

        delta = stats.get('id-delta')
        last_req = stats.get('last-req')
        if delta is None or not last_req or time.time() - last_req > 20:
            self.status_bar.lbl_id_delta.config(image=self.status_bar.grey)
        # elif delta < 30:
        #     self.status_bar.lbl_id_delta.config(image=self.status_bar.dark_green)
        elif delta < 50:
            self.status_bar.lbl_id_delta.config(image=self.status_bar.green)
        elif delta < 150:
            self.status_bar.lbl_id_delta.config(image=self.status_bar.yellow)
        else:
            self.status_bar.lbl_id_delta.config(image=self.status_bar.red)

        self.status_bar.var_id_delta.set(self._get_stat(delta))
        self.status_bar.var_delta_rate.set(self._get_stat(stats.get('delta-rate'), suffix=' d/s'))
        self.status_bar.var_peek_time.set(self._get_stat(stats.get('peek-time'), suffix='s'))
        self.status_bar.var_req_time.set(self._get_stat(stats.get('req-time'), suffix='s'))

        self.status_bar.var_queue_time.set(self._get_stat(stats.get('queue-time'), suffix='s'))
        self.status_bar.var_req_delay_time.set(self._get_stat(stats.get('req-delay-time'), suffix='s'))

        self.status_bar.var_parse_speed.set(self._get_stat(stats.get('parse-speed'), suffix=' item/s'))
        self.status_bar.var_parse_time.set(self._get_stat(stats.get('parse-time'), suffix='s'))

        self.after(1000, self.update_statistics)

    def start_scan(self):
        self.scanner = StashScanner()
        self.scan_thread = Thread(target=self.scanner.start)
        self.scan_thread.start()

        self.update_started()

    def stop_scan(self):
        self.btn_toggle.config(text="Stopping..", state=DISABLED)

        ls = LoadingScreen(self, determinate=False)
        threading.Thread(target=self._stop_scan, args=(ls,)).start()
        self.wait_window(ls)

        if self.stop_error:
            self.update_started()
            messagebox.showwarning('Operation timed out',
                                   "Stop request timed out. If the issue persists, restart the application.",
                                   parent=self)
        else:
            self.update_stopped()

    def update_started(self):
        self.btn_toggle.config(text="Stop", state=NORMAL)

    def update_stopped(self):
        self.btn_toggle.config(text="Start", state=NORMAL)
        self.btn_toggle.update_idletasks()

    def _stop_scan(self, ls):
        ls.updateStatus('Stopping scan..')

        self.stop_error = None
        if self.is_scan_active:
            self.scanner.stop()
            self.scan_thread.join(timeout=60)

            if self.scan_thread.is_alive():
                self.stop_error = TimeoutError()

        if not self.stop_error:
            self.scanner = None
            self.scan_thread = None

        ls.close()

    @property
    def is_scan_active(self):
        return self.scan_thread and self.scan_thread.is_alive()

    def show_editor_window(self):
        if self.wnd_editor is None or not self.wnd_editor.winfo_exists():
            self.wnd_editor = FilterEditor(self)

        if self.wnd_editor.winfo_exists():
            self.wnd_editor.focus()

    def close_editor_window(self):
        if self.wnd_editor:
            self.wnd_editor.onClose()
        self.wnd_editor = None

    def set_msglevel(self, event):
        self.msg_level = logging._nameToLevel[self.cmb_msglevel.get().upper()]

    def openFilterSearch(self, event):
        if self.last_index:
            obj = self.msg_tags.get(self.last_index)
            if isinstance(obj, ItemDisplay):
                obj.openFilterSearch()

    def openItemSearch(self, event):
        if self.last_index:
            obj = self.msg_tags.get(self.last_index)
            if isinstance(obj, ItemDisplay):
                obj.openItemSearch()

    def lst_selected(self, event):
        w = event.widget
        if not w.curselection():
            return

        index = int(w.curselection()[0])
        # value = w.get(index)

        if index == self.last_index:
            return

        # if any(self.txt_details.winfo_name() in child for child in self.pane_wnd.panes()):
            # self.pane_wnd.forget(self.txt_details)

        if index in self.msg_tags:
            self.update_details_lock(self.msg_tags[index], index)

    def update_details_lock(self, obj, index=-1):
        with self.details_lock:
            self.last_index = index
            self.update_details(obj)

    def update_details(self, obj):
        # if not any(self.frm_details.winfo_name() in child for child in self.pane_wnd.panes()):
        #     self.pane_wnd.add(self.frm_details)

        if isinstance(obj, ItemDisplay):
            self.update_details_item(obj)
        elif isinstance(obj, CurrencyInfo):
            self.update_details_currency(obj)
        elif isinstance(obj, FiltersInfo):
            self.update_details_filters(obj)

        # if not any(self.txt_details.winfo_name() in child for child in self.pane_wnd.panes()):
        #     self.pane_wnd.add(self.txt_details)

        if not any(self.frm_details.winfo_name() in child for child in self.pane_wnd.panes()):
            self.pane_wnd.add(self.frm_details)
        else:
            self.pane_wnd.forget(self.frm_details)
            self.pane_wnd.add(self.frm_details)
            self.update_idletasks()

    def update_details_filters(self, obj):
        if not isinstance(obj, FiltersInfo):
            return

        self.clear_details()
        self.frm_details_btns.grid_remove()
        details = self.txt_details

        details.configure(padx=10)
        details.insert(END, 'Active Filters\n', ('justified', 'title'))

        if not obj.n_active:
            details.insert(END, '\n', 'title')
            details.insert(END, 'No filters are active.', 'justified')
            return

        details.insert(END, 'Loaded {} filters, {} are active\n\n'.format(obj.n_loaded, obj.n_active),
                       ('justified', 'subtitle'))

        if obj.user_filters:
            details.insert(END, 'User filters:\n', 'bold')
            for fltr in sorted(obj.user_filters):
                details.insert(END, fltr + '\n')
            details.insert(END, '\n')

        if obj.auto_filters:
            details.insert(END, 'Generated filters:\n', 'bold')
            for fltr in sorted(obj.auto_filters):
                details.insert(END, fltr + '\n')
            details.insert(END, '\n')

        if obj.last_update:
            details.insert(END, '\nLast update: \t{}'.format(obj.last_update.strftime('%I:%M %p - %d, %b %Y')))

        txt_size = details.update_size(self.app_fonts['DetailsDefault'], self.app_fonts['DetailsTitleBig'])
        # self.update_idletasks()
        # self.pane_wnd.config(width=self.frm_details.winfo_reqwidth())
        self.update_details_pane_size(txt_size)

    def update_details_currency(self, obj):
        if not isinstance(obj, CurrencyInfo):
            return

        self.clear_details()
        self.frm_details_btns.grid_remove()
        details = self.txt_details

        details.configure(padx=20)
        # details.insert(END, '\n')
        details.insert(END, 'Currency Rates\n\n', ('justified', 'title'))

        if obj.rates is None:
            details.insert(END, 'Currency rates weren\'t loaded yet.\nStart a scan and try again.\n', 'justified')
            return

        tabs = round_up(max(len(curr) for curr in obj.rates) / self.TK_TABWIDTH)
        tabs = max(tabs, 1)

        for curr in sorted(obj.rates, key=lambda x: obj.rates[x], reverse=True):
            rate = obj.rates[curr]
            if int(rate) != rate:
                rate = round(rate, 3)
            details.insert(END, '{}:{}{}\n'.format(curr, '\t'*tabs, rate))

        if obj.last_update:
            details.insert(END, '\nLast update: \t{}'.format(obj.last_update.strftime('%I:%M %p - %d, %b %Y')))

        txt_size = details.update_size(self.app_fonts['DetailsDefault'], self.app_fonts['DetailsTitleBig'])
        self.update_details_pane_size(txt_size)

    def update_details_pane_size(self, txt_size):
        pass
        # self.update_idletasks()
        # size = txt_size + self.frm_details_img.winfo_width() + 30 * 2
        # # print('padding: ', self.frm_details.cget('padding'))
        # # print(self.pane_wnd.panes())
        # # print(self.pane_wnd.pane(1))
        # self.frm_details.config(width=size)


    def update_details_item(self, obj):
        if not isinstance(obj, ItemDisplay):
            return

        if not obj.image:
            obj.downloadImages()

        self.clear_details()
        details = self.txt_details
        item = obj.item

        details.configure(padx=0)

        if item.corrupted:
            details.insert(END, 'corrupted', 'corrupted')
            details.insert(END, ' ')

        type_tag = self.type_tags[item.type] if item.type in self.type_tags else self.type_tags[ItemType.Normal]
        details.insert(END, item.name + '\n', type_tag)

        reqs = ''

        if item.requirements:
            for prop in item.requirements:
                if reqs:
                    reqs += ' - '
                if prop.values:
                    # ValueType logic here
                    reqs += '{}: {}'.format(prop.name, prop.values[0].val)
                else:
                    reqs += '{}'.format(prop.name)

        if item.ilvl:
            if reqs:
                reqs += ' - '
            reqs += 'ilvl: {}'.format(item.ilvl)

        if reqs:
            details.insert(END, reqs, 'requirement')

        if item.type_max_sockets >= 3 and not item.mirrored and not item.corrupted \
                and item.name not in ItemCollection.SIX_LINK_EXCEPTIONS:
            tag = 'requirement-warning' if item.max_sockets < item.type_max_sockets else 'requirement'
            if reqs:
                details.insert(END, ' - ', 'requirement')
            details.insert(END, 'Max sockets: {} ({})\n'.format(min(item.max_sockets, item.type_max_sockets), item.type_max_sockets), tag)
        else:
            details.insert(END, '\n', 'requirement')

        details.insert(END, '\n', 'tiny')

        if item.enchant or item.implicit:
            for mod in item.enchant:
                details.insert(END, 'enchanted', 'enchanted')
                details.insert(END, " {}\n".format(mod))
            for mod in item.implicit:
                if item.identified:
                    details.insert(END, "{}\n".format(mod), 'implicit')
                else:
                    details.insert(END, "{}\n".format(mod))

        if not item.identified:
            details.insert(END, 'Unidentified\n', 'unid')
        elif item.explicit or item.craft:
            for mod in item.explicit:
                details.insert(END, "{}\n".format(mod))
            for mod in item.craft:
                details.insert(END, 'crafted', 'crafted')
                details.insert(END, " {}\n".format(mod))

        if item.mirrored:
            if item.mods:
                details.insert(END, '\n')
            details.insert(END, 'Mirrored\n', 'bold')

        if item.filter_totals:
            details.insert(END, '\n')
            totals = []
            for mf_type, mf_expr, val in item.filter_totals:
                val = int(val) if float(val) == int(val) else round(val, 2)
                mod_text = mod_helper.modToText(mf_type, mf_expr).replace('#', str(val))
                mod_text = mod_helper.stripTags(mod_text)
                mod_text = '{}: {}'.format(mf_type.name.lower(), mod_text)
                totals.append(mod_text)

            for total in sorted(totals):
                details.insert(END, total + '\n', 'totals')

        managed_props = ['Armour', 'Evasion Rating', 'Energy Shield',
                         'Quality', 'Level', 'Experience',
                         # 'Attacks per Second', 'Critical Strike Chance', 'Chance to Block'
                         'Physical Damage', 'Elemental Damage', 'Chaos Damage',
                         'Currently has %0 Charges',
                         ]

        props = ''
        if item.properties:
            if item.mods or not item.identified or item.mirrored:
                details.insert(END, '\n'*2, 'tiny')

            generic_props = [prop for prop in item.properties if prop.name not in managed_props]
            tabbed_props = [prop for prop in generic_props
                            if prop.display_mode != PropDisplayMode.Format and prop.values]

            if len(tabbed_props) <= 1:
                tabs = 0
            else:
                prop_lengths = [len(prop.name) for prop in tabbed_props]
                tabs = max(round_up(max(prop_lengths) / self.TK_TABWIDTH), 2)

            spacing = '\t' * tabs if tabs else ' '
            for prop in sorted(generic_props, key=lambda x: x.display_mode):
                if props:
                    props += '\n'
                if prop.values:
                    # PropDisplayMode logic here
                    if prop.display_mode == PropDisplayMode.Progress:
                        props += '{}:{spacing}{}%'.format(prop.name, round(prop.progress * 100), spacing=spacing)
                    elif prop.display_mode == PropDisplayMode.Format:
                        # PropValueType logic here
                        props += prop.format()
                    else:
                        # PropValueType logic here
                        props += '{}:{spacing}{}'.format(prop.name, prop.values[0].val, spacing=spacing)
                else:
                    props += '{}'.format(prop.name)
            if props:
                details.insert(END, props + '\n')
                details.insert(END, '\n', 'tiny')

            quality_max = 20
            enhanceable = not (item.mirrored or item.corrupted or item.quality >= quality_max)
            value_tag = 'enhanced' if enhanceable else ''
            lbl_tag = 'prop'
            sep = '\t\t'

            if item.quality:
                details.insert(END, 'Quality: ', lbl_tag)
                details.insert(END, '{}'.format(item.quality))
                if enhanceable:
                    details.insert(END, '+{}'.format(quality_max - item.quality), value_tag)
                details.insert(END, sep)

            # if item.tier:
            #     details.insert(END, 'Tier: ', lbl_tag)
            #     details.insert(END, '{}{}'.format(item.tier, sep))

            if item.level:
                details.insert(END, 'Level: ', lbl_tag)
                details.insert(END, '{}{}'.format(dround(item.level), sep))
            if item.exp:
                details.insert(END, 'Exp: ', lbl_tag)
                details.insert(END, '{}%{}'.format(round_up(item.exp), sep))

            if not details.is_line_empty():
                details.insert(END, '\n')

            if item.armour:
                details.insert(END, 'Armour: ', lbl_tag)
                details.insert(END, '{}{}'.format(dround(item.armour), sep), value_tag)
            if item.evasion:
                details.insert(END, 'Evasion: ', lbl_tag)
                details.insert(END, '{}{}'.format(dround(item.evasion), sep), value_tag)
            if item.es:
                details.insert(END, 'Shield: ', lbl_tag)
                details.insert(END, '{}{}'.format(dround(item.es), sep), value_tag)

            if not details.is_line_empty():
                details.insert(END, '\n')

            if item.dps:
                details.insert(END, 'DPS: ', lbl_tag)
                details.insert(END, '{}{}'.format(dround(item.dps), sep), value_tag)
            if item.pdps:
                details.insert(END, 'pDPS: ', lbl_tag)
                details.insert(END, '{}{}'.format(dround(item.pdps), sep), value_tag)
            if item.edps:
                details.insert(END, 'eDPS: ', lbl_tag)
                details.insert(END, '{}{}'.format(dround(item.edps), sep))

            if not details.is_line_empty():
                details.insert(END, '\n')

        if item.prophecy:
            details.insert(END, item.prophecy + '\n')

        # if item.sockets:
        #     if props or item.enchant or item.implicit or item.explicit or item.crafted or not item.identified:
        #         details.insert(END, '\n')
        #     other = 'Sockets:\t{}\n'.format(item.sockets)
        #
        #     links = item.links_string.replace('G', '<white>{W}')
        #     links = links.replace('S', '<red>{R}')
        #     links = links.replace('D', '<green>{G}')
        #     links = links.replace('I', '<blue>{B}')
        #
        #     other += 'Links:\t{}\t{}\n'.format(item.links, links)
        #
        #     details.insert(END, other)

        details.highlight_tags()

        ppad = ' ' * 4
        if item.price_display:
            # img_index = '{}.0'.format(int(float(details.index(END))) - 1)
            amount, currency = item.price_display

            details.insert(END, '\n' * 3, 'tiny')
            details.insert(END, 'Price:\t', 'bold')
            if not item.item_value:
                details.insert(END, '{} x '.format(amount))
            else:
                details.insert(END, '{}{} x \t'.format(ppad, amount))
            if currency in ItemDisplay.currency_images:
                details.window_create(END, window=Label(self.txt_details, background=self.DETAILS_BG_COLOR,
                                                        image=ItemDisplay.currency_images[currency]))
            else:
                details.insert(END, currency)
        if item.item_value:
            amount, currency = item.item_value
            details.insert(END, '\nValue:\t', 'bold')
            # details.insert(END, '{} x'.format(amount))
            details.insert(END, '{}{} x \t'.format(ppad, amount))
            if currency in ItemDisplay.currency_images:
                details.window_create(END, window=Label(self.txt_details, background=self.DETAILS_BG_COLOR,
                                                        image=ItemDisplay.currency_images[currency]))
            else:
                details.insert(END, currency)

            if item.profit is not None:
                # details.insert(END, '\n\t' + '-' * 20 + '\n', 'tiny')
                details.insert(END, '\n\t', 'tiny')
                details.insert(END, ppad)
                details.insert(END, '-'*21, 'tiny')
                # details.insert(END, ppad + '-'*15)
                details.insert(END, '\n', 'tiny')

                profit_tag = '' if item.profit > 0 else 'red'
                details.insert(END, '\t{}{}c'.format(ppad, dround(item.profit)), profit_tag)

        if item.filter_name:
            details.insert(END, '\n' * 2, 'tiny')
            details.insert(END, '\n')
            details.insert(END, 'Matched by \'{}\''.format(item.filter_name), 'italic')

            # details.tag_add('justified', img_index, END)
        # self.lbl_item_img = Label(self.txt_details, background=self.DETAILS_BG_COLOR, image=obj.image_overlay)
        # if item.sockets:
        #     self.lbl_item_img.bind('<Enter>', functools.partial(self.update_item_img, img=obj.image))
        #     self.lbl_item_img.bind('<Leave>', functools.partial(self.update_item_img, img=obj.image_overlay))

        # img_index = '{}.0'.format(int(float(details.index(END))) - 1)
        # details.window_create(END, window=self.lbl_item_img)
        #
        # details.tag_add('justified', img_index, END)

        if obj.image:
            self.update_details_img(img=obj.image_overlay)

        if item.sockets:
            self.lbl_details_img.bind('<Enter>', functools.partial(self.update_details_img, img=obj.image))
            self.lbl_details_img.bind('<Leave>', functools.partial(self.update_details_img, img=obj.image_overlay))

        # lbl = Label(self.txt_details, background=self.BUTTON_BGCOLOR, relief=RAISED, foreground=self.BUTTON_FOREGROUND,
        #             padding=5,
        #             text='Search', font=self.app_fonts['DetailsTagBig'])
        # lbl.bind('<1>', obj.openSearch)
        # # lbl.bind('<Enter>', functools.partial(lbl.config, background=self.BUTTON_HOVER_BGCOLOR))
        # # lbl.bind('<Leave>', functools.partial(lbl.config, background=self.BUTTON_BGCOLOR))

        self.btn_filter_search.config(command=obj.openFilterSearch)
        self.btn_item_search.config(command=obj.openItemSearch)
        self.frm_details_btns.grid()

        txt_size = details.update_size(self.app_fonts['DetailsDefault'], self.app_fonts['DetailsTitle'])
        self.update_details_pane_size(txt_size)
        # self.update_idletasks()

    def clear_details(self):
        # with self.details_img_lock:
        #     self.txt_details.delete(1.0, END)
        #
        #     # cannot configure img label after text delete is called because
        #     # it deletes the embedded window which is this label's parent
        #     self.lbl_item_img = None

        self.txt_details.delete(1.0, END)
        self.lbl_details_img.configure(image='', padding=0)
        self.lbl_details_img.unbind('<Enter>')
        self.lbl_details_img.unbind('<Leave>')

    def clear_msgs(self):
        self.lst_msgs.delete(0, END)
        self.last_index = -1
        self.msg_tags.clear()

    def handle_msgs(self):
        try:
            while True:
                msg = msgr.msg_queue.get_nowait()

                if msg[0] == MsgType.ScanStopped:
                    self.stop_scan()
                elif msg[0] == MsgType.UpdateID:
                    id = msg[1]

                    self.status_bar.var_req_id.set(id)
                elif msg[0] == MsgType.Text:
                    msg_level, text, tag = msg[1:]

                    if msg_level >= self.msg_level or msg_level == logging.NOTSET:
                        self.lst_msgs.insert(END, text)
                        if tag:
                            if isinstance(tag, ItemResult):
                                item = ItemDisplay(tag, msgr.msg_queue)
                                item.downloadImages()
                                self.msg_tags[self.lst_msgs.size() - 1] = item
                            else:
                                self.msg_tags[self.lst_msgs.size() - 1] = tag
                        if msg_level == logging.WARN:
                            self.lst_msgs.itemconfigure(END, foreground=self.WARN_COLOR)
                        elif msg_level == logging.ERROR:
                            self.lst_msgs.itemconfigure(END, foreground=self.ERROR_COLOR)
                        else:
                            self.lst_msgs.itemconfigure(END, foreground=self.DEFAULT_COLOR)

                        self.lst_msgs.update_idletasks()
                        self.lst_msgs.see(END)
                elif msg[0] == MsgType.Object:
                    obj = msg[1]
                    if isinstance(obj, CurrencyInfo):
                        self.currency_info = obj
                        self.nb_cfg.loadCurrency()
                    elif isinstance(obj, FiltersInfo):
                        if self.filters_info.last_update != obj.last_update:
                            if self.wnd_editor and self.wnd_editor.winfo_exists():
                                self.wnd_editor.onFiltersUpdated()
                        self.filters_info = obj
                        self.nb_cfg.loadPrices()
                    elif isinstance(obj, ItemDisplay):
                        # selected = self.lst_msgs.curselection()
                        # if selected:
                        with self.details_lock:
                            curItem = self.msg_tags.get(self.last_index)
                            if curItem and curItem is obj:
                                # # print('Updating image: {}'.format(obj.item.name))
                                # self.update_details_img(img=obj.image_overlay)
                                self.update_details(curItem)
                    elif isinstance(obj, VersionInfo):
                        self.check_version_callback(obj)
        except queue.Empty:
            pass

        self.after(50, self.handle_msgs)

    # def handle_ui_msgs(self):
    #     try:
    #         while True:
    #             obj = self.ui_queue.get_nowait()
    #             if isinstance(obj, ItemDisplay):
    #                 selected = self.lst_msgs.curselection()
    #                 if selected:
    #                     curItem = self.msg_tags.get(int(selected[0]))
    #                     if curItem and curItem is obj:
    #                         self.txt_details.image_configure(self.IMG_NAME, image=obj.image)
    #                         print('WE NEED TO UPDATE THE VIEWED ITEM WITH THE COOL NEW IMAGES')
    #                         # do stuff to text widget
    #     except queue.Empty:
    #         pass
    #
    #     self.after(200, self.handle_ui_msgs)

    def on_close(self):
        if self.scanner:
            self.scanner.stop()

        self.destroy()
        # if self.scan_thread.is_alive():
        #     self.scan_thread.join()

    # def update_item_img(self, evt=None, img=None):
    #     with self.details_img_lock:
    #         if self.lbl_item_img:
    #             self.lbl_item_img.config(image=img)

    def update_details_img(self, evt=None, img=None):
        if self.lbl_details_img:
            self.lbl_details_img.config(image=img, padding=0)

class VersionInfo:
    def __init__(self, data):
        self.version = data.get('version')

    def is_newer_than(self, version):
        curr = self._get_ver_nums(self.version)
        v = self._get_ver_nums(version)
        # sections
        for n1, n2 in zip(curr, v):
            # digits
            for d1, d2 in zip(n1, n2):
                if d1 > d2:
                    return True
                if d1 < d2:
                    return False
            if len(n1) > len(n2):
                return True
            if len(n1) < len(n2):
                return False
        if len(curr) > len(v):
            return True
        if len(curr) < len(v):
            return False

        return False

    def _get_ver_nums(self, version):
        m = re.match('v([0-9.]+)', version)
        if m:
            l = []
            version = self._remove_trailing_zero_sections(str(m.group(1)))
            for v in version.split('.'):
                v = self._remove_zeroes(v)
                if v == '':
                    l.append([0])
                else:
                    l.append([int(c) for c in v])
            return l
        return []

    def _remove_trailing_zero_sections(self, s):
        return re.match('([0-9.]*?)[0.]*$', s).group(1)
    def _remove_zeroes(self, s):
        return re.match('([0-9]*?)[0]*$', s).group(1)

class ReadOnlyText(Text):

    REGEX_TAG = re.compile('(<[^<]+>){([^<]+)}')

    def __init__(self, *args, **kwargs):
        Text.__init__(self, *args, **kwargs)
        self.redirector = WidgetRedirector(self)
        self.insert = self.redirector.register("insert", lambda *args, **kw: "break")
        self.delete = self.redirector.register("delete", lambda *args, **kw: "break")

    def highlight_tags(self):
        self.mark_set('matchEnd', 1.0)
        self.mark_set('searchLimit', END)

        # pattern = '<[^<]+>{[^<]+}'
        pattern = self.REGEX_TAG.pattern

        count = IntVar()
        tags = [tag.lower() for tag in self.tag_names()]
        while True:
            index = self.search(pattern, 'matchEnd', 'searchLimit',
                                count=count, regexp=True)
            if index == "": break
            if count.get() == 0: break  # degenerate pattern which matches zero-length strings

            indexEnd = "%s+%sc" % (index, count.get())
            self.mark_set('matchEnd', indexEnd)

            text = self.get(index, 'matchEnd')
            match = self.REGEX_TAG.match(text)
            if match: # should always be true
                tag, newtext = match.groups()
                if tag.lower() in tags:
                    self.delete(index, 'matchEnd')
                    self.insert(index, newtext, tag)

    def update_size(self, font_default, font_title=None):
        # hacky function to get the size right for the text widget
        # 1. assumes the first line with content is the title
        # 2. relies on input for correct fonts (which is fine in our case)

        width = 0
        found_title = font_title is None
        title_width = 0

        # txt = self.get("1.0", END)
        # tw = TextWrapper(break_long_words=False, expand_tabs=True, tabsize=AppGUI.TK_TABWIDTH)

        # for line in txt.expandtabs(int(AppGUI.TK_TABWIDTH)).split('\n'):
        # for line in tw.fill(txt).split('\n'):
        lines = self.get("1.0", END).split("\n")
        for line in lines:
            if not found_title and len(line):
                title_width = round_up(font_title.measure(line) / font_default.measure(line) * len(line) + 1)
                # print('title: {}, width: {}'.format(line, title_width))
                found_title = True
            else:
                #     tabIndex = 0
                #     delta = 0
                #     index = 0
                #     for c in line:
                #         index += 1
                #         if c == '\t':
                #             tabIndex += 1
                #             delta += max(0, tabIndex * AppGUI.TK_TABWIDTH - index - delta)
                #             print('delta: {}, tabIndex: {}'.format(delta, tabIndex))

                # calculate line width after expanding tabs in a 'tabular' fashion
                # since this is the mode we're using with the Text widget (tabStyle)
                x = 0
                tabIndex = 0

                for c in line:
                    x += 1
                    if c == '\t':
                        tabIndex += 1
                        if x < tabIndex*AppGUI.TK_TABWIDTH:
                            x = tabIndex*AppGUI.TK_TABWIDTH
                # if x + 1 > width:
                #     print('{}(len {}): {}'.format(x+1, len(line), line))
                width = max(width, x + 1)
        # print('width: ', width)

        if title_width >= width:
            width = title_width + 2
        width = max(30, width)
        width = min(width, 75)
        # width = min(width, 600 / font_default.measure('a'))
        # height = max(self.winfo_reqheight(), )
        self.config(width=width)
        # self.config(height=self.winfo_reqheight())

        return font_default.measure('a' * round(width))

    def is_line_empty(self, index='end-1c'):
        return self.compare(index + ' linestart', '==', index + ' lineend')

    def get_index(self, text, index):
        return tuple(map(int, str.split(text.index(index), ".")))

class ItemDisplay:
    CACHE = {}
    thread_pool = ThreadPoolExecutor(max_workers=8)
    currency_images = {}

    @classmethod
    def init(cls):
        try:
            cls.red = PIL.Image.open('res\\str.png')
            cls.blue = PIL.Image.open('res\\int.png')
            cls.green = PIL.Image.open('res\\dex.png')
            cls.white = PIL.Image.open('res\\gen.png')
            cls.link_vertical = PIL.Image.open('res\\link_vertical.png')
            cls.link_horizontal = PIL.Image.open('res\\link_horizontal.png')
            cls.search_icon = PIL.ImageTk.PhotoImage(file="res\\search-icon.ico")

            image_path = 'res\\currency'

            if os.path.isdir(image_path):
                image_list = [f for f in os.listdir(image_path) if
                              f.endswith('.png') and os.path.isfile(os.path.join(image_path, f))]

                for fname in image_list:
                    img = PIL.Image.open(os.path.join(image_path, fname)).resize((24, 24), PIL.Image.ANTIALIAS)
                    cls.currency_images[os.path.splitext(fname)[0]] = PIL.ImageTk.PhotoImage(img)

            cls.s_height = cls.red.width
            cls.s_width = cls.red.height
        except IOError as e:
            raise AppException('Failed to load image resources.\n{}\n'
                               'Make sure the files are valid and in place.'.format(e))
        except Exception as e:
            raise AppException('Failed to load image resources.\nUnexpected Error: {}'.format(e))

    def __init__(self, item, ui_queue):
        if not isinstance(item, ItemResult):
            raise TypeError('item is expected to be of type ItemResult')

        self.item = item
        self.image = None
        self.image_overlay = None
        self.ui_queue = ui_queue  # we use this queue to inform UI thread when the item changes
        self.requested = False

    def downloadImages(self):
        if self.requested or self.image:
            return
        self.requested = True
        if self.item.icon in self.CACHE:
            self.onDownloadComplete(self.item.icon, self.CACHE[self.item.icon])
        else:
            # print('Requesting Img: {} - {}'.format(self.item.name, self.item.icon))

            # worker = Thread(target=getDataFromUrl, args=(self.item.icon, self.onDownloadComplete, 5), daemon=True)
            # worker.start()
            self.thread_pool.submit(getDataFromUrl, self.item.icon, self.onDownloadComplete, max_attempts=5)

    def onDownloadComplete(self, url, data):
        self.requested = False
        if not data:
            # print('Request Failed: {}'. format(self.result.item.name))
            return
        if self.image:
            return

        # CONVERT DATA TO GIF IMAGE
        try:
            img = PIL.Image.open(data)
            self.image = PIL.ImageTk.PhotoImage(img)
            self.updateOverlayImage(img)

            if url not in self.CACHE:
                self.CACHE[url] = data

            # notify ui
            self.ui_queue.put((MsgType.Object, self))
        except OSError as e:
            item = self.item
            with open('tmp\\{}.err.png'.format(item.name.strip()), mode='wb') as f:
                f.write(data.getvalue())
            logger.error('Image conversion failed: {}, Length: {}\t{}'.format(item.name, len(data.getvalue()), url))

    def updateOverlayImage(self, item_image):
        item = self.item

        if not item.sockets:
            self.image_overlay = self.image
            return

        base_img = item_image.copy()

        w = item.w
        h = item.h

        links_string = item.links_string
        sockets = (len(links_string) + 1) / 2
        n_line_sockets = min(w, sockets)
        n_col_sockets = min(h, round_up(sockets / w))

        # socket start position
        sx = round(base_img.width / 2 - n_line_sockets * self.s_width / 2)
        sy = round(base_img.height / 2 - n_col_sockets * self.s_height / 2)
        socket_list = []

        for i, color in enumerate(re.split('[- ]', links_string)):
            socket_index = i % w
            line_index = int(i / w)

            if line_index % 2 == 0:
                pos = (sx + self.s_width * socket_index, sy + self.s_height * line_index)
            else:
                pos = (sx + self.s_width * (w - 1 - socket_index), sy + self.s_height * line_index)

            color = ItemSocketType(color)
            if color == ItemSocketType.Strength:
                socket_type = self.red
            elif color == ItemSocketType.Dexterity:
                socket_type = self.green
            elif color == ItemSocketType.Intelligence:
                socket_type = self.blue
            else:
                socket_type = self.white

            base_img.paste(socket_type, pos, socket_type)

            socket_list.append((pos, socket_type))

        for i, link in enumerate(filter(lambda x: x, re.split('[^- ]', links_string))):
            if link == ' ':
                continue

            curr_x, curr_y = socket_list[i][0]
            next_x, next_y = socket_list[i + 1][0]
            line_index = int((i + 1) / w)

            if curr_y == next_y:
                if line_index % 2 == 0:
                    pos = (round(curr_x + self.s_width - self.link_horizontal.width / 2),
                           round(curr_y + self.s_height / 2 - self.link_horizontal.height / 2))
                else:
                    pos = (round(next_x + self.s_width - self.link_horizontal.width / 2),
                           round(next_y + self.s_height / 2 - self.link_horizontal.height / 2))

                link_type = self.link_horizontal
            else:
                pos = (round(curr_x + self.s_width / 2 - self.link_vertical.width / 2),
                       round(curr_y + self.s_height - self.link_vertical.height / 2))
                link_type = self.link_vertical

            socket_list.append((pos, link_type))

        for socket in socket_list:
            pos, img = socket
            base_img.paste(img, pos, img)

        self.image_overlay = PIL.ImageTk.PhotoImage(base_img)

    def openFilterSearch(self):
        self.openSearch(self.item.filter_params)

    def openItemSearch(self):
        self.openSearch(self.item.item_params)

    def openSearch(self, params=None):
        form = self.getRequestFormString(params)
        temp_file = 'tmp\\search.htm'
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(form)
            f.flush()

        webbrowser.open(temp_file)

    def getRequestFormString(self, params=None):
        if params is None:
            params = self.item.filter_params
        #encode values?
        params_str = str([list(param) for param in params])
        return """
        <html>
        <head>
        <script src="..\\res\\postForm.js" type="text/javascript"></script>
        </head>
        <body bgcolor="black">
            <script>
                window.addEventListener("DOMContentLoaded", function() {{
                   post('http://poe.trade/search', {});
                }}, false);
            </script>
        </body>
        </html>
        """.format(params_str)

class StatusBar(Frame):

    @classmethod
    def init(cls):
        def load_img(fpath):
            img = PIL.Image.open(fpath).resize((20, 20), PIL.Image.ANTIALIAS)
            return PIL.ImageTk.PhotoImage(img)
        try:
            cls.red = load_img('res\\status-red.ico')
            cls.yellow = load_img('res\\status-yellow.ico')
            cls.green = load_img('res\\status-green.ico')
            cls.dark_green = load_img('res\\status-dark-green.ico')
            cls.grey = load_img('res\\status-grey.ico')
        except IOError as e:
            raise AppException('Failed to load image resources.\n{}\n'
                               'Make sure the files are valid and in place.'.format(e))
        except Exception as e:
            raise AppException('Failed to load image resources.\nUnexpected Error: {}'.format(e))

    def __init__(self, master):
        Frame.__init__(self, master, relief=SUNKEN, borderwidth=2)

        # frm = Frame(self)
        # self.lbl = Label(frm, text='wTF')
        # self.lbl.grid(row=0, column=0, sticky='w')
        # frm.grid(row=0, column=0, sticky='w')

        lbl, self.lbl_id_val, self.var_req_id = self.add('Req ID:', value='N/A')
        # self.lbl_id_val.config(foreground='blue')
        self.lbl_id_delta, val, self.var_id_delta = self.add('Delta avg:', value='N/A')
        self.lbl_id_delta.config(compound=LEFT, image=self.grey)
        lbl, val, self.var_delta_rate = self.add('Delta rate:', value='N/A')
        lbl, val, self.var_req_time = self.add('DL time:', value='N/A')
        lbl, val, self.var_peek_time = self.add('Peek time:', value='N/A')
        lbl, val, self.var_req_delay_time = self.add('Delay time:', value='N/A')
        lbl, val, self.var_queue_time = self.add('Queue time:', value='N/A')

        lbl, val, self.var_parse_time = self.add('Parse time:', value='N/A')
        lbl, val, self.var_parse_speed = self.add('Parse speed:', value='N/A')

        self.rowconfigure(0, pad=5)
        self.columnconfigure(0, weight=1)

    def add(self, label, value=''):
        cols, rows = self.grid_size()
        frm = Frame(self)
        frm.grid(row=0, column=cols, sticky='ew')
        # frm.columnconfigure(2, weight=1)

        lbl = Label(frm, text=label)
        var = StringVar(value=value)
        lbl_val = Label(frm, textvariable=var)

        lbl.grid(row=0, column=1, sticky='w')
        lbl_val.grid(row=0, column=2, padx=5, sticky='w')

        if cols > 0:
            sep = Separator(frm, orient=VERTICAL)
            sep.grid(row=0, column=0, sticky='nsw', padx=5)

        return lbl, lbl_val, var

if __name__ == "__main__":
    multiprocessing.freeze_support()
    logger = logging.getLogger('ui')

    try:
        app = AppGUI()

        if app.initialized:
            app.mainloop()

        app.quit()
    except Exception as e:
        logger.error('Application closed with error: {}'.format(e), exc_info=1)

