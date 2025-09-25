import socket

import numpy as np

import math

import jupyter_probe_pb2

#0a2e5472616e736d697373696f6e206f662076656c6f63697479206461746120696e20782c20792c207a20617865732e1206080410001801


# Ground Station Protocol Specification (v0.1)

# Outbound transmission:
# - engine burn time and angle of thrust

# Inbound transmission:
# - status message
# - 3-axis velocity (x, y, z)

# My ip: 127.0.0.1:50320
# Probe ip: 127.0.0.1:64037#

def calculate_thrust(current_velocity):
    # Constants
    g_mars = 3.72076  # gravity acceleration on Mars in m/s^2
    mass = 500  # mass of the spacecraft in kg
    specific_impulse = 300  # specific impulse of the engine in seconds
    desired_velocity = np.array([3, 1, 0])  # desired velocity vector for correction in km/s
    delta_v = desired_velocity - current_velocity
    exhaust_velocity = specific_impulse * g_mars  # in m/s
    thrust = mass * np.linalg.norm(delta_v) / specific_impulse
    burn_time = (mass * exhaust_velocity / thrust) * (1 - math.exp(-np.linalg.norm(delta_v) / exhaust_velocity))
    angle_of_thrust = np.arccos(
        np.dot(delta_v, current_velocity) / (np.linalg.norm(delta_v) * np.linalg.norm(current_velocity)))
    return burn_time, angle_of_thrust


# to_send: "Transmission of velocity data in x, y, z axes."
# type {
#   num: 4
#   num1: 0
#   num2: 1
# }
def recv_message(s):
    message = s.recv(2048)
    new_message = jupyter_probe_pb2.Message2()
    new_message.ParseFromString(message)
    received_telemetry_message = new_message.to_send
    x, y, z = new_message.type.num, new_message.type.num1, new_message.type.num2
    current_velocity = np.array([x, y, z])
    print(new_message)
    return current_velocity

def send_message(s, burn_time, angle_of_thrust):
    new_message = jupyter_probe_pb2.Message3()
    new_message.engine_burn_time = burn_time
    new_message.angle_of_thrust = angle_of_thrust
    message = new_message.SerializeToString()
    s.sendto(message, ("127.0.0.1", 64037))
    print(f"sent message: {message} with burn time {burn_time} and angle_of_thrust {angle_of_thrust}")
    # binary_representation = ''.join(format(byte, '08b') for byte in message)
    # print(f"bin rep:{binary_representation}")


def run():
    # Set up socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('127.0.0.1', 50320))
    current_velocity = recv_message(s)
    while current_velocity[0] != 3 and current_velocity[1] != 1 and current_velocity[2] != 0:
        # thang = "0a2e5472616e736d697373696f6e206f662076656c6f63697479206461746120696e20782c20792c207a20617865732e1206080410001801"
        # thang = bytes.fromhex(thang)
        #
        # new_message = jupyter_probe_pb2.Message2()
        #
        # new_message.ParseFromString(thang)
        # print(new_message)


        # #receive message 1 from satellite
        # message = s.recv(2048)
        # new_message = jupyter_probe_pb2.Message1()
        # new_message.ParseFromString(message)
        # received_message = new_message.to_send
        # print(received_message)

        # receive message 2 from satellite
        current_velocity = recv_message(s)

        # calculate parameters to send
        burn_time, angle_of_thrust = calculate_thrust(current_velocity)

        #burn_time, angle_of_thrust = calculate_thrust(np.array([4, 0, 1]))

        # send message to satellite
        send_message(s, burn_time, angle_of_thrust)

        # s.close()
        # s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # s.bind(('127.0.0.1', 50320))

        # # receive message 1 from satellite
        # message = s.recv(2048)
        # new_message = jupyter_probe_pb2.Message1()
        # new_message.ParseFromString(message)
        # received_message = new_message.to_send
        # print(received_message)

    s.close()

if __name__ == "__main__":
    run()