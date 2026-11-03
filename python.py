import os
import logging
import sqlite3
from abc import ABC, abstractmethod
from contextlib import closing
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
from typing import ClassVar

app = FastAPI()
logger = logging.getLogger(__name__)


class User(BaseModel):
    ID: int
    Nom: str
    Prénom: str
    Email: str
    Téléphone: str
    Adresse: str
    Mot_de_passe_haché: str 

    PAGE_SIZE: ClassVar[int] = 51


class UserCreate(BaseModel):
    """Champs envoyés pour créer un utilisateur ; SQLite génère son ID."""

    Nom: str
    Prénom: str
    Email: str
    Téléphone: str
    Adresse: str
    Mot_de_passe_haché: str


class UserPublic(BaseModel):
    """Informations d'utilisateur renvoyées par l'API, sans le mot de passe haché."""

    ID: int
    Nom: str
    Prénom: str
    Email: str
    Téléphone: str
    Adresse: str


@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!doctype html>
    <html lang="fr">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Gestion des utilisateurs</title>
      </head>
      <body>
        <main>
          <h1>Gestion des utilisateurs</h1>
          <p>Bienvenue sur l’application de gestion des utilisateurs.</p>
        </main>
      </body>
    </html>
    """


class UserManager:
    def __init__(self, db_path: str):
        self.db_path = db_path

        # SQLite crée le fichier de base de données s'il n'existe pas.
        with closing(sqlite3.connect(self.db_path)) as connection:
            with connection:
                connection.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY,
                        nom TEXT NOT NULL,
                        prenom TEXT NOT NULL,
                        email TEXT NOT NULL,
                        telephone TEXT NOT NULL,
                        adresse TEXT NOT NULL,
                        mot_de_passe_hache TEXT NOT NULL
                    )
                """)
        logger.info("Base SQLite initialisee : %s", self.db_path)

    def read_users(self) -> list[User]:
        # Les colonnes SQL sont converties vers les noms attendus par le modèle User.
        with closing(sqlite3.connect(self.db_path)) as connection:
            rows = connection.execute("""
                SELECT id, nom, prenom, email, telephone, adresse, mot_de_passe_hache
                FROM users
                ORDER BY id
            """).fetchall()

        logger.info("Lecture SQLite terminee : %s utilisateur(s).", len(rows))
        return [
            User(
                ID=row[0],
                Nom=row[1],
                Prénom=row[2],
                Email=row[3],
                Téléphone=row[4],
                Adresse=row[5],
                Mot_de_passe_haché=row[6],
            )
            for row in rows
        ]

    def add_user(self, user: UserCreate) -> User:
        # Les ? transmettent les valeurs séparément, sans les concaténer au SQL.
        with closing(sqlite3.connect(self.db_path)) as connection:
            with connection:
                cursor = connection.execute("""
                    INSERT INTO users
                        (nom, prenom, email, telephone, adresse, mot_de_passe_hache)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    user.Nom,
                    user.Prénom,
                    user.Email,
                    user.Téléphone,
                    user.Adresse,
                    user.Mot_de_passe_haché,
                ))
                new_id = cursor.lastrowid

        logger.info("Utilisateur ajoute dans SQLite avec l'ID %s.", new_id)
        return User(ID=new_id, **user.model_dump())


# La base est placée à côté de ce fichier Python.
user_manager = UserManager(os.path.join(os.path.dirname(__file__), "users.db"))


@app.get("/users", response_model=list[UserPublic])
def get_users() -> list[UserPublic]:
    """Renvoie la liste des utilisateurs enregistrés dans SQLite."""
    return [
        UserPublic(
            ID=user.ID,
            Nom=user.Nom,
            Prénom=user.Prénom,
            Email=user.Email,
            Téléphone=user.Téléphone,
            Adresse=user.Adresse,
        )
        for user in user_manager.read_users()
    ]


@app.post("/users", response_model=UserPublic, status_code=201)
def create_user(user: UserCreate) -> UserPublic:
    """Enregistre un utilisateur ; SQLite génère son identifiant."""
    saved_user = user_manager.add_user(user)
    return UserPublic(
        ID=saved_user.ID,
        Nom=saved_user.Nom,
        Prénom=saved_user.Prénom,
        Email=saved_user.Email,
        Téléphone=saved_user.Téléphone,
        Adresse=saved_user.Adresse,
    )


class afichage(ABC):
    def __init__(self, largeur: int, hauteur: int):
        self.largeur = largeur
        self.hauteur = hauteur

    @property
    @abstractmethod
    def dimensions(self) -> tuple[int, int]:
        """Retourne les dimensions de l'affichage."""
        return (self.largeur, self.hauteur)

    @abstractmethod
    def render(self) -> str:
        """Génère le HTML de rendu de l'affichage."""
        return (
            "<section style='width:{width}px; height:{height}px; "
            "display:flex; align-items:center; justify-content:center; "
            "border:1px solid #d0d7de; box-sizing:border-box; background:#f6f8fa; "
            "font-family:Arial,sans-serif; color:#24292f;'>"
            "<strong>Affichage {width}x{height}</strong>"
            "</section>".format(width=self.largeur, height=self.hauteur)
        )

    @abstractmethod
    def to_dict(self) -> dict[str, int]:
        """Retourne les informations de l'affichage dans un dictionnaire."""
        return {"largeur": self.largeur, "hauteur": self.hauteur}
 