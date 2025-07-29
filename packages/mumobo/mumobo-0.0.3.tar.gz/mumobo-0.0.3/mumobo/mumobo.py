import socket

class MuMoBo:
    """Client for MuMoBo microcontroller communication via TCP socket."""

    def __init__(self, host : str, port : int = 80, timeout : float = 20.0, verbose : bool = False):
        """Initialize the client 
        
        Parameters
        ==========
        host : str
            hostname or ip address of the mumobo
        port : int
            port on which the socket server is running
        timeout : float
            timeout for socket communication
        verbose : bool
            how talkative the API will be   

        ToDo
        ====
        Implement persistant socket connection with failsafe checking of connection. Currently
        each command opens and closes a socket.


        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.verbose = verbose

    def _send_numbers(self, mode, axis, sID, nID, position):
        """Method: Send a communication package

        Paramaters
        ==========
        mode : int
            determines the type of command
        axis : int
            which axis (group of servos) to address
        sID : int
            which servo ID to address
        nID : int
            new servo id if mode is 'change servo id'
        position : int
            how many steps to turn if mode is 'move by steps'       
        """
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(20)
            client_socket.connect((self.host, self.port))
            data = f'{mode},{axis},{sID},{nID},{position}\n'
            client_socket.sendall(data.encode('utf-8'))
            if self.verbose:
                print(f"Sending data: {data.strip()}")
                print('Waiting for responses from the server:')
            response_buffer = ''
            while True:
                try:
                    response = client_socket.recv(1024).decode('utf-8')                 
                    if not response:
                        break
                    response_buffer += response
                    while '\n' in response_buffer:
                        complete_response, response_buffer = response_buffer.split('\n', 1)
                        print(f' {complete_response.strip()}')
                except socket.timeout:
                    print('No more responses from server (timeout).')
                    break
        except Exception as e:
            print(f'Error: {e}')
        finally:
            try:
                client_socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            client_socket.close()
            print('Connection closed.')

    def move_motor_by(self, AXIS, SERVO_ID, STEPS):
        """Move a motor.

        Parameters
        ==========
        AXIS : int
            which axis to address
        SERVO_ID : int
            which servo to address
        STEPS : int
            how many steps to turn       
        
        """
        if AXIS in (1, 2):
            if abs(STEPS) < 3 * 4096:
                self._send_numbers(2, AXIS, SERVO_ID, 0, STEPS)
            else:
                print('Error: The step is too large!')
        else:
            print('Error: Laser axis is not valid!')

    def move_motor_zero(self, AXIS, SERVO_ID):
        """Method: Move motor by zero steps."""
        if AXIS in (1, 2):
            if SERVO_ID in range(1,254):
                self._send_numbers(2, AXIS, SERVO_ID, 0, 0)
            else:
                print('Error: Servo ID is not valid!')
        else:
            print('Error: axis is not valid!')

    def changeID(self, AXIS, SERVO_ID, NEW_ID):
        """Change the motor ID
        
        Parameters
        ==========
        AXIS : int
            which axis to address
        SERVO_ID : int
            which servo to address
        NEW_ID : int
            new servo ID       
        
        """
        if AXIS in (1, 2):
            if SERVO_ID in range(1,254):
                self._send_numbers(1, AXIS, SERVO_ID, NEW_ID, 0)
            else:
                print('Error: Servo ID is not valid!')
        else:
            print('Error: axis is not valid!')

    def getID(self, AXIS):
        """Method: Getid."""
        if AXIS in (1, 2):
            self._send_numbers(5, AXIS, 0, 0, 0)
        else:
            print('Error: axis is not valid!')

    def ping_1(self, AXIS, SERVO_ID):
        """Method: Ping 1."""
        if AXIS in (1, 2):
            if SERVO_ID in range(1,254):
                self._send_numbers(4, AXIS, SERVO_ID, 0, 0)
            else:
                print('Error: Servo ID is not valid!')
        else:
            print('Error: Laser axis is not valid!')

    def step_Mode(self, AXIS, SERVO_ID):
        """Method: Step mode."""
        self._send_numbers(6, AXIS, SERVO_ID, 0, 0)

