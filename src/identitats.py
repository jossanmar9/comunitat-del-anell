# SPDX-License-Identifier: GPL-3.0-or-later
"""Identitats, àlies i credencials; incrustat per build.py en el servidor.
Les funcions de sala utilitzen el registre autoritatiu del servidor.
"""
RACE_ALIASES = {
    "home": (["Vespran", "Talvex", "Odravel", "Cervun", "Peldrav", "Zervat"],
             ["Valclar", "Riuargent", "Montverd", "Ferroclar", "Ventdelnord", "Pedrablanca"]),
    "elf": (["Vaelusi", "Nuvarel", "Isevria", "Lumaves", "Cirevua", "Esvuli"],
            ["Fullaclara", "Brisaverda", "Llumdelriu", "Rosadafina", "Celargent", "Fulladormida"]),
    "nan": (["Drevuk", "Zavruk", "Kelvud", "Pravnek", "Veskud", "Drumvek"],
            ["Barbaferma", "Rocaforta", "Martellgris", "Ferroroig", "Pedrafonda", "Escutdur"]),
    "hobbit": (["Pebrun", "Tavop", "Nuvet", "Cerpuli", "Vespuc", "Melvot"],
               ["Peuverd", "Bonacasa", "Tossalbaix", "Fullatendra", "Pomaroja", "Bonataula"]),
}

def norm_player_name(value):
    value = " ".join(str(value or "").strip().split())
    return "".join(c for c in unicodedata.normalize("NFKD", value.casefold())
                   if not unicodedata.combining(c))

# Orientació lingüística local; els noms desconeguts o ambigus queden neutres.
ALIAS_GENDERS = ("male", "female", "neutral")
FEMALE_NAMES = set("maria maría anna ana nuria núria laura carmen carme rosa roser teresa teresa isabel elisabet elena helena marta clara sara sarah silvia sílvia sandra raquel cristina paula julia júlia lucia lucía llucia llúcia irene ines inés blanca alba ainhoa ainara mireia laia neus montserrat merce mercè esther ester natalia natàlia patricia patrícia andrea beatriz beatriu eva olga monica mònica sonia sònia noelia noèlia nerea vanessa veronica verònica victoria victòria amparo empar dolores dolors pilar rocio rocío candela carolina diana alicia alícia susana susanna estela adriana aurora lola pepa josefa joana juana concepcion concepció mariona martina emma olivia chloe sofia sofía lluisa lluïsa luisa elvira irati aitana belen belén arantxa itziar maite gemma gema leire alejandra alexia elisa elsa lara amelia cecilia cecília fátima fatima francesca francisca gabriela georgina gloria glòria jessica joaquina judith lidia lídia lorena lourdes magdalena manuela mar margarita margalida mirian miriam nadia naia paloma rebecca rebeca remedios remei rita salome salomé valentina valeria yolanda iolanda zoe".split())
MALE_NAMES = set("jose josé josep joan juan josepmiquel josepmaria jesus jesús manuel manel vicent vicente carlos carles antonio antoni toni francisco francesc paco miguel miquel angel àngel ángel david daniel dani pablo pau pedro pere javier xavier xavi jordi jorge joel marc marcos mario mário sergio sergi luis lluis lluís jaume jaime ramon ramón ramón raul raúl ruben rubén robert roberto ricard ricardo albert alberto alejandro alexandre alexander ferran fernando enric enrique hector héctor oscar òscar óscar ivan iván ivà isaac adrian adrián adrià adria andres andrés andreu guillem guillermo bernat bernardo artur arturo marti martí martin martín mateu mateo pol nil nicolau nicolas nicolás eduard eduardo ignasi ignacio santi santiago salvador pasqual pascual emili emilio eugeni eugenio gabriel gerard gerardo guille gonzalo hugo iker iñaki inaki leandro leonardo leroy lucas marcelo marcel matias matías max maximo máximo noel oriol ot pio pío rafael rafa ramiro rodrigo rubens saul saúl sebastia sebastià sebastian sebastián tomas tomás tomàs valentí valenti valentin valentín victor víctor ximo yago eric erik henry john james william michael thomas peter paul george anthony".split())
AMBIGUOUS_NAMES = {"alex", "aleks", "alix", "ariel", "andrea", "noa", "noah", "gael", "rene", "renee", "sasha", "sacha", "sam", "cris", "chris", "dani", "toni", "toni", "francis", "angel", "montse", "trini", "toni", "pat", "robin", "charlie", "jordan", "taylor", "kim"}
GENDER_ALIAS_NAMES = {
    "male": {
        "home": ["Vespran", "Talvex", "Odravel", "Cervun", "Peldrav", "Zervat"],
        "elf": ["Nuvarel", "Lumaves", "Cirevun", "Esvulon", "Vaeluso", "Isevran"],
        "nan": ["Drevuk", "Zavruk", "Kelvud", "Pravnek", "Veskud", "Drumvek"],
        "hobbit": ["Pebrun", "Tavop", "Nuvet", "Cerpuli", "Vespuc", "Melvot"],
    },
    "female": {
        "home": ["Vesprina", "Talvessa", "Odravela", "Cervuna", "Peldriva", "Zervata"],
        "elf": ["Vaelusia", "Nuvareva", "Isevria", "Lumavessa", "Cirevua", "Esvulia"],
        "nan": ["Drevuka", "Zavruna", "Kelvuda", "Pravneka", "Veskuda", "Drumveka"],
        "hobbit": ["Pebruna", "Tavopa", "Nuveta", "Cerpula", "Vespuca", "Melvota"],
    },
}


