import sys


def parse_variables(path):
    variables = []
    domains = {}

    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue

            name, values = line.split(":", 1)
            name = name.strip()
            variables.append(name)
            domains[name] = [int(value) for value in values.split()]

    return variables, domains


def parse_constraints(path):
    constraints = []

    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            parts = line.strip().split()
            if not parts:
                continue
            constraints.append((parts[0], parts[1], parts[2]))

    return constraints


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


def allows(constraint, variable, value, other_variable, other_value):
    left, operator, right = constraint

    if variable == left and other_variable == right:
        return compare(value, operator, other_value)
    if variable == right and other_variable == left:
        return compare(other_value, operator, value)

    return True


def build_neighbors(variables, constraints):
    neighbors = {variable: [] for variable in variables}

    for constraint in constraints:
        left, _, right = constraint
        neighbors[left].append((right, constraint))
        neighbors[right].append((left, constraint))

    return neighbors


def violates_assigned_constraint(assignments, constraints):
    for left, operator, right in constraints:
        if left in assignments and right in assignments:
            if not compare(assignments[left], operator, assignments[right]):
                return True
    return False


def select_variable(variables, domains, assignments, neighbors):
    unassigned = [variable for variable in variables if variable not in assignments]

    def key(variable):
        constraining_count = sum(
            1 for neighbor, _ in neighbors[variable] if neighbor not in assignments
        )
        return (len(domains[variable]), -constraining_count, variable)

    return min(unassigned, key=key)


def count_eliminated_values(variable, value, domains, assignments, neighbors):
    eliminated = 0

    for neighbor, constraint in neighbors[variable]:
        if neighbor in assignments:
            continue

        for neighbor_value in domains[neighbor]:
            if not allows(constraint, variable, value, neighbor, neighbor_value):
                eliminated += 1

    return eliminated


def order_values(variable, domains, assignments, neighbors):
    return sorted(
        domains[variable],
        key=lambda value: (
            count_eliminated_values(variable, value, domains, assignments, neighbors),
            value,
        ),
    )


def forward_check(variable, value, domains, assignments, neighbors):
    new_domains = {name: list(values) for name, values in domains.items()}
    new_domains[variable] = [value]

    for neighbor, constraint in neighbors[variable]:
        if neighbor in assignments:
            continue

        new_domain = [
            neighbor_value
            for neighbor_value in new_domains[neighbor]
            if allows(constraint, variable, value, neighbor, neighbor_value)
        ]

        if not new_domain:
            return None

        new_domains[neighbor] = new_domain

    return new_domains


def format_branch(order, assignments, status):
    text = ", ".join("{}={}".format(variable, assignments[variable]) for variable in order)
    return "{}  {}".format(text, status)


class Solver:
    def __init__(self, variables, domains, constraints, mode):
        self.variables = variables
        self.constraints = constraints
        self.mode = mode
        self.neighbors = build_neighbors(variables, constraints)
        self.branch_number = 1

    def print_branch(self, order, assignments, status):
        print("{}. {}".format(self.branch_number, format_branch(order, assignments, status)))
        self.branch_number += 1

    def search(self, assignments, order, domains):
        if len(assignments) == len(self.variables):
            self.print_branch(order, assignments, "solution")
            return True

        variable = select_variable(self.variables, domains, assignments, self.neighbors)

        for value in order_values(variable, domains, assignments, self.neighbors):
            next_assignments = dict(assignments)
            next_assignments[variable] = value
            next_order = order + [variable]

            if violates_assigned_constraint(next_assignments, self.constraints):
                self.print_branch(next_order, next_assignments, "failure")
                continue

            next_domains = domains
            if self.mode == "fc":
                next_domains = forward_check(
                    variable, value, domains, next_assignments, self.neighbors
                )
                if next_domains is None:
                    self.print_branch(next_order, next_assignments, "failure")
                    continue

            if self.search(next_assignments, next_order, next_domains):
                return True

        return False


def main():
    if len(sys.argv) != 4:
        return

    var_file, con_file, mode = sys.argv[1], sys.argv[2], sys.argv[3]
    if mode not in ("none", "fc"):
        return

    variables, domains = parse_variables(var_file)
    constraints = parse_constraints(con_file)

    solver = Solver(variables, domains, constraints, mode)
    solver.search({}, [], domains)


if __name__ == "__main__":
    main()
