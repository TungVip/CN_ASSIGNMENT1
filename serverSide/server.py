import socket
import threading
import PySimpleGUI as sg
import pickle

# Print to GUI 
def add_to_output(window, text):
    window['-OUTPUT-'].print(text, end='\n')

# Start GUI for server 
def start_server_gui():
    
    # Server config
    SERVER_HOST = '127.0.0.1'
    SERVER_PORT = 8888
    
    # File name dictionary
    clients = {}
    
    server_socket = None
    # Server thread
    exit_event = threading.Event()
    lock = threading.Lock()

    # GUI 
    layout = [
        [sg.Text('User Command and Server Response', font=('Helvetica', 16))],
        [sg.Multiline('', key='-OUTPUT-', size=(60, 20), autoscroll=True, reroute_cprint=True)],
        [sg.InputText(key='-INPUT-', size=(30, 1)), sg.Button('Send Command'), sg.Button('Start Server'), sg.Button('Stop Server')]
    ]

    window = sg.Window('File Server GUI', layout, finalize=True)

    # Handle server action 
    while True:
        event, values = window.read(timeout=100)
        
        # Click button "X"
        if event == sg.WIN_CLOSED:
            # Set the exit event and wait for the server thread to finish
            exit_event.set()
            break
        
        # Click button "Send command"
        elif event == 'Send Command':
            command = values['-INPUT-']     # text field to enter command
            add_to_output(window, f"User Command: {command}")
            # Handle the command 
            if client_socket:
                if command.startswith('discover'):
                    handle_server_discover(command, clients, window)
                elif command.startswith('ping'):
                    handle_server_ping(command, clients, window)
                else:
                    add_to_output(window, 'Invalid command. Use "discover" or "ping".')

        elif event == 'Start Server':
            if server_socket is None:
                add_to_output(window, 'Server started')
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_socket.bind((SERVER_HOST, SERVER_PORT))
                server_socket.listen(5)
                threading.Thread(target=server_accept_connections, args=(server_socket, clients, window, exit_event, lock), daemon=True).start()

        elif event == 'Stop Server':
            if server_socket:
                add_to_output(window, 'Server stopped')
                server_socket.close()
                server_socket = None

    window.close()

# When client side click "Connect" button, use this function to start connection
def server_accept_connections(server_socket, clients, window, exit_event, lock):
    while not exit_event.is_set():
        # Find a client connection 
        try:
            client_socket, client_address = server_socket.accept()
            add_to_output(window, f"Accepted connection from {client_address}.")

            # Create a new thread for each client connection
            threading.Thread(target=client_listen, args=(client_socket, client_address, clients, window, exit_event, lock), daemon=True).start()

        except Exception as e:
            # Handle exceptions (e.g., if the server socket is closed)
            print(f"Exception in server thread: {e}")
            break

    server_socket.close()

# When client send command on client side, some data will be sent to the server. This function is used to listen to client. 
def client_listen(client_socket, client_address, clients, window, exit_event, lock):
    try:
        while not exit_event.is_set():
            # Receive file name from client on connection
            data = client_socket.recv(4096)
            
            # If no data is received, assume the client has disconnected and remove client's data from server
            if not data:
                with lock:
                    add_to_output(window, f"Client {client_address} disconnected")
                    clients.pop(client_address, None)
                    add_to_output(window, "All Client Information:")
                    add_to_output(window, clients)
                break
            
            # If data is received
            decoded_data = pickle.loads(data)

            # Check the type of data
            if decoded_data["type"] == "files_info":
                files_info = decoded_data["data"]
                # Now you can use files_info as needed
                add_to_output(window, f"Received files_info from {client_address}: {files_info}")

                # Store client's files information
                with lock:
                    if client_address in clients:
                        # If client has sent some data before, append the new files_info to the existing list
                        checkVar = True
                        for file_name in clients[client_address]["files"]:
                            # check existence of file name
                            file_lname, file_fname = file_name["local_name"], file_name["final_name"]
                            if file_lname.lower() == files_info[0][0].lower():
                                add_to_output(window, f"File {file_lname} already exists.")
                                checkVar = False
                                break
                            elif file_fname == files_info[0][1]:
                                add_to_output(window, f"File {file_fname} already exists.")
                                checkVar = False
                                break
                        # New file -> insert to dictionary
                        if checkVar:
                            clients[client_address]["files"].append({"local_name": files_info[0][0], "final_name": files_info[0][1]})
                    else:
                        # If no, create a new entry for the client
                        clients[client_address] = {
                            "host_name": None,
                            "status": "online",
                            "files": [
                                {"local_name": files_info[0][0], "final_name": files_info[0][1]}
                            ]
                        }

                    # Testing
                    # Print all client information to the GUI 
                    add_to_output(window, "All Client Information:")
                    add_to_output(window, clients)
            elif decoded_data["type"] == "hostname":
                hostname = decoded_data["data"][0]
                add_to_output(window, f"Received hostname from {client_address}: {hostname}")
                with lock:
                    if client_address in clients:
                        clients[client_address]["host_name"] = hostname
                    else:
                        clients[client_address] = {
                            "host_name": hostname,
                            "status": "online",
                            "files": []
                        }
                    # Testing
                    # Print all client information to the GUI 
                    add_to_output(window, "All Client Information:")
                    add_to_output(window, clients)

    except Exception as e:
        # Handle exceptions (e.g., if the client socket is closed)
        print(f"Exception in client thread: {e}")

    finally:
        client_socket.close()

def handle_server_discover(command, clients, window):
    # Implement the logic for the "discover" command
    _, hostname = command.split()
    checkFind = False
    with lock:
        # Check if the hostname is in the clients dictionary
        for client in clients:
            if hostname == client["host_name"]:
                add_to_output(window, f"Files on host {hostname}: {client['files']}")
                checkFind = True
                break
        if checkFind == False:
            add_to_output(window, f"Host {hostname} not found")

def handle_server_ping(command, clients, window):
    # Implement the logic for the "ping" command
    _, hostname = command.split()
    checkPing = False
    with lock:
        # Check if the hostname is in the clients dictionary
        for client in clients:
            if hostname == client["host_name"]:
                if client["status"] == "online":
                    add_to_output(window, f"Host name {hostname} is live")
                else:
                    add_to_output(window, f"Host name {hostname} is offline")
                checkPing = True
                break
        if checkPing == False:
            add_to_output(window, f"Host {hostname} not found")

if __name__ == "__main__":
    start_server_gui()
