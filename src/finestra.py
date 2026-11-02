# ---------------------------------------------------------------- finestres (Windows i Linux)
# La Comunitat s'obri en una finestra pròpia, sense navegador:
#   - a Windows, amb WebView2 (el motor d'Edge que porta Windows), a través de pywebview;
#   - a Linux, amb WebKitGTK (el motor web de GNOME).
# Si no es pot, s'obri al navegador amb una finestreta (Tk) per a aturar-la; i si tampoc hi ha Tk o
# pantalla, tot va al terminal. Quan es tanca la finestra, el programa s'atura.
#
# COMUNITAT_PROVA_FINESTRA=fitxer: en carregar l'app, escriu «ok <títol>» al fitxer i tanca la finestra
# (per a les proves automàtiques de GitHub).

FINESTRA_TEXTOS = {
    "ca": {
        "titol": "La Comunitat",
        "tancar_t": "Tancar La Comunitat",
        "tancar_q": "Vols tancar La Comunitat? La partida ja està guardada.",
        "tancar": "Tancar", "cancel": "Cancel·lar", "d_acord": "D'acord",
        "guardar": "Guardar el fitxer",
        "guardat": "S'ha guardat el fitxer",
        "obri_carpeta": "Obrir la carpeta",
        "no_guardat": "No s'ha pogut guardar el fitxer.",
        "oberta_t": "La Comunitat ja està oberta",
        "oberta_q": "La Comunitat ja està oberta en aquest ordinador. Busca-la a la barra de tasques.",
        "error_t": "No s'ha pogut obrir La Comunitat",
        "reserva": "La Comunitat està oberta al navegador.",
        "reserva_peu": "Mentre aquesta finestra estiga oberta, La Comunitat funciona. Tanca-la quan acabeu.",
        "navegador": "Tornar a obrir al navegador",
        "aturar": "Aturar",
    },
    "es": {
        "titol": "La Comunidad",
        "tancar_t": "Cerrar La Comunidad",
        "tancar_q": "¿Quieres cerrar La Comunidad? La partida ya está guardada.",
        "tancar": "Cerrar", "cancel": "Cancelar", "d_acord": "Aceptar",
        "guardar": "Guardar el archivo",
        "guardat": "Se ha guardado el archivo",
        "obri_carpeta": "Abrir la carpeta",
        "no_guardat": "No se ha podido guardar el archivo.",
        "oberta_t": "La Comunidad ya está abierta",
        "oberta_q": "La Comunidad ya está abierta en este ordenador. Búscala en la barra de tareas.",
        "error_t": "No se ha podido abrir La Comunidad",
        "reserva": "La Comunidad está abierta en el navegador.",
        "reserva_peu": "Mientras esta ventana esté abierta, La Comunidad funciona. Ciérrala cuando terminéis.",
        "navegador": "Volver a abrir en el navegador",
        "aturar": "Detener",
    },
}

PROVA_FINESTRA = os.environ.get("COMUNITAT_PROVA_FINESTRA", "")


def hi_ha_pantalla():
    return os.name == "nt" or sys.platform == "darwin" or bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def hi_ha_finestra():
    """Hi ha tkinter i una pantalla on mostrar la finestreta de l'adreça?"""
    if not hi_ha_pantalla():
        return False
    try:
        import tkinter  # noqa: F401
        return True
    except Exception:  # noqa: BLE001
        return False


def avis_finestra(titol, text):
    """Un missatge d'error en una finestra (per a l'executable de Windows, que no té terminal)."""
    try:
        import tkinter as tk
        from tkinter import messagebox
        r = tk.Tk()
        r.withdraw()
        messagebox.showerror(titol, text)
        r.destroy()
    except Exception:  # noqa: BLE001
        pass


def obrir_carpeta(path):
    try:
        if os.name == "nt":
            os.startfile(str(path))  # noqa: S606
        else:
            import subprocess
            subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", str(path)])
    except Exception:  # noqa: BLE001
        pass


def dades_finestra():
    """On guarda la finestra pròpia el que recorda el navegador (qui ha entrat, l'idioma, el tema)."""
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local") / "LaComunitat"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share") / "comunitat-del-anell"
    d = base / "finestra"
    d.mkdir(parents=True, exist_ok=True)
    return d


