from ttkbootstrap import ScrolledText
import sys

class Console(ScrolledText):
    def __init__(self, *args, **kwargs):
        kwargs.update({"state": "disabled"})
        super().__init__(*args, **kwargs)
        self.bind("<Destroy>", self.reset)
        self.old_stdout = sys.stdout
        sys.stdout = self

    def delete(self, *args, **kwargs):
        self.config(state="normal")
        self.delete(*args, **kwargs)
        self.config(state="disabled")

    def write(self, content):
        self.config(state="normal")
        self.insert("end", content)
        self.config(state="disabled")
        self.see('end')

    def reset(self, event):
        sys.stdout = self.old_stdout
