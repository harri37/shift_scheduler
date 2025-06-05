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
        
        
FULLY_AVAILABLE = [1] * len(times)
NEVER_AVAILABLE = [0] * len(times)
# Data
availability = {
    ("Harrison", "Monday"): FULLY_AVAILABLE,
    ("Harrison", "Tuesday"): [1, 0, 0, 1, 1, 1, 1, 1],  
    ("Harrison", "Wednesday"): [0, 1, 1, 1, 1, 1, 1, 1],
    ("Harrison", "Thursday"): [0, 0, 0, 0, 0, 0, 1, 1],
    ("Harrison", "Friday"): [1, 1, 0, 1, 1, 1, 0, 0],
    ("Dhanan", "Monday"): [1, 1, 1, 1, 1, 0, 0, 0],
    ("Dhanan", "Tuesday"): [0, 0, 0, 0, 0, 1, 1, 0],
    ("Dhanan", "Wednesday"): [1, 0, 0, 1, 1, 1, 0, 0],
    ("Dhanan", "Thursday"): [1, 1, 1, 1, 1, 0, 0, 0],
    ("Dhanan", "Friday"): [0, 1, 1, 0, 0, 0, 0, 0],
    ("Erin", "Monday"): [0, 0, 0, 0, 0, 0, 1, 1],
    ("Erin", "Tuesday"): [0, 0, 0, 0, 0, 0, 1, 1],
    ("Erin", "Wednesday"): [0, 0, 0, 0, 0, 0, 1, 1],
    ("Erin", "Thursday"): FULLY_AVAILABLE,
    ("Erin", "Friday"): [0, 0, 0, 0, 0, 0, 1, 1],
    ("Ella", "Monday"): [0, 0, 0, 0, 0, 0, 1, 0],
    ("Ella", "Tuesday"): [0, 0, 1, 1, 1, 1, 1, 0],
    ("Ella", "Wednesday"): [0, 0, 0, 0, 0, 1, 1, 0],
    ("Ella", "Thursday"): [0, 1, 1, 1, 0, 0, 0, 0],
    ("Ella", "Friday"): NEVER_AVAILABLE,
}

max_total = {
    "Harrison": 100,
    "Dhanan": 100,
    "Erin": 100,
    "Ella": 100
}

max_consecutive = {
    "Harrison": 8,
    "Dhanan": 8,
    "Erin": 8,
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
    # ("Erin", "Tuesday"): [(15, 17)],
    # ("Erin", "Thursday"): [(13, 17), (9, 10)],
    # ("Erin", "Friday"): [(15, 17)],
}

available_hours = len(times) * days 

num_days_weight = 2e2
num_shifts_weight = 2e1
hours_covered_weight = 2e6
max_hours_weight = 2e5
min_hours_weight = 2e4
worthwhile_weight = 2e3

WORTHWHILE_THRESHOLD = 4
MAX_SHIFT_LENGTH = len(times)  

# Variables 
model = gp.Model("Shift Scheduling")
X = {(person, shift, day): model.addVar(vtype=gp.GRB.BINARY) for person in people for shift in shifts for day in days}
Y = {(person, day): model.addVar(vtype=gp.GRB.BINARY) for person in people for day in days}
MAX_HOURS = model.addVar(vtype=gp.GRB.INTEGER)
MIN_HOURS = model.addVar(vtype=gp.GRB.INTEGER)
W = {(person, day): model.addVar(vtype=gp.GRB.BINARY) for person in people for day in days}

# Objective
model.setObjective(
    gp.quicksum(Y[person, day] for person in people for day in days) * num_days_weight + \
    gp.quicksum(X[person, shift, day] for person in people for shift in shifts for day in days) * num_shifts_weight - \
    gp.quicksum(X[person, shift, day] * lengths[shift] for person in people for shift in shifts for day in days) * hours_covered_weight + \
    max_hours_weight * MAX_HOURS - \
    min_hours_weight * MIN_HOURS - \
    gp.quicksum(W[person, day] for person in people for day in days) * worthwhile_weight,
    gp.GRB.MINIMIZE)

days_in = {
    "Harrison": ["Wednesday", "Thursday", "Friday"],
    "Dhanan": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    "Erin": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    "Ella": ["Monday", "Tuesday", "Wednesday", "Thursday"]
}

# Constraints
maxHours = {person: model.addConstr(
    gp.quicksum(X[person, shift, day] * lengths[shift] for shift in shifts for day in days) <= max_total[person])
    for person in people}

noOverlap = {(time, day): model.addConstr(
    gp.quicksum(X[person, shift, day] * contains[(shift, time)] for person in people for shift in shifts) <= 1)
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

noBackToBack = {(person, shift, other_shift, day): model.addConstr(
    X[person, other_shift, day] + X[person, shift, day] <= 1)
                for person in people for shift in shifts for other_shift in shifts if shift[0] ==  other_shift[1] for day in days}

maxHours = {person: model.addConstr(
    MAX_HOURS >= gp.quicksum(X[person, shift, day] * lengths[shift] for shift in shifts for day in days))
    for person in people}

minHours = {person: model.addConstr(
    MIN_HOURS <= gp.quicksum(X[person, shift, day] * lengths[shift] for shift in shifts for day in days))
    for person in people}

daysAlreadyIn = {(person, day): model.addConstr(
    W[person, day] == 1)
    for person in people for day in days if day in days_in[person]}

worthwhileShifts = {(person, day): model.addConstr(
    W[person, day] >= (gp.quicksum(X[person, shift, day] * lengths[shift] for shift in shifts) - WORTHWHILE_THRESHOLD) / MAX_SHIFT_LENGTH)
    for person in people for day in days}

# Results
model.optimize()
if model.status == gp.GRB.OPTIMAL:
    for person in people:
        total_hours = sum(X[person, shift, day].X * lengths[shift] for shift in shifts for day in days)
        print(f"{person}'s shifts:")
        for day in days:
            for shift in shifts:
                if X[person, shift, day].X > 0.5:  # If the variable is 1
                    print(f"  {day}: {shift[0]}-{shift[1]}")
        print(f"Total hours: {total_hours}\n")
        
for day in days:
    for time in times:
        covered = sum(X[person, shift, day].X * contains[(shift, time)] for person in people for shift in shifts)
        if not covered:
            print(f"No one is scheduled at {time} on {day}.")