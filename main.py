import gurobipy as gp


# Sets
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
times = [9, 10, 11, 12, 13, 14, 15, 16]
people = ["Harrison", "Dhanan", "Erin", "Ella"]
shifts = []

for i, start_time in enumerate(times):
    for other_time in times[i:]:
        end_time = other_time + 1
        shifts.append((start_time, end_time))
        
print("Shifts:", shifts)
        
# Data
availability = {
    ("Harrison", "Monday"): [1] * len(times),
    ("Harrison", "Tuesday"): [1] * len(times),
    ("Harrison", "Wednesday"): [1] * len(times),
    ("Harrison", "Thursday"): [1] * len(times),
    ("Harrison", "Friday"): [1] * len(times),
    ("Dhanan", "Monday"): [1] * len(times),
    ("Dhanan", "Tuesday"): [1] * len(times),
    ("Dhanan", "Wednesday"): [1] * len(times),
    ("Dhanan", "Thursday"): [1] * len(times),
    ("Dhanan", "Friday"): [1] * len(times),
    ("Erin", "Monday"): [1] * len(times),
    ("Erin", "Tuesday"): [1] * len(times),
    ("Erin", "Wednesday"): [1] * len(times),
    ("Erin", "Thursday"): [1] * len(times),
    ("Erin", "Friday"): [1] * len(times),
    ("Ella", "Monday"): [1] * len(times),
    ("Ella", "Tuesday"): [1] * len(times),
    ("Ella", "Wednesday"): [1] * len(times),
    ("Ella", "Thursday"): [1] * len(times),
    ("Ella", "Friday"): [1] * len(times)
}

max_total = {
    "Harrison": 11,
    "Dhanan": 11,
    "Erin": 11,
    "Ella": 11
}

max_consecutive = {
    "Harrison": 4,
    "Dhanan": 8,
    "Erin": 100,
    "Ella": 8
}

contains = {}

for shift in shifts:
    start_time, end_time = shift
    for time in times:
        if start_time <= time < end_time:
            contains[(shift, time)] = 1
        else:
            contains[(shift, time)] = 0
            
print("Contains:", contains)
        
            
lengths = {shift: end_time - start_time for shift, (start_time, end_time) in zip(shifts, shifts)}

fixed_shifts = {
    ("Erin", "Tuesday"): [(15, 17)],
    ("Erin", "Thursday"): [(13, 17), (9, 10)],
    ("Erin", "Friday"): [(15, 17)],
}

num_days_weight = 1
num_shifts_weight = 1

# Variables 
model = gp.Model("Shift Scheduling")
X = {(person, shift, day): model.addVar(vtype=gp.GRB.BINARY) for person in people for shift in shifts for day in days}
Y = {(person, day): model.addVar(vtype=gp.GRB.BINARY) for person in people for day in days}

# Objective
model.setObjective(
    gp.quicksum(Y[person, day] for person in people for day in days) * num_days_weight + \
    gp.quicksum(X[person, shift, day] for person in people for shift in shifts for day in days) * num_shifts_weight,
    gp.GRB.MINIMIZE)

# Constraints
maxHours = {person: model.addConstr(
    gp.quicksum(X[person, shift, day] * lengths[shift] for shift in shifts for day in days) <= max_total[person])
    for person in people}

allTimesCovered = {(time, day): model.addConstr(
    gp.quicksum(X[person, shift, day] * contains[(shift, time)] for person in people for shift in shifts) == 1)
    for time in times for day in days}

respectAvailability = {(person, time, shift, day): model.addConstr(
    X[person, shift, day] * contains[shift, time] <= availability[(person, day)][times.index(time)])
    for person in people for time in times for shift in shifts for day in days}

maxConsecutive = {(person, day, shift): model.addConstr(
    X[person, shift, day] * lengths[shift] <= max_consecutive[person])
    for person in people for shift in shifts for day in days}

daysWorked = {(person, day): model.addConstr(
    Y[person, day] >= gp.quicksum(X[person, shift, day] for shift in shifts) / len(shifts))
    for person in people for day in days}



fixedShifts = {(person, shift, day): model.addConstr(
    X[person, shift, day] == 1) 
    for person in people for day in days if (person, day) in fixed_shifts for shift in fixed_shifts[person, day]}

# Results
model.optimize()
if model.status == gp.GRB.OPTIMAL:
    for person in people:
        print(f"{person}'s shifts:")
        for day in days:
            for shift in shifts:
                if X[person, shift, day].X > 0.5:  # If the variable is 1
                    print(f"  {day}: {shift[0]}-{shift[1]}")
                    