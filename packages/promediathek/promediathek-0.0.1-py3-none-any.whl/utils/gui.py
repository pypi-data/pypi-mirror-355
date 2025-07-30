from os import PathLike
from tkinter import *
from textwrap import fill
from tkinter.ttk import Progressbar
from PIL import Image, ImageTk
import pillow_avif

from lib.pakete.progresspaket import Progresspaket


# noinspection PyPep8Naming
class Column:

    def __init__(self, tk: Tk | Frame, relative_width=1):
        self.tk = tk
        self.frame = Frame(self.tk)
        self.relative_width = relative_width
        self.elements = []
        self.frame.pack(side=LEFT, fill=BOTH)

    def addText(self, text: str) -> Label:
        label = Label(self.frame, text=fill(text))
        label.pack(side=TOP)
        self.elements.append(label)
        return label

    def addTextInput(self, callback=None) -> Entry:
        text_input_frame = Frame(self.frame)

        if callback:
            callback_dummy = StringVar()
            callback_dummy.trace('w', lambda name, index, mode, sv=callback_dummy: callback(sv))
            text_input = Entry(text_input_frame, textvariable=callback_dummy)

        else:
            text_input = Entry(text_input_frame)

        text_input.pack(side=TOP)
        text_input_frame.pack(side=TOP)
        text_input.bind('<Destroy>', func=lambda x, frame=text_input_frame: frame.destroy())
        return text_input

    def addList(self, value: dict | list = None, has_search=False, callback=None) -> Listbox:
        def search(search_term: str):
            search_term = search_term.strip().lower()

            if type(value) is dict:
                searched_value = {key: val for key, val in value.items() if search_term in val.strip().lower()}
                # noinspection PyTypeChecker
                searched_list_var = StringVar(value=list(searched_value.values()))
                searched_callback_var = list(searched_value.keys())

            else:
                searched_value = [val for val in value if search_term in val.strip().lower()]
                # noinspection PyTypeChecker
                searched_list_var = StringVar(value=searched_value)
                searched_callback_var = searched_value

            listbox.configure(listvariable=searched_list_var)
            if callback:
                listbox.unbind(sequence="<<ListboxSelect>>")
                listbox.bind(sequence="<<ListboxSelect>>", func=lambda x: callback(searched_callback_var[x.widget.curselection()[0]]) if x.widget.curselection() else None)

        if type(value) is dict:
            # noinspection PyTypeChecker
            list_var = StringVar(value=list(value.values()))
            callback_var = list(value.keys())
        else:
            list_var = StringVar(value=value)
            callback_var = value

        if has_search:
            search_box = self.addTextInput(callback=lambda x: search(x.get()))

        listbox = Listbox(self.frame, listvariable=list_var)
        if callback:
            listbox.bind(sequence="<<ListboxSelect>>", func=lambda x: callback(callback_var[x.widget.curselection()[0]]) if x.widget.curselection() else None)

        if has_search:
            listbox.bind(sequence="<Destroy>", func=lambda x, sb=search_box: sb.destroy())

        listbox.pack(side=LEFT, fill=BOTH, expand=YES)
        self.elements.append(listbox)
        return listbox

    def addButtons(self, value: str | list[str], callback) -> Button | list[Button]:
        if type(value) is not list:
            value = [value]

        button_frame = Frame(self.frame)
        buttons = []
        for i, text in enumerate(value):
            button = Button(button_frame, text=text, command=lambda t=i: callback(buttons[t]))
            button.grid(row=0, column=i)
            buttons.append(button)

        button_frame.pack(side=TOP)
        if len(buttons) == 1:
            return buttons[0]
        return buttons

    def addImage(self, image_path: PathLike | str, width: int = 0, height: int = 0):
        image_pil = Image.open(image_path)

        if height:
            width = int(height * image_pil.width/image_pil.height)

        elif width:
            height = int(width * image_pil.height/image_pil.width)

        else:
            raise ValueError("height or width must be specified")

        image_pil_resized = image_pil.resize((width, height))
        image = ImageTk.PhotoImage(image_pil_resized)

        # noinspection PyTypeChecker
        label = Label(self.frame, image=image)
        label.pack(side=TOP)

        self.elements.append(image)


# noinspection PyPep8Naming
class ProGUI:

    def __init__(self, title="Test GUI"):
        self.tk = Tk()
        self.tk.title(title)

        self.columns: list[Column] = []

    def addColumn(self, position=-1) -> Column:
        column = Column(self.tk)
        if position < 0:
            position = len(self.columns) - position

        self.columns.insert(position, column)
        return column

    def deleteColumn(self, column: Column):
        self.columns.remove(column)

    def deleteColumns(self, until_len=0):
        while len(self.columns) > until_len:
            self.columns.pop().frame.destroy()

    def addProgressbar(self, progresspaket: Progresspaket):
        def update_progressbar():
            if progresspaket.done:
                frame.destroy()
                return

            progressbar.configure(value=progresspaket.progress * 100)
            status_text.configure(text="Status: " + progresspaket.status)
            # noinspection PyTypeChecker
            self.tk.after(ms=50, func=update_progressbar)

        frame = Frame(self.tk)
        frame.place(x=1, rely=1, anchor="sw")

        pb_column = Column(frame)
        titel_text = pb_column.addText("Titel: " + progresspaket.text)
        status_text = pb_column.addText("Status: " + progresspaket.status)

        progressbar = Progressbar(frame, orient=HORIZONTAL, length=100, mode='determinate')
        progressbar.pack(side=BOTTOM, fill=BOTH, expand=YES)

        self.tk.bind("<Configure>", lambda event: progressbar.configure(length=self.tk.winfo_width() - max(status_text.winfo_width(), titel_text.winfo_width())))
        update_progressbar()

    def tick(self):
        self.tk.update()

    def run(self):
        self.tk.mainloop()
