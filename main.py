import tkinter
import customtkinter
import segmentacion as seg
import procesamiento as proc

customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme("green")


class GUI(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("Selección de entrega de proyecto")
        self.geometry(f"{580}x{100}")
        self.resizable(False, False)
        self.columnconfigure((0, 1), weight=1)
        self.rowconfigure(0, weight=1)

        self.create_widgets()

    def select_option1(self):
        self.destroy()
        seg.main()

    def select_option2(self):
        self.destroy()
        proc.main()

    def create_widgets(self):
        self.button1 = customtkinter.CTkButton(
            self, text="Segmentación", command=self.select_option1
        )
        self.button1.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.button2 = customtkinter.CTkButton(
            self, text="Procesamiento", command=self.select_option2
        )
        self.button2.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")


if __name__ == "__main__":
    app = GUI()
    app.mainloop()
