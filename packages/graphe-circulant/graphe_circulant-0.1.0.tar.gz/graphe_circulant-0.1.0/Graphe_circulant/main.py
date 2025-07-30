from tkinter import Tk
import tkinter as tk
from interface import GraphC

def main():
    fenetre = tk.Tk()
    GraphC(fenetre)
    fenetre.mainloop()

if __name__ == "__main__":
    main()