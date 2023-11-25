import socket
import pickle
import os
import PySimpleGUI as sg

def start_client_gui():
    # Client configuration
    SERVER_HOST = '127.0.0.1'
    SERVER_PORT = 8888

    # GUI layout
    layout = [
        [sg.Text('File client GUI', font=('Helvetica', 16))],
        [sg.Multiline('', key='-OUTPUT-', size=(60, 20), autoscroll=True, reroute_cprint=True)],
        [sg.InputText(key='-COMMAND-', size=(30, 1)), sg.Button('Send Command'), sg.Button('Connect')],
    ]

    window = sg.Window('File Client GUI', layout, finalize=True)

    client_socket = None

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED:
            break

        elif event == 'Send Command':
            command = values['-COMMAND-']
            add_to_output(window, f"User Command: {command}")

            if client_socket:
                if command.startswith('publish'):
                    handle_publish_command(command, client_socket, window)
                elif command.startswith('fetch'):
                    handle_fetch_command(command, client_socket, window)
                elif command.startswith('hostname'):
                    handle_set_hostname(command, client_socket, window)
                else:
                    add_to_output(window, 'Invalid command. Use "publish" or "fetch".')
            else:
                add_to_output(window, 'Not connected to the server. Use "Connect" button.')

        elif event == 'Connect':
            if client_socket is None:
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.connect((SERVER_HOST, SERVER_PORT))
                add_to_output(window, 'Connected to the server')

    if client_socket:
        client_socket.close()

    window.close()

def handle_set_hostname(command, client_socket, window):
    # Extract the hostname from the command
    _, hostname = command.split()
    data = pickle.dumps({"type": "hostname", "data": [hostname]})
    # Connect to the server
    try:
        # Send the hostname to the server
        client_socket.sendall(data)
        add_to_output(window, f'Sent hostname to the server.')
    except Exception as e:
        add_to_output(window, f'Error connecting to the server: {e}')

def handle_publish_command(command, client_socket, window):
    # Extract file information from the command
    _, lname, fname = command.split()

    # Check if the file exists in the client's repository
    if os.path.isfile(os.path.join('repo', lname)):
        # Send the file information to the server
        files_info = pickle.dumps({"type": "files_info", "data": [(lname, fname)]})
        client_socket.sendall(files_info)

        add_to_output(window, f"Published file: {lname} as {fname}")
    else:
        add_to_output(window, f"Error: File {lname} not found in the client's repository.")

def handle_fetch_command(command, client_socket, window):
    # Extract file information from the command
    _, fname = command.split()

    # Send the fetch command to the server
    fetch_command = f"fetch {fname}"
    client_socket.sendall(fetch_command.encode('utf-8'))

    # Receive the response from the server
    response = client_socket.recv(4096)
    response = response.decode('utf-8')

    add_to_output(window, f"Server Response: {response}")

def add_to_output(window, text):
    window['-OUTPUT-'].print(text, end='\n')

if __name__ == "__main__":
    start_client_gui()
