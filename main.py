import gurobipy as gp
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from datetime import datetime, timedelta


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
    ("Harrison", "Tuesday"): [1, 1, 1, 1, 1, 1, 1, 0],  
    ("Harrison", "Wednesday"): [1, 1, 1, 1, 1, 0, 0, 1],
    ("Harrison", "Thursday"): FULLY_AVAILABLE,
    ("Harrison", "Friday"): [1, 1, 1, 0, 0, 0, 0, 1],
    
    ("Dhanan", "Monday"): [0, 0, 0, 0, 0, 1, 1, 1],
    ("Dhanan", "Tuesday"): [0, 0, 0, 0, 0, 0, 0, 1],
    ("Dhanan", "Wednesday"): [0, 0, 0, 0, 0, 1, 1, 1],
    ("Dhanan", "Thursday"): [0, 0, 0, 1, 1, 1, 1, 1],
    ("Dhanan", "Friday"): [0, 0, 0, 0, 0, 0, 0, 1],
    
    ("Erin", "Monday"): [0, 1, 0, 0, 1, 1, 1, 1],
    ("Erin", "Tuesday"): [0, 1, 0, 0, 0, 1, 1, 1],
    ("Erin", "Wednesday"): [0, 1, 0, 0, 0, 1, 1, 1],
    ("Erin", "Thursday"): [0, 1, 0, 0, 0, 1, 1, 1],
    ("Erin", "Friday"): [0, 1, 0, 0, 0, 1, 1, 1],
    
    ("Ella", "Monday"): NEVER_AVAILABLE,
    ("Ella", "Tuesday"): [1, 0, 0, 1, 1, 0, 0, 0],
    ("Ella", "Wednesday"): [0, 1, 1, 1, 1, 0, 0, 0],
    ("Ella", "Thursday"): NEVER_AVAILABLE,
    ("Ella", "Friday"): [0, 1, 1, 1, 1, 1, 1, 0],
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

WORTHWHILE_THRESHOLD = 4
MAX_SHIFT_LENGTH = len(times)  

# Variables 
model = gp.Model("Shift Scheduling")
X = {(person, shift, day): model.addVar(vtype=gp.GRB.BINARY) for person in people for shift in shifts for day in days}
Y = {(person, day): model.addVar(vtype=gp.GRB.BINARY) for person in people for day in days}
MAX_HOURS_DIFF = model.addVar(vtype=gp.GRB.INTEGER)
W = {(person, day): model.addVar(vtype=gp.GRB.BINARY) for person in people for day in days}

# Multi-objective formulation with pure priority-based optimization
# Priority 1: Maximize hours covered (most important) - use negative to maximize in minimization
model.setObjectiveN(-gp.quicksum(X[person, shift, day] * lengths[shift] 
                                for person in people for shift in shifts for day in days),
                    index=0, priority=5, name="Hours Covered")

# Priority 2: Minimize hours difference between people (fairness)
model.setObjectiveN(MAX_HOURS_DIFF, 
                    index=1, priority=4, name="Hours Difference")

# Priority 3: Maximize worthwhile shifts - use negative to maximize in minimization
model.setObjectiveN(-gp.quicksum(W[person, day] for person in people for day in days), 
                    index=2, priority=3, name="Worthwhile Shifts")

# Priority 4: Minimize days worked (fewer days is better)
model.setObjectiveN(gp.quicksum(Y[person, day] for person in people for day in days), 
                    index=3, priority=2, name="Days Worked")

# Priority 5: Minimize total shifts (fewer shifts is better)
model.setObjectiveN(gp.quicksum(X[person, shift, day] for person in people for shift in shifts for day in days),
                    index=4, priority=1, name="Total Shifts")

# Set model to minimize
model.ModelSense = gp.GRB.MINIMIZE

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

maxHoursDiff = {(person_1, person_2): model.addConstr(
    MAX_HOURS_DIFF >= gp.quicksum(X[person_1, shift, day] * lengths[shift] for shift in shifts for day in days) - \
        gp.quicksum(X[person_2, shift, day] * lengths[shift] for shift in shifts for day in days))
    for person_1 in people for person_2 in people if person_1 != person_2}

daysAlreadyIn = {(person, day): model.addConstr(
    W[person, day] == 1)
    for person in people for day in days if day in days_in[person]}

worthwhileShifts = {(person, day): model.addConstr(
    W[person, day] >= (gp.quicksum(X[person, shift, day] * lengths[shift] for shift in shifts) - WORTHWHILE_THRESHOLD) / MAX_SHIFT_LENGTH)
    for person in people for day in days}

