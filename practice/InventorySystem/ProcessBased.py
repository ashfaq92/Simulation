import simpy
import numpy as np
import matplotlib.pyplot as plt

# INPUTS
CUSTOMER_INTERARRIVAL = 5.0
SIMULATION_TIME = 50.0  # run simulation for 5 days

# OUTPUTS


np.random.seed(0)

def warehouseRun(env, orderCutoff, orderTarget):
    global inventory, balance, numOrdered

    inventory = orderTarget
    balance = 0.0
    numOrdered = 0

    while True:
        interarrival = generateInterarrival()
        yield env.timeout(interarrival)
        balance -= inventory * 2 * interarrival
        demand = generateDemand()
        if demand < inventory:
            balance += 100 * demand
            inventory -= demand
            print(f'{env.now:.2f} \t sold \t {demand:.2f}')
        else:
            balance += 100 * inventory
            inventory = 0
            print(f'{env.now:.2f} \t sold (out of stock) \t {inventory:.2f}')
        
        if inventory < orderCutoff and numOrdered == 0:
            env.process(handleOrder(env, orderTarget))
             

def handleOrder(env, orderTarget):
    global inventory, balance, numOrdered
    numOrdered = orderTarget - inventory
    print(f'{env.now:.2f} \t placed the order for \t {numOrdered:.2f}')
    balance -= 50 * numOrdered
    yield env.timeout(2.0)
    inventory += numOrdered
    numOrdered = 0
    print(f'{env.now:.2f} \t received the order. In inventory: \t {inventory:.2f}')

def generateInterarrival():
    return np.random.exponential(1.0 / CUSTOMER_INTERARRIVAL)

def generateDemand():
    return np.random.randint(1, 5)


obsTimes = []
inventoryLevels = []

def observe(env):
    global inventory
    while True:
        obsTimes.append(env.now)
        inventoryLevels.append(inventory)
        yield env.timeout(0.1)



env = simpy.Environment()

env.process(warehouseRun(env, 10, 30))
env.process(observe(env))

env.run(until=SIMULATION_TIME)  # run till 5 days

plt.figure()
plt.step(obsTimes, inventoryLevels, where='post')
plt.xlabel('simulation time (days)')
plt.ylabel('inventory level')
plt.show()