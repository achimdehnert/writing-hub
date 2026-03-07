"""
Worlds App — writing-hub

Welten und Charaktere werden über iil-weltenfw (WeltenHub REST Client) verwaltet.
Kein Django-ORM für Welten/Charaktere — weltenfw ist die SSoT.

Verwendung:
    from weltenfw.django import get_client

    client = get_client()  # lazy singleton per Worker
    worlds = list(client.worlds.iter_all())
    chars  = list(client.characters.iter_all())

Dokumentation: https://pypi.org/project/iil-weltenfw/
"""
