#Partner 1: Sathwika Thatiparthi
#Partner 2: Sadwitha Thopucharla

#this program implements a constraint satisfaction problem (CSP) solver
#it uses:
#  - Backtracking search
#  - MRV (minimum remaining value) heuristic
#  - Degree heuristic
#  - LCV heuristic
#  - optional forward checking

#input:
#  -Varaible file: defines variables and their domains
# -constraint file: defines relationships between variables

#output:
#  -step-by-step search tree with solutions and failures

import sys

#Parses the variables and their domains from the given file
#Each line in the file looks like: X: 1 2 3
def parseVariables(path):
    #List to store variable names
    variables = []

    #dictionary to store variable domains
    domains = {}

    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                #skip empty lines 
                continue
            #split the line into variable name and its domain values
            name, values = line.split(":", 1)
            name = name.strip()
            variables.append(name)
            # Convert each domain value to an integer
            domains[name] = [int(value) for value in values.split()]

    return variables, domains

# Parses constraints from the file
# Example line looks like: X > Y
def parseConstraints(path):
    constraints = []

    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            parts = line.strip().split()
            if not parts:
                continue
            #Stores each constraint as a tuple: (left, operator, right)
            constraints.append((parts[0], parts[1], parts[2]))

    return constraints

#Compares two values using the given operator
def compare(leftValue, operator, rightValue):
    if operator == "=":
        return leftValue == rightValue
    if operator == "!":
        return leftValue != rightValue
    if operator == ">":
        return leftValue > rightValue
    if operator == "<":
        return leftValue < rightValue
    #If operator is unknown then return False
    return False

#Checks whether assigning 'value' to 'variable' is allowed when compared to another variables assignment.
def allows(constraint, variable, value, otherVariable, otherValue):
    left, operator, right = constraint

    # Checks both directions of the constraint
    if variable == left and otherVariable == right:
        return compare(value, operator, otherValue)
    if variable == right and otherVariable == left:
        return compare(otherValue, operator, value)
    return True

# Builds a neighbor list so we know which variables directly interact via constraints.
def buildNeighbors(variables, constraints):
    # Start with empty neighbor lists
    neighbors = {variable: [] for variable in variables}

    for constraint in constraints:
        left, _, right = constraint
        # Add each variable as a neighbor of the other
        neighbors[left].append((right, constraint))
        neighbors[right].append((left, constraint))

    return neighbors

# Checks whether any constraints are violated by the current partial assignment.
def violatesAssignedConstraint(assignments, constraints):
    for left, operator, right in constraints:
        # Only check constraints where both variables have been assigned
        if left in assignments and right in assignments:
            if not compare(assignments[left], operator, assignments[right]):
                return True
    return False

# Selects the next variable to assign using:
# 1. MRV - Minimum Remaining Values
# 2. Degree heuristic 
def selectVariable(variables, domains, assignments, neighbors):
    unassigned = [variable for variable in variables if variable not in assignments]

    def key(variable):
        # Count how many neighbors are still unassigned (degree heuristic)
        constrainingCount = sum(
            1 for neighbor, _ in neighbors[variable] if neighbor not in assignments
        )
        # Sort by:
        # 1. Smallest domain size 
        # 2. Most constraining variable 
        # 3. Alphabetical order 
        return (len(domains[variable]), -constrainingCount, variable)

    return min(unassigned, key=key)

# Counts how many values would be eliminated from neighbors if we assign this value.
# Used for the Least Constraining Value heuristic.
def countEliminatedValues(variable, value, domains, assignments, neighbors):
    eliminated = 0

    for neighbor, constraint in neighbors[variable]:
        if neighbor in assignments:
            continue

        for neighborValue in domains[neighbor]:
            if not allows(constraint, variable, value, neighbor, neighborValue):
                eliminated += 1

    return eliminated

# Orders values using the LCV heuristic.
def orderValues(variable, domains, assignments, neighbors):
    return sorted(
        domains[variable],
        key=lambda value: (
            countEliminatedValues(variable, value, domains, assignments, neighbors),
            value,
        ),
    )

# Applies forward checking by removing values from neighbor domains
# that are no longer possible after assigning (variable = value).
def forwardCheck(variable, value, domains, assignments, neighbors):
     # Make a deep copy of domains so we don't modify the original
    newDomains = {name: list(values) for name, values in domains.items()}
    newDomains[variable] = [value]

    for neighbor, constraint in neighbors[variable]:
        if neighbor in assignments:
            continue
        
        # Keep only values that satisfy the constraint
        newDomain = [
            neighborValue
            for neighborValue in newDomains[neighbor]
            if allows(constraint, variable, value, neighbor, neighborValue)
        ]
        # If a domain becomes empty, forward checking fails
        if not newDomain:
            return None

        newDomains[neighbor] = newDomain

    return newDomains

# Formats the branch information for printing
def formatBranch(order, assignments, status):
    text = ", ".join("{}={}".format(variable, assignments[variable]) for variable in order)
    return "{}  {}".format(text, status)

#CSP Solver class using backtracking
class Solver:
    def __init__(self, variables, domains, constraints, mode):
        self.variables = variables
        self.constraints = constraints
        self.mode = mode
        self.neighbors = buildNeighbors(variables, constraints)
        self.branch_number = 1
    # Prints each branch of search tree
    def print_branch(self, order, assignments, status):
        print("{}. {}".format(self.branch_number, formatBranch(order, assignments, status)))
        self.branch_number += 1
    # Recursive backtrackign search
    def search(self, assignments, order, domains):
        # If all variables assigned, then solution is found
        if len(assignments) == len(self.variables):
            self.print_branch(order, assignments, "solution")
            return True

        variable = selectVariable(self.variables, domains, assignments, self.neighbors)

        #try values in LCV order
        for value in orderValues(variable, domains, assignments, self.neighbors):
            nextAssignments = dict(assignments)
            nextAssignments[variable] = value
            nextOrder = order + [variable]

            # Check if this assignment violates any constraints
            if violatesAssignedConstraint(nextAssignments, self.constraints):
                self.print_branch(nextOrder, nextAssignments, "failure")
                continue
            # Apply forward checking if enabled
            next_domains = domains
            if self.mode == "fc":
                next_domains = forwardCheck(
                    variable, value, domains, nextAssignments, self.neighbors
                )
                if next_domains is None:
                    self.print_branch(nextOrder, nextAssignments, "failure")
                    continue
            #recurse
            if self.search(nextAssignments, nextOrder, next_domains):
                return True

        return False

#main function that loads files and starts the solver
def main():
    if len(sys.argv) != 4:
        return

    varFile, conFile, mode = sys.argv[1], sys.argv[2], sys.argv[3]
    if mode not in ("none", "fc"):
        return
    #modes:
    # none: plain backtracking
    # fc: forward checking enabled
    variables, domains = parseVariables(varFile)
    constraints = parseConstraints(conFile)

    solver = Solver(variables, domains, constraints, mode)
    solver.search({}, [], domains)


if __name__ == "__main__":
    main()
