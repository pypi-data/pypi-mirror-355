import json
import math
from pathlib import Path  # Importation de la bibliothèque Path pour gérer les chemins de fichiers
import random
import time
import tkinter as tk

from tkinter import Menu, Canvas, Entry, Button, PhotoImage, Scale, IntVar, Label, Scrollbar, messagebox, filedialog

from matplotlib.patches import Patch

from .Floyd_Warshall import calculer_diametre_floyd
from .circulant_graph import generer_graphe_circulant, set_dimensions, construire_liste_adjacence
from .connexe import est_connexe, calculer_tolerance_sommets, trouver_composants_connexes
from .distance import calculer_distance_PL , calculer_plus_court_chemin
from .degre import calculer_degre_sommet
from .diametre import calculer_diametre, calculer_diametre_pondere, diam, FormulDiam
from .Dijkstra import calculer_dijkstra, chemin_dijkstra
import customtkinter as ctk

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import numpy as np

from matplotlib.ticker import FixedLocator, FuncFormatter
from collections import defaultdict

# Définition du chemin de sortie et des ressources
CHEMIN_SORTIE = Path(__file__).parent  # Le chemin du dossier courant du fichier Python
CHEMIN_IMAGE = CHEMIN_SORTIE / Path(r"assets\frame0")  # Chemin vers le dossier des ressources (images)


def recuperer_chemin_Fichier(path: str) -> Path:
    return CHEMIN_IMAGE / Path(path)


class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        if self.tooltip_window or not self.text:
            return
        x = y = 0
        x = self.widget.winfo_pointerx() + 10
        y = self.widget.winfo_pointery() + 10

        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            tw, text=self.text,
            background="#bfd4e0", foreground="#4a4a4a", borderwidth=1,
            font=("Helvetica", 9, "normal"),
            padx=5, pady=2
        )
        label.pack()

    def hide_tooltip(self, event=None):
        tw = self.tooltip_window
        self.tooltip_window = None
        if tw:
            tw.destroy()


def create_rounded_rect(canvas, x1, y1, x2, y2, r=15, **kwargs):
    """
    Dessine un rectangle aux coins arrondis sur le canvas.
    """
    points = [
        x1 + r, y1,
        x2 - r, y1,
        x2, y1,
        x2, y1 + r,
        x2, y2 - r,
        x2, y2,
        x2 - r, y2,
        x1 + r, y2,
        x1, y2,
        x1, y2 - r,
        x1, y1 + r,
        x1, y1
    ]
    return canvas.create_polygon(points, **kwargs, smooth=True)


