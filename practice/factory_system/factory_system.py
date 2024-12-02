import simpy
import numpy as np
import matplotlib.pyplot as plt    

# input parameters
rand_seed = 0
total_machines = 50
working_hours = 8  # machines work 8 hours a day
working_days = 5  # machines work 5 days a week 
repairers_num = 3  # number of avilable repairers at the factory
repairer_wage = 3.75
spare_cost = 30  # purchase S repairs cost 30$ a day
opportunity_cost = 20  # the cost when machine was down
machine_failure_time = [132, 182]
repair_time = [4, 10]

# output 
obs_time = []
obs_cost = []
obs_spares = []

def factory_run(env, reps, sps):
    global cost
    cost = 0.0
    for i in range(total_machines):
        env.process(operate_machine(env, reps, sps))

    while True:
        cost += repairer_wage * working_hours * reps.capacity + spare_cost * sps.capacity
        yield env.timeout(working_hours)  # cost will be appended after each 8 hours

def operate_machine(env, reps, sps):
    global cost

    # consider location of each machine instead of specific machin bcz machines are swapped after repair
    while True:
        yield env.timeout(generate_failure_time(machine_failure_time))
        t_broken = env.now
        print(f'{t_broken:.2f} \t machine broke')
        # launch repair
        env.process(repair_machine(env, reps, sps))
        # get a spare
        yield sps.get(1)
        t_replaced = env.now
        print(f'{t_replaced:.2f} \t machine replaced')
        # add opportunity cost
        cost += opportunity_cost * (t_replaced - t_broken)


def repair_machine(env, reps, sps):
    with reps.request() as request:
        yield request
        yield env.timeout(generate_repair_time(repair_time))
        sps.put(1)
    print(f'{env.now:.2f} \t repair complete')



def generate_failure_time(failure_time):
    return np.random.uniform(failure_time[0], failure_time[1])


def generate_repair_time(repair_time):
    return np.random.uniform(repair_time[0], repair_time[1])


def observe(env, spares):
    while True:
        obs_time.append(env.now)
        obs_cost.append(cost)
        obs_spares.append(spares.level)
        yield env.timeout(1.0)

np.random.seed(rand_seed)

env = simpy.Environment()

repairers = simpy.Resource(env, capacity=repairers_num)
spares = simpy.Container(env, init=15, capacity=15)

env.process(factory_run(env, repairers, spares))
env.process(observe(env, spares))

env.run(until=working_days * working_hours * 52)

plt.figure()
plt.step(obs_time, obs_spares, where='post')
plt.xlabel('Time (hours)')
plt.ylabel('Spares Level')


plt.figure()
plt.step(obs_time, obs_cost, where='post')
plt.xlabel('Time (hours)')
plt.ylabel('cost')
plt.show()


print(f'TOTAL COST:\t {cost:.2f}')
