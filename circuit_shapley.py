#!/usr/bin/env python3

import pandas as pd
from decimal import *
from collections import deque
from comb_cache import CombCache

OTHERVAR = -1

VARGATE = 1
NEGGATE = 2
ORGATE = 3
ANDGATE = 4
TRUECONST = 5
FALSECONST = 6

def factorial(k):
    return Decimal(CombCache.getInstance().factorial(k))

def comb(N, k):
    return Decimal(CombCache.getInstance().comb(N, k))


class CircuitShapley:

    def __init__(self, circuit_filepath, forget_vars=None):

        self._forget_vars = set()
        if forget_vars is not None:
            self._forget_vars = set(forget_vars)

        self.__read_nnf__(circuit_filepath)
        self.__topsort__()

    # nnf format described here http://reasoning.cs.ucla.edu/c2d/download.php. We make the circuit binary at the same time
    def __read_nnf__(self, filepath):
        file = open(filepath)
        self._children = {}  # children[i] is a list containing the children of gate i (size 0 or 1 or 2 since I assume my circuits to be binary and I have explicit constant gates)
        self._gateTypes = {}  # gateType[i] is the type of gate i
        self._variables = {}  # when gateType[i] is VARGATE, variables[i] is the variable that this gate holds
        self._outputGate = -1

        currentGate = 0
        for line in file:
            parsed = [x.strip() for x in line.split(' ')]
            if parsed[0] == 'nnf':
                nbgates = int(parsed[1])
                additionalGate = nbgates  # Used to make the nnf binary and also to represent negative literals as negation gates of a variable gate
                self._outputGate = nbgates - 1
            elif parsed[0] == 'L':
                if abs(int(parsed[1])) in self._forget_vars:  # a literal we wish to forget
                    self._gateTypes[currentGate] = TRUECONST
                    self._children[currentGate] = []
                else:
                    if int(parsed[1]) > 0:  # a positive literal
                        self._variables[currentGate] = int(parsed[1])
                        self._gateTypes[currentGate] = VARGATE
                        self._children[currentGate] = []
                    elif int(parsed[1]) < 0:  # a negative literal. We create an additional variable gate and create a neggate for the negative literal
                        self._variables[additionalGate] = - int(parsed[1])
                        self._gateTypes[additionalGate] = VARGATE
                        self._children[additionalGate] = []
                        self._gateTypes[currentGate] = NEGGATE
                        self._children[currentGate] = [additionalGate]
                        additionalGate += 1
                currentGate += 1
            elif parsed[0] == 'A':
                if int(parsed[1]) == 0:  # this is a constant 1-gate
                    self._gateTypes[currentGate] = TRUECONST
                    self._children[currentGate] = []
                elif int(parsed[1]) == 1:  # only one input gate. we create an additional constant true gate to make it binary (this will simplify the code later)
                    self._gateTypes[currentGate] = ANDGATE
                    self._gateTypes[additionalGate] = TRUECONST
                    self._children[currentGate] = [int(parsed[2]), additionalGate]
                    self._children[additionalGate] = []
                    additionalGate += 1
                elif int(parsed[1]) == 2:  # two input gates
                    self._gateTypes[currentGate] = ANDGATE
                    self._children[currentGate] = [int(parsed[2]), int(parsed[3])]
                else:  # strictly more than 2 input gates, we binarize
                    self._gateTypes[currentGate] = ANDGATE
                    self._children[currentGate] = [int(parsed[2])]
                    self._gateTypes[additionalGate] = ANDGATE
                    self._children[currentGate].append(additionalGate)
                    i = 1
                    while i <= int(parsed[1]) - 3:
                        self._children[additionalGate] = [int(parsed[2 + i])]
                        self._gateTypes[additionalGate + 1] = ANDGATE
                        self._children[additionalGate].append(additionalGate + 1)
                        additionalGate += 1
                        i += 1
                    self._children[additionalGate] = [int(parsed[2 + i]), int(parsed[3 + i])]
                    additionalGate += 1
                currentGate += 1
            elif parsed[0] == 'O':
                if int(parsed[2]) == 0:  # this is a constant 0-gate
                    self._gateTypes[currentGate] = FALSECONST
                    self._children[currentGate] = []
                elif int(parsed[2]) == 1:  # only one input gate. we create an additional constant false gate to make it binary (this will simplify the code later)
                    self._gateTypes[currentGate] = ORGATE
                    self._gateTypes[additionalGate] = FALSECONST
                    self._children[currentGate] = [int(parsed[3]), additionalGate]
                    self._children[additionalGate] = []
                    additionalGate += 1
                elif int(parsed[2]) == 2:  # two input gates
                    self._gateTypes[currentGate] = ORGATE
                    self._children[currentGate] = [int(parsed[3]), int(parsed[4])]
                else:  # strictly more than 2 input gates, we binarize
                    self._gateTypes[currentGate] = ORGATE
                    self._children[currentGate] = [int(parsed[3])]
                    self._gateTypes[additionalGate] = ORGATE
                    self._children[currentGate].append(additionalGate)
                    i = 1
                    while i <= int(parsed[2]) - 3:
                        self._children[additionalGate] = [int(parsed[3 + i])]
                        self._gateTypes[additionalGate + 1] = ORGATE
                        self._children[additionalGate].append(additionalGate + 1)
                        additionalGate += 1
                        i += 1
                    self._children[additionalGate] = [int(parsed[3 + i]), int(parsed[4 + i])]
                    additionalGate += 1
                currentGate += 1

    def to_dot(self):
        ret = "digraph{\n"
        for gate in self._children.keys():
            if self._gateTypes[gate] == VARGATE: lab = str(self._variables[gate])
            if self._gateTypes[gate] == NEGGATE: lab = "NOT"
            if self._gateTypes[gate] == ANDGATE: lab = "AND"
            if self._gateTypes[gate] == ORGATE: lab = "OR"
            if self._gateTypes[gate] == TRUECONST: lab = "TRUE"
            if self._gateTypes[gate] == FALSECONST: lab = "FALSE"
            ret += "id" + str(gate) + " [ label=\"" + str(gate) + ": " + lab + " \"];\n"
        for gate, neighs in self._children.items():
            for child in neighs:
                ret += "id" + str(gate) + " -> id" + str(child) + ";\n"
        ret += "}"
        return ret

    # topological sort of the circuit, and compute the variables that have a path to the output gate
    def __topsort__(self):
        self._topsort = deque([])
        marked = set()
        self._varset = set()  # the input variables that have a path to the output gate (note that there can be less than the number of variables reported by the "nnf" line, which itself can be less than the number of variables in the original CNF formula)

        def visit(gate):
            if gate in marked:
                return
            marked.add(gate)
            if self._gateTypes[gate] == VARGATE:
                self._varset.add(self._variables[gate])
            for child in self._children[gate]:
                visit(child)
            self._topsort.append(gate)

        visit(self._outputGate)


    # compute alphas and betas
    def __alphas_and_betas__(self):
        varsets = {}  # varsets[i] is the set of variables that have a path to gate i
        alphas = {}  # alphas[x][i] are the #SAT(f_+x,k) values of the gates
        betas = {}  # betas[x][i] are the #SAT(f_-x,k) values

        for var in self._varset:  # initialization
            alphas[var] = {}
            betas[var] = {}
        alphas[OTHERVAR] = {}
        betas[OTHERVAR] = {}

        for gate in self._topsort:
            if self._gateTypes[gate] == VARGATE:
                varsets[gate] = {self._variables[gate]}
                alphas[self._variables[gate]][gate] = [Decimal(1)]
                betas[self._variables[gate]][gate] = [Decimal(0)]
                alphas[OTHERVAR][gate] = [Decimal(0), Decimal(1)]
                betas[OTHERVAR][gate] = [Decimal(0), Decimal(1)]
            elif self._gateTypes[gate] == TRUECONST:
                varsets[gate] = set()
                alphas[OTHERVAR][gate] = [Decimal(1)]
                betas[OTHERVAR][gate] = [Decimal(1)]
            elif self._gateTypes[gate] == FALSECONST:
                varsets[gate] = set()
                alphas[OTHERVAR][gate] = [Decimal(0)]
                betas[OTHERVAR][gate] = [Decimal(0)]
            elif self._gateTypes[gate] == ANDGATE:  # it has exactly two inputs
                in_gate1 = self._children[gate][0]
                in_gate2 = self._children[gate][1]
                gate_varsets = varsets[in_gate1].union(varsets[in_gate2])
                varsets[gate] = gate_varsets
                in_gate1_varsets = varsets[in_gate1]
                in_gate2_varsets = varsets[in_gate2]
                for var in gate_varsets:
                    s1 = len(in_gate1_varsets) - (1 if var in in_gate1_varsets else 0)
                    s2 = len(in_gate2_varsets) - (1 if var in in_gate2_varsets else 0)
                    s = s1 + s2  # (because the AND gate is decomposable)
                    cur_alphas = [Decimal(0)] * (s + 1)   # initialization
                    cur_betas = [Decimal(0)] * (s + 1)   # initialization
                    in_gate1_var = var if in_gate1 in alphas[var] else OTHERVAR
                    in_gate1_alphas = alphas[in_gate1_var][in_gate1]
                    in_gate1_betas = betas[in_gate1_var][in_gate1]
                    in_gate2_var = var if in_gate2 in alphas[var] else OTHERVAR
                    in_gate2_alphas = alphas[in_gate2_var][in_gate2]
                    in_gate2_betas = betas[in_gate2_var][in_gate2]
                    for i in range(s1 + 1):
                        for j in range(s2 + 1):
                            cur_alphas[i + j] += in_gate1_alphas[i] * in_gate2_alphas[j]
                            cur_betas[i + j] += in_gate1_betas[i] * in_gate2_betas[j]
                    alphas[var][gate] = cur_alphas
                    betas[var][gate] = cur_betas
                if len(gate_varsets) < len(self._varset):  # Handle OTHERVAR (and)
                    s1 = len(in_gate1_varsets)
                    s2 = len(in_gate2_varsets)
                    s = s1 + s2  # (because the AND gate is decomposable)
                    cur_alphas = [Decimal(0)] * (s + 1)  # initialization
                    cur_betas = [Decimal(0)] * (s + 1)  # initialization
                    in_gate1_alphas = alphas[OTHERVAR][in_gate1]
                    in_gate1_betas = betas[OTHERVAR][in_gate1]
                    in_gate2_alphas = alphas[OTHERVAR][in_gate2]
                    in_gate2_betas = betas[OTHERVAR][in_gate2]
                    for i in range(s1 + 1):
                        for j in range(s2 + 1):
                            cur_alphas[i + j] += in_gate1_alphas[i] * in_gate2_alphas[j]
                            cur_betas[i + j] += in_gate1_betas[i] * in_gate2_betas[j]
                    alphas[OTHERVAR][gate] = cur_alphas
                    betas[OTHERVAR][gate] = cur_betas
            elif self._gateTypes[gate] == ORGATE:  # again, it has exactly two inputs
                in_gate1 = self._children[gate][0]
                in_gate2 = self._children[gate][1]
                gate_varsets = varsets[in_gate1].union(varsets[in_gate2])
                varsets[gate] = gate_varsets
                in_gate1_varsets = varsets[in_gate1]
                in_gate2_varsets = varsets[in_gate2]
                s1_diff = len(in_gate2_varsets.difference(in_gate1_varsets))
                s2_diff = len(varsets[in_gate1].difference(varsets[in_gate2]))
                for var in gate_varsets:
                    s1 = s1_diff - (1 if var in in_gate2_varsets and var not in in_gate1_varsets else 0)
                    s2 = s2_diff - (1 if var in in_gate1_varsets and var not in in_gate2_varsets else 0)
                    s = len(gate_varsets) - (1 if var in gate_varsets else 0)
                    cur_alphas = [Decimal(0)] * (s + 1)   # initialization
                    cur_betas = [Decimal(0)] * (s + 1)   # initialization
                    in_gate1_var = var if in_gate1 in alphas[var] else OTHERVAR
                    in_gate1_alphas = alphas[in_gate1_var][in_gate1]
                    in_gate1_betas = betas[in_gate1_var][in_gate1]
                    in_gate2_var = var if in_gate2 in alphas[var] else OTHERVAR
                    in_gate2_alphas = alphas[in_gate2_var][in_gate2]
                    in_gate2_betas = betas[in_gate2_var][in_gate2]
                    for i in range(s - s1 + 1):
                        for j in range(s1 + 1):
                            cur_alphas[i + j] += in_gate1_alphas[i] * comb(s1, j)
                            cur_betas[i + j] += in_gate1_betas[i] * comb(s1, j)
                    for i in range(s - s2 + 1):
                        for j in range(s2 + 1):
                            cur_alphas[i + j] += in_gate2_alphas[i] * comb(s2, j)
                            cur_betas[i + j] += in_gate2_betas[i] * comb(s2, j)
                    alphas[var][gate] = cur_alphas
                    betas[var][gate] = cur_betas
                if len(gate_varsets) < len(self._varset):  # Handle OTHERVAR (or)
                    s1 = s1_diff
                    s2 = s2_diff
                    s = len(gate_varsets)
                    cur_alphas = [0] * (s + 1)  # initialization
                    cur_betas = [0] * (s + 1)  # initialization
                    in_gate1_alphas = alphas[OTHERVAR][in_gate1]
                    in_gate1_betas = betas[OTHERVAR][in_gate1]
                    in_gate2_alphas = alphas[OTHERVAR][in_gate2]
                    in_gate2_betas = betas[OTHERVAR][in_gate2]
                    for i in range(s - s1 + 1):
                        for j in range(s1 + 1):
                            cur_alphas[i + j] += in_gate1_alphas[i] * comb(s1, j)
                            cur_betas[i + j] += in_gate1_betas[i] * comb(s1, j)
                    for i in range(s - s2 + 1):
                        for j in range(s2 + 1):
                            cur_alphas[i + j] += in_gate2_alphas[i] * comb(s2, j)
                            cur_betas[i + j] += in_gate2_betas[i] * comb(s2, j)
                    alphas[OTHERVAR][gate] = cur_alphas
                    betas[OTHERVAR][gate] = cur_betas
            elif self._gateTypes[gate] == NEGGATE:  # has exactly one input
                in_gate1 = self._children[gate][0]
                gate_varsets = varsets[in_gate1]
                varsets[gate] = gate_varsets
                s = len(gate_varsets) - 1  # 0?
                for var in gate_varsets:
                    cur_alphas = [Decimal(0)] * (s + 1)  # initialization
                    cur_betas = [Decimal(0)] * (s + 1)  # initialization
                    in_gate1_alphas = alphas[var][in_gate1]
                    in_gate1_betas = betas[var][in_gate1]
                    for i in range(s + 1):
                        cur_alphas[i] = comb(s, i) - in_gate1_alphas[i]
                        cur_betas[i] = comb(s, i) - in_gate1_betas[i]
                    alphas[var][gate] = cur_alphas
                    betas[var][gate] = cur_betas
                if len(gate_varsets) < len(self._varset):  # Handle OTHERVAR (neg)
                    s += 1
                    # s = len(varsets[gate])  # 1?
                    cur_alphas = [Decimal(0)] * (s + 1)  # initialization
                    cur_betas = [Decimal(0)] * (s + 1)  # initialization
                    in_gate1_alphas = alphas[OTHERVAR][in_gate1]
                    in_gate1_betas = betas[OTHERVAR][in_gate1]
                    for i in range(s + 1):
                        cur_alphas[i] = comb(s, i) - in_gate1_alphas[i]
                        cur_betas[i] = comb(s, i) - in_gate1_betas[i]
                    alphas[OTHERVAR][gate] = cur_alphas
                    betas[OTHERVAR][gate] = cur_betas
        return alphas, betas

    # compute the Shapley values
    def shapley_values(self):
        alphas, betas = self.__alphas_and_betas__()

        shapley_values = {}
        s = len(self._varset)
        for var in self._varset:
            output_alphas = alphas[var][self._outputGate]
            output_betas = betas[var][self._outputGate]
            value = 0
            for k in range(s):
                value += (factorial(k) * factorial(s - k - 1)) * (output_alphas[k] - output_betas[k])
            try:
                shapley_values[var] = float(value / factorial(s))
            except OverflowError as err:
                shapley_values[var] = None

        return shapley_values