import sys

#parsing variables and their domains from the file
#example line: X: 1 2 3
def parseVariables(path):
    #list of variable names
    variables = []
    domains = {}

    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                #skips empty lines
                continue
            #split into variable name and it's domain values
            name, values = line.split(":", 1)
            name = name.strip()
            variables.append(name)
            #convert domain values to integers 
            domains[name] = [int(value) for value in values.split()]

    return variables, domains

#parse constraints from the file
#example line: X > Y
def parseConstraints(path):
    constraints = []

    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            parts = line.strip().split()
            if not parts:
                continue
            #each component is stored as (left, operator, right)
            constraints.append((parts[0], parts[1], parts[2]))

    return constraints

#compares two values based on the operator
def compare(left_value, operator, right_value):
    if operator == "=":
        return left_value == right_value
    if operator == "!":
        return left_value != right_value
    if operator == ">":
        return left_value > right_value
    if operator == "<":
        return left_value < right_value
    return False

#checks if the assigning values to variables satisfies the constraint
def allows(constraint, variable, value, other_variable, other_value):
    left, operator, right = constraint

    #checks both directions of the constraint
    if variable == left and other_variable == right:
        return compare(value, operator, other_value)
    if variable == right and other_variable == left:
        return compare(other_value, operator, value)
    #constraint not relevant to the variable assignment
    return True

#builds neighbor relationships between variables based on constraints
def buildNeighbors(variables, constraints):
    neighbors = {variable: [] for variable in variables}

    for constraint in constraints:
        left, _, right = constraint
        #add both directions of the constraint to the neighbors list
        neighbors[left].append((right, constraint))
        neighbors[right].append((left, constraint))

    return neighbors

#checks if any already-assigned variables violate the constraints with the new assignment
def violatesAssignedConstraint(assignments, constraints):
    for left, operator, right in constraints:
        if left in assignments and right in assignments:
            if not compare(assignments[left], operator, assignments[right]):
                return True
    return False

#select next variable to assign
#uses:
    #Minimum Remaining Values (MRV)
    #Degree Heuristic (tie-breaker)
def selectVariable(variables, domains, assignments, neighbors):
    #get unassigned variables
    unassigned = [variable for variable in variables if variable not in assignments]

    def key(variable):
        #count how many variables are still unassigned
        constraining_count = sum(
            1 for neighbor, _ in neighbors[variable] if neighbor not in assignments
        )
        #sort by:
            #1. smallest domain size(MRV)
            #2. most constraining variable (degree heuristic)
            #3. alphabetical order of variable name
        return (len(domains[variable]), -constraining_count, variable)

    return min(unassigned, key=key)

#count how many values would be eliminated from neibhors
#used for least constraining value heuristic
def countEliminatedValues(variable, value, domains, assignments, neighbors):
    eliminated = 0

    for neighbor, constraint in neighbors[variable]:
        if neighbor in assignments:
            continue

        for neighbor_value in domains[neighbor]:
            if not allows(constraint, variable, value, neighbor, neighbor_value):
                eliminated += 1

    return eliminated

#order values using least constraining value (LCV) heuristic
def orderValues(variable, domains, assignments, neighbors):
    return sorted(
        domains[variable],
        key=lambda value: (
            countEliminatedValues(variable, value, domains, assignments, neighbors),
            value,
        ),
    )

#reduces domains after assigning variable
def forwardCheck(variable, value, domains, assignments, neighbors):
    #copy domains
    new_domains = {name: list(values) for name, values in domains.items()}
    new_domains[variable] = [value]

    for neighbor, constraint in neighbors[variable]:
        if neighbor in assignments:
            continue
        
        #filter neighbor domain
        new_domain = [
            neighbor_value
            for neighbor_value in new_domains[neighbor]
            if allows(constraint, variable, value, neighbor, neighbor_value)
        ]
        #if domain becomes empty, then failure
        if not new_domain:
            return None

        new_domains[neighbor] = new_domain

    return new_domains

#formats the branch information for printing
def formatBranch(order, assignments, status):
    text = ", ".join("{}={}".format(variable, assignments[variable]) for variable in order)
    return "{}  {}".format(text, status)

#CSP Solver class (backtracking)
class Solver:
    def __init__(self, variables, domains, constraints, mode):
        self.variables = variables
        self.constraints = constraints
        self.mode = mode
        self.neighbors = buildNeighbors(variables, constraints)
        self.branch_number = 1
    #prints each branch (step)
    def print_branch(self, order, assignments, status):
        print("{}. {}".format(self.branch_number, formatBranch(order, assignments, status)))
        self.branch_number += 1
    #recursive backtrackign search function
    def search(self, assignments, order, domains):
        #if all variables assigned, then solution is found
        if len(assignments) == len(self.variables):
            self.print_branch(order, assignments, "solution")
            return True
        #select next variable to assign
        variable = selectVariable(self.variables, domains, assignments, self.neighbors)

        #try values in LCV order
        for value in orderValues(variable, domains, assignments, self.neighbors):
            next_assignments = dict(assignments)
            next_assignments[variable] = value
            next_order = order + [variable]

            #check the constraint violation
            if violatesAssignedConstraint(next_assignments, self.constraints):
                self.print_branch(next_order, next_assignments, "failure")
                continue
            #apply forward checking if enabled
            next_domains = domains
            if self.mode == "fc":
                next_domains = forwardCheck(
                    variable, value, domains, next_assignments, self.neighbors
                )
                if next_domains is None:
                    self.print_branch(next_order, next_assignments, "failure")
                    continue
            #recurse
            if self.search(next_assignments, next_order, next_domains):
                return True

        return False

#start of the main function
def main():
    if len(sys.argv) != 4:
        return

    var_file, con_file, mode = sys.argv[1], sys.argv[2], sys.argv[3]
    if mode not in ("none", "fc"):
        return
    #mode could be:
        #none - plain backtracking
        #fc - forward checking
    variables, domains = parseVariables(var_file)
    constraints = parseConstraints(con_file)

    solver = Solver(variables, domains, constraints, mode)
    solver.search({}, [], domains)


if __name__ == "__main__":
    main()
