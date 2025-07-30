# -*- coding: utf-8 -*-
"""
Created on Tue Apr  8 10:36:41 2025

@author: DiMartino
"""

import os
from pywinauto import Desktop
from pywinauto.keyboard import send_keys
from pywinauto.findwindows import ElementNotFoundError
import time
import urllib


def move_window_to_primary_monitor(window):
    """
    Focus window and avoid writing passwords all over the place.
    """
    window.move_window(x=0, y=0)

def login_row(lines, lookup_string): # Create config.txt to store secrets.
    for line in lines:
        if lookup_string in line:
            target_line = line.strip()
            break
    else:
        return None
    cleaned_line = target_line.strip().split(" ")[1]
    return cleaned_line

def build_config():
    windows_user = os.getlogin().casefold()
    if not os.path.exists(fr"C:\Users\{windows_user}\AppData\Local\pysecrets"):
        os.makedirs(fr"C:\Users\{windows_user}\AppData\Local\pysecrets")    
    config_file = fr"C:\Users\{windows_user}\AppData\Local\pysecrets\pyconfig.txt"
    print("Adesso ti guiderò nella creazione di questo file config.txt. Le impostazioni di default sono \
        per user, password, server, database, ftp server, ftp user, ftp password, tenant id, app id, secret. Probabilmente \
        non ti serviranno tutte queste impostazioni. Inserisci quelle che ti servono. Altrimenti, \
        inserisci '0'. Quei campi saranno ignorati. Se poi dovessero servirti, in caso di errore, \
        ti verrà richiesto se vuoi ricreare il tuo file config.txt, così potrai reinserire le nuove credenziali.")
    username = input("Inserisci la tua mail di Microsoft: ")
    password = input("Inserisci la tua password: ")
    server = input("Inserisci il nome del server (es. sql-tuazienda-prod...): ")
    database = input("Inserisci il nome del database a cui accedere (es. BuyAnalysis...): ")
    ftp_server_address = input("Inserisci l'indirizzo del server FTP: ")
    ftp_user = input("Inserisci il nome utente per il server FTP: ")
    ftp_password = input("Inserisci la password per il server FTP: ")
    tenant_id = input("Inserisci l'id del tenant dell'applicazione Azure': ")
    app_id = input("Inserisci l'id dell'applicazione Azure': ")
    secret = input("Inserisci la password per l'applicazione Azure': ")
    with open(config_file, 'w') as file:
        file.write("username: "+ username + "\n")
        file.write("password: "+ password + "\n")
        file.write("server: "+ server + "\n")
        file.write("database: "+ database + "\n")
        file.write("ftp_server_address: "+ ftp_server_address + "\n")
        file.write("ftp_user: "+ ftp_user + "\n")
        file.write("ftp_password: "+ ftp_password + "\n")
        file.write("tenant_id: "+ tenant_id + "\n")
        file.write("app_id: "+ app_id + "\n")
        file.write("random_id: "+ secret)
    print(f"User e password salvati nel file {config_file}.")

def get_login_info_from_config(config_file=""): # Get login info from config.
    """    

    Returns variables used for logins.
    -------
    How to use it:
    remember that in case you do not need to call all the variables, you can call the variables using
    only the needed variables and adding *rest for the others. Example: if you only need
    user and password, you can call user, password, *rest = get_login_info_from_config().

    """
    if config_file == "":
        windows_user = os.getlogin().casefold()
        if not os.path.exists(fr"C:\Users\{windows_user}\AppData\Local\pysecrets"):
            os.makedirs(fr"C:\Users\{windows_user}\AppData\Local\pysecrets")   
        config_file = fr"C:\Users\{windows_user}\AppData\Local\pysecrets\pyconfig.txt"
    
    rebuild = False
    while True:
        if rebuild:
            os.remove(config_file)
        rebuild = False
        if not os.path.exists(config_file):
            build_config()
        else:
            with open(config_file, 'r') as file:
                lines = file.readlines()
                if len(lines) != 10:
                    print("Attenzione: il file di configurazione non è corretto. Reinserisci i tuoi dati.")
                    rebuild = True
                    continue
                username = login_row(lines, "username:").strip()
                password = login_row(lines, "password:").strip()
                server = login_row(lines, "server:").strip()
                database = login_row(lines, "database:").strip()
                ftp_server_address = login_row(lines, "ftp_server_address:").strip()
                ftp_user = login_row(lines, "ftp_user:").strip()
                ftp_password = login_row(lines, "ftp_password:").strip()
                tenant_id = login_row(lines, "tenant_id:").strip()
                app_id = login_row(lines, "app_id:").strip()
                secret = login_row(lines, "random_id:").strip()
                return username, password, server, database, ftp_server_address, ftp_user, ftp_password, tenant_id, app_id, secret

def simulate_user_login(user, password):
    """
    This function takes the result of the previous function and automatically performs the login procedure for Microsoft-based applications.
    
    Parameters
    ----------
    Parameters are passed by the function get_login_info_from_config(). 
    """
    try:
        
        time.sleep(3.5)
        app = Desktop(backend='win32').window(title_re=".*autenticaz.*", visible_only=False)
        dlg = app
        dlg.set_focus()
        move_window_to_primary_monitor(dlg)
        time.sleep(3)
        send_keys(user)
        send_keys('{ENTER}{TAB}{ENTER}', with_spaces=True)
        user = "*"
        time.sleep(2)

        if dlg.wait('ready', timeout=10):
            send_keys(password)
            send_keys('{ENTER}') 
            password = "*"
            print("Login completato.")
        else:
            print("Login completato. La password non è stata necessaria.")
            pass
    except ElementNotFoundError:
        pass
    except Exception as e:
        print(f"Errore nel login {e} Tipo errore: {type(e).__name__}. Forse il tuo config.txt è errato?")
        decision = None
        while decision.casefold() != "y" and decision.casefold() != "n":
            decision = input("\n Vuoi ricreare il file config? y/n")
        if decision.casefold() == "y":
            windows_user = os.getlogin().casefold()
            if os.path.exists(fr"C:\Users\{windows_user}\AppData\Local\pysecrets\pyconfig.txt"):
                os.remove(fr"C:\Users\{windows_user}\AppData\Local\pysecrets\pyconfig.txt")
                build_config()
            else:
                build_config()
                
def build_connection_string():
    username, password, server, database, ftp_server_address, ftp_user, ftp_password, tenant_id, app_id, secret = get_login_info_from_config()
    app_id_encoded = urllib.parse.quote_plus(app_id)
    secret_encoded = urllib.parse.quote_plus(secret)
    connection_string = (
        f"mssql+pyodbc://{app_id_encoded}:{secret_encoded}@"
        f"{server}/{database}?"
        f"driver=ODBC+Driver+17+for+SQL+Server&"
        f"Authentication=ActiveDirectoryServicePrincipal&"
        f"TenantID={tenant_id}&"
        f"Encrypt=yes&"
        f"TrustServerCertificate=no"
    )
    return connection_string


            