def detect_alias_gender(name):
    words = norm_player_name(name).replace(".", " ").split()
    if not words:
        return "neutral"
    if words[0] in ("m", "ma", "mª") and len(words) > 1:
        return "female"
    first = words[0]
    if first in AMBIGUOUS_NAMES:
        return "neutral"
    female = {norm_player_name(n) for n in FEMALE_NAMES}
    male = {norm_player_name(n) for n in MALE_NAMES}
    if first in female and first not in male:
        return "female"
    if first in male and first not in female:
        return "male"
    return "neutral"


def resolve_alias_gender(value, name):
    if value in (None, "auto"):
        return detect_alias_gender(name)
    if not isinstance(value, str) or value not in ALIAS_GENDERS:
        raise ValueError("alias_gender")
    return value


def user_record(value):
    if isinstance(value, dict):
        return {"name": str(value.get("name") or ""), "alias": str(value.get("alias") or ""),
                "race": str(value.get("race") or "home"),
                "alias_gender": value.get("alias_gender") if value.get("alias_gender") in ALIAS_GENDERS else "neutral"}
    return {"name": str(value or ""), "alias": "", "race": "home", "alias_gender": "neutral"}

def alias_in_use(alias, except_uid=None):
    wanted = norm_player_name(alias)
    return any(uid != except_uid and norm_player_name(user_record(raw)["alias"]) == wanted
               for uid, raw in state["users"].items())

def generate_alias(race, except_uid=None, alias_gender="neutral"):
    race = race if race in RACE_ALIASES else "home"
    names, surnames = RACE_ALIASES[race]
    names = GENDER_ALIAS_NAMES.get(alias_gender, {}).get(race, names)
    for _ in range(300):
        alias = f"{secrets.choice(names)} {secrets.choice(surnames)}"
        if not alias_in_use(alias) and (except_uid is None or alias != user_record(state["users"].get(except_uid))["alias"]):
            return alias
    while True:
        alias = f"{secrets.choice(names)} {secrets.token_hex(6).upper()}"
        if not alias_in_use(alias):
            return alias


PIN_ITERATIONS = 200_000


def set_pin(user):
    pin = f"{secrets.randbelow(10000):04d}"
    while user.get("pin") and verify_pin(user, pin):
        pin = f"{secrets.randbelow(10000):04d}"
    salt = secrets.token_hex(16)
    user["pin"] = {"salt": salt, "iterations": PIN_ITERATIONS,
                   "hash": hashlib.pbkdf2_hmac("sha256", pin.encode(), bytes.fromhex(salt), PIN_ITERATIONS).hex()}
    return pin