def visualize_timetable():
    """
    Create a visual representation of the optimized timetable using matplotlib.
    Shows a grid with days on x-axis, times on y-axis, and colored blocks for each person's shifts.
    """
    if model.status != gp.GRB.OPTIMAL:
        print("No optimal solution found. Cannot visualize timetable.")
        return
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Define colors for each person
    colors = {
        "Harrison": "#FF6B6B",  # Red
        "Dhanan": "#4ECDC4",    # Teal
        "Erin": "#45B7D1",      # Blue
        "Ella": "#96CEB4"       # Green
    }
    
    # Create the grid
    day_positions = {day: i for i, day in enumerate(days)}
    time_positions = {time: len(times) - 1 - times.index(time) for time in times}
    
    # Plot the scheduled shifts
    for person in people:
        for day in days:
            for shift in shifts:
                if X[person, shift, day].X > 0.5:  # If the shift is scheduled
                    start_time, end_time = shift
                    
                    # Calculate position and size
                    x = day_positions[day]
                    y = time_positions[end_time - 1]  # Start from the end time position
                    width = 0.8
                    height = end_time - start_time
                    
                    # Create rectangle for the shift
                    rect = patches.Rectangle(
                        (x + 0.1, y), width, height,
                        linewidth=1, edgecolor='black',
                        facecolor=colors[person], alpha=0.7
                    )
                    ax.add_patch(rect)
                    
                    # Add person's name in the middle of the shift
                    if height >= 1:  # Only add text if shift is long enough
                        ax.text(
                            x + 0.5, y + height/2, person,
                            ha='center', va='center', fontsize=8,
                            fontweight='bold', color='white'
                        )
    
    # Set up the grid
    ax.set_xlim(0, len(days))
    ax.set_ylim(0, len(times))
    
    # Set labels
    ax.set_xticks([i + 0.5 for i in range(len(days))])
    ax.set_xticklabels(days)
    ax.set_yticks([i + 0.5 for i in range(len(times))])
    ax.set_yticklabels([f"{times[len(times) - 1 - i]}:00" for i in range(len(times))])
    
    # Add grid lines
    ax.set_xticks(range(len(days) + 1), minor=True)
    ax.set_yticks(range(len(times) + 1), minor=True)
    ax.grid(True, which='minor', alpha=0.3)
    
    # Labels and title
    ax.set_xlabel('Days', fontsize=12, fontweight='bold')
    ax.set_ylabel('Time', fontsize=12, fontweight='bold')
    ax.set_title('Optimized Timetable', fontsize=16, fontweight='bold')
    
    # Create legend
    legend_elements = [patches.Rectangle((0, 0), 1, 1, facecolor=colors[person], 
                                       alpha=0.7, label=person) for person in people]
    ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.02, 1))
    
    # Adjust layout to prevent legend cutoff
    plt.tight_layout()
    
    # Show coverage statistics
    print("\n" + "="*50)
    print("TIMETABLE COVERAGE ANALYSIS")
    print("="*50)
    
    total_slots = 0
    covered_slots = 0
    
    for day in days:
        uncovered_times = []
        for time in times:
            total_slots += 1
            covered = sum(X[person, shift, day].X * contains[(shift, time)] 
                         for person in people for shift in shifts)
            if covered > 0:
                covered_slots += 1
            else:
                uncovered_times.append(f"{time}:00")
        
        if uncovered_times:
            print(f"{day}: Uncovered times: {', '.join(uncovered_times)}")
        else:
            print(f"{day}: Fully covered!")
    
    coverage_percentage = (covered_slots / total_slots) * 100
    print(f"\nOverall Coverage: {covered_slots}/{total_slots} ({coverage_percentage:.1f}%)")
    
    # Show individual workload
    print("\n" + "="*30)
    print("INDIVIDUAL WORKLOADS")
    print("="*30)
    
    for person in people:
        total_hours = sum(X[person, shift, day].X * lengths[shift] for shift in shifts for day in days)
        days_worked = sum(1 for day in days if any(X[person, shift, day].X > 0.5 for shift in shifts))
        print(f"{person:>8}: {total_hours:>4.0f} hours across {days_worked} days")
    
    plt.show()


def print_detailed_schedule():
    """
    Print a detailed text-based schedule for each person.
    """
    if model.status != gp.GRB.OPTIMAL:
        print("No optimal solution found.")
        return
    
    print("\n" + "="*60)
    print("DETAILED SCHEDULE")
    print("="*60)
    
    for person in people:
        print(f"\n{person.upper()}'S SCHEDULE:")
        print("-" * 25)
        
        total_hours = 0
        person_schedule = {}
        
        for day in days:
            day_shifts = []
            for shift in shifts:
                if X[person, shift, day].X > 0.5:
                    start_time, end_time = shift
                    day_shifts.append((start_time, end_time))
                    total_hours += lengths[shift]
            
            if day_shifts:
                # Sort shifts by start time
                day_shifts.sort()
                person_schedule[day] = day_shifts
        
        if person_schedule:
            for day, shifts_list in person_schedule.items():
                shift_strings = [f"{start}:00-{end}:00" for start, end in shifts_list]
                print(f"  {day:>9}: {', '.join(shift_strings)}")
            print(f"  {'Total':>9}: {total_hours} hours")
        else:
            print("  No shifts assigned")


# Results
model.optimize()
if model.status == gp.GRB.OPTIMAL:
    print("Optimization completed successfully!")
    print(f"Objective value: {model.objVal}")
    
    # Call the visualization functions
    print_detailed_schedule()
    visualize_timetable()
    
else:
    print(f"Optimization failed with status: {model.status}")
    if model.status == gp.GRB.INFEASIBLE:
        print("The problem is infeasible - no solution exists that satisfies all constraints.")
    elif model.status == gp.GRB.UNBOUNDED:
        print("The problem is unbounded.")
    else:
        print("Other optimization status encountered.")


