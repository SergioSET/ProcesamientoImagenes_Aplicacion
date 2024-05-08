import tkinter
import customtkinter
import segmentacion as seg
import procesamiento as proc
import registro as reg
import demo as demo

customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme("green")


class GUI(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("Selección de entrega de proyecto")
        self.geometry(f"{580}x{100}")
        self.resizable(False, False)
        self.columnconfigure((0, 1, 2, 3), weight=1)
        self.rowconfigure(0, weight=1)

        self.create_widgets()

    def select_option1(self):
        self.destroy()
        seg.main()

    def select_option2(self):
        self.destroy()
        proc.main()

    def select_option3(self):
        self.destroy()
        reg.main()

    def select_option4(self):
        self.destroy()
        demo.main()

    def create_widgets(self):
        self.button1 = customtkinter.CTkButton(
            self, text="Segmentación", command=self.select_option1
        )
        self.button1.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.button2 = customtkinter.CTkButton(
            self, text="Procesamiento", command=self.select_option2
        )
        self.button2.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.button3 = customtkinter.CTkButton(
            self, text="Bordes y Registro", command=self.select_option3
        )
        self.button3.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")

        self.button4 = customtkinter.CTkButton(
            self, text="Demo", command=self.select_option4
        )
        self.button4.grid(row=0, column=3, padx=10, pady=10, sticky="nsew")


if __name__ == "__main__":
    app = GUI()
    app.mainloop()