def prova_feta(titol):
    """Per a les proves automàtiques: apunta que l'app s'ha carregat a la finestra pròpia."""
    try:
        Path(PROVA_FINESTRA).write_text(f"ok {titol}", encoding="utf-8")
    except OSError:
        pass


# ---------------------------------------------------------------- la finestra pròpia
def finestra_app(url, idioma):
    """Obri l'app en una finestra pròpia i espera fins que es tanca.
    Torna False, sense haver obert res, si en aquest ordinador no es pot."""
    if not hi_ha_pantalla():
        return False
    if os.name == "nt" or sys.platform == "darwin":
        return _finestra_pywebview(url, idioma)
    return _finestra_gtk(url, idioma)


def _finestra_pywebview(url, idioma):
    """Windows (i Mac, si hi ha pywebview): la finestra amb pywebview. A Windows només amb WebView2;
    l'antic motor d'Internet Explorer no pot mostrar l'app."""
    try:
        import webview
        if os.name == "nt":
            import webview.platforms.winforms as winforms
            if getattr(winforms, "renderer", "") != "edgechromium":
                print("  No hi ha WebView2: s'obri el navegador.")
                return False
    except Exception as e:  # noqa: BLE001
        if os.name == "nt" and FROZEN:
            print(f"  No s'ha pogut preparar la finestra ({e}): s'obri el navegador.")
        return False
    T = FINESTRA_TEXTOS[idioma]
    webview.settings["ALLOW_DOWNLOADS"] = True            # exportar partides
    webview.settings["OPEN_EXTERNAL_LINKS_IN_BROWSER"] = True
    w = webview.create_window(
        T["titol"], url, width=1360, height=880, min_size=(380, 520), confirm_close=not PROVA_FINESTRA,
        text_select=True, zoomable=True, background_color="#E9DCBC",
        localization={"global.quitConfirmation": T["tancar_q"], "global.saveFile": T["guardar"],
                      "global.ok": T["d_acord"], "global.cancel": T["cancel"], "global.quit": T["tancar"]})
    if PROVA_FINESTRA:
        def carregada():
            if Path(PROVA_FINESTRA).exists():
                return
            time.sleep(1)
            try:
                titol = w.evaluate_js("document.title")
            except Exception as e:  # noqa: BLE001
                titol = f"(no s'ha pogut llegir el títol: {e})"
            prova_feta(titol)
            w.destroy()
        w.events.loaded += carregada
    try:
        webview.start(gui="edgechromium" if os.name == "nt" else None, private_mode=False,
                      storage_path=str(dades_finestra()))
    except Exception as e:  # noqa: BLE001
        print(f"  No s'ha pogut obrir la finestra ({e}): s'obri el navegador.")
        return False
    return True


def _bwrap_funciona():
    """WebKitGTK aïlla les pàgines amb bubblewrap. Si el sistema no ho permet (passa en alguns Ubuntu 24.04),
    no es veuria res. Com que la finestra només mostra La Comunitat d'aquest ordinador, llavors es desactiva."""
    import shutil
    import subprocess
    bwrap = shutil.which("bwrap")
    if not bwrap:
        return True
    try:
        return subprocess.run([bwrap, "--ro-bind", "/", "/", "--unshare-user", "true"], stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL, timeout=10).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return True