def verify_pin(user, pin):
    record = user.get("pin") or {}
    if not re.fullmatch(r"[0-9]{4}", str(pin)) or not record:
        return False
    digest = hashlib.pbkdf2_hmac("sha256", str(pin).encode(), bytes.fromhex(record["salt"]), record["iterations"]).hex()
    return hmac.compare_digest(digest, record["hash"])


def migrate_users():
    # No convertim les credencials antigues sense autenticació en sessions vàlides.
    state["sessions"] = {tok: sess for tok, sess in state["sessions"].items()
                         if isinstance(sess, dict) and sess.get("auth_version") == 2
                         and not sess.get("dm") and sess.get("uid") in state["users"]}
    used = set()
    for uid, raw in list(state["users"].items()):
        user = user_record(raw)
        name = " ".join(user["name"].split())[:40] or "Jugador"
        base, n = name, 2
        while norm_player_name(name) in used:
            name = f"{base[:32]} ({n})"
            n += 1
        used.add(norm_player_name(name))
        user["name"] = name
        user["uid"] = uid
        user["race"] = user["race"] if user["race"] in RACE_ALIASES else "home"
        if isinstance(raw, dict):
            for key in ("pin", "last_seen", "alias_version"):
                if key in raw:
                    user[key] = raw[key]
        state["users"][uid] = user
        # Els pools antics incloïen noms canònics: substitució prudent, sense tocar les partides.
        if user.get("alias_version") != 2 or not user["alias"] or alias_in_use(user["alias"], uid):
            user["alias"] = generate_alias(user["race"], uid)
        user["alias_version"] = 2


def restore_roster(docs):
    """Recupera identitats de la partida; mai importa PIN ni sessions."""
    game = docs.get("game/state") or {}
    used = set()
    for i, player in enumerate(game.get("players", [])):
        if not isinstance(player, dict):
            continue
        uid = player.get("uid")
        if not isinstance(uid, str) or uid not in state["users"]:
            uid = next((key for key, user in state["users"].items()
                        if norm_player_name(user["name"]) == norm_player_name(player.get("name"))), None)
        if not uid or uid in used:
            name = " ".join(str(player.get("name") or f"Jugador {i+1}").split())[:40]
            base, n = name, 2
            while any(norm_player_name(u["name"]) == norm_player_name(name) for u in state["users"].values()):
                name = f"{base[:32]} ({n})"
                n += 1
            saved_uid = player.get("uid")
            uid = saved_uid if isinstance(saved_uid, str) and re.fullmatch(r"u[a-f0-9]{12,24}", saved_uid) and saved_uid not in state["users"] else "u" + secrets.token_hex(12)
            race = player.get("race", "home")
            if not isinstance(race, str) or race not in RACE_ALIASES:
                race = "home"
            alias = player.get("alias")
            if player.get("alias_version") != 2 or not isinstance(alias, str) or not alias or alias_in_use(alias):
                alias = generate_alias(race, alias_gender=player.get("alias_gender") if player.get("alias_gender") in ALIAS_GENDERS else "neutral")
            state["users"][uid] = {"uid": uid, "name": name, "race": race, "alias": alias, "alias_version": 2,
                                    "alias_gender": player.get("alias_gender") if player.get("alias_gender") in ALIAS_GENDERS else "neutral"}
        user = state["users"][uid]
        player.update(uid=uid, **user_record(user), alias_version=2)
        used.add(uid)


def revoke_player(uid):
    for tok, sess in list(state["sessions"].items()):
        if sess["uid"] == uid:
            del state["sessions"][tok]


def room_players(admin=False):
    out = []
    for uid, raw in state["users"].items():
        bound = any(s["uid"] == uid for s in state["sessions"].values())
        if admin or (not bound and raw.get("pin")):
            out.append({"uid": uid, **user_record(raw), "bound": bound,
                        "connected": any(c.sess["uid"] == uid for c in clients),
                        "last_seen": raw.get("last_seen"), "pin_ready": bool(raw.get("pin"))})
    return out