# === Classe RoundedMenuItem ===
class RoundedMenuItem(tk.Canvas):
    def __init__(self, master, text, command=None, width=200, height=30,
                 font=("Segoe UI", 11, "bold"), text_color="#5c5c5c",
                 normal_bg="#e8f8ff", active_bg="#bfd4e0", radius=10, side_padding=10,
                 angle=0, indent=True, **kwargs):
        super().__init__(master, width=width, height=height, bg="#e8f8ff",
                         bd=0, highlightthickness=0, relief='flat', **kwargs)

        self.bind("<Configure>", lambda e: self.draw_background())

        self.text = text
        self.command = command
        self.font = font
        self.text_color = text_color
        self.normal_bg = normal_bg
        self.active_bg = active_bg
        self.radius = radius
        self.side_padding = side_padding
        self.force_active = False
        self.angle = 0  # Rotation désactivée
        self.indent = indent

        # Ajout du préfixe d'indentation uniquement si indent est True
        if self.indent:
            display_text = "  " + self.text
        else:
            display_text = self.text

        self.text_item = self.create_text(self.side_padding, height // 2,
                                          anchor="w", text=display_text,
                                          fill=self.text_color, font=self.font)

        self.draw_background()  # fond normal par défaut
        self.config(cursor="hand2")  # curseur main au survol

        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)

    def update_text(self):
        self.delete("bg")  # Supprimer l'ancien fond
        self.draw_background()  # Redessiner le fond
        self.coords(self.text_item, self.side_padding, self.winfo_height() // 2)  # Réajuster le texte
        self.itemconfig(self.text_item, text=("       " + self.text if self.indent else self.text))
        self.tag_lower("bg", self.text_item)  # S'assurer que le fond est derrière le texte

    def set_active(self, state):
        """Forcer ou réinitialiser l'état actif du widget."""
        self.force_active = state
        if state:
            self.on_enter(None)
        else:
            self.delete("bg")
            self.draw_background()
            self.on_leave(None)
            self.force_active = False

    def on_enter(self, event):
        self.delete("bg")
        w = self.winfo_width()
        h = self.winfo_height()
        if not self.indent:
            extra = 11  
            left_side = max(self.side_padding - extra, 0)
            right_side = w - self.side_padding + extra
        else:
            left_side = self.side_padding
            right_side = w - self.side_padding

        create_rounded_rect(self, left_side, 0, right_side, h,
                            r=self.radius, fill=self.active_bg,
                            outline="", tags="bg")
        self.tag_lower("bg", self.text_item)

        self.itemconfig(self.text_item, fill="#517e93")  # couleur du texte au survol (optionnel)

    def on_leave(self, event):
        if not self.force_active:
            self.draw_background()
            self.itemconfig(self.text_item, fill=self.text_color)

    def on_click(self, event):
        self.force_active = False
        self.draw_background()
        if self.command:
            self.command()

    def draw_background(self):
        self.delete("bg")
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()

        if not self.indent:
            extra = 11
            left_side = max(self.side_padding - extra, 0)
            right_side = w - self.side_padding + extra
        else:
            left_side = self.side_padding
            right_side = w - self.side_padding

        create_rounded_rect(self, left_side, 0, right_side, h,
                            r=self.radius, fill=self.normal_bg,
                            outline="", tags="bg")

        if hasattr(self, "text_item"):
            self.tag_lower("bg", self.text_item)


# === Classe SidebarSubMenu ===
class SidebarSubMenu(tk.Toplevel):
    def __init__(self, parent, items, x, y, width=185):  # <-- paramètre width ajouté
        super().__init__(parent)
        self.overrideredirect(True)
        self.parent_button = parent

        self.parent_button.winfo_toplevel().bind("<Configure>", self._on_parent_resize)

        # Dimensions du sous-menu
        item_height = 30
        gap = 4
        extra_vertical = 22
        total_height = len(items) * (item_height + gap) + 10 + extra_vertical
        total_width = width

        shadow_offset = 4
        shadow_color = "#dddddd"

        total_width_with_shadow = total_width + shadow_offset
        total_height_with_shadow = total_height + shadow_offset

        self.geometry(f"{total_width_with_shadow}x{total_height_with_shadow}+{x}+{y}")
        self.configure(bg="#ffffff")

        self.canvas = tk.Canvas(self, width=total_width_with_shadow,
                                height=total_height_with_shadow,
                                bg="#ffffff", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        create_rounded_rect(self.canvas,
                            shadow_offset, shadow_offset,
                            total_width + shadow_offset, total_height + shadow_offset,
                            r=50, fill=shadow_color, outline="")
        create_rounded_rect(self.canvas,
                            0, 0,
                            total_width, total_height,
                            r=50, fill="#f3fbff", outline="")

        self.frame = tk.Frame(self.canvas, bg="#ffffff", width=total_width, height=total_height)
        self.canvas.create_window(total_width // 2, total_height // 2, window=self.frame)

        for text, command in items:
            menu_item = RoundedMenuItem(
                self.frame,
                text=text,
                command=lambda cmd=command: self.run_and_close(cmd),
                width=total_width - 25,
                height=35,
                font=("Segoe UI", 12, "normal"),
                normal_bg="#f3fbff",
                active_bg="#bfd4e0",
                radius=24,
                side_padding=10,
                angle=0,
                indent=False
            )
            menu_item.pack(fill="x", pady=0)

        self.bind("<FocusOut>", lambda e: self.on_focus_out())

    def _on_parent_resize(self, event):
        """ Méthode appelée lors du redimensionnement du parent.
            Ici, on ferme le sous-menu pour éviter tout décalage.
        """
        self.on_focus_out()  # Déclenche la fermeture

    def on_focus_out(self):
        self.parent_button.set_active(False)
        self.destroy()

    def run_and_close(self, command):
        self.destroy()
        self.parent_button.set_active(False)
        command()


# === Classe StyleSidebar (Barre latérale principale) ===
class StyleSidebar(tk.Frame):
    def __init__(self, parent, actions_with_submenus, app):
        super().__init__(parent, bg="#e8f8ff", width=205)
        self.pack_propagate(False)
        self.pack(side="left", fill="y")
        self.font = ("Segoe UI", 12, "bold")
        self.active_menu = None
        self.active_popup = None
        self.active_menu_item = None
        self.app = app
        self.menu_items = []  # Pour stocker les RoundedMenuItem

        tk.Button(
            self, text="+ Nouveau Graphe", font=("Segoe UI", 13, "bold"),
            fg="white", bg="#8dbad1", activebackground="#b1cfdb",
            bd=0, anchor="w", padx=18,
            command=self.app.afficher_popup_creation_graphe,
        ).pack(fill="x", pady=(10, 5), ipady=10)

        for item in actions_with_submenus:
            if isinstance(item[1], list):
                self.create_popup_menu(item[0], item[1])
            else:
                self.create_action_button(item[0], item[1])

    def create_action_button(self, label, command):
        menu_item = RoundedMenuItem(self, text=label, command=command,
                                    width=200, height=40, font=self.font,
                                    normal_bg="#e8f8ff", active_bg="#bfd4e0",
                                    radius=21, side_padding=10, angle=0, indent=True)
        menu_item.pack(fill="x", pady=10)
        self.menu_items.append(menu_item)  # on stocke le bouton dans la liste

    def create_popup_menu(self, label, submenu_items):
        menu_item = RoundedMenuItem(
            self, text=label + " ▶",
            command=lambda: self.show_popup(menu_item, submenu_items, label),
            width=300, height=40, font=self.font,
            normal_bg="#e8f8ff", active_bg="#bfd4e0",
            radius=21, side_padding=10, angle=0, indent=True
        )
        menu_item.pack(fill="x", pady=10)

        menu_item.bind("<Enter>", lambda event: self.show_popup(menu_item, submenu_items, label))
        menu_item.bind("<Leave>", lambda event: self.schedule_hide_popup())

    def show_popup(self, widget, submenu_items, label):
        if self.active_menu and self.active_menu.winfo_exists():
            self.active_menu.destroy()
            if self.active_menu_item:
                self.active_menu_item.set_active(False)

        x = widget.winfo_rootx() + widget.winfo_width()
        y = widget.winfo_rooty()

        # Déterminer la largeur personnalisée selon le libellé du menu
        if label == "Connexité":
            width = 200
        elif label == "Plus court chemin":
            width = 150
        else:
            width = 185  # largeur par défaut

        self.active_menu = SidebarSubMenu(widget, submenu_items, x, y, width=width)
        self.active_menu_item = widget
        widget.set_active(True)

        self.active_menu.bind("<Enter>", lambda e: self.cancel_hide_popup())
        self.active_menu.bind("<Leave>", lambda e: self.schedule_hide_popup())

    def hide_popup(self):
        if self.active_menu and self.active_menu.winfo_exists():
            self.active_menu.destroy()
        if self.active_menu_item:
            self.active_menu_item.set_active(False)
        self.active_menu = None
        self.active_menu_item = None

    def hide_popup_if_needed(self, widget):
        self.after(200, lambda: self._check_mouse_leave(widget))

    def _check_mouse_leave(self, widget):
        # Vérifie si la souris est hors du widget ET hors du sous-menu
        x, y = self.winfo_pointerxy()
        widget_under_pointer = self.winfo_containing(x, y)

        if widget_under_pointer not in (widget, self.active_menu):
            self.hide_popup()

    def schedule_hide_popup(self):
        self.hide_job = self.after(200, self.hide_popup)

    def cancel_hide_popup(self):
        if hasattr(self, "hide_job"):
            self.after_cancel(self.hide_job)
            del self.hide_job

    def update_menu_items_text(self):
        for widget in self.winfo_children():
            if isinstance(widget, RoundedMenuItem):
                widget.update_text()


# === Classe GraphC (Fenêtre principale) ===
class GraphC:
    def __init__(self, fenetre):
        self.fenetre = fenetre  # La fenêtre principale de l'application
        # Définir la taille de la fenêtre
        largeur_fenetre = 1400  # Largeur de la fenêtre
        hauteur_fenetre = 800  # Hauteur de la fenêtre

        # Calculer la position pour centrer la fenêtre
        largeur_ecran = self.fenetre.winfo_screenwidth()
        hauteur_ecran = self.fenetre.winfo_screenheight()
        position_x = (largeur_ecran // 2) - (largeur_fenetre // 2)
        position_y = (hauteur_ecran // 4) - (hauteur_fenetre // 4)

        # Appliquer la géométrie centrée
        self.fenetre.configure(bg="#FFFFFF")  # Définir la couleur de fond de la fenêtre
        fenetre.state("zoomed")  # Fonctionne sur Windows uniquement

        # self.fenetre.resizable(False, False)  # Empêcher le redimensionnement de la fenêtre
        self.fenetre.title("Graphe Circulant")  # Définir le titre de la fenêtre

        # Définir la frame racine qui contiendra la navbar et le contenu principal
        self.root_frame = tk.Frame(self.fenetre, bg="white", width=1300)
        self.root_frame.pack(expand=True, fill="both")
        self.root_frame.pack_propagate(False)

        # Définition de la liste des actions du menu
        actions = [
            ("ajouter sommet", self.ajouter_sommet),
            ("Sauvegarder", self.sauvegarder_graphe),
            ("Charger", self.charger_graphe),
            ("Réinitialiser", self.reinitialiser_graphe),
            # ("Connexité", [
            #     ("Composants connexes", self.composants_connexes),
            #     ("Tolérance aux Pannes", self.afficher_tolerance_graphe)
            # ]), 
            ("Composantes connexes", self.composants_connexes),
            ("Degré", self.degre_sommets),
            ("Distance", self.plus_court_chemin),
            ("Plus court chemin", [
                ("Affecter Poids", self.affecter_poids_aleatoires),
                ("Modifier Poids", self.modifier_poids),
                ("Calculer", self.afficher_dijkstra)
            ]),
            ("Diamètre", self.afficher_diametre),
            ("Diamètre Cn(1,s)", self.tester_formule_diametre),
            # ("Diamètre optimisé", self.afficher_diametre_circulant),
            ("Historique", self.afficher_historique_pannes)
        ]
        self.sidebar = StyleSidebar(self.root_frame, actions, self)

        # Zone principale
        self.main_frame = tk.Frame(self.root_frame, bg="white")
        self.main_frame.pack(side="right", expand=True, fill="both")
        self.main_frame.pack_propagate(False)  # Empêche le redimensionnement automatique

        # Zone du graphe (à gauche)
        self.graph_frame = tk.Frame(self.main_frame, bg="white")
        # self.graph_frame.pack(side="top", expand=True, fill="both")

        # Création du panneau de statistiques à droite du graphe
        # self.canvas_stats = tk.Canvas(self.main_frame, bg="#aed9ee", width=350, height=300)
        # #self.canvas_stats.place(x=0, y=0, width=380, height=300)
        # self.canvas_stats.pack(side="right", padx=8, pady=0)

        # Créer un label pour afficher le message
        # self.label_message = Label(self.fenetre, text="", fg="red", font=("Arial", 12, "bold"))
        # self.label_message.place(x=400, y=600, width=300, height=30)

        # Ajout d'une barre de défilement (scrollbar) pour la zone principale
        self.navbar = tk.Frame(self.root_frame, bg="#3c5e6e", height=50)
        self.navbar.pack(side="top", fill="x")

        # Création du canevas (zone pour dessiner les éléments graphiques)
        self.canevas = Canvas(self.main_frame, bg="#FFFFFF", width=990, bd=0, highlightthickness=0, relief="ridge")
        self.canevas.pack(expand=True, fill="both")  # Positionner le canevas dans la fenêtre
        self.canevas.bind("<Configure>", self.redimensionner_fenetre)

        # self.canevas.create_rectangle(0.0, 0.0, 20.0, 700.0, fill="#AED9EF",
        #                               outline="")  # Dessiner un rectangle pour l'arrière-plan

        # Créez une frame dédiée aux contrôles en bas de la fenêtre (bg="white" pour homogénéiser)

        # self.root_frame.configure(bg="white")  # Couleur de fond de la frame racine
        self.navbar.configure(bg="white")
        self.graph_frame.configure(bg="blue")  # Couleur de fond de la frame du graphe
        # self.stats_panel.configure(bg="#aed9ee")  # Couleur de fond de la frame des statistiques
        # self.canevas.configure(bg="red")  # Couleur de fond du canevas

        # 111111111111111111111111111111111111111
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        # 11111111111111111111111111111111111111
        # Liste historique des événements de panne
        self.historique_pannes = []

        # Menu "Graphe"
        self.S = []  # Initialiser la liste des cordes

        # Chargement des images
        self.images = {
            "image_1": PhotoImage(file=recuperer_chemin_Fichier("image_1.png")),
            "image_21": PhotoImage(file=recuperer_chemin_Fichier("image_21.png")),
        }
        fenetre.iconphoto(False, self.images["image_1"])  # Définir l'icône de la fenêtre

        # # Placement des images dans le canevas
        self.image_id_1 = self.canevas.create_image(165.0, 40.0, image=self.images["image_1"])
        self.image_id_21 = self.canevas.create_image(550.0, 40.0, image=self.images["image_21"])

        # Ensemble pour stocker les sommets en panne
        self.sommets_en_panne = set()
        self.points = []
        self.canevas.bind("<Button-1>", self.gerer_clic)

        # Dictionnaire pour stocker les poids des arêtes
        self.aretes = []
        self.poids_aretes = {}

        self.original_poids_aretes = self.poids_aretes.copy()

        self.S_definie_par_popup = False  # Indicateur pour savoir si S a été défini par le popup
        self.curseur_modifie = False  # Indicateur pour savoir si le curseur a été modifié
        self.index_couleur = 0
        self.animation_en_cours = True
        self.id_animation_after = None
        self.last_header = None
        self.popup = None

        self.diametres_cache = []
        self.temps_cache = []
        self.methodes_cache = []
        self.couleurs_cache = []
        self.bars1 = None
        self.bars2 = None
        self.ax1 = None
        self.ax2 = None
        self.canvas_graph_diam = None

        # Curseurs pour ajuster le nombre de sommets et de cordes
        self.sommets_var = IntVar(value=6)  # Nombre de sommets, initialisé à 5
        self.cordes_var = IntVar(value=2)  # Nombre de cordes, initialisé à 2

        # Scale: est un curseur interactif qui permet à l'utilisateur de choisir une valeur numérique dans une plage donnée.
        self.label_sommets = ctk.CTkLabel(self.fenetre,
                                          text=f"Sommets : {int(self.sommets_var.get())}",
                                          font=("Arial", 14, "bold"), text_color="#55859c")

        self.sommets_slider = ctk.CTkSlider(
            self.fenetre,
            from_=3,
            to=31,
            variable=self.sommets_var,
            command=self.mise_a_jour_sommets,
            width=280,
            progress_color="#55859c",
            button_color="#55859c"
        )

        # Scale: est un curseur interactif qui permet à l'utilisateur de choisir une valeur numérique dans une plage donnée.
        n = self.sommets_var.get()
        max_cordes = self.calculer_max_cordes(n)

        self.label_cordes = ctk.CTkLabel(self.fenetre,
                                         text=f"Cordes : {int(self.cordes_var.get())}",
                                         font=("Arial", 14, "bold"), text_color="#55859c")

        self.cordes_slider = ctk.CTkSlider(
            self.fenetre,
            from_=1,
            to=max_cordes,
            variable=self.cordes_var,
            command=self.mise_a_jour_cordes,
            width=280,
            progress_color="#55859c",
            button_color="#55859c"
        )

        # Mise à jour du graphe au démarrage
        self.label_cn = Label(
            self.fenetre,
            text="",
            font=("Arial", 20, "bold"),
            fg="#3c5e6e",
            bg="#FFFFFF",
            # wraplength=200  # Limite la largeur du texte à 300 pixels
        )

        self.creer_zone_graphique_diametres()
        self.initialiser_graphique_diametres()
        self.mettre_a_jour_graphe()
        # Les variables susceptibles de changer (nombre de sommets) peuvent être tracées
        self.sommets_var.trace("w", lambda *args: self.afficher_statistiques())
        # Mise à jour initiale des statistiques dans le panneau
        self.afficher_statistiques()

    # Met à jour la notation Cn(S) en fonction des valeurs de n et S
    def mettre_a_jour_cn(self):
        n = self.sommets_var.get()

        # Prend la vraie valeur de S (manuelle ou curseur)
        if getattr(self, 'S_manuelle', False):
            S = self.S
        else:
            S = list(range(1, self.cordes_var.get() + 1))

        # Construire la notation Cn(S)
        if isinstance(S, list):
            S_str = ",".join(map(str, S))
        else:
            S_str = str(S)

        self.label_cn.config(text=f"C{n}({S_str})")

    def mettre_a_jour_cn2(self, S):
        n = self.sommets_var.get()

        # Toujours construire correctement S_str que ce soit une liste ou une chaîne
        if isinstance(S, list):
            S_str = ",".join(map(str, S))
        elif isinstance(S, str):
            S_str = S
        else:
            S_str = str(S)

        self.label_cn.config(text=f"C{n}({S_str})")

    # Des fonction de menu
    def afficher_popup_creation_graphe(self):
        """Ouvre une fenêtre popup pour entrer le nombre de sommets et la liste S."""

        popup = tk.Toplevel(self.fenetre)
        popup.title("Créer un Graphe Circulant")
        popup.iconphoto(False, self.images["image_1"])
        popup.geometry("300x200")
        popup.resizable(False, False)  # Empêcher le redimensionnement de la fenêtre
        # Centrer le popup sur l'écran
        self.fenetre.update_idletasks()  # Met à jour les informations de la fenêtre principale
        largeur_ecran = self.fenetre.winfo_screenwidth()
        hauteur_ecran = self.fenetre.winfo_screenheight()
        largeur_popup = 400
        hauteur_popup = 300
        position_x = (largeur_ecran // 2) - (largeur_popup // 2)
        position_y = (hauteur_ecran // 2) - (hauteur_popup // 2)
        popup.geometry(f"{largeur_popup}x{hauteur_popup}+{position_x}+{position_y}")

        popup.transient(self.fenetre)  # Rendre le popup indépendant
        popup.grab_set()  # Bloquer l'interaction avec la fenêtre principale
        popup.configure(bg="#cde8f5")  # Couleur de fond du popup

        self.images["entry_1"] = PhotoImage(file=recuperer_chemin_Fichier("entry_1.png"))
        self.images["button_3"] = PhotoImage(file=recuperer_chemin_Fichier("button_3.png"))

        canvas = tk.Canvas(popup, bg="#aed9ee", highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        # Champ pour le nombre de sommets

        canvas.create_text(200, 50, text="Nombre de Sommets (n) :", font=("More Sugar", 17, "bold"), fill="#ffffff")
        canvas.create_image(200, 90, image=self.images["entry_1"])  # Image en arrière-plan
        entry_n = Entry(popup, bd=0, bg="#F3F3F3", fg="#545454", highlightthickness=0, justify="center",
                        font=("Arial", 14))
        canvas.create_window(200, 90, window=entry_n, width=140, height=30)

        # Champ pour la liste des connexions

        canvas.create_text(210, 150, text="Liste des Cordes (S) :", font=("Airstrip Arabic", 17, "bold"),
                           fill="#ffffff")
        canvas.create_image(200, 190, image=self.images["entry_1"])  # Image en arrière-plan
        entry_S = Entry(popup, bd=0, bg="#F3F3F3", fg="#545454", highlightthickness=0, justify="center",
                        font=("Arial", 14))
        canvas.create_window(200, 190, window=entry_S, width=140, height=30)

        def generer_graphe():
            """Récupère les valeurs et génère le graphe manuellement."""
            n_text = entry_n.get().strip()
            S_text = entry_S.get().strip()

            if not n_text or not S_text:  # Vérifie que les champs ne sont pas vides
                messagebox.showerror("Erreur", "Veuillez remplir tous les champs.")
                return

            try:
                n = int(n_text)  # Conversion en entier
                S = list(map(int, S_text.replace(" ", "").split(",")))  # Convertit en liste d'entiers

                if n < 3:
                    messagebox.showerror("Erreur", "Le nombre de sommets doit être au moins 3.")
                    return

                # Calcul de la valeur maximale autorisée pour chaque élément de S
                max_val = self.calculer_max_cordes(n)

                if any(s > max_val for s in S):
                    messagebox.showerror("Erreur", f"Chaque élément de S doit être ≤ {max_val}")
                    return

                # Mode manuel activé
                self.S_manuelle = True
                self.S = S.copy()

                # Réinitialiser les pannes et poids
                self.sommets_en_panne.clear()
                self.poids_aretes = {}

                # Générer le graphe
                self.points, self.aretes = generer_graphe_circulant(n, S)

                if not self.aretes or not self.points:
                    messagebox.showerror("Erreur", "Impossible de générer le graphe avec les données fournies.")
                    return

                # Mettre à jour curseurs et labels
                self.sommets_var.set(n)
                self.mettre_a_jour_label_sommets()
                self.cordes_var.set(len(S))
                self.mettre_a_jour_curseur_cordes()

                # Mettre à jour le label du curseur de sommets (c'est ce que tu voulais !)
                self.label_sommets.configure(text=f"Sommets : {n}")

                # Mettre à jour le label du curseur de cordes aussi pour être cohérent
                self.label_cordes.configure(text=f"Cordes : {len(S)}")

                # Mettre à jour Cn(S)
                self.mettre_a_jour_cn()
                self.mettre_a_jour_barres_diametres()
                # Nettoyer historique des pannes si besoin
                if self.sommets_en_panne:
                    heure = time.strftime('%H:%M:%S')
                    date = time.strftime('%d/%m/%Y')
                    # Afficher Cn(S)
                    current_header = self.header_graphe()
                    if self.last_header != current_header:
                        self.historique_pannes.append(current_header)
                        self.last_header = current_header
                    for sommet in self.sommets_en_panne.copy():
                        self.historique_pannes.append(
                            f"{date} - {heure} : Sommet {sommet} réparé suite à la création du graphe.")
                    self.sommets_en_panne.clear()

                # Dessiner le graphe
                self.dessiner_graphe(S_text)

                # Fermer le popup proprement
                popup.destroy()

            except ValueError:
                messagebox.showerror("Erreur", "Veuillez entrer des valeurs valides.")

        # Bouton pour générer le graphe
        bouton_generer = Button(
            popup,
            text="Générer",
            image=self.images["button_3"],
            command=generer_graphe,
            bg="#aed9ee",
            relief="flat",
            cursor="hand2",
            activebackground="#aed9ee"
        )
        canvas.create_window(200, 255, window=bouton_generer, width=198, height=38)

    # Récupère la valeur de S en fonction des curseurs ou des entrées utilisateur.
    def obtenir_valeur_S(self):
        # Si une liste de cordes est saisie manuellement
        if hasattr(self, "champ_2") and self.champ_2.get().strip():
            try:
                S_text = self.champ_2.get().strip()
                S = list(map(int, S_text.replace(" ", "").split(",")))  # Convertir en liste d'entiers
                return S
            except ValueError:
                self.label_cn.config(text="Erreur dans S")
                return None

        # Sinon, utiliser la valeur du curseur
        return list(range(1, self.cordes_var.get() + 1))

    def mettre_a_jour_S(self, S=None):
        if S is not None:
            self.S = S
        else:
            self.S = list(range(1, self.cordes_var.get() + 1))

    #  Calculer les composants connexes
    def composants_connexes(self):
        n = self.sommets_var.get()

        if self.S is None or len(self.S) == 0:
            messagebox.showerror("Erreur", "La liste des cordes (S) est vide ou invalide.")
            return

        sommets_actifs = [i for i in range(n) if i not in self.sommets_en_panne]
        if not sommets_actifs:
            messagebox.showwarning("Attention", "Tous les sommets sont en panne. Le graphe est non connexe.")
            return

        graphe = construire_liste_adjacence(n, self.aretes)
        sous_graphe = {
            sommet: [voisin for voisin in voisins if voisin in sommets_actifs]
            for sommet, voisins in graphe.items() if sommet in sommets_actifs
        }
        connexe = est_connexe(sous_graphe)

        if connexe:
            messagebox.showinfo("Composants connexes", "Le graphe est connexe.\nIl contient un seul composant.")
        else:
            composants = trouver_composants_connexes(sous_graphe)
            couleurs_composants = ["#0cc0df", "#ff66c4", "#44de3c", "#fff02c",
                                   "#ffa227", "#ff4127", "#ff27f6", "#294bff"]
            self.canevas.delete("graph")

            # Dessiner les arêtes (toutes, même celles avec sommet en panne)
            for (src, dest) in self.aretes:
                x1, y1 = self.points[src]
                x2, y2 = self.points[dest]

                if src in self.sommets_en_panne or dest in self.sommets_en_panne:
                    couleur = "#ebebeb"
                else:
                    couleur = None
                    for idx, comp in enumerate(composants):
                        if src in comp and dest in comp:
                            couleur = couleurs_composants[idx % len(couleurs_composants)]
                            break
                    if couleur is None:
                        couleur = "#aaaaaa"

                self.canevas.create_line(x1, y1, x2, y2, fill=couleur, width=2, tags="graph")

            # Dessiner les sommets
            for i in range(n):
                x, y = self.points[i]
                if i in self.sommets_en_panne:
                    self.canevas.create_oval(x - 10, y - 10, x + 10, y + 10,
                                             fill="#ebebeb", outline="gray", tags="graph")
                    self.canevas.create_text(x, y, text=str(i),
                                             font=("Arial", 12, "bold"), fill="gray", tags="graph")
                else:
                    couleur = "#cccccc"
                    for idx, comp in enumerate(composants):
                        if i in comp:
                            couleur = couleurs_composants[idx % len(couleurs_composants)]
                            break
                    self.canevas.create_oval(x - 10, y - 10, x + 10, y + 10,
                                             fill=couleur, outline="black", tags="graph")
                    self.canevas.create_text(x, y, text=str(i),
                                             font=("Arial", 12, "bold"), fill="white", tags="graph")

            # Affiche la fiche après dessin
            self.afficher_fiche_composants_connexes(composants)

    def afficher_fiche_composants_connexes(self, composants):
        self.popup_composants = tk.Toplevel(self.fenetre)
        self.popup_composants.title("Composants Connexes")
        self.popup_composants.iconphoto(False, self.images["image_1"])
        self.popup_composants.configure(bg="#aed9ee")
        self.popup_composants.resizable(False, False)

        # Positionnement à gauche du graphe
        canevas_x = self.canevas.winfo_rootx()
        canevas_y = self.canevas.winfo_rooty()
        centre_x, centre_y = 500, 325
        rayon = 235
        graph_left = canevas_x + (centre_x - rayon)

        popup_width = 400
        popup_height = 400
        margin = 10
        offset = 55
        new_x = int(graph_left - popup_width - margin - offset)
        graph_center_y = canevas_y + centre_y
        new_y = int(graph_center_y - popup_height / 2)
        self.popup_composants.geometry(f"{popup_width}x{popup_height}+{new_x}+{new_y}")

        # Cadre blanc (conteneur principal)
        cadre_blanc = tk.Frame(self.popup_composants, bg="#F3F3F3")
        cadre_blanc.pack(fill="both", expand=True, padx=10, pady=10)

        # Titre centré
        label_titre = tk.Label(
            cadre_blanc,
            text=" Fiche des Composants Connexes",
            font=("Arial", 16, "bold"),
            fg="#3c5e6e",
            bg="#F3F3F3",
            pady=10
        )
        label_titre.pack(anchor="center")

        # Stocker les références des labels
        self.labels_composants = {}

        # Liste des couleurs pour l'affichage sur le graphe
        couleurs_composants = ["#0cc0df", "#ff66c4", "#44de3c", "#fff02c",
                               "#ffa227", "#ff4127", "#ff27f6", "#294bff"]

        # Liste des composants (centrés et interactifs)
        for i, composant in enumerate(composants, start=1):
            texte = f"Composant {i} : {composant}"
            label = tk.Label(
                cadre_blanc,
                text=texte,
                font=("Arial", 12),
                fg="#545454",
                bg="#F3F3F3",
                cursor="hand2",
                pady=5
            )
            label.pack(anchor="center")

            Tooltip(label, f"Cliquer pour visualiser ce composant")
            # Stocker la référence du label pour le changement de couleur
            self.labels_composants[label] = composant

            # Gestion du clic pour afficher le composant sur le graphe
            def on_component_click(event, lbl=label, comp=composant):
                """ Met en surbrillance le composant sélectionné et l'affiche sur le graphe. """

                # **Désélectionner les autres composants**
                for other_lbl in self.labels_composants:
                    other_lbl.config(bg="#F3F3F3", fg="#545454")  # Remettre en couleur d'origine

                # **Sélectionner le composant cliqué**
                lbl.config(bg="#c9e9f9", fg="#545454")
                self.labels_composants_selected = lbl  # Stocker la sélection actuelle

                # **Afficher le composant en couleur sur le graphe**
                self.dessiner_graphe("")
                comp_index = composants.index(comp)
                highlight_color = couleurs_composants[comp_index % len(couleurs_composants)]

                # **Dessiner les arêtes et sommets du composant**
                for src, dest in self.aretes:
                    if src in comp and dest in comp:
                        x1, y1 = self.points[src]
                        x2, y2 = self.points[dest]
                        col = "#ebebeb" if src in self.sommets_en_panne or dest in self.sommets_en_panne else highlight_color
                        self.canevas.create_line(x1, y1, x2, y2, fill=col, width=3, tags="graph")

                for sommet in comp:
                    x, y = self.points[sommet]
                    fill_color = "#d3d3d3" if sommet in self.sommets_en_panne else highlight_color
                    text_color = "gray" if sommet in self.sommets_en_panne else "white"
                    self.canevas.create_oval(x - 10, y - 10, x + 10, y + 10, fill=fill_color, outline="black",
                                             tags="graph")
                    self.canevas.create_text(x, y, text=str(sommet), font=("Arial", 12, "bold"), fill=text_color,
                                             tags="graph")

            label.bind("<Button-1>", on_component_click)

        # Fermeture de la fiche
        def on_close_popup():
            self.dessiner_graphe("")
            self.popup_composants.destroy()

        self.popup_composants.protocol("WM_DELETE_WINDOW", on_close_popup)

    # Fonction k-connexe
    def afficher_tolerance_graphe(self):
        try:
            graphe = construire_liste_adjacence(self.sommets_var.get(), self.aretes)
            graphe = {
                sommet: [voisin for voisin in voisins if voisin not in self.sommets_en_panne]
                for sommet, voisins in graphe.items()
                if sommet not in self.sommets_en_panne
            }

            tolerance = calculer_tolerance_sommets(graphe)

            popup = tk.Toplevel(self.fenetre)
            popup.title("Tolérance aux pannes")
            popup.iconphoto(False, self.images["image_1"])
            popup.geometry("300x120")
            popup.configure(bg="#aed9ee")
            popup.resizable(False, False)

            # Centrer le popup sur l'écran
            self.fenetre.update_idletasks()
            largeur_ecran = self.fenetre.winfo_screenwidth()
            hauteur_ecran = self.fenetre.winfo_screenheight()
            largeur_popup = 350
            hauteur_popup = 150
            position_x = (largeur_ecran // 2) - (largeur_popup // 2)
            position_y = (hauteur_ecran // 2) - (hauteur_popup // 2)
            popup.geometry(f"{largeur_popup}x{hauteur_popup}+{position_x}+{position_y}")

            frame = tk.Frame(popup, bg="#aed9ee")
            frame.pack(expand=True, pady=25)

            if est_connexe(graphe):
                label1 = tk.Label(frame, text="Le graphe est ", font=("Arial", 15, "bold"),
                                  fg="#3c5e6e", bg="#aed9ee")
                label1.pack(side=tk.LEFT)

                label2 = tk.Label(frame, text=f"{tolerance}", font=("Arial", 15, "bold"),
                                  fg="red", bg="#aed9ee")
                label2.pack(side=tk.LEFT)

                label3 = tk.Label(frame, text="- Connecté", font=("Arial", 15, "bold"),
                                  fg="#3c5e6e", bg="#aed9ee")
                label3.pack(side=tk.LEFT)
            else:
                label1 = tk.Label(frame, text="Le graphe n'est pas connexe ", font=("Arial", 15, "bold"),
                                  fg="red", bg="#aed9ee")
                label1.pack(side=tk.LEFT)



        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du calcul de la tolérance : {e}")

    # Fonction pour calculer degré des sommets
    def degre_sommets(self):
        popup = tk.Toplevel(self.fenetre)
        popup.title("Informations sur un sommet")
        popup.iconphoto(False, self.images["image_1"])
        popup.geometry("400x300")
        popup.resizable(False, False)
        popup.configure(bg="#aed9ee")

        # Centrer le popup sur l'écran
        self.fenetre.update_idletasks()
        largeur_ecran = self.fenetre.winfo_screenwidth()
        hauteur_ecran = self.fenetre.winfo_screenheight()
        largeur_popup = 400
        hauteur_popup = 290
        position_x = (largeur_ecran // 2) - (largeur_popup // 2)
        position_y = (hauteur_ecran // 2) - (largeur_popup // 2)
        popup.geometry(f"{largeur_popup}x{hauteur_popup}+{position_x}+{position_y}")

        self.images["entry_1"] = PhotoImage(file=recuperer_chemin_Fichier("entry_1.png"))
        self.images["button_4"] = PhotoImage(file=recuperer_chemin_Fichier("button_4.png"))

        # Canvas pour afficher les éléments graphiques
        canvas = tk.Canvas(popup, bg="#aed9ee", highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        # Champ d'entrée pour le sommet
        canvas.create_image(200, 110, image=self.images["entry_1"])
        canvas.create_text(200, 70, text="Entrez un sommet :", font=("More Sugar", 18, "bold"), fill="#ffffff")
        entry_sommet = tk.Entry(popup, bd=0, bg="#F3F3F3", fg="#545454", highlightthickness=0, justify="center",
                                font=("Arial", 14))
        canvas.create_window(200, 110, window=entry_sommet, width=140, height=30)

        # Label pour afficher le résultat
        label_resultat = tk.Label(popup, text="", bg="#aed9ee", font=("Arial", 15), wraplength=320)
        canvas.create_window(200, 237, window=label_resultat, width=350, height=60)

        # Fonction pour afficher les informations du sommet
        def afficher_informations():
            sommet_text = entry_sommet.get().strip()
            if not sommet_text.isdigit():
                messagebox.showerror("Erreur", "Veuillez entrer un numéro de sommet valide.")
                return

            sommet = int(sommet_text)
            if sommet < 0 or sommet >= self.sommets_var.get():
                messagebox.showerror("Erreur", f"Le sommet doit être compris entre 0 et {self.sommets_var.get() - 1}.")
                return

            if sommet in self.sommets_en_panne:
                messagebox.showerror("Erreur", f"Le sommet {sommet} est en panne.")
                return

            # les connexions et le degré
            aretes = [(src, dest) for src, dest in self.aretes
                      if src not in self.sommets_en_panne and dest not in self.sommets_en_panne]

            connexions, degre = calculer_degre_sommet(sommet, aretes)

            # Construire le message
            message = f"Connecté à {', '.join(map(str, connexions))}\n"
            message += f"Degré = {degre}"

            # Afficher le message dans le label
            label_resultat.config(text=message, fg="#3c5e6e", font=("Arial", 12, "bold"))

        # Bouton pour afficher les informations
        bouton_afficher = Button(
            popup,
            image=self.images["button_4"],
            command=afficher_informations,
            bg="#AED9EF",
            fg="black",
            font=("Arial", 12, "bold"),
            relief="flat",
            cursor="hand2",
            activebackground="#aed9ee"
        )
        bouton_afficher.pack(pady=20)
        canvas.create_window(200, 180, window=bouton_afficher, width=198, height=38)

    # Calcule le diamètre du graphe
    COULEURS = ["#0cc0df", "#ff66c4", "#44de3c", "#fff02c", "#ffa227", "#ff4127", "#ff27f6", "#294bff"]

    def dessiner_graphe_diametre(self, chemin):
        """
        Dessine le graphe avec le plus court chemin en rouge, en prenant en compte les sommets en panne.
        :param chemin: Liste des sommets du chemin.
        """
        self.canevas.delete("graph")

        # Choisir une couleur unique pour l'ensemble du chemin s'il contient au moins 2 sommets
        uniform_color = None
        if len(chemin) >= 2:
            uniform_color = self.COULEURS[self.index_couleur]
            self.index_couleur = (self.index_couleur + 1) % len(self.COULEURS)

        # Dessiner les arêtes
        for src, dest in self.aretes:
            # Ne pas dessiner les arêtes connectées à des sommets en panne
            if src in self.sommets_en_panne or dest in self.sommets_en_panne:
                couleur = "#ebebeb"  # Gris pour les arêtes connectées à un sommet en panne
            elif src in chemin and dest in chemin and abs(chemin.index(src) - chemin.index(dest)) == 1:
                couleur = uniform_color if uniform_color is not None else "red"
            else:
                couleur = "gray"  # Couleur normale des arêtes
            x1, y1 = self.points[src]
            x2, y2 = self.points[dest]
            self.canevas.create_line(x1, y1, x2, y2, fill=couleur, width=2, tags="graph")

        # Dessiner les sommets
        for i, (x, y) in enumerate(self.points):
            if i in self.sommets_en_panne:
                couleur = "#ebebeb"
                texte_couleur = "gray"
            elif i in chemin:
                couleur = "#AED9EF"
                texte_couleur = "black"
            else:
                couleur = "#AED9EF"
                texte_couleur = "black"
            if i in self.sommets_en_panne:
                self.canevas.create_oval(x - 10, y - 10, x + 10, y + 10, fill=couleur, outline="gray", tags="graph")
            else:
                self.canevas.create_oval(x - 10, y - 10, x + 10, y + 10, fill=couleur, outline="black", tags="graph")
            self.canevas.create_text(x, y, text=str(i), font=("Arial", 12, "bold"), fill=texte_couleur, tags="graph")

    def afficher_diametre(self):
        try:
            popup = tk.Toplevel(self.fenetre)
            self.popup_diametre = popup
            popup.title("Diamètre du Graphe")
            popup.iconphoto(False, self.images["image_1"])
            popup.geometry("330x150")
            popup.resizable(False, False)
            popup.configure(bg="#aed9ee")

            # Centrage
            self.fenetre.update_idletasks()
            w, h = 330, 150
            x = (self.fenetre.winfo_screenwidth() // 2) - (w // 2)
            y = (self.fenetre.winfo_screenheight() // 2) - (h // 2)
            popup.geometry(f"{w}x{h}+{x}+{y}")

            # Préparer le graphe
            graphe = construire_liste_adjacence(self.sommets_var.get(), self.aretes)
            graphe = {
                s: [v for v in voisins if v not in self.sommets_en_panne]
                for s, voisins in graphe.items() if s not in self.sommets_en_panne
            }

            connexe = est_connexe(graphe)
            is_pondere = bool(self.poids_aretes) and all(
                isinstance(p, (int, float)) for p in self.poids_aretes.values())

            if connexe:
                if is_pondere:
                    if any(p < 0 for p in self.poids_aretes.values()):
                        messagebox.showerror("Erreur",
                                             "Les poids négatifs ne sont pas supportés pour le diamètre pondéré.")
                        return

                    # Graphe pondéré pour Dijkstra
                    from collections import defaultdict
                    graphe_pondere = defaultdict(list)
                    for (u, v), poids in self.poids_aretes.items():
                        if u not in self.sommets_en_panne and v not in self.sommets_en_panne:
                            graphe_pondere[u].append((v, poids))
                            graphe_pondere[v].append((u, poids))

                    diam_dij, raw_couples = calculer_diametre_pondere(graphe_pondere)

                    seen = set()
                    couples = []
                    for a, b in raw_couples:
                        key = tuple(sorted((a, b)))
                        if key not in seen:
                            seen.add(key)
                            couples.append((a, b))

                    texte_diametre = f"Diamètre du graphe : {diam_dij}"

                else:
                    diam, raw_couples = calculer_diametre(graphe)

                    seen = set()
                    couples = []
                    for a, b in raw_couples:
                        key = tuple(sorted((a, b)))
                        if key not in seen:
                            seen.add(key)
                            couples.append((a, b))

                    texte_diametre = f"Diamètre du graphe : {diam}"
            else:
                couples = []
                texte_diametre = "Le graphe n'est pas connexe.\nLe diamètre est infini."

            # Affichage
            label = tk.Label(popup, text=texte_diametre,
                             font=("Arial", 15, "bold"),
                             fg="#3c5e6e", bg="#aed9ee", justify="left")
            if connexe:
                label.place(x=55, y=37)
            else:
                popup.geometry(f"440x150+{x}+{y}")
                label.place(x=0, y=50)

            # Bouton pour afficher les couples seulement pour Dijkstra
            if connexe:
                def afficher_couples():
                    popup.destroy()

                    if is_pondere:
                        diametre = diam_dij
                    else:
                        diametre = diam

                    self.afficher_fiche_couples_diametre(couples, diametre)
                    self.index_diametre = 0
                    self.animation_en_cours = True
                    self.couples_diametre = couples
                    self.graphe_sans_pannes = graphe
                    self.afficher_prochaine_pair()

                self.images["button_7"] = PhotoImage(file=recuperer_chemin_Fichier("button_7.png"))
                btn = Button(popup, image=self.images["button_7"], command=afficher_couples,
                             bg="#AED9EF", relief="flat", cursor="hand2")
                btn.place(x=70, y=90)

            popup.protocol("WM_DELETE_WINDOW", lambda: [popup.destroy(), self.dessiner_graphe("")])

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du calcul du diamètre : {e}")

    def afficher_prochaine_pair(self):
        if not hasattr(self, "couples_diametre") or self.index_diametre >= len(self.couples_diametre):
            self.canevas.delete("graph")
            self.dessiner_graphe("")
            self.animation_en_cours = False
            self.id_animation_after = None
            return

        a, b = self.couples_diametre[self.index_diametre]
        if self.poids_aretes:
            from .Dijkstra import chemin_dijkstra  # à créer si elle n’existe pas
            graphe_pondere = defaultdict(list)
            for (u, v), poids in self.poids_aretes.items():
                if u not in self.sommets_en_panne and v not in self.sommets_en_panne:
                    graphe_pondere[u].append((v, poids))
                    graphe_pondere[v].append((u, poids))
            chemin = chemin_dijkstra(graphe_pondere, a, b)
        else:
            chemin = calculer_plus_court_chemin(self.graphe_sans_pannes, a, b)
        self.dessiner_graphe_diametre(chemin)
        self.index_diametre += 1
        self.id_animation_after = self.fenetre.after(1500, self.afficher_prochaine_pair)

    # def afficher_prochaine_pair(self):
    #     """
    #     Affiche simultanément tous les plus courts chemins correspondant aux couples du diamètre.
    #     Chaque chemin (pour un couple donné) est dessiné avec une couleur différente.
    #     Cette méthode supprime l'animation séquentielle et affiche tous les chemins en un seul coup.
    #     """
    #     # Effacer l'ancien dessin
    #     self.canevas.delete("graph")

    #     # Dessiner le fond du graphe : toutes les arêtes en gris (ou gris clair si au moins un sommet en panne)
    #     for src, dest in self.aretes:
    #         if src in self.sommets_en_panne or dest in self.sommets_en_panne:
    #             couleur_fond = "#ebebeb"
    #         else:
    #             couleur_fond = "gray"
    #         x1, y1 = self.points[src]
    #         x2, y2 = self.points[dest]
    #         self.canevas.create_line(x1, y1, x2, y2, fill=couleur_fond, width=2, tags="graph")

    #     # Pour chaque couple du diamètre, calculer et dessiner le plus court chemin avec une couleur spécifique
    #     for idx, (a, b) in enumerate(self.couples_diametre):
    #         couleur_couple = self.COULEURS[idx % len(self.COULEURS)]
    #         chemin = calculer_plus_court_chemin(self.graphe_sans_pannes, a, b)
    #         if chemin is not None and len(chemin) >= 2:
    #             for i in range(len(chemin) - 1):
    #                 src = chemin[i]
    #                 dest = chemin[i + 1]
    #                 x1, y1 = self.points[src]
    #                 x2, y2 = self.points[dest]
    #                 self.canevas.create_line(x1, y1, x2, y2, fill=couleur_couple, width=2, tags="graph")

    #     # Redessiner les sommets par-dessus pour une meilleure visibilité
    #     for i, (x, y) in enumerate(self.points):
    #         if i in self.sommets_en_panne:
    #             fill_color = "#ebebeb"
    #             outline_color = "gray"
    #             text_color = "gray"
    #         else:
    #             fill_color = "#AED9EF"
    #             outline_color = "black"
    #             text_color = "black"
    #         self.canevas.create_oval(x - 10, y - 10, x + 10, y + 10,
    #                                 fill=fill_color, outline=outline_color, tags="graph")
    #         self.canevas.create_text(x, y, text=str(i), font=("Arial", 12, "bold"),
    #                                 fill=text_color, tags="graph")

    def afficher_fiche_couples_diametre(self, couples, diametre):
        self.labels_couples_selected = None

        if hasattr(self, 'popup_couples') and self.popup_couples.winfo_exists():
            self.popup_couples.destroy()

        self.popup_couples = tk.Toplevel(self.fenetre)
        self.popup_couples.title("Couples à distance maximale")
        self.popup_couples.iconphoto(False, self.images["image_1"])
        self.popup_couples.configure(bg="#aed9ee")
        self.popup_couples.resizable(False, False)

        canevas_x = self.canevas.winfo_rootx()
        canevas_y = self.canevas.winfo_rooty()
        centre_x, centre_y = 500, 325
        rayon = 235
        graph_left = canevas_x + (centre_x - rayon)
        popup_width, popup_height = 400, 400
        margin, offset = 10, 55
        new_x = int(graph_left - popup_width - margin - offset)
        new_y = int(canevas_y + centre_y - popup_height / 2)
        self.popup_couples.geometry(f"{popup_width}x{popup_height}+{new_x}+{new_y}")

        # --- SCROLLABLE CONTAINER ---
        container = tk.Frame(self.popup_couples, bg="#F3F3F3")
        container.pack(fill="both", expand=True, padx=10, pady=10)

        canvas = tk.Canvas(container, bg="#F3F3F3", highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview, width=25)
        scrollable_frame = tk.Frame(canvas, bg="#F3F3F3")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- Scrolling via molette et clavier ---
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Up>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Down>", lambda e: canvas.yview_scroll(1, "units"))

        label_titre = tk.Label(scrollable_frame, text=f"Couples à distance maximale = {diametre}",
                               font=("Arial", 16, "bold"), fg="#3c5e6e", bg="#F3F3F3", pady=10)
        label_titre.grid(row=0, column=0, sticky="n", pady=(0, 10), padx=20)

        self.labels_couples = {}

        for i, (u, v) in enumerate(couples, start=1):
            texte = f"({u}, {v})"
            label = tk.Label(scrollable_frame, text=texte, font=("Arial", 12),
                             fg="#545454", bg="#F3F3F3", cursor="hand2", pady=5)
            label.grid(row=i, column=0, pady=2)

            self.labels_couples[label] = (u, v)

            def on_enter(e, lbl=label):
                lbl.config(bg="#d5e3ee", cursor="hand2")

            def on_leave(e, lbl=label):
                if self.labels_couples_selected != lbl:
                    lbl.config(bg="#F3F3F3", cursor="hand2")

            label.bind("<Enter>", on_enter)
            label.bind("<Leave>", on_leave)
            label.bind("<Button-1>", lambda e, lbl=label: self.on_couple_click(*self.labels_couples[lbl]))

        def on_close_popup():
            self.dessiner_graphe("")
            self.popup_couples.destroy()

        self.popup_couples.protocol("WM_DELETE_WINDOW", on_close_popup)

    def on_couple_click(self, u, v):

        # 1. Annuler animation si en cours
        if hasattr(self, "id_animation_after") and self.id_animation_after:
            self.fenetre.after_cancel(self.id_animation_after)
            self.animation_en_cours = False
            self.id_animation_after = None

        # 2. Mise à jour interface visuelle
        for other_lbl in self.labels_couples:
            other_lbl.config(bg="#F3F3F3", fg="#545454")

        for lbl, couple in self.labels_couples.items():
            if couple == (u, v):
                lbl.config(bg="#d0eaff", fg="#545454")
                self.labels_couples_selected = lbl

        # 3. Nettoyer le graphe
        self.dessiner_graphe("")

        try:
            # 4. Vérifier si le graphe est pondéré
            is_pondere = bool(self.poids_aretes) and all(
                isinstance(p, (int, float)) for p in self.poids_aretes.values()
            )

            # 5. Construire graphe actif (selon mode)
            if is_pondere:
                graphe_pondere = defaultdict(list)
                for (a, b), w in self.poids_aretes.items():
                    if a not in self.sommets_en_panne and b not in self.sommets_en_panne:
                        graphe_pondere[a].append((b, w))
                        graphe_pondere[b].append((a, w))
                chemin = chemin_dijkstra(graphe_pondere, u, v)
            else:
                graphe = construire_liste_adjacence(self.sommets_var.get(), self.aretes)
                graphe = {
                    s: [v for v in voisins if v not in self.sommets_en_panne]
                    for s, voisins in graphe.items()
                    if s not in self.sommets_en_panne
                }
                chemin = calculer_plus_court_chemin(graphe, u, v)

            # 6. Affichage du chemin
            if not chemin:
                messagebox.showerror("Erreur", f"Aucun chemin trouvé pour le couple ({u}, {v}).")
                return

            self.dessiner_graphe_diametre(chemin)

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'affichage du chemin : {e}")

        # 7. Fermeture propre
        def on_close_popup():
            self.dessiner_graphe("")
            self.popup_couples.destroy()

        self.popup_couples.protocol("WM_DELETE_WINDOW", on_close_popup)

    def tester_formule_diametre(self):
        # 🚫 Bloquer si des sommets sont en panne
        if self.sommets_en_panne:
            panne_str = ", ".join(map(str, sorted(self.sommets_en_panne)))
            messagebox.showwarning("Calcul désactivé",
                                   f"Le calcul du diamètre est désactivé car les sommets suivants sont en panne : {panne_str}")
            return
        try:
            n = self.sommets_var.get()

            # Prend la vraie valeur de S (manuelle ou curseur)
            if getattr(self, 'S_manuelle', False):
                S = self.S
            else:
                S = list(range(1, self.cordes_var.get() + 1))

            # Vérification du type Cn(1,s)
            if len(S) == 2 and S[0] == 1:
                s = S[1]
                diametre, is_borne = FormulDiam(n, s)
                if is_borne:
                    texte_diametre = f"Diamètre du graphe ≤ {diametre} (borne supérieure)"
                else:
                    texte_diametre = f"Diamètre du graphe : {diametre}"
            else:
                texte_diametre = (f"Formule valable uniquement pour Cn(1,s)")

            # Créer un popup pour afficher le résultat
            popup = tk.Toplevel(self.fenetre)
            popup.title("Diamètre du Graphe")
            popup.geometry("330x150")
            # popup.resizable(False, False)
            popup.configure(bg="#aed9ee")

            # Centrer le popup sur l'écran
            self.fenetre.update_idletasks()
            largeur_ecran = self.fenetre.winfo_screenwidth()
            hauteur_ecran = self.fenetre.winfo_screenheight()
            # Supposons que S soit défini plus haut (par exemple récupéré ou calculé)
            if len(S) == 2:
                largeur_popup = 330
            else:
                largeur_popup = 500
            hauteur_popup = 150
            largeur_ecran = self.fenetre.winfo_screenwidth()
            hauteur_ecran = self.fenetre.winfo_screenheight()
            hauteur_popup = 150
            position_x = (largeur_ecran // 2) - (largeur_popup // 2)
            position_y = (hauteur_ecran // 2) - (hauteur_popup // 2)
            popup.geometry(f"{largeur_popup}x{hauteur_popup}+{position_x}+{position_y}")

            label_diametre = tk.Label(
                popup,
                text=texte_diametre,
                font=("Arial", 15, "bold"),
                fg="#3c5e6e",
                bg="#aed9ee"
            )
            label_diametre.place(x=60, y=60)


        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du calcul du diamètre : {e}")

    # Affiche le plus court chemin entre deux sommets sur le graphe.
    def dessiner_graphe_plus_court_chemin(self, chemin):
        """
        Dessine le graphe avec le plus court chemin en rouge, en prenant en compte les sommets en panne.
        :param chemin: Liste des sommets du chemin.
        """
        self.canevas.delete("graph")

        # Dessiner les arêtes
        for src, dest in self.aretes:
            # Ne pas dessiner les arêtes connectées à des sommets en panne
            if src in self.sommets_en_panne or dest in self.sommets_en_panne:
                couleur = "#ebebeb"  # Gris pour les arêtes connectées à un sommet en panne
            elif src in chemin and dest in chemin and abs(chemin.index(src) - chemin.index(dest)) == 1:
                couleur = "red"  # Rouge pour les arêtes faisant partie du plus court chemin
            else:
                couleur = "gray"  # Couleur normale des arêtes
            x1, y1 = self.points[src]
            x2, y2 = self.points[dest]
            self.canevas.create_line(x1, y1, x2, y2, fill=couleur, width=2, tags="graph")

        # Dessiner les sommets
        for i, (x, y) in enumerate(self.points):
            if i in self.sommets_en_panne:
                couleur = "#ebebeb"
                texte_couleur = "gray"
            elif i in chemin:
                couleur = "#AED9EF"
                texte_couleur = "black"
            else:
                couleur = "#AED9EF"
                texte_couleur = "black"
            if i in self.sommets_en_panne:
                self.canevas.create_oval(x - 10, y - 10, x + 10, y + 10, fill=couleur, outline="gray", tags="graph")
            else:
                self.canevas.create_oval(x - 10, y - 10, x + 10, y + 10, fill=couleur, outline="black", tags="graph")
            self.canevas.create_text(x, y, text=str(i), font=("Arial", 12, "bold"), fill=texte_couleur, tags="graph")

    def plus_court_chemin(self):
        popup = tk.Toplevel(self.fenetre)
        popup.title("Distance entre deux sommets")
        popup.iconphoto(False, self.images["image_1"])
        popup.geometry("400x300")
        popup.resizable(False, False)
        popup.configure(bg="#aed9ee")

        # Centrer le popup sur l'écran
        self.fenetre.update_idletasks()
        largeur_ecran = self.fenetre.winfo_screenwidth()
        hauteur_ecran = self.fenetre.winfo_screenheight()
        largeur_popup = 400
        hauteur_popup = 310
        position_x = (largeur_ecran // 2) - (largeur_popup // 2)
        position_y = (hauteur_ecran // 2) - (hauteur_popup // 2)
        popup.geometry(f"{largeur_popup}x{hauteur_popup}+{position_x}+{position_y}")

        self.images["entry_1"] = PhotoImage(file=recuperer_chemin_Fichier("entry_1.png"))
        self.images["button_4"] = PhotoImage(file=recuperer_chemin_Fichier("button_4.png"))

        # Canvas pour afficher les éléments graphiques
        canvas = tk.Canvas(popup, bg="#aed9ee", highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        # Texte pour demander le premier sommet
        canvas.create_image(200, 90, image=self.images["entry_1"])
        canvas.create_text(200, 50, text="Sommet de départ :", font=("More Sugar", 16, "bold"), fill="#ffffff")
        entry_depart = tk.Entry(popup, bd=0, bg="#F3F3F3", fg="#545454", highlightthickness=0, justify="center",
                                font=("Arial", 14))
        canvas.create_window(200, 90, window=entry_depart, width=140, height=30)

        # Texte pour demander le second sommet
        canvas.create_image(200, 170, image=self.images["entry_1"])
        canvas.create_text(200, 130, text="Sommet d'arrivée :", font=("More Sugar", 16, "bold"), fill="#ffffff")
        entry_arrivee = tk.Entry(popup, bd=0, bg="#F3F3F3", fg="#545454", highlightthickness=0, justify="center",
                                 font=("Arial", 14))
        canvas.create_window(200, 170, window=entry_arrivee, width=140, height=30)

        # Label pour afficher le résultat
        label_resultat = tk.Label(popup, text="", bg="#aed9ee", font=("Arial", 12), wraplength=320)
        canvas.create_window(200, 280, window=label_resultat, width=350, height=60)

        # Fonction pour afficher le plus court chemin
        def afficher_chemin():
            sommet_depart = entry_depart.get().strip()
            sommet_arrivee = entry_arrivee.get().strip()

            if not sommet_depart.isdigit() or not sommet_arrivee.isdigit():
                messagebox.showerror("Erreur", "Veuillez entrer des numéros de sommets valides.")
                return

            sommet_depart = int(sommet_depart)
            sommet_arrivee = int(sommet_arrivee)

            if sommet_depart < 0 or sommet_depart >= self.sommets_var.get() or \
                    sommet_arrivee < 0 or sommet_arrivee >= self.sommets_var.get():
                messagebox.showerror("Erreur",
                                     f"Les sommets doivent être compris entre 0 et {self.sommets_var.get() - 1}.")
                return

            if sommet_depart in self.sommets_en_panne or sommet_arrivee in self.sommets_en_panne:
                sommets_pannes = []
                if sommet_depart in self.sommets_en_panne:
                    sommets_pannes.append(sommet_depart)
                if sommet_arrivee in self.sommets_en_panne:
                    sommets_pannes.append(sommet_arrivee)

                messagebox.showerror("Erreur",
                                     f"Le(s) sommet(s) {', '.join(map(str, sommets_pannes))} suivant(s) est/sont en panne.")
                return

            # Construire la liste d'adjacence sans les sommets en panne
            graphe = construire_liste_adjacence(self.sommets_var.get(), self.aretes)
            graphe = {sommet: [voisin for voisin in voisins if voisin not in self.sommets_en_panne]
                      for sommet, voisins in graphe.items() if sommet not in self.sommets_en_panne}

            # Utiliser parcours_largeur pour trouver le plus court chemin
            chemin = calculer_plus_court_chemin(graphe, sommet_depart, sommet_arrivee)
            distance = calculer_distance_PL(graphe, sommet_depart, sommet_arrivee)

            if chemin is None:
                messagebox.showerror("Erreur", "Aucun chemin trouvé entre les deux sommets.")
                return

            # Dessiner le graphe avec le chemin en rouge
            self.dessiner_graphe_plus_court_chemin(chemin)

            # Afficher le résultat
            label_resultat.config(text=f"Distance entre {sommet_depart} et {sommet_arrivee} : {distance}", fg="#3c5e6e",
                                  font=("Arial", 12, "bold"))

            # Fermer le popup après l'affichage du résultat avec un délai
            popup.after(1000, popup.destroy)  # Ferme le popup après 1 seconde

        # Bouton pour afficher le chemin
        bouton_afficher = Button(
            popup,
            image=self.images["button_4"],
            command=afficher_chemin,
            bg="#AED9EF",
            fg="black",
            font=("Arial", 12, "bold"),
            relief="flat",
            cursor="hand2",
            activebackground="#aed9ee"
        )
        bouton_afficher.pack(pady=20)
        canvas.create_window(200, 230, window=bouton_afficher, width=198, height=38)

    # Fonction pour affecter des poids
    def affecter_poids_aleatoires(self):
        """Affecte des poids aléatoires aux arêtes du graphe en excluant les sommets en panne."""
        self.poids_aretes = {arete: random.randint(1, 50)
                             for arete in self.aretes
                             if arete[0] not in self.sommets_en_panne and arete[1] not in self.sommets_en_panne}
        self.afficher_statistiques()
        self.mettre_a_jour_barres_diametres()

        messagebox.showinfo("Succès", "Des poids aléatoires ont été affectés aux arêtes.")

    def modifier_poids(self):
        """Affiche une fiche éditable des poids, avec option de sauvegarde."""
        if not self.poids_aretes or all(poids is None for poids in self.poids_aretes.values()):
            self.poids_aretes = {arete: 1
                                 for arete in self.aretes
                                 if arete[0] not in self.sommets_en_panne and arete[1] not in self.sommets_en_panne}

        # Vérifier si certains sommets réparés ont encore des poids "None"
        for arete in self.aretes:
            if arete[0] in self.sommets_en_panne or arete[1] in self.sommets_en_panne:
                # Supprimer les poids des arêtes connectées à des sommets en panne
                if arete in self.poids_aretes:
                    del self.poids_aretes[arete]
            elif self.poids_aretes.get(arete) is None:
                # Réinitialiser les poids des arêtes valides à 1
                self.poids_aretes[arete] = 1

        popup = tk.Toplevel(self.fenetre)
        popup.title("Modifier les Poids des Arêtes")
        popup.iconphoto(False, self.images["image_1"])
        popup.attributes("-topmost", True)
        # popup.attributes("-alpha", 0.9) # Rendre le popup légèrement transparent
        #popup.overrideredirect(True)
        popup_width, popup_height = 400, 500
        canevas_x = self.canevas.winfo_rootx()
        canevas_y = self.canevas.winfo_rooty()
        centre_x, centre_y = 500, 325
        rayon = 235
        graph_left = canevas_x + (centre_x - rayon)
        margin = 10
        new_x = int(graph_left - popup_width - margin)
        new_y = int(canevas_y + centre_y - popup_height / 2)
        popup.geometry(f"{popup_width}x{popup_height}+{new_x}+{new_y}")
        popup.configure(bg="#aed9ee")
        popup.resizable(False, False)

        # Texte d'édition
        self.text_widget_poids = tk.Text(popup, wrap="word", font=("Arial", 12), bg="#F3F3F3", fg="#545454")
        self.images["button_6"] = PhotoImage(file=recuperer_chemin_Fichier("button_6.png"))

        # Pré-remplir avec les poids actuels
        fiche_poids = "Fiche des Poids des Arêtes :\n\n"

        #  Appliquer un style au titre avec un tag
        self.text_widget_poids.insert("1.0", fiche_poids)

        self.text_widget_poids.tag_configure("titre", font=("Arial", 18, "bold"), foreground="#3c5e6e",
                                             justify="center")
        self.text_widget_poids.tag_add("titre", "1.0", "1.end")  # Appliquer le tag au titre

        #  Configurer le reste du texte
        for (src, dest), poids in self.poids_aretes.items():
            self.text_widget_poids.insert("end", f"Arête ({src}, {dest}) : {poids}\n")

        self.text_widget_poids.config(state="normal", bg="#F3F3F3", fg="#545454", font=("Arial", 12), height=20,
                                      width=40)
        self.text_widget_poids.tag_configure("center", justify="center")
        self.text_widget_poids.tag_add("center", "2.0", "end")  # Centrer tout le texte sauf le titre
        self.text_widget_poids.pack(fill="both", expand=True, padx=10, pady=10)

        # Fonction de sauvegarde et de fermeture
        def enregistrer_et_fermer():
            self.enregistrer_poids_modifies()  # Enregistre les modifications
            self.afficher_statistiques()
            self.mettre_a_jour_barres_diametres()

            popup.destroy()  # Ferme le popup

        # Bouton Enregistrer
        bouton_enregistrer = Button(
            popup,
            image=self.images["button_6"],
            command=enregistrer_et_fermer,
            bg="#AED9EF",
            fg="black",
            font=("Arial", 12, "bold"),
            relief="flat",
            cursor="hand2"
        )
        # Bouton Enregistrer
        bouton_enregistrer.pack(pady=5)


    def enregistrer_poids_modifies(self):
        """Lit les valeurs modifiées depuis le Text et met à jour les poids."""
        texte = self.text_widget_poids.get("1.0", "end").strip()
        nouveaux_poids = {}

        try:
            for ligne in texte.splitlines():
                if not ligne.startswith("Arête") or ":" not in ligne:
                    continue
                ligne = ligne.replace("Arête (", "").replace(")", "")
                arete_str, poids_str = ligne.split(":")
                src_str, dest_str = arete_str.split(",")
                src, dest = int(src_str.strip()), int(dest_str.strip())

                poids_str = poids_str.strip()
                # ✅ Conversion stricte avec vérification
                poids = float(poids_str)
                if poids < 0:
                    raise ValueError(f"Poids négatif détecté pour l'arête ({src}, {dest}).")

                # ✅ Conversion en int si c’est entier
                if poids.is_integer():
                    poids = int(poids)

                nouveaux_poids[(src, dest)] = poids

            self.poids_aretes = nouveaux_poids

        except ValueError as e:
            messagebox.showerror("Erreur", f"Erreur de format ou de valeur : {e}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur inattendue : {e}")

    # def gerer_clic(self, event):
    #     """Gère le clic gauche pour marquer un sommet comme en panne ou afficher le poids d'une arête."""
    #     heure = time.strftime('%H:%M:%S')
    #     date = time.strftime('%d/%m/%Y')

    #     # 1) On regarde si on a cliqué sur un sommet
    #     for i, (x, y) in enumerate(self.points):
    #         if (x - 10 <= event.x <= x + 10) and (y - 10 <= event.y <= y + 10):
    #             # Historique
    #             current_header = self.header_graphe()
    #             if self.last_header != current_header:
    #                 self.historique_pannes.append(current_header)
    #                 self.last_header = current_header

    #             if i in self.sommets_en_panne:
    #                 # Réparation : on remet le sommet actif
    #                 self.sommets_en_panne.remove(i)
    #                 self.historique_pannes.append(f"{date} - {heure} : Sommet {i} réparé.")

    #                 # Ajouter à nouveau les arêtes avec poids 1
    #                 for (u, v) in self.aretes:
    #                     if i in (u, v):
    #                         self.poids_aretes[(u, v)] = 1

    #             else:
    #                 # Mise en panne
    #                 self.sommets_en_panne.add(i)
    #                 self.historique_pannes.append(f"{date} - {heure} : Sommet {i} en panne.")

    #                 # Forcer poids à 1 sur arêtes incidentes
    #                 for (u, v) in list(self.poids_aretes.keys()):
    #                     if u == i or v == i:
    #                         self.poids_aretes[(u, v)] = 1

    #             #  Nettoyer les arêtes vers sommets en panne
    #             self.poids_aretes = {
    #                 arete: w for arete, w in self.poids_aretes.items()
    #                 if arete[0] not in self.sommets_en_panne and arete[1] not in self.sommets_en_panne
    #             }

    #             # Mise à jour affichage + calculs
    #             self.dessiner_graphe("")
    #             self.afficher_statistiques()
    #             self.mettre_a_jour_barres_diametres()
    #             return

    #     # 2) Si clic sur une arête
    #     if not self.poids_aretes:
    #         return

    #     for src, dest in self.aretes:
    #         x1, y1 = self.points[src]
    #         x2, y2 = self.points[dest]
    #         dist_clic = abs((y2 - y1) * event.x - (x2 - x1) * event.y + x2 * y1 - y2 * x1) / math.hypot(y2 - y1,
    #                                                                                                     x2 - x1)
    #         if dist_clic <= 5:
    #             poids = self.poids_aretes.get((src, dest))
    #             if (src in self.sommets_en_panne or dest in self.sommets_en_panne) and poids is None:
    #                 messagebox.showwarning("Avertissement", f"Aucun poids pour l'arête ({src}, {dest}).")
    #             elif poids is not None:
    #                 messagebox.showinfo("Poids de l'Arête", f"Poids de l'arête ({src}, {dest}) : {poids}")
    #             return

    def gerer_clic(self, event):
        """Gère le clic gauche pour marquer un sommet comme en panne ou afficher le poids d'une arête."""
        heure = time.strftime('%H:%M:%S')
        date = time.strftime('%d/%m/%Y')

        # Vérifier si un sommet a été cliqué
        for i, (x, y) in enumerate(self.points):
            if (x - 10 <= event.x <= x + 10) and (y - 10 <= event.y <= y + 10):
                # Ajouter le graphe actuel à l'historique avant l'événement
                # Afficher Cn(S)
                current_header = self.header_graphe()
                if self.last_header != current_header:
                    self.historique_pannes.append(current_header)
                    self.last_header = current_header

                if i in self.sommets_en_panne:
                    # Réparer le sommet sans réinitialiser les poids des arêtes
                    self.sommets_en_panne.remove(i)
                    self.historique_pannes.append(f"{date} - {heure} : Sommet {i} réparé.")
                    # self.afficher_message(f"Sommet {i} réparé ✅", couleur="green")
                else:
                    # Mettre le sommet en panne et supprimer les arêtes associées
                    self.sommets_en_panne.add(i)
                    self.historique_pannes.append(f"{date} - {heure} : Sommet {i} supprimé.")
                    # self.afficher_message(f"Sommet {i} supprimé ⚠️", couleur="red")
                    # Supprimer toutes les arêtes connectées au sommet en panne
                    self.poids_aretes = {
                        arete: poids for arete, poids in self.poids_aretes.items()
                        if arete[0] != i and arete[1] != i
                    }

                # Mettre à jour les arêtes actives (celles connectées à des sommets non en panne)
                self.poids_aretes = {
                    arete: poids for arete, poids in self.poids_aretes.items()
                    if arete[0] not in self.sommets_en_panne and arete[1] not in self.sommets_en_panne
                }

                # Mettre à jour le graphe et les statistiques
                self.dessiner_graphe("")  # Actualiser l'affichage du graphe
                self.afficher_statistiques()  # Actualiser les statistiques
                self.mettre_a_jour_barres_diametres()

                return

        # Vérifier si une arête a été cliquée
        if not self.poids_aretes:
            return

        for src, dest in self.aretes:
            x1, y1 = self.points[src]
            x2, y2 = self.points[dest]
            distance = abs((y2 - y1) * event.x - (x2 - x1) * event.y + x2 * y1 - y2 * x1) / (
                    ((y2 - y1) ** 2 + (x2 - x1) ** 2) ** 0.5)
            if distance <= 5:
                poids = self.poids_aretes.get((src, dest))
                if (src in self.sommets_en_panne or dest in self.sommets_en_panne) and any(self.poids_aretes.values()):
                    messagebox.showwarning("Avertissement", f"Aucun poids défini pour l'arête ({src}, {dest}).")
                elif poids is not None:
                    messagebox.showinfo("Poids de l'Arête", f"Poids de l'arête ({src}, {dest}) : {poids}")
                return

    # def afficher_message(self, texte, couleur="black"):
    #     self.label_message.config(text=texte, fg=couleur)
    #     self.fenetre.after(3000, lambda: self.label_message.config(text=""))

    # Affiche les distances calculées par l'algorithme de Dijkstra depuis un sommet de départ.
    def afficher_dijkstra(self):
        """
        Affiche les distances calculées par l'algorithme de Dijkstra depuis un sommet de départ.
        """
        # Vérifier si des poids ont été affectés
        if not self.poids_aretes or all(poids is None for poids in self.poids_aretes.values()):
            messagebox.showerror("Erreur",
                                 "Veuillez affecter des poids aux arêtes avant de calculer le plus court chemin.")
            return

        popup = tk.Toplevel(self.fenetre)
        popup.title("Algorithme de Dijkstra")
        popup.iconphoto(False, self.images["image_1"])
        popup.geometry("400x300")
        popup.resizable(False, False)
        popup.configure(bg="#aed9ee")

        # Centrer le popup sur l'écran
        self.fenetre.update_idletasks()
        largeur_ecran = self.fenetre.winfo_screenwidth()
        hauteur_ecran = self.fenetre.winfo_screenheight()
        largeur_popup = 400
        hauteur_popup = 310
        position_x = (largeur_ecran // 2) - (largeur_popup // 2)
        position_y = (hauteur_ecran // 2) - (largeur_popup // 2)
        popup.geometry(f"{largeur_popup}x{hauteur_popup}+{position_x}+{position_y}")

        self.images["entry_1"] = PhotoImage(file=recuperer_chemin_Fichier("entry_1.png"))
        self.images["button_4"] = PhotoImage(file=recuperer_chemin_Fichier("button_4.png"))

        # Canvas pour afficher les éléments graphiques
        canvas = tk.Canvas(popup, bg="#aed9ee", highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        # Texte pour demander le sommet de départ
        canvas.create_image(200, 90, image=self.images["entry_1"])
        canvas.create_text(200, 50, text="Sommet de départ :", font=("More Sugar", 16, "bold"), fill="#ffffff")
        entry_depart = tk.Entry(popup, bd=0, bg="#F3F3F3", fg="#545454", highlightthickness=0, justify="center",
                                font=("Arial", 14))
        canvas.create_window(200, 90, window=entry_depart, width=140, height=30)

        # Texte pour demander le sommet d'arrivée
        canvas.create_image(200, 170, image=self.images["entry_1"])
        canvas.create_text(200, 130, text="Sommet d'arrivée :", font=("More Sugar", 16, "bold"), fill="#ffffff")
        entry_arrivee = tk.Entry(popup, bd=0, bg="#F3F3F3", fg="#545454", highlightthickness=0, justify="center",
                                 font=("Arial", 14))
        canvas.create_window(200, 170, window=entry_arrivee, width=140, height=30)

        # Label pour afficher le résultat
        # Label pour afficher le résultat
        label_resultat = tk.Label(popup, text="", bg="#aed9ee", font=("Arial", 12), wraplength=320)
        canvas.create_window(200, 280, window=label_resultat, width=350, height=60)

        # Fonction pour calculer et afficher les distances
        def afficher_distances():
            sommet_depart = entry_depart.get().strip()
            sommet_arrivee = entry_arrivee.get().strip()

            if not sommet_depart.isdigit():
                messagebox.showerror("Erreur", "Veuillez entrer un numéro de sommet valide.")
                return

            sommet_depart = int(sommet_depart)
            sommet_arrivee = int(sommet_arrivee)

            if sommet_depart < 0 or sommet_depart >= self.sommets_var.get() or \
                    sommet_arrivee < 0 or sommet_arrivee >= self.sommets_var.get():
                messagebox.showerror("Erreur",
                                     f"Les sommets doivent être compris entre 0 et {self.sommets_var.get() - 1}.")
                return

            if sommet_depart in self.sommets_en_panne or sommet_arrivee in self.sommets_en_panne:
                sommets_pannes = []
                if sommet_depart in self.sommets_en_panne:
                    sommets_pannes.append(sommet_depart)
                if sommet_arrivee in self.sommets_en_panne:
                    sommets_pannes.append(sommet_arrivee)

                messagebox.showerror("Erreur",
                                     f"Le(s) sommet(s) {', '.join(map(str, sommets_pannes))} suivant(s) est/sont en panne.")
                return

            # Calculer les distances avec Dijkstra
            graphe = construire_liste_adjacence(self.sommets_var.get(), self.aretes)
            graphe = {}
            for (src, dest), poids in self.poids_aretes.items():
                if src not in self.sommets_en_panne and dest not in self.sommets_en_panne:
                    if src not in graphe:
                        graphe[src] = []
                    if dest not in graphe:
                        graphe[dest] = []
                    graphe[src].append((dest, poids if poids is not None else float('inf')))
                    graphe[dest].append(
                        (src, poids if poids is not None else float('inf')))  # Ajout de l'arête bidirectionnelle

            # Calculer les distances en utilisant Dijkstra
            distance, chemins = calculer_dijkstra(graphe, sommet_depart)

            # Afficher les distances et le chemin
            chemin = chemins.get(sommet_arrivee, None)
            if chemin is None:
                messagebox.showerror("Erreur", "Aucun chemin trouvé entre les deux sommets.")
                return

            self.dessiner_graphe_plus_court_chemin(chemin)

            # Afficher les distances
            distances = distance.get(sommet_arrivee, float('inf'))
            chemin_str = ' → '.join(map(str, chemin))
            label_resultat.config(
                text=f"La distance minimale entre le sommet {sommet_depart} et {sommet_arrivee} est : {distances}\nChemin : {chemin_str}",
                fg="#3c5e6e", font=("Arial", 12, "bold"))

        # Bouton pour afficher les distances
        bouton_afficher = Button(
            popup,
            image=self.images["button_4"],
            command=afficher_distances,
            bg="#AED9EF",
            fg="black",
            font=("Arial", 12, "bold"),
            relief="flat",
            cursor="hand2",
            activebackground="#aed9ee"
        )
        bouton_afficher.pack(pady=20)
        canvas.create_window(200, 230, window=bouton_afficher, width=198, height=38)

    # Méthode pour afficher l'historique des pannes
    def header_graphe(self):
        """
        Retourne le header du graphe avec le format souhaité : Cn(1,2)
        en transformant self.S en chaîne sans crochets.
        """
        s_str = ",".join(map(str, self.S))
        return f"C{self.sommets_var.get()}({s_str})"

    def afficher_historique_pannes(self):
        popup = tk.Toplevel(self.fenetre)
        popup.title("Historique des Pannes")
        popup.iconphoto(False, self.images["image_1"])
        popup.geometry("550x400")
        popup.resizable(False, False)
        popup.configure(bg="#aed9ee")

        # Centrage de la popup
        self.fenetre.update_idletasks()
        largeur_ecran = self.fenetre.winfo_screenwidth()
        hauteur_ecran = self.fenetre.winfo_screenheight()
        position_x = (largeur_ecran - 550) // 2
        position_y = (hauteur_ecran - 400) // 2
        popup.geometry(f"550x400+{position_x}+{position_y}")

        # Utilisation d'un widget Text pour permettre le formatage
        text_widget = tk.Text(popup, font=("Arial", 12), bg="#FFFFFF", fg="#3c5e6e", wrap="word")
        text_widget.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        scrollbar = tk.Scrollbar(popup, command=text_widget.yview)
        scrollbar.pack(side="right", fill="y")
        text_widget.config(yscrollcommand=scrollbar.set)

        # Configurer le tag "header" pour afficher lCn(S) en gras
        text_widget.tag_config("header", font=("Arial", 12, "bold"))

        previous_header = None  # Pour savoir si un header a déjà été inséré
        if self.historique_pannes:
            for event in self.historique_pannes:
                event = event.strip()
                # Détection d'un header (exemple : "C5(1,2)")
                if event.startswith("C") and "(" in event and ")" in event:
                    # Si ce n'est pas le premier header, insérer une ligne vide pour séparer
                    if previous_header is not None:
                        text_widget.insert("end", "\n")
                    text_widget.insert("end", event + "\n", "header")
                    previous_header = event
                else:
                    text_widget.insert("end", event + "\n")
        else:
            text_widget.insert("end", "Aucun événement enregistré.\n")

    def sauvegarder_graphe(self):
        """Sauvegarde le graphe actuel dans un fichier JSON, y compris les poids s'il est pondéré.
           En Python, on peut facilement convertir un dictionnaire Python en JSON avec json.dump(), et inversement avec json.load().
        """
        try:
            filepath = filedialog.asksaveasfilename(defaultextension=".json",
                                                    filetypes=[("Fichiers JSON", "*.json")],
                                                    title="Enregistrer le Graphe")
            if not filepath:
                return  # L'utilisateur a annulé

            # Convertir les poids en dictionnaire avec des clés sous forme de chaînes pour la compatibilité JSON
            poids_convertis = {
                f"{src},{dest}": poids
                for (src, dest), poids in self.poids_aretes.items()
            } if hasattr(self, "poids_aretes") and self.poids_aretes else {}

            data = {
                "n": self.sommets_var.get(),
                "S": self.S,
                "sommets_en_panne": list(self.sommets_en_panne),
                "poids_aretes": poids_convertis
            }

            with open(filepath, "w") as f:
                json.dump(data, f, indent=4)

            self.fenetre.after(100, lambda: messagebox.showinfo("Sauvegarde réussie",
                                                                "Le graphe a été sauvegardé avec succès."))

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde : {e}")

    def charger_graphe(self):
        """Charge un graphe depuis un fichier JSON (y compris les poids des arêtes)."""
        try:
            filepath = filedialog.askopenfilename(defaultextension=".json",
                                                  filetypes=[("Fichiers JSON", "*.json")],
                                                  title="Charger un Graphe")
            if not filepath:
                return  # L'utilisateur a annulé

            with open(filepath, "r") as f:
                data = json.load(f)

            n = data.get("n")
            S = data.get("S")
            sommets_en_panne = set(data.get("sommets_en_panne", []))
            poids_str = data.get("poids_aretes", {})

            if not n or not S:
                messagebox.showerror("Erreur", "Le fichier sélectionné est invalide.")
                return

            # Mettre à jour l'interface
            self.sommets_var.set(n)
            self.cordes_var.set(len(S))
            self.mettre_a_jour_curseur_cordes()
            self.mettre_a_jour_S(S)
            self.points, self.aretes = generer_graphe_circulant(n, S)
            self.sommets_en_panne = sommets_en_panne

            # Reconstruction des poids
            self.poids_aretes = {}
            for cle_str, poids in poids_str.items():
                try:
                    a, b = map(int, cle_str.strip("()").split(","))
                    self.poids_aretes[(a, b)] = poids
                except Exception as e:
                    print(f"Erreur lors du traitement du poids {cle_str} : {e}")

            self.mettre_a_jour_cn()
            self.dessiner_graphe(S)
            self.afficher_statistiques()
            self.mettre_a_jour_barres_diametres()

            messagebox.showinfo("Chargement réussi", "Le graphe a été chargé avec succès.")

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement : {e}")

    def afficher_notification(self, titre, message):
        popup = tk.Toplevel(self.fenetre)
        popup.title(titre)
        popup.geometry("300x100")
        popup.configure(bg="#aed9ee")
        label = tk.Label(popup, text=message, font=("Arial", 12), bg="#aed9ee")
        label.pack(expand=True, fill="both", padx=10, pady=10)
        # Fermeture automatique après 2 secondes
        popup.after(2000, popup.destroy)

    def afficher_statistiques(self):
        # Nettoyer les anciennes stats dessinées
        self.canevas.delete("stats")

        total_sommets = self.sommets_var.get()
        sommets_actifs = [i for i in range(total_sommets) if i not in self.sommets_en_panne]
        sommets_en_panne = list(self.sommets_en_panne)

        graphe = construire_liste_adjacence(total_sommets, self.aretes)
        graphe = {
            sommet: [voisin for voisin in voisins if voisin in sommets_actifs]
            for sommet, voisins in graphe.items() if sommet in sommets_actifs
        }

        aretes_actives = sum(len(voisins) for voisins in graphe.values()) // 2
        connexe = est_connexe(graphe)

        is_pondere = bool(getattr(self, "poids_aretes", {})) and all(
            isinstance(p, (int, float)) for p in self.poids_aretes.values()
        )

        if connexe and sommets_actifs:
            if is_pondere:
                from collections import defaultdict

                graphe_pondere = defaultdict(list)
                for (u, v), poids in self.poids_aretes.items():
                    if u in sommets_actifs and v in sommets_actifs:
                        graphe_pondere[u].append((v, poids))
                        graphe_pondere[v].append((u, poids))  # si non orienté

                diametre, _ = calculer_diametre_pondere(graphe_pondere)
            else:
                from .diametre import calculer_diametre
                diametre, _ = calculer_diametre(graphe)
        else:
            diametre = "Infini (non connexe)"

        # Dimensions du canevas
        cw = self.canevas.winfo_width()
        ch = self.canevas.winfo_height()

        # --- Premier carré : Paramètres du graphe ---
        if cw <= 1300:
            x1, y1, x2, y2 = 738, 340, 1065, 580
        else:
            x1 = 810
            x2 = 1285
            y1 = 115
            y2 = 260

        r = 50
        shadow_offset = 6

        # Ombre
        create_rounded_rect(self.canevas, x1 + shadow_offset, y1 + shadow_offset,
                            x2 + shadow_offset, y2 + shadow_offset,
                            r=r, fill="#bfdbea", outline="", tags="stats")

        # Rectangle principal "Paramètres"
        create_rounded_rect(self.canevas, x1, y1, x2, y2,
                            r=r, fill="#e8f8ff", outline="", tags="stats")

        centre_texte = (x1 + x2) // 2
        self.canevas.create_text(centre_texte, y1 + 25, text="Informations sur le graphe",
                                 font=("Arial", 18, "bold"),
                                 fill="#3c5e6e", tags="stats")

        texte_stats = f"Ordre : {len(sommets_actifs)}    Taille : {aretes_actives}    Diamètre : {diametre}"

        if cw <= 1300:
            y_position = 410
        else:
            y_position = 185

        self.canevas.create_text(centre_texte, y_position, text=texte_stats,
                                 font=("Arial", 12, "bold"), fill="#3c5e6e", tags="stats")

        y_position += 30

        # Texte pondéré
        couleur_pondere = "#ee6c34" if is_pondere else "#37add2"
        texte_pondere = "Pondéré" if is_pondere else "Non pondéré"

        # Texte connexité
        couleur_connexite = "green" if connexe else "red"
        texte_connexite = f"Connexité : {'Oui ✅' if connexe else 'Non ❌'}"

        # Largeur approximative des textes (en pixels), à ajuster si besoin
        # Ici on prend une estimation grossière, sinon tu peux mesurer précisément avec font metrics

        largeur_pondere = len(texte_pondere) * 8
        largeur_connexite = len(texte_connexite) * 8
        if is_pondere:
            espacement = 70
        else:
            espacement = 50

        # Position horizontale de départ pour centrer les deux textes ensemble
        x_pondere = centre_texte - (largeur_pondere + largeur_connexite + espacement) // 2
        x_connexite = x_pondere + largeur_pondere + espacement

        # Affichage pondéré
        self.canevas.create_text(
            x_pondere + 60, y_position + 10,
            text=texte_pondere,
            font=("Arial", 12, "bold"),
            fill=couleur_pondere,
            tags="stats"
        )

        # Affichage connexité
        self.canevas.create_text(
            x_connexite + 60, y_position + 10,
            text=texte_connexite,
            font=("Arial", 12, "bold"),
            fill=couleur_connexite,
            tags="stats"
        )

    def ajouter_sommet(self):
        """
        Lorsque le bouton "Ajouter sommet" est cliqué,
        incrémente le nombre de sommets et met à jour le graphe.
        Si le graphe était pondéré, seules les arêtes incidentes
        au nouveau sommet recevront un poids par défaut de 1.
        Si le graphe n'était pas pondéré, la pondération n'est pas modifiée.
        """
        # Conserver l'ancien nombre de sommets et incrémenter de 1
        old_n = self.sommets_var.get()
        new_n = old_n + 1
        self.sommets_var.set(new_n)

        # Déterminer si le graphe était pondéré
        graph = bool(self.poids_aretes)  # True si self.poids_aretes non vide

        # Conserver une copie des anciens poids seulement si le graphe était pondéré
        old_poids = self.poids_aretes.copy() if graph else {}

        # Si on est en mode automatique pour S, recalculer S ; sinon, ne rien modifier (pour conserver par exemple [2,4])
        if not getattr(self, "S_manuelle", False):
            self.S = list(range(1, self.cordes_var.get() + 1))
        # Sinon, en mode manuel, self.S reste tel quel.

        # Mettre à jour les curseurs et l'affichage du graphe
        self.mettre_a_jour_curseur_cordes()
        self.mettre_a_jour_graphe()

        # Si le graphe était précédemment pondéré, reconstruire le dictionnaire des poids
        if graph:
            new_poids = {}
            new_sommet = new_n - 1  # On suppose une numérotation de 0 à new_n-1
            for edge in self.aretes:
                if edge in old_poids:
                    # L'arête existait déjà, on conserve son poids
                    new_poids[edge] = old_poids[edge]
                elif new_sommet in edge:
                    # C'est une nouvelle arête incidente au sommet ajouté, on l'initialise avec le poids 1
                    new_poids[edge] = 1
            self.poids_aretes = new_poids
        else:
            # Le graphe n'était pas pondéré, on s'assure que le dictionnaire reste vide.
            self.poids_aretes = {}

        # Actualiser l'affichage du graphe, les statistiques et autres indicateurs
        self.afficher_statistiques()
        self.mettre_a_jour_cn()
        self.mettre_a_jour_barres_diametres()

    @staticmethod
    def couper_texte_ligne_automatique(texte, longueur_max=40):
        """
        Coupe une chaîne de caractères trop longue en plusieurs lignes de longueur maximale.
        """
        lignes = []
        ligne = ""
        for mot in texte.split():
            if len(ligne) + len(mot) + 1 <= longueur_max:
                ligne += (mot + " ")
            else:
                lignes.append(ligne.strip())
                ligne = mot + " "
        if ligne:
            lignes.append(ligne.strip())
        return lignes

    def reinitialiser_graphe(self):
        """Réinitialise les sommets en panne s'ils existent, sinon réinitialise uniquement les arêtes."""

        if not self.sommets_en_panne:
            # Aucun sommet en panne -> Réinitialiser uniquement les arêtes
            self.reinitialiser_arretes()
            # self.label_message.config(text="Les arêtes ont été réinitialisées.")
            # self.fenetre.after(3000, lambda: self.label_message.config(text=""))
            return

        # Afficher Cn(S)
        current_header = self.header_graphe()
        if self.last_header != current_header:
            self.historique_pannes.append(current_header)
            self.last_header = current_header

        # Si des sommets sont en panne, on fait l'animation de réparation
        sommets_a_reparer = list(self.sommets_en_panne)
        clignotements = 4
        delai = 150  # en millisecondes

        def clignoter(etape):
            # Alterne entre deux couleurs pour créer l'effet de clignotement
            couleur = "#ffaf75" if etape % 2 == 0 else "#ebebeb"

            # Animation sur chaque sommet en panne
            for sommet in sommets_a_reparer:
                x, y = self.points[sommet]
                self.canevas.create_oval(x - 12, y - 12, x + 12, y + 12,
                                         fill=couleur, outline="black", tags="graph")
                self.canevas.create_text(x, y, text=str(sommet),
                                         font=("Arial", 12, "bold"), fill="black", tags="graph")

            if etape < clignotements:
                self.fenetre.after(delai, lambda: clignoter(etape + 1))
            else:
                # Ajout de l'historique des réparations
                heure = time.strftime('%H:%M:%S')
                date = time.strftime('%d/%m/%Y')
                for sommet in sommets_a_reparer:
                    self.historique_pannes.append(f"{date} - {heure} : Sommet {sommet} réparé.")

                # Vider la liste des pannes – tous les sommets passent à l'état actif
                self.sommets_en_panne.clear()

                # Réinitialiser les arêtes après la réinitialisation des sommets
                self.reinitialiser_arretes()

                # Effacer totalement le canevas et redessiner le graphe en mode normal
                self.canevas.delete("graph")
                self.dessiner_graphe("")
                self.afficher_statistiques()
                self.mettre_a_jour_barres_diametres()

                # self.label_message.config(text="Tous les sommets et arêtes ont été réinitialisés.")
                # self.fenetre.after(3000, lambda: self.label_message.config(text=""))

        clignoter(0)

    def reinitialiser_arretes(self):
        """
        Réinitialise la couleur de toutes les arêtes (lines) déjà dessinées,
        en forçant leur couleur à "gray". Puis redessine tous les sommets.
        """
        # Itérer sur tous les items du canevas ayant le tag "graph"
        items = self.canevas.find_withtag("graph")
        for item in items:
            # Vérifier si l'élément est une ligne (donc une arête)
            if self.canevas.type(item) == "line":
                # Mettre à jour la couleur de l'arête pour qu'elle soit grise
                self.canevas.itemconfig(item, fill="gray")

        # Dans le cas où des arêtes rouges persistent par ailleurs via une structure dédiée,
        # on s'assure de réinitialiser l'attribut associé.
        if hasattr(self, 'aretes_rouges'):
            self.aretes_rouges = []  # On vide la liste

        # Redessiner tous les sommets pour être sûr qu'ils soient affichés correctement.
        for i, (x, y) in enumerate(self.points):
            couleur = "#AED9EF"  # Couleur par défaut pour un sommet actif
            texte_couleur = "black"
            # Si pour une raison i est toujours dans l'ensemble de panne, on peut ajuster (même si normalement, la liste est vidée)
            if i in self.sommets_en_panne:
                couleur = "#ebebeb"
                texte_couleur = "gray"
            self.canevas.create_oval(x - 10, y - 10, x + 10, y + 10,
                                     fill=couleur, outline="black", tags="graph")
            self.canevas.create_text(x, y, text=str(i),
                                     font=("Arial", 12, "bold"), fill=texte_couleur, tags="graph")

    # Fonction pour mettre à jour le graphe à chaque changement des curseurs
    def mettre_a_jour_graphe(self, event=None):
        """
        Reconstruit le graphe circulant en fonction du nombre de sommets (n) et
        de la liste S, en gérant le mode manuel pour S.

        Si le paramètre event est fourni, on repasse en mode automatique pour S.
        Si le graphe (n ou S) a changé depuis la dernière mise à jour, on
        répare les sommets en panne et on met à jour l'affichage.
        """
        self.poids_aretes = {}
        n = self.sommets_var.get()

        # Si l'événement est présent, forcer le passage en mode automatique
        if event is not None:
            self.S_manuelle = False

        # Respecter le mode manuel ou automatique pour S
        if getattr(self, 'S_manuelle', False):
            S = self.S
        else:
            S = list(range(1, self.cordes_var.get() + 1))
            self.S = S.copy()

        # Vérifier si le graphe a changé (nombre de sommets ou S différent)
        graphe_change = (getattr(self, 'dernier_n', None) != n) or (getattr(self, 'dernier_S', None) != S)

        if graphe_change:
            # Si le graphe change, considérer que tous les sommets en panne se réparent
            if self.sommets_en_panne:
                heure = time.strftime('%H:%M:%S')
                date = time.strftime('%d/%m/%Y')

                # Afficher Cn(S)
                current_header = self.header_graphe()
                if self.last_header != current_header:
                    self.historique_pannes.append(current_header)
                    self.last_header = current_header

                for sommet in self.sommets_en_panne.copy():
                    self.historique_pannes.append(
                        f"{date} - {heure} : Sommet {sommet} réparé suite à la mise à jour du graphe.")
                self.sommets_en_panne.clear()

            self.dernier_n = n
            self.dernier_S = S.copy()

        # Générer le graphe circulant en fonction de n et S
        self.points, self.aretes = generer_graphe_circulant(n, S)

        # Supprimer l'ancien dessin identifié par le tag "graph"
        self.canevas.delete("graph")

        # Redessiner le graphe (vous devez implémenter dessiner_graphe de sorte qu'il attribue le tag "graph")
        self.dessiner_graphe("")

        # Mettre à jour d'autres indicateurs (exemple: connectivité)
        self.mettre_a_jour_cn()

        self.mettre_a_jour_barres_diametres()

    # Fonction pour dessiner le graphe sur le canevas

    def dessiner_graphe(self, S):
        self.canevas.delete("diametre")
        self.canevas.delete("graph")

        # Dessiner les arêtes
        for src, dest in self.aretes:  # Liste des arêtes [(0,1), (1,2), ...]
            if src in self.sommets_en_panne or dest in self.sommets_en_panne:
                couleur = "#ebebeb"  # Gris pour les arêtes connectées à un sommet en panne
            else:
                couleur = "gray"  # Couleur normale des arêtes
            x1, y1 = self.points[src]
            x2, y2 = self.points[dest]
            self.canevas.create_line(x1, y1, x2, y2, fill=couleur, width=2, tags="graph")

        # Dessiner les sommets
        for i, (x, y) in enumerate(self.points):
            if i in self.sommets_en_panne:
                couleur = "#ebebeb"
                texte_couleur = "gray"  # Couleur du texte pour les sommets en panne
                self.canevas.create_oval(x - 10, y - 10, x + 10, y + 10, fill=couleur, outline="gray", tags="graph")
            else:
                couleur = "#AED9EF"  # Couleur normale des sommets
                texte_couleur = "black"  # Couleur normale du texte
                self.canevas.create_oval(x - 10, y - 10, x + 10, y + 10, fill=couleur, outline="black", tags="graph")
            self.canevas.create_text(x, y, text=str(i), font=("Arial", 12, "bold"), fill=texte_couleur, tags="graph")

        # Mettre à jour la notation Cn(S)
        if S == "":
            self.mettre_a_jour_cn()
        else:
            self.mettre_a_jour_cn2(S)

    def calculer_max_cordes(self, n):
        if n % 2 == 0:
            return max(1, (n // 2) - 1)
        else:
            return max(1, n // 2)

    """
    n=8 ===> max_cordes=3
    n=9 ===> max_cordes=4
    """

    def mise_a_jour_sommets(self, event=None):
        """
        Met à jour le nombre de sommets à partir du slider, ajuste le curseur des cordes,
        passe en mode automatique pour S (si ce n'est pas en mode manuel), et actualise le graphe et l'affichage.
        """
        # Mettre à jour la variable de sommets à partir du slider
        self.sommets_var.set(int(float(self.sommets_slider.get())))

        # Actualiser le curseur des cordes en fonction du nouveau nombre de sommets
        self.mettre_a_jour_curseur_cordes()

        # Si S a été défini manuellement auparavant
        if getattr(self, "S_manuelle", False):
            # Si l'utilisateur modifie les sommets, on sort du mode manuel et fixe S = [1, 2]
            self.S_manuelle = False
            self.S = [1, 2]
            self.cordes_var.set(len(self.S))
            self.label_cordes.configure(text=f"Cordes : {len(self.S)}")

        # Mode automatique pour S (si non manuel)
        if not getattr(self, "S_manuelle", False):
            self.S = list(range(1, self.cordes_var.get() + 1))

        # Actualisation du graphe et de ses indicateurs complémentaires
        self.mettre_a_jour_graphe()
        self.afficher_statistiques()
        self.mettre_a_jour_cn()
        self.mettre_a_jour_barres_diametres()

        # Mettre à jour le label d'affichage du nombre de sommets
        self.label_sommets.configure(text=f"Sommets : {self.sommets_var.get()}")

    def mise_a_jour_cordes(self, value):
        """
        Met à jour le nombre de cordes à partir du slider, repasse en mode automatique pour S,
        et actualise le graphe ainsi que la notation associée.
        """
        # Mettre à jour la variable liée au slider de cordes
        self.cordes_var.set(int(float(value)))

        # Repasse en mode automatique pour S
        self.S_manuelle = False

        # Actualise S en fonction de la valeur du slider
        self.S = list(range(1, self.cordes_var.get() + 1))

        # Actualiser le graphe et la notation complémentaire (ex: connectivité)
        self.mettre_a_jour_graphe()
        self.mettre_a_jour_cn()
        self.afficher_statistiques()
        self.mettre_a_jour_barres_diametres()

        # Mettre à jour le label affichant le nombre de cordes
        self.label_cordes.configure(text=f"Cordes : {int(self.cordes_var.get())}")

    def mettre_a_jour_curseur_cordes(self):
        """
        Calcule et ajuste le curseur des cordes en fonction du nombre de sommets.
        Désactive le slider si le nombre maximal de cordes autorisées est 1.
        """
        # Calcul du maximum de cordes autorisé
        max_cordes = self.calculer_max_cordes(self.sommets_var.get())

        # S'assurer que la valeur actuelle du curseur est dans la plage autorisée
        valeur_actuelle = self.cordes_var.get()
        if valeur_actuelle > max_cordes:
            valeur_actuelle = max_cordes
            self.cordes_var.set(valeur_actuelle)
        elif valeur_actuelle < 1:
            valeur_actuelle = 1
            self.cordes_var.set(valeur_actuelle)

        if max_cordes == 1:
            # Si le max est 1, désactiver le slider et fixer la valeur
            self.cordes_slider.configure(state="disabled")
            self.label_cordes.configure(text="Cordes : 1")
        else:
            self.cordes_slider.configure(
                state="normal",
                to=max_cordes,
                from_=1,
                number_of_steps=max_cordes - 1
            )
            self.cordes_slider.set(valeur_actuelle)
            self.label_cordes.configure(text=f"Cordes : {valeur_actuelle}")

    def mettre_a_jour_label_sommets(self):
        """
        Met à jour le label affichant le nombre de sommets.
        """
        self.label_sommets.configure(text=f"Sommets : {self.sommets_var.get()}")

    def redimensionner_graphe(self, event):

        # Dimensions actuelles de la fenêtre
        largeur = event.width
        hauteur = event.height

        # Supprimer label_cn temporairement
        self.label_cn.place_forget()

        if largeur <= 1300:
            centre_x = 280
            centre_y = 420
            rayon = 245
        else:
            centre_x = 450
            centre_y = 400
            rayon = 310

        # Mise à jour des dimensions dans votre fonction set_dimensions
        set_dimensions(centre_x, centre_y, rayon)

        # Recalculer le graphe
        n = self.sommets_var.get()
        if getattr(self, 'S_manuelle', False):
            S = self.S
        else:
            S = list(range(1, self.cordes_var.get() + 1))
        self.points, self.aretes = generer_graphe_circulant(n, S)

        # Redessiner le graphe avec, par exemple, la liste S comme paramètre (selon votre implémentation)
        self.dessiner_graphe(S)
        # Attendre 100ms après le dessin du graphe pour afficher Cn
        self.fenetre.after(10, lambda: self.afficher_label_cn(largeur))
        self.afficher_statistiques()
        self.mettre_a_jour_barres_diametres()

    def afficher_label_cn(self, largeur):
        if largeur <= 1300:
            self.label_cn.place(x=230, y=85, width=200, height=100)
            self.label_cn.config(wraplength=200)
        else:
            self.label_cn.place(x=220, y=100, width=190, height=100)
            self.label_cn.config(wraplength=190)

    def redimensionner_fenetre(self, event):
        largeur = self.fenetre.winfo_width()

        if largeur <= 1300:
            self.label_sommets.place(x=255, y=670)
            self.sommets_slider.place(x=250, y=700)
            self.label_cordes.place(x=775, y=670)
            self.cordes_slider.place(x=760, y=700)
            # Placement des images
            self.canevas.coords(self.image_id_1, 165.0, 40.0)
            self.canevas.coords(self.image_id_21, 540.0, 40.0)

            self.frame_graphique_diam.place(x=555, y=400, width=450, height=200)

        else:
            self.label_sommets.place(x=335, y=725)
            self.sommets_slider.place(x=330, y=755)
            self.label_cordes.place(x=675, y=725)
            self.cordes_slider.place(x=670, y=755)
            self.canevas.coords(self.image_id_1, 265.0, 37.0)
            self.canevas.coords(self.image_id_21, 640.0, 37.0)

            self.frame_graphique_diam.place(x=820, y=290, width=470, height=473)

        # Mise à jour graphique
        self.redimensionner_graphe(event)

        # Empêche les appels multiples en rafale
        if hasattr(self, "_resize_job"):
            self.fenetre.after_cancel(self._resize_job)

        self._resize_job = self.fenetre.after(100, self._do_resize_update)

    def _do_resize_update(self):
        # Met à jour les éléments du menu après le redimensionnement
        self.sidebar.update_idletasks()
        for item in self.sidebar.menu_items:
            item.draw_background()
            item.update_idletasks()

    def afficher_diametre_circulant(self):
        """Affiche le diamètre du graphe circulant selon différentes méthodes."""

        # Bloquer si des sommets sont en panne
        if self.sommets_en_panne:
            panne_str = ", ".join(map(str, sorted(self.sommets_en_panne)))
            messagebox.showwarning("Calcul désactivé",
                                   f"Le calcul du diamètre est désactivé car les sommets suivants sont en panne : {panne_str}")
            return
        try:
            n = self.sommets_var.get()
            if getattr(self, 'S_manuelle', False):
                S = self.S
            else:
                S = list(range(1, self.cordes_var.get() + 1))

            if len(S) == 2 and S[0] == 1:
                s = S[1]
                d = diam(n, s)
                messagebox.showinfo("Diamètre (Optimisé)", f"Diamètre de C{n}(1,{s}) : {d}")
            else:
                messagebox.showwarning("Non applicable", "Cette méthode est uniquement pour Cn(1,s)")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur : {e}")

    def creer_zone_graphique_diametres(self):
        """Créer un frame dédié au graphique et le placer dans l'interface (ex: à droite ou en bas)."""
        # Créer un frame (si pas déjà créé)
        if hasattr(self, 'frame_graphique_diam'):
            self.frame_graphique_diam.destroy()  # Détruire l'ancien s'il existe

        self.frame_graphique_diam = tk.Frame(self.main_frame, bg="#e8f8ff", bd=0, relief="flat",
                                             highlightbackground="#6ea8c9", highlightthickness=1)
        self.frame_graphique_diam.pack(side="bottom", fill="both", expand=True, padx=5, pady=5)

    def initialiser_graphique_diametres(self):
        """Initialise le graphique (axes) et effectue le premier calcul."""
        self.calculer_diametres_et_temps()

        fig = Figure(figsize=(6, 3))
        fig.subplots_adjust(right=0.82)
        fig.patch.set_facecolor("#e8f8ff")  # Fond clair pour la figure

        self.ax1 = fig.add_subplot(111)
        self.ax2 = self.ax1.twinx()

        self.canvas_graph_diam = FigureCanvasTkAgg(fig, master=self.frame_graphique_diam)
        self.canvas_graph_diam.draw()

        # Fond du widget contenant le graphique
        self.canvas_graph_diam.get_tk_widget().config(bg="#e8f8ff", highlightthickness=0, bd=0)
        self.canvas_graph_diam.get_tk_widget().pack(fill='both', expand=True)

        self.mettre_a_jour_barres_diametres()

    def calculer_diametres_et_temps(self):
        """Calcule les diamètres et les temps des méthodes et met à jour les caches."""
        n = self.sommets_var.get()
        S = self.S if getattr(self, 'S_manuelle', False) else list(range(1, self.cordes_var.get() + 1))

        graphe = construire_liste_adjacence(n, self.aretes)
        graphe = {
            s: [v for v in voisins if v not in self.sommets_en_panne]
            for s, voisins in graphe.items() if s not in self.sommets_en_panne
        }

        # Vérifier si le graphe est pondéré
        is_pondere = bool(self.poids_aretes) and all(
            isinstance(p, (int, float)) for p in self.poids_aretes.values()
        )

        self.diametres_cache = []
        self.temps_cache = []
        self.methodes_cache = []
        self.couleurs_cache = []

        if est_connexe(graphe):
            if is_pondere:
                from collections import defaultdict
                graphe_pondere = defaultdict(list)
                for (u, v), poids in self.poids_aretes.items():
                    if u not in self.sommets_en_panne and v not in self.sommets_en_panne:
                        graphe_pondere[u].append((v, poids))
                        graphe_pondere[v].append((u, poids))  # non orienté

                # ➕ Dijkstra
                t7 = time.perf_counter()
                diametre_max = 0
                for sommet in graphe_pondere:
                    distances, _ = calculer_dijkstra(graphe_pondere, sommet)
                    max_dist = max(distances.values()) if distances else 0
                    diametre_max = max(diametre_max, max_dist)
                t8 = time.perf_counter()

                self.diametres_cache.append(diametre_max)
                self.temps_cache.append(t8 - t7)
                self.methodes_cache.append("Dijkstra")
                self.couleurs_cache.append("#3a3a3a")

                # ➕ Floyd–Warshall
                t_fw0 = time.perf_counter()
                diam_fw, _ = calculer_diametre_floyd(graphe_pondere)
                t_fw1 = time.perf_counter()

                self.diametres_cache.append(diam_fw)
                self.temps_cache.append(t_fw1 - t_fw0)
                self.methodes_cache.append("Floyd–Warshall")
                self.couleurs_cache.append("#3a3a3a")

            else:
                # ➕ BFS (classique)
                t1 = time.perf_counter()
                d_classique, _ = calculer_diametre(graphe)
                t2 = time.perf_counter()

                self.diametres_cache.append(d_classique)
                self.temps_cache.append(t2 - t1)
                self.methodes_cache.append("BFS")
                self.couleurs_cache.append("#3a3a3a")

                # ➕ Formule et nouvelle approche si applicable
                if len(S) == 2 and S[0] == 1 and not self.sommets_en_panne:
                    s = S[1]

                    t3 = time.perf_counter()
                    d_formule, borne = FormulDiam(n, s)
                    t4 = time.perf_counter()
                    self.diametres_cache.append(d_formule)
                    self.temps_cache.append(t4 - t3)
                    self.methodes_cache.append("Borne" if borne else "Formule \n Mathématique")
                    self.couleurs_cache.append("#3a3a3a")

                    t5 = time.perf_counter()
                    d_opt = diam(n, s)
                    t6 = time.perf_counter()
                    self.diametres_cache.append(d_opt)
                    self.temps_cache.append(t6 - t5)
                    self.methodes_cache.append("Nouvelle \n Approche")
                    self.couleurs_cache.append("#3a3a3a")
        else:
            self.diametres_cache = [0, 0, 0]
            self.temps_cache = [0.0, 0.0, 0.0]
            self.methodes_cache = ["BFS", "Formule\nMathématique", "Nouvelle\napproche"]
            self.couleurs_cache = ["#3a3a3a", "#3a3a3a", "#3a3a3a"]

    def mettre_a_jour_barres_diametres(self):
            """Met à jour les barres sans redéfinir les axes."""
            if not hasattr(self, 'ax1') or not hasattr(self, 'ax2'):
                return

            def format_scientifique(val):
                if val < 1e-12:
                    return "0"
                exp = int(f"{val:.0e}".split('e')[1])
                base = val / (10 ** exp)
                if exp == 0:
                    return f"{base:.1f}"
                return r"${:.1f} \times 10^{{{}}}$".format(base, exp)

            def format_scientifique2(val):
                if val < 1e-12:
                    return "0"
                exp = int(f"{val:.0e}".split('e')[1])
                base = val / (10 ** exp)
                if exp == 0:
                    return f"{base:.1f}"
                return r"$\mathbf{{{:.1f} \times 10^{{{}}}}}$".format(base, exp)

            self.ax2.yaxis.set_major_formatter(FuncFormatter(format_scientifique))
            self.ax2.tick_params(axis='y', labelsize=12, labelcolor="black", width=2)

            self.calculer_diametres_et_temps()

            diametres = self.diametres_cache
            temps = self.temps_cache
            methodes = self.methodes_cache
            couleurs = self.couleurs_cache
            x = list(range(len(diametres)))

            self.ax1.cla()
            self.ax2.cla()

            # Axe diamètres
            self.ax1.set_xticks([i + 0.2 for i in x])
            self.ax1.set_xticklabels(methodes, fontsize=10, fontweight='bold')
            # self.ax1.set_ylabel("Diamètre", fontsize=11, fontweight='bold', color="#3a3a3a")
            diam_max = max(diametres)
            self.ax1.set_ylim(0, 15 if diam_max <= 14 else diam_max + 2)
            self.ax1.set_yticks(np.linspace(0, 15 if diam_max <= 14 else diam_max + 2, 16))

            # Axe temps
            # self.ax2.set_ylabel("Temps (s)", fontsize=11, fontweight='bold' , color="#3a3a3a")

            temps_non_nuls = [t for t in temps if t > 0]

            if not temps_non_nuls:
                # Cas où tous les temps sont nuls ou liste vide
                self.ax2.set_yscale("linear")
                self.ax2.set_ylim(0, 1)
                base_ticks = np.linspace(0, 1, 7)
                self.ax2.set_yticks(base_ticks)
                self.ax2.set_yticklabels([format_scientifique(val) for val in base_ticks])
                self.ax2.tick_params(axis='y', which='minor', length=0)
                self.ax2.tick_params(axis='y', which='major', length=6)
            else:
                t_min = min(temps_non_nuls)
                t_max = max(temps_non_nuls)
                if t_min <= 0:
                    # Si jamais il y a un temps nul ou négatif, on force l'échelle linéaire
                    self.ax2.set_yscale("linear")
                    self.ax2.set_ylim(0, 1e-2)
                    fixed_ticks = [0, 1e-6, 1e-5, 1e-4, 1e-3, 1e-2]
                    self.ax2.set_yticks(fixed_ticks)
                    self.ax2.set_yticklabels([format_scientifique(val) for val in fixed_ticks])
                    self.ax2.tick_params(axis='y', which='minor', length=0)
                    self.ax2.tick_params(axis='y', which='major', length=6)
                else:
                    self.ax2.set_yscale("log")

                    seuil_fixe = 1.6e-2
                    if t_max <= seuil_fixe:
                        self.ax2.set_ylim(t_min / 10, seuil_fixe)
                        base_ticks = np.logspace(np.floor(np.log10(t_min / 10)), np.log10(seuil_fixe), num=6)
                    else:
                        self.ax2.set_ylim(t_min / 10, t_max * 10)
                        base_ticks = np.logspace(np.floor(np.log10(t_min / 10)), np.ceil(np.log10(t_max * 10)), num=6)

                    self.ax2.set_yticks(base_ticks)
                    self.ax2.set_yticklabels([format_scientifique(val) for val in base_ticks])
                    self.ax2.tick_params(axis='y', which='minor', length=0)
                    self.ax2.tick_params(axis='y', which='major', length=6)

            # Barres
            x = [i for i in range(len(diametres))]
            bar_width_diam = 0.3
            bar_width_temps = 0.2

            bars1 = self.ax1.bar(
                [i - bar_width_diam / 2 for i in x],
                diametres,
                width=bar_width_diam,
                color=couleurs,
                label="Diamètre"

            )

            bars2 = self.ax2.bar(
                [i + bar_width_diam / 2 for i in x],
                temps,
                width=bar_width_temps,
                color=couleurs,
                alpha=0.7,
                label="Temps (s)"
            )

            # Fixer les ticks correctement
            self.ax1.set_xticks(x)
            self.ax1.set_xticklabels(methodes, fontsize=10, fontweight='bold')

            # 🔒 Fixer les limites X pour éviter l'étalement quand 1 seule barre
            padding = 0.5  # espace avant/après
            if len(x) == 1:
                self.ax1.set_xlim(x[0] - padding, x[0] + padding)
                self.ax2.set_xlim(x[0] - padding, x[0] + padding)
            else:
                self.ax1.set_xlim(min(x) - 0.5, max(x) + 0.5)
                self.ax2.set_xlim(min(x) - 0.5, max(x) + 0.5)

            couleurs_pastelF = ["#dbd3e9"]
            for i, bar in enumerate(bars1):
                bar.set_edgecolor('#e8f8ff')
                bar.set_linewidth(2)
                bar.set_alpha(0.95)
                bar.set_color(couleurs_pastelF[i % len(couleurs_pastelF)])
                # Arrondi visuel (effet)
                bar.set_zorder(3)
                h = bar.get_height()
                self.ax1.text(bar.get_x() + bar.get_width() / 2., h + 0.2, f'{int(h)}',
                            ha='center', va='bottom', fontsize=9, fontweight='bold', color='#3a3a3a',
                            fontfamily='Segoe UI')

            couleurs_pastel = ["#cae2c2"]
            for i, bar in enumerate(bars2):
                bar.set_edgecolor('#e8f8ff')
                bar.set_linewidth(2)
                bar.set_alpha(0.8)
                bar.set_color(couleurs_pastel[i % len(couleurs_pastel)])
                bar.set_zorder(3)
                h = bar.get_height()
                self.ax2.text(bar.get_x() + bar.get_width() / 2., h + h * 0.05, format_scientifique2(temps[i]),
                            ha='center', va='bottom', fontsize=9, color='#3a3a3a', fontfamily='Segoe UI')

            self.ax1.set_xticks(x)
            self.ax1.set_xticklabels(methodes, fontsize=12, fontweight='bold', fontfamily='Segoe UI')
            for ticklabel, color in zip(self.ax1.get_xticklabels(), couleurs):
                ticklabel.set_color(color)
            # Grille légère
            self.ax1.grid(axis='y', linestyle='--', linewidth=0.7, color='#aed0e2', alpha=0.5, zorder=0)
            self.ax2.grid(False)  # Pas de grille sur l'axe secondaire

            # Style axes
            # Axes fins et sobres
            for ax in [self.ax1, self.ax2]:
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(1)
                ax.spines['left'].set_linewidth(1)
                ax.spines['bottom'].set_linewidth(1)
                ax.spines['right'].set_color('#9dbdce')
                ax.spines['left'].set_color('#9dbdce')
                ax.spines['bottom'].set_color('#9dbdce')

            self.ax1.tick_params(axis='y', labelsize=8)
            self.ax2.tick_params(axis='y', labelsize=8)
            self.ax1.legend(loc='upper left', fontsize=8,  bbox_to_anchor=(-0.11, 1.10), ncol=2)
            self.ax2.legend(loc='upper right', fontsize=8, bbox_to_anchor=(1.22, 1.10), ncol=2)

            self.ax2.yaxis.set_label_position("right")
            self.ax2.yaxis.tick_right()
            self.ax1.set_facecolor('#f4fcff')
            self.ax2.set_facecolor('#f4fcff')
            # Ajout du titre selon connexité
            n = self.sommets_var.get()
            S = self.S if getattr(self, 'S_manuelle', False) else list(range(1, self.cordes_var.get() + 1))
            graphe = construire_liste_adjacence(n, self.aretes)
            graphe = {
                s: [v for v in voisins if v not in self.sommets_en_panne]
                for s, voisins in graphe.items() if s not in self.sommets_en_panne
            }
            if est_connexe(graphe):
                self.ax1.set_title(
                    "     Comparaison des temps d'exécution des méthodes \nde calcul du diamètre",
                    fontsize=14,
                    fontweight='semibold',
                    fontstyle='italic',
                    color='#3c5e6e',
                    loc='center',
                    pad=15,
                    fontfamily='Calibri'
                )
            else:
                self.ax1.cla()
                self.ax2.cla()

                x = list(range(len(self.methodes_cache)))
                self.ax1.set_xticks(x)
                self.ax1.set_xticklabels(self.methodes_cache, fontsize=12, fontweight='bold', fontfamily='Segoe UI')
                self.ax1.set_ylim(0, 15)
                self.ax1.set_yticks(np.linspace(0, 15, 16))
                self.ax1.grid(axis='y', linestyle='--', linewidth=0.7, color='#aed0e2', alpha=0.5, zorder=0)

                self.ax2.set_ylim(0, 1)
                self.ax2.set_xticks(x)
                self.ax2.set_xticklabels(self.methodes_cache, fontsize=10, fontweight='bold', fontfamily='Segoe UI')

                # Fond propre
                self.ax1.set_facecolor('#f4fcff')
                self.ax2.set_facecolor('#f4fcff')



                # Couleurs cohérentes
                couleur_diametre = "#dbd3e9"
                couleur_temps = "#cae2c2"

                # Création manuelle des carrés de légende
                legende_diametre = Patch(facecolor=couleur_diametre, edgecolor='none', label="Diamètre")
                legende_temps = Patch(facecolor=couleur_temps, edgecolor='none', label="Temps (s)")

                # Affichage manuel des légendes

                self.ax1.legend(handles=[legende_diametre], loc='upper left', fontsize=8, bbox_to_anchor=(-0.11, 1.10), ncol=2)
                self.ax2.legend(handles=[legende_temps], loc='upper right', fontsize=8, bbox_to_anchor=(1.22, 1.10), ncol=2)
                # Grille propre
                self.ax1.spines['top'].set_visible(False)
                self.ax1.spines['right'].set_linewidth(1)
                self.ax2.spines['top'].set_visible(False)
                self.ax2.spines['right'].set_linewidth(1)

                # ✅ Message au centre
                self.ax1.set_title(
                    "Le graphe n'est pas connexe",
                    fontsize=14,
                    fontweight='bold',
                    fontstyle='italic',
                    color='red',
                    loc='center',
                    pad=18,
                    fontfamily='Calibri'
                )

                self.canvas_graph_diam.draw()
                return

            self.canvas_graph_diam.draw()


# interface.py
def lancer_interface():
    import tkinter as tk
    fenetre = tk.Tk()
    app = GraphC(fenetre)
    fenetre.mainloop()