def _finestra_gtk(url, idioma):
    """Linux: la finestra amb GTK 3 i WebKitGTK (paquets python3-gi i gir1.2-webkit2-4.1)."""
    os.environ.setdefault("WEBKIT_DISABLE_DMABUF_RENDERER", "1")   # evita finestres en blanc amb alguns controladors
    try:
        import gi
        gi.require_version("Gtk", "3.0")
        gi.require_version("GdkPixbuf", "2.0")
        try:
            gi.require_version("WebKit2", "4.1")
        except ValueError:
            gi.require_version("WebKit2", "4.0")
        from gi.repository import GdkPixbuf, Gio, GLib, Gtk, WebKit2
    except (ImportError, ValueError):
        return False
    GLib.set_prgname("comunitat-del-anell")      # lliga la finestra amb l'accés del menú
    GLib.set_application_name(FINESTRA_TEXTOS[idioma]["titol"])
    if not Gtk.init_check(None)[0]:
        return False
    if not _bwrap_funciona():
        os.environ["WEBKIT_DISABLE_SANDBOX_THIS_IS_DANGEROUS"] = "1"
    T = FINESTRA_TEXTOS[idioma]
    local = urlparse(url)

    def es_local(uri):
        u = urlparse(uri)
        return u.scheme in ("about", "data", "blob") or (
            u.scheme == "http" and u.hostname in ("localhost", "127.0.0.1") and u.port == local.port)

    def obri_fora(uri):
        if urlparse(uri).scheme in ("http", "https", "mailto", "file"):
            try:
                Gio.AppInfo.launch_default_for_uri(uri, None)
            except GLib.Error:
                pass

    dades = dades_finestra()
    gestor = WebKit2.WebsiteDataManager(base_data_directory=str(dades),
                                        base_cache_directory=str(dades / "memoria-cau"))
    context = WebKit2.WebContext.new_with_website_data_manager(gestor)

    win = Gtk.Window(title=T["titol"])
    win.set_default_size(1360, 880)
    win.set_size_request(380, 520)
    try:
        carrega = GdkPixbuf.PixbufLoader()
        carrega.write(base64.b64decode(ICONA_PNG))
        carrega.close()
        win.set_icon(carrega.get_pixbuf())
    except Exception:  # noqa: BLE001
        pass

    vista = WebKit2.WebView.new_with_context(context)
    s = vista.get_settings()
    s.set_enable_developer_extras(False)
    s.set_javascript_can_open_windows_automatically(False)
    win.add(vista)

    def avis(tipus, text, detall=""):
        d = Gtk.MessageDialog(transient_for=win, modal=True, message_type=tipus, buttons=Gtk.ButtonsType.OK, text=text)
        if detall:
            d.format_secondary_text(detall)
        d.run()
        d.destroy()

    # Què s'obri ací i què fora: només La Comunitat va a la finestra; la resta, al navegador habitual.
    def decideix(_v, decisio, tipus):
        if tipus in (WebKit2.PolicyDecisionType.NAVIGATION_ACTION, WebKit2.PolicyDecisionType.NEW_WINDOW_ACTION):
            uri = decisio.get_navigation_action().get_request().get_uri()
            if not es_local(uri):
                decisio.ignore()
                obri_fora(uri)
                return True
        elif tipus == WebKit2.PolicyDecisionType.RESPONSE and not decisio.is_mime_type_supported():
            decisio.download()           # les partides exportades es guarden a Baixades
            return True
        return False

    # Baixades: a la carpeta Baixades, sense sobreescriure res
    def desti(baixada, suggerit):
        carpeta = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD) or str(Path.home())
        os.makedirs(carpeta, exist_ok=True)
        nom = os.path.basename(suggerit or "") or "partida.json"
        base, ext = os.path.splitext(nom)
        cami, n = os.path.join(carpeta, nom), 1
        while os.path.exists(cami):
            n += 1
            cami = os.path.join(carpeta, f"{base} ({n}){ext}")
        baixada.cami = cami
        baixada.set_destination(GLib.filename_to_uri(cami, None))
        return True

    def feta(baixada):
        cami = getattr(baixada, "cami", None)
        if not cami or not os.path.exists(cami):
            return
        d = Gtk.MessageDialog(transient_for=win, modal=True, message_type=Gtk.MessageType.INFO,
                              buttons=Gtk.ButtonsType.NONE, text=T["guardat"])
        d.format_secondary_text(cami)
        d.add_button(T["obri_carpeta"], 1)
        d.add_button(T["d_acord"], Gtk.ResponseType.OK)
        if d.run() == 1:
            obrir_carpeta(os.path.dirname(cami))
        d.destroy()

    def baixada(_c, b):
        b.connect("decide-destination", desti)
        b.connect("finished", feta)
        b.connect("failed", lambda _b, error: avis(Gtk.MessageType.ERROR, T["no_guardat"], error.message))

    def titol(_v, _p):
        win.set_title(vista.get_title() or T["titol"])

    carregada = []

    def carrega_feta(_v, esdeveniment):
        if esdeveniment != WebKit2.LoadEvent.FINISHED or carregada:
            return
        carregada.append(1)
        if PROVA_FINESTRA:
            def acaba():
                prova_feta(vista.get_title() or "")
                win.destroy()
                return False
            GLib.timeout_add(1500, acaba)

    def tancant(_w, _e):
        if PROVA_FINESTRA:
            return False
        d = Gtk.MessageDialog(transient_for=win, modal=True, message_type=Gtk.MessageType.QUESTION,
                              buttons=Gtk.ButtonsType.NONE, text=T["tancar_t"])
        d.format_secondary_text(T["tancar_q"])
        d.add_button(T["cancel"], Gtk.ResponseType.CANCEL)
        d.add_button(T["tancar"], Gtk.ResponseType.OK)
        d.set_default_response(Gtk.ResponseType.OK)
        r = d.run()
        d.destroy()
        return r != Gtk.ResponseType.OK          # True = no la tanques

    context.connect("download-started", baixada)
    vista.connect("decide-policy", decideix)
    vista.connect("notify::title", titol)
    vista.connect("load-changed", carrega_feta)
    win.connect("delete-event", tancant)
    win.connect("destroy", lambda *_: Gtk.main_quit())
    try:  # en tancar la sessió o apagar l'ordinador, es tanca sense preguntar i es guarda tot
        import signal
        GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM, lambda: (Gtk.main_quit(), False)[1])
    except Exception:  # noqa: BLE001
        pass
    vista.load_uri(url)
    win.show_all()
    Gtk.main()
    return True


