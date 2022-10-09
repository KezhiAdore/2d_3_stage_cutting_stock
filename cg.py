import numpy as np
import gurobipy as gp
from gurobipy import GRB


class MasterProblem:
    def __init__(self):
        self.model = gp.Model("master")
        self.vars = None
        self.constrs = None

    def setup(self, patterns, demand, aij):
        self.J = len(aij[0])
        num_patterns = len(patterns)
        self.aij = aij
        self.vars = self.model.addVars(num_patterns, obj=1, name="Pattern")
        aij_pattern_i_k = np.dot(np.array(aij), np.array(patterns).T)
        print('finish aij_pattern_i_k')
        self.constrs = self.model.addConstrs((gp.quicksum(aij_pattern_i_k[i][pattern]*self.vars[pattern]
                                                          for pattern in range(num_patterns))
                                              >= demand[i] for i in range(len(demand))),
                                             name="Demand")

        self.model.modelSense = GRB.MINIMIZE
        # Turning off output because of the iterative procedure
        self.model.params.outputFlag = 0
        self.model.update()
        print('finish master setup')

    def update(self, pattern, index):
        # j 通过aij变成i
        pattern_i = np.dot(self.aij, pattern)
        new_col = gp.Column(coeffs=pattern_i, constrs=self.constrs.values())
        self.vars[index] = self.model.addVar(obj=1, column=new_col,
                                             name=f"Pattern[{index}]")
        self.model.update()
        print('finish master update')


class SubProblem:
    def __init__(self):
        self.model = gp.Model("subproblem")
        self.vars = {}
        self.constr = None

    def dual_axis(self, duals):
        duals_new = [0 for _ in range(len(self.lengths))]
        for j in range(len(self.lengths)):  # j索引
            max_dual = 0
            for i in range(len(duals)):
                duals_new[j] += duals[i]*self.aij[i][j]

        return duals_new

    def setup(self, plate_length, lengths, duals, aij):
        # dual维度转换，现在是i的维度，需要转换成j的维度
        self.lengths = lengths
        self.aij = aij

        duals_new = self.dual_axis(duals)
        self.vars = self.model.addVars(len(lengths), obj=duals_new, vtype=GRB.BINARY,
                                       name="Frequency")
        self.constr = self.model.addConstr(self.vars.prod(lengths) <= plate_length,
                                           name="Knapsack")
        self.model.modelSense = GRB.MAXIMIZE
        # Turning off output because of the iterative procedure
        self.model.params.outputFlag = 0
        # Stop the subproblem routine as soon as the objective's best bound becomes
        # less than or equal to one, as this implies a non-negative reduced cost for
        # the entering column.
        self.model.params.bestBdStop = 1
        self.model.update()
        print('finish sub setup')

    def uptate_forbidden(self, pattern):
        for i in range(len(pattern)):
            if pattern[i] > 0:
                self.forbidden[i] = 0
        print('finish forbidden update')

    def update(self, duals):
        duals_new = self.dual_axis(duals)
        self.model.setAttr("obj", self.vars, duals_new)
        self.model.update()
        print('finish sub update')


class CuttingStock:
    def __init__(self, plate_length, demand, lengths, aij):
        # demand 是items i的需求量，lengths是segment j 的长度,aij是segment j提供的item i的数量
        self.plate_length = plate_length
        # self.pieces, self.lengths, self.demand = gp.multidict(pieces)
        self.I = len(demand)
        self.J = len(lengths)
        print(self.I, self.J)
        self.demand = demand
        self.lengths = lengths
        self.aij = aij
        self.patterns = None
        self.duals = [0 for _ in range(self.I)]
        # piece_reqs = [length*req for length, req in pieces.values()]
        # self.min_plate = np.ceil(sum(demand)/plate_length)
        self.solution = {}
        self.master = MasterProblem()
        self.subproblem = SubProblem()
        print('finish init')

    def _initialize_patterns(self):
        # Find trivial patterns that consider one final piece at a time,
        # fitting as many pieces as possible into the stock material unit
        # 用单个segment去装满plate_length
        patterns = []
        # for idx, length in self.lengths.items():
        for i in range(len(self.lengths)):
            pattern = [0 for _ in range(self.J)]
            pattern[i] = 1
            patterns.append(pattern)
        self.patterns = patterns
        print('finish init patterns')

    def _generate_patterns(self):
        self._initialize_patterns()
        self.master.setup(self.patterns, self.demand, self.aij)
        self.subproblem.setup(
            self.plate_length, self.lengths, self.duals, self.aij)
        while True:
            self.master.model.optimize()
            print('Obj: %g' % self.master.model.objVal)
            self.duals = self.master.model.getAttr("pi", self.master.constrs)
            self.subproblem.update(self.duals)

            self.subproblem.model.optimize()
            reduced_cost = 1 - self.subproblem.model.objVal
            if reduced_cost >= -0.01:
                break
            pattern = [0]*self.J
            for piece, var in self.subproblem.vars.items():
                if var.x > 0.5:
                    pattern[piece] = round(var.x)
                    print(piece)
            self.master.update(pattern, len(self.patterns))
            self.patterns.append(pattern)

            print(f"Reduced cost: {reduced_cost:.2f}")

    def solve(self):
        """
        Gurobi does not support branch-and-price, as this requires to add columns
        at local nodes of the search tree. A heuristic is used instead, where the
        integrality constraints for the variables of the final root LP relaxation
        are installed and the resulting MIP is solved. Note that the optimal
        solution could be overlooked, as additional columns are not generated at
        the local nodes of the search tree.
        """
        self._generate_patterns()
        self.master.model.setAttr("vType", self.master.vars, GRB.INTEGER)
        self.master.model.params.timeLimit = 300
        self.master.model.optimize()
        print('finish master solve')

        for pattern, var in self.master.vars.items():
            if var.x > 0.5:
                self.solution[pattern] = round(var.x)
