import simpy
import numpy as np
import matplotlib.pyplot as plt
import statistics

# INPUTS
np.random.seed(0)
SERVERS_NUM = 1
CUSTOMER_RATE = 3  # number of arriving customers per minute
SERVICE_RATE = 4  # number of customers satisfied per minute

# OUTPUTS
waiting_times = []  # to record waiting time of all customers
obs_times = []
q_length = []

def get_customer_interarrival_time():
    return np.random.exponential(1.0/CUSTOMER_RATE)


def generate_service_time():
    return np.random.exponential(1.0 / SERVICE_RATE)


def cafe_run(env, servers):
    global arrival_time
    i = 0
    while True:
        i += 1
        yield env.timeout(get_customer_interarrival_time())
        env.process(handle_customer(env, i, servers))
    

def handle_customer(env, customer, servers):
    with servers.request() as request:
        t_arrival = env.now
        print(f'{t_arrival:.2f} \t customer_{customer} arrives')
        yield request
        print(f'{env.now:.2f} \t customer_{customer} is being served')
        yield env.timeout(generate_service_time()) 
        t_depart = env.now
        print(f'{t_depart:.2f} \t customer_{customer} departs')
        t_wait = t_depart - t_arrival
        print(f'{t_wait:.2f} \t wait time for customer_{customer}')
        waiting_times.append(t_wait)


def observe(env, servers):
    '''
    servers: shared resource we wanna observe
    observe process happens continuously in the background
    '''
    while True:
        obs_times.append(env.now)
        q_length.append(len(servers.queue))
        yield env.timeout(0.5)  # observe at every time unit

env = simpy.Environment()

servers = simpy.Resource(env, capacity=SERVERS_NUM)

env.process(cafe_run(env, servers))
env.process(observe(env, servers))

env.run(10)

plt.figure()
plt.hist(waiting_times)
plt.xlabel('Waiting time (min)')
plt.ylabel('Number of Customers')


plt.figure()
plt.step(obs_times, q_length, where='post')
plt.xlabel('Time (min)')
plt.ylabel('Queue Length')

plt.show()