# ---------------------------------------------------------------- la finestreta de reserva (Tk)
def finestra_reserva(url, idioma):
    """Quan l'app s'obri al navegador: una finestreta per a saber que funciona i per a aturar-la."""
    import tkinter as tk

    T = FINESTRA_TEXTOS[idioma]
    root = tk.Tk(className="comunitat-del-anell")   # a Linux, lliga la finestra amb l'accés del menú
    root.title(T["titol"])
    root.resizable(False, False)
    try:
        root.iconphoto(True, tk.PhotoImage(data=ICONA_PNG))
    except Exception:  # noqa: BLE001
        pass
    paper, carta, tinta, suau, linia, roig = "#E9DCBC", "#F4EAD2", "#2A1C10", "#6F5A40", "#C4AB80", "#8C2A1C"
    root.configure(bg=paper)
    cos = tk.Frame(root, bg=paper, padx=22, pady=18)
    cos.pack(fill="both")
    cap = tk.Frame(cos, bg=paper)
    cap.pack(fill="x")
    try:
        logo = tk.PhotoImage(data=ICONA_PNG).subsample(2)
        tk.Label(cap, image=logo, bg=paper).pack(side="left", padx=(0, 12))
        cap.logo = logo
    except Exception:  # noqa: BLE001
        pass
    text = tk.Frame(cap, bg=paper)
    text.pack(side="left")
    tk.Label(text, text=T["titol"], font=("Georgia", 19), fg=tinta, bg=paper).pack(anchor="w")
    tk.Label(text, text=T["reserva"], font=("Georgia", 11), fg=suau, bg=paper).pack(anchor="w")
    tk.Label(cos, text=T["reserva_peu"], font=("Georgia", 10), fg=suau, bg=paper, wraplength=380,
             justify="left").pack(anchor="w", pady=(14, 10))
    botons = tk.Frame(cos, bg=paper)
    botons.pack(fill="x")

    def boto(text_, ordre, principal=False):
        return tk.Button(botons, text=text_, command=ordre, font=("Georgia", 11, "bold" if principal else "normal"),
                         bg=roig if principal else carta, fg="#FBEFDA" if principal else tinta, relief="flat", bd=0,
                         highlightthickness=1, highlightbackground=roig if principal else linia, padx=14, pady=7,
                         cursor="hand2")

    boto(T["navegador"], lambda: webbrowser.open(url), principal=True).pack(side="left")
    boto(T["aturar"], root.destroy).pack(side="right")
    root.protocol("WM_DELETE_WINDOW", root.destroy)
    root.update_idletasks()
    w, h = root.winfo_reqwidth(), root.winfo_reqheight()
    root.geometry(f"+{max(0, (root.winfo_screenwidth() - w) // 2)}+{max(0, (root.winfo_screenheight() - h) // 3)}")
    root.mainloop()
