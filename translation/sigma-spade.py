#!/bin/env python3

import yaml
import sys
import os
from enum import Enum
from typing import List
import re

SPADE_CODE = ""
GLOBAL_SPADE_KEYWORD = ""


#Outer class, can be later further specified as a leaf or Expression
class Constraint():
    class Join_term(Enum):
        AND = "and"
        OR = "or"
        def toString(self) -> str:
            return self.value
    
class Leaf(Constraint):
    def __init__(self, spade_expression: str):
        self.spade_expression = spade_expression
    def all_empty(self):
        return False
    def generate_spade_constraint(self, condition_name ) -> str:
        SPADE_CODE : str = "" 
        SPADE_CODE = "%" + condition_name + " = " + str(self.spade_expression) + "\n"
        return SPADE_CODE
class Expression(Constraint):
    def __init__(self, join_term: Constraint.Join_term,  constraints: List[Constraint], negate: bool = False,):
        self.joint_term = join_term
        self.negate = negate
        self.constraints = constraints

    def all_empty(self):
        if len(self.constraints) == 0:
            return True
        #at least one of contrainst is not empty
        if not any(self.constraints):
            return True 
        return False
    
    #return True if at least one Expression is not empty
    #return False when all underlying Expressions are empty
    def __bool__(self):
        return not self.all_empty()


    #Transform the programmatic Expression to a SPADE constraint
    def generate_spade_constraint(self, condition_name) -> str:

        _SPADE_CODE : str = ""

        if self.all_empty():
            return ""

        for i, term in enumerate(self.constraints):
            if term == None:
                continue

            internalCondName = condition_name + "_" + str(i) 
            _SPADE_CODE +=  term.generate_spade_constraint(internalCondName) 

        _SPADE_CODE += "%" + condition_name + " = "

        for i, term in enumerate(self.constraints):
            if term == None:
                continue

            internalCondName = condition_name + "_" + str(i) 
            _SPADE_CODE += "not " if (not isinstance(term, Leaf)) and term.negate else ""
            _SPADE_CODE += "%" + internalCondName

            if i < len(self.constraints)-1 and all(self.constraints[i+1:]) :
                _SPADE_CODE += " " + self.joint_term.toString() + " "  

        _SPADE_CODE += "\n"

        return _SPADE_CODE

    def _generate_spade_constraint(self, condition_name = "condition") -> str:
        total : str = ""
        total += self.joint_term.toString() + ":( "
        for term in self.constraints:
            total += term.generate_spade_constraint() + " ; "
        total += ")"
        return total


def test_cases():
    detection_str  = [
    "A and B or C or D",
    "A and B or 1 of all",
    "A and (B or C) or 1 of all",
    "A and B or not 1 of all",
    "(A and B) or (not (1 of all))"
    ]
    
    detection_str_expected = [
    #only placeholders
    "A and B or C or D",
    "A and B or 1 of all",
    "A and (B or C) or 1 of all",
    "A and B or not 1 of all",
    "(A and B) or (not (1 of all))"
    ]

    for i in enumarete(detection_str):
        assert(add_paranethesis(detection_str[i]) == detection_str_expected[i])

def clean_string(detection: str) -> str:
    #no leading and trailing spaces
    detection = detection.lstrip().rstrip()
    #space before and after parenthesis
    detection = detection.replace("(", " ( ").replace(")", " ) ")
    #no double spaces
    detection = " ".join(detection.split())
    return detection

def add_paranethesis(detection: str) -> str:
    detection = clean_string(detection)

    detection = add_paranethesis_term(detection, "of")
    detection = add_paranethesis_term(detection, "not")
    detection = add_paranethesis_term(detection, "and")
    detection = add_paranethesis_term(detection, "or")

    return detection 


def add_paranethesis_term(detection: str, term: str):
    for _ in range(0, detection.count(term)):
        detection = add_paranethesis_rec(detection, term)

    return detection

def add_paranethesis_rec(detection: str, term: str):
    tokens : list[str] = detection.split(" ")

    for index,token in enumerate(tokens):
        #are parenthesis needed?
        if token == term:
            needed : bool = False

            #calculates the index in the streing of where the parenthesis should start
            index_should_start : int = 0
            index_should_end : int = 0

            if term == "not":
                index_should_start = index - 1
                index_should_end = index + 2 if tokens[index+1] != "(" else index_of_matching_parenthesis(tokens, index+1)+1
            else:
                index_should_start = index - 2  if tokens[index-1] != ")" else index_of_matching_parenthesis_l(tokens, index-1)-1
                index_should_end = index + 2 if tokens[index+1] != "(" else index_of_matching_parenthesis(tokens, index+1)+1


            if  not term == "not" and (index == 1 or index+1 == len(tokens)):
                needed = True
            elif (token == "not") and (index == 0 or index+2 == len(tokens)):
                needed = True
            elif tokens[index_should_start] == "(":
                #check if the parenthesis already actually exist
                end = index_of_matching_parenthesis(tokens, index_should_start)

                if index_should_end == end:
                    needed = False
                else:
                    needed = True
            else:
                needed = True


            if needed:
                #add ( to index_should_start + 1
                #add ) to index_should_end - 1
                start = index_should_start + 1
                end = index_should_end - 1
                tokens[start] = "( " + tokens[start]
                tokens[end] = tokens[end] + " )" 

                detection = " ".join(tokens)
                return detection

    return detection


#find the left index of the matching parenthesis
def index_of_matching_parenthesis_l(tokens, index):
    matching_parenth = matching_parentheses(tokens)

    for i in list(matching_parenth):
        if matching_parenth[i] == index:
            return i
    return None

def index_of_matching_parenthesis(tokens, index : int):
    matching_parenth = matching_parentheses(tokens)

    return matching_parenth[index]



#Retuns a dict with the index to each matching parenthesis
def matching_parentheses(string: List):
    opening = [] 
    mydict = {}

    # loop over the string
    for i,c in enumerate(string):

        # new ( found => push it to the stack
        if c == '(':
            opening.append(i)


        # new ) found => pop and create an entry in the dict 
        elif c==')':

            # we found a ) so there must be a ( on the stack
            if not opening:
                return False
            else:
                mydict[opening.pop()] = i

    # return dict if stack is empty
    return mydict if not opening else None


def main():


    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    else:
        print("Please provide a filepath as an argument to the script")
        sys.exit()



    if not os.path.isfile(filepath):
        print("File path {} does not exist. Exiting...".format(filepath))
        sys.exit()

    sigma_yaml = None
    with open(filepath) as fp:
        sigma_yaml = yaml.safe_load(fp)

    assert(sigma_yaml != None)

    #manage only auditd for now
    if sigma_yaml["logsource"]["service"] != "auditd":
        print("Source not audtid")
        exit


    detection_dict = sigma_yaml["detection"]

    assert(filepath.endswith(".yml"))
    first_char : int = 0
    for index,elem in enumerate(reversed(filepath)):
        if elem == "/":
            first_char = len(filepath) - (index)
            break

    rule_name = filepath[first_char:-4]

    condition_str : str = add_paranethesis(detection_dict["condition"])
    expression : Constraint = parseStart(detection_dict, condition_str)
    assert expression != None
    combine(rule_name, expression)


def parseStart(detection_dict : dict, condition_str : str) -> Expression:
    expression : Expression = None

    print(condition_str)

    expression = parseAndOrExpression(detection_dict, condition_str) 
    if expression:
        return expression 

    expression = parseNotExpression(detection_dict, condition_str) 
    if expression:
        return expression 

    expression = parseAllExpression(detection_dict, condition_str) 
    if expression:
        return expression 

    expression = parse_Condition(detection_dict, condition_str)
    if expression:
        return expression

    return expression


def  parseAllExpression(detection_dict : dict, condition_str: str) -> Expression:
    if condition_str[0] != "(" or condition_str[-1] != ")":
        return None


    condition_str = condition_str[1:-1]
    condition_str = clean_string(condition_str)

    if len(condition_str.split(" ")) < 2:
        assert(False)

    if condition_str.split(" ")[1] != "of":
        return None

    splitted = split_expression(condition_str)

    join_term = Constraint.Join_term.AND
    if splitted[0] == "all":
        join_term = Constraint.Join_term.AND
    elif splitted[0] == "1":
        join_term = Constraint.Join_term.OR
    else:
        assert not "Not yet supported"

    expression = Expression(join_term=join_term, constraints=[])

    modified_dict = detection_dict
    #no idea what was the point of that
    #TODO:
    del modified_dict["condition"]

    if splitted[2] == "them":
        #AND all conditions
        for condition in modified_dict:
            expr : Constraint = parse_Condition(modified_dict, condition)
            expression.constraints.append(expr)
    else:
        #search term
        assert("*" in splitted[2])
        match_term = splitted[2].replace("*", "[\w]*")
        for condition in modified_dict:
            if re.match(match_term, condition):
                expr : Constraint = parse_Condition(modified_dict, condition)
                expression.constraints.append(expr)


    assert expression.constraints
    return expression

def  parseNotExpression(detection_dict : dict, condition_str: str) -> Expression:
    if condition_str[0] != "(" or condition_str[-1] != ")":
        return None

    condition_str = condition_str[1:-1]
    condition_str = clean_string(condition_str)

    if condition_str.split(" ")[0] != "not":
        return None
    
    splitted = split_expression(condition_str)
    expression : Expression = parseExpression(detection_dict, splitted[1])
    assert expression
    expression.negate = True
    return expression


def split_expression(condition_str: str) -> list:
    splitted = []
    i : int = 0
    concat : str = ""
    while i < len(condition_str):
        if condition_str[i] == "(":
            splitted.append(condition_str[i:index_of_matching_parenthesis(condition_str, i)+1])
            i = index_of_matching_parenthesis(condition_str, i) + 2
        elif condition_str[i] == " " or i == (len(condition_str)-1):
            concat += condition_str[i] if condition_str[i] != " " else ""
            splitted.append(concat)
            concat = ""
            i += 1
        else:
            concat += condition_str[i]
            i += 1
    return splitted

def  parseAndOrExpression(detection_dict : dict, condition_str: str) -> Expression:
    if condition_str[0] != "(" or condition_str[-1] != ")":
        return None

    condition_str = condition_str[1:-1]
    condition_str = clean_string(condition_str)

    splitted = split_expression(condition_str) 
    #The And/or Expressin contains exaclty 3 tokens
    if len(splitted) != 3:
        return None

    left = splitted[0]
    right = splitted[2]

    if splitted[1] != "and" and splitted[1] != "or":
        return None

   
    join_term = Constraint.Join_term.AND
    if splitted[1] == "and":
        join_term = Constraint.Join_term.AND
    if splitted[1] == "or":
        join_term = Constraint.Join_term.OR

    top_expression : Expression = Expression(join_term=join_term, constraints=[])

    left = clean_string(left)
    right = clean_string(right)


    #Further parse each Expression with recursion
    left_expression : Constraint = parseExpression(detection_dict, left)

    # assert left_expression
    top_expression.constraints.append(left_expression)


    right_expression: Constraint = parseExpression(detection_dict, right)

    # assert right_expression
    top_expression.constraints.append(right_expression)

    return top_expression 

def parseExpression(detection_dict : dict, condition_str: str) -> Expression:

    result : Expression = None

    #TODO:
    result = parse_Condition(detection_dict, condition_str)
    if result:
        return result

    result = parseStart(detection_dict, condition_str)
    if result:
        return result


    return result


def parseCondAndOrCond(detection_dict : dict, condition_str: str, result) -> Expression:
    tokens = condition_str.split(" ")

    assert tokens[0] == "(" and tokens[-1] == ")"
    tokens = tokens[1:-1]


    join_term = Constraint.Join_term.AND
    if tokens[1] == "and":
        join_term = Constraint.Join_term.AND
    if tokens[1] == "or":
        join_term = Constraint.Join_term.OR

    top_expression : Expression = Expression(join_term=join_term, constraints=[])

    left_expression : Expression = parseCond(detection_dict, tokens[0], result)
    assert left_expression
    top_expression.constraints.append(left_expression)


    right_expression: Constraint = parseCond(detection_dict, tokens[2], result)
    assert right_expression
    top_expression.constraints.append(right_expression)

    return top_expression
    



def parseCond(detection_dict : dict, condition_str : str, result) -> Expression:
    _result = None
    if len(condition_str.split(" ")) > 1:
        return None
    tokens = condition_str.split(" ")
    if tokens[0] == "not":
        expr : Expression = parse_Condition(detection_dict,  condition_str, tokens, result)
        assert expr 
        expr.negate = True
        return expr
    
    expr : Expression = parse_Condition(detection_dict, condition_str, tokens, _result)
    if expr :
        return expr

    return None



def parse_Condition(detection_dict: dict, condition_name : str) -> Expression:
    if condition_name[0] == "(" or condition_name[-1] == ")":
        return None

    condition_name = clean_string(condition_name)

    selection_name = detection_dict.get(condition_name)
    if selection_name == None:
        return None
    try:
        Matchall : list = list(selection_name.items())
    except AttributeError:
        #it means keyword mode
        Matchall : list = selection_name

    assert(len(Matchall) != 0)
    expr : Expression = parseMatchall( Matchall)

    return expr


def type_execve(matchall : list) -> bool:
    if len(matchall) == 0:
        return False

    return any(item[0] == "type" and item[1] == "EXECVE" for item in matchall)



def combine(condition_name, spade_constraints : Constraint):
    #Output the SPADE constraint
    print(spade_constraints.generate_spade_constraint(condition_name))


def generate_leaf(SPADE_KEY : str , SPADE_OP : str, SPADE_VALUE : str):
    return Leaf(str( SPADE_KEY + SPADE_OP + SPADE_VALUE))

def rewrite_args_execve(old_args) -> dict:
    old_args.remove(('type', 'EXECVE'))

    #Find and replace missing arguments with wildcard
    missing_args = []
    missing_elements = []
    last_element = -1
    for arg in old_args:
        curr_element = int(arg[0].split("|")[0][1:])
        if not curr_element == last_element + 1:
            missing_elements = list(range(last_element +1,  curr_element))
        last_element = curr_element
    missing_args = [ ("a" + str(i), "%")  for i in missing_elements ]


    old_args = old_args  + missing_args
    old_args.sort(key = lambda x: x[0]) 


    args : dict = {}
    for i,term in enumerate(old_args):
        a_i = ""
        transformation = ""
        if "|" in term[0]:
            a_i = term[0][0:term[0].index("|")]
            transformation = term[0][term[0].index("|")+1:]
        else:
            a_i = term[0]
            transformation = None

        value = term[1]


        args[a_i] = {}
        args[a_i]["value"] = value
        args[a_i]["transformation"] = transformation

    return args

#Each type is parsed separately
def parseExecve(Matchall : list) -> Expression:
    if not type_execve(Matchall):
        return None 

    top_expr : Expression = Expression(join_term=Constraint.Join_term.OR, constraints=[])

    args = rewrite_args_execve(Matchall)

    if len(args) == 0:
        #keyword mode
        global GLOBAL_SPADE_KEYWORD
        GLOBAL_SPADE_KEYWORD = "command line"
        #empty expression
        return None

    else:
        return parseExecve_permutations(args)


    #TODO:
    arg_internal_counters = [ len(args[term[0]]-1) for term in args ]
    for i in range(0, number_cases):
    
        parameter = {}

        for i,term in enumerate(args):
            parameter[i] = term[1][arg_internal_counters[i]]
            arg_internal_counters[i] -= 1
         
        parseExecve_permutations(parameter)


    top_expr.constraints.append(parseExecve_permutations(Matchall_copy))
    return top_expr
    
def parseExecve_only_a0(args) -> Expression :
    assert args.get("a0")
    assert len(args) == 1

    expr : Expression = Expression(join_term=Constraint.Join_term.OR, constraints=[])
    
    values_a0 = perfrom_transformation(args["a0"])
    for term in values_a0:
        SPADE_KEY = "\"command line\""
        SPADE_OP = " = "
        SPADE_VALUE = "'" + str(term) + "'"
        expr.constraints.append(generate_leaf(SPADE_KEY, SPADE_OP, SPADE_VALUE))

        SPADE_KEY = "\"command line\""
        SPADE_OP = " like "
        SPADE_VALUE = "'" + str(term) + " %'"
        expr.constraints.append(generate_leaf(SPADE_KEY, SPADE_OP, SPADE_VALUE))

    return expr



def parseExecve_a0_a1(args) -> Expression:
    assert args.get("a0")
    assert args.get("a1")
    assert len(args) == 2

    expr : Expression = Expression(join_term=Constraint.Join_term.OR, constraints=[])

    values_a0 = perfrom_transformation(args["a0"])
    for value_a0 in values_a0:
        values_a1 = perfrom_transformation(args["a1"])
        for value_a1 in values_a1:

            SPADE_KEY = "\"command line\""
            SPADE_OP = " like "
            SPADE_VALUE = "'" + value_a0 + " " + value_a1 + "'"
            SPADE_VALUE = SPADE_VALUE.replace('%%', '%')
            expr.constraints.append(generate_leaf(SPADE_KEY, SPADE_OP, SPADE_VALUE))


            SPADE_KEY = "\"command line\""
            SPADE_OP = " like "
            SPADE_VALUE = "'" + value_a0 + " " + value_a1 + " %'"
            SPADE_VALUE = SPADE_VALUE.replace('%%', '%')
            expr.constraints.append(generate_leaf(SPADE_KEY, SPADE_OP, SPADE_VALUE))

    return expr

def perfrom_transformation(term : dict) -> list:
    assert term["value"] != "" or term["value"] != None

    #make it a list
    term["value"] = term["value"] if isinstance(term["value"], list) else [term["value"]]

    term["value"] = [ str(value).replace("*", "%") for value in term["value"]]


    if term["transformation"] == None:
        return term["value"]
    
    if term["transformation"] == "contains":
        return ["%" + value + "%" for value in term["value"]]

    if term["transformation"] == "endswith":
        return ["%" + value for value in term["value"]]

    if term["transformation"] == "startswith":
        return [ value + "%" for value in term["value"]]

    assert False
    return None

def parseExecve_a0_a1_a2(args) -> Expression:

    assert args.get("a0")
    assert args.get("a1")
    assert args.get("a2")
    assert len(args) == 3


    expr : Expression = Expression(join_term=Constraint.Join_term.OR, constraints=[])

    values_a0 = perfrom_transformation(args["a0"])
    for value_a0 in values_a0:

        values_a1 = perfrom_transformation(args["a1"])
        for value_a1 in values_a1:

            values_a2 = perfrom_transformation(args["a2"])
            for value_a2 in values_a2:
                spade_key = "\"command line\""
                spade_op = " like "
                spade_value = "'" + value_a0 + " " + value_a1 + " " + value_a2 + "'"
                spade_value = spade_value.replace('%%', '%')
                expr.constraints.append(generate_leaf(spade_key, spade_op, spade_value))


                spade_key = "\"command line\""
                spade_op = " like "
                spade_value = "'" + value_a0 + " " + value_a1 + " " + value_a2 + " %'"
                spade_value = spade_value.replace('%%', '%')
                expr.constraints.append(generate_leaf(spade_key, spade_op, spade_value))

    return expr



def parseExecve_a0_a1_a2_a3(args) -> Expression:

    assert args.get("a0")
    assert args.get("a1")
    assert args.get("a2")
    assert args.get("a3")
    assert len(args) == 4


    expr : Expression = Expression(join_term=Constraint.Join_term.OR, constraints=[])

    values_a0 = perfrom_transformation(args["a0"])
    for value_a0 in values_a0:

        values_a1 = perfrom_transformation(args["a1"])
        for value_a1 in values_a1:

            values_a2 = perfrom_transformation(args["a2"])
            for value_a2 in values_a2:

                values_a3 = perfrom_transformation(args["a3"])
                for value_a3 in values_a3:
                    spade_key = "\"command line\""
                    spade_op = " like "
                    spade_value = "'" + value_a0 + " " + value_a1 + " " + value_a2 + " " + value_a3 + " %'"
                    spade_value = spade_value.replace('%%', '%')
                    expr.constraints.append(generate_leaf(spade_key, spade_op, spade_value))

                    spade_key = "\"command line\""
                    spade_op = " like "
                    spade_value = "'" + value_a0 + " " + value_a1 + " " + value_a2 + " " + value_a3 + "'"
                    spade_value = spade_value.replace('%%', '%')
                    expr.constraints.append(generate_leaf(spade_key, spade_op, spade_value))

    return expr


def parseExecve_a0_a1_a2_a3_a4(args) -> Expression:

    assert args.get("a0")
    assert args.get("a1")
    assert args.get("a2")
    assert args.get("a3")
    assert args.get("a4")
    assert len(args) == 5


    expr : Expression = Expression(join_term=Constraint.Join_term.OR, constraints=[])

    values_a0 = perfrom_transformation(args["a0"])
    for value_a0 in values_a0:

        values_a1 = perfrom_transformation(args["a1"])
        for value_a1 in values_a1:

            values_a2 = perfrom_transformation(args["a2"])
            for value_a2 in values_a2:


                values_a3 = perfrom_transformation(args["a3"])
                for value_a3 in values_a3:

                    values_a4 = perfrom_transformation(args["a4"])
                    for value_a4 in values_a4:
                        spade_key = "\"command line\""
                        spade_op = " like "
                        spade_value = "'" + value_a0 + " " + value_a1 + " " + value_a2 + " " + value_a3 + " " + value_a4 + "'"
                        spade_value = spade_value.replace('%%', '%')
                        expr.constraints.append(generate_leaf(spade_key, spade_op, spade_value))

                        spade_key = "\"command line\""
                        spade_op = " like "
                        spade_value = "'" + value_a0 + " " + value_a1 + " " + value_a2 + " " + value_a3 + " " + value_a4 + " %'"
                        spade_value = spade_value.replace('%%', '%')
                        expr.constraints.append(generate_leaf(spade_key, spade_op, spade_value))



    return expr




def parseExecve_a0_a1_a2_a3_a4_a5(args) -> Expression:

    assert args.get("a0")
    assert args.get("a1")
    assert args.get("a2")
    assert args.get("a3")
    assert args.get("a4")
    assert args.get("a5")
    assert len(args) == 6


    expr : Expression = Expression(join_term=Constraint.Join_term.OR, constraints=[])

    values_a0 = perfrom_transformation(args["a0"])
    for value_a0 in values_a0:

        values_a1 = perfrom_transformation(args["a1"])
        for value_a1 in values_a1:

            values_a2 = perfrom_transformation(args["a2"])
            for value_a2 in values_a2:


                values_a3 = perfrom_transformation(args["a3"])
                for value_a3 in values_a3:

                    values_a4 = perfrom_transformation(args["a4"])
                    for value_a4 in values_a4:

                        values_a5 = perfrom_transformation(args["a5"])
                        for value_a5 in values_a5:
                            spade_key = "\"command line\""
                            spade_op = " like "
                            spade_value = "'" + value_a0 + " " + value_a1 + " " + value_a2 + " " + value_a3 + " " + value_a4 + " " + value_a5 + "'"
                            spade_value = spade_value.replace('%%', '%')
                            expr.constraints.append(generate_leaf(spade_key, spade_op, spade_value))

                            spade_key = "\"command line\""
                            spade_op = " like "
                            spade_value = "'" + value_a0 + " " + value_a1 + " " + value_a2 + " " + value_a3 + " " + value_a4 + " " + value_a5 + " %'"
                            spade_value = spade_value.replace('%%', '%')
                            expr.constraints.append(generate_leaf(spade_key, spade_op, spade_value))



    return expr





def parseExecve_permutations(args: dict) -> Expression:

    if len(args) == 0:
        return None

    # expr : Expression = Expression(join_term=Constraint.Join_term.AND, constraints=[])
    max_supported_args : int = 10


    #we only support expression with an existing a0
    assert(args.get("a0"))

    #if onyl a0
    if args.get("a0") and not any( [ args.get("a" + str(i)) for i in range(1, max_supported_args) ]):
        return parseExecve_only_a0(args)

    #if a0 and a1
    if args.get("a0") and args.get("a1")  and not any( [ args.get("a" + str(i)) for i in range(2, max_supported_args) ]):
        return parseExecve_a0_a1(args)

    if args.get("a0") and args.get("a1") and args.get("a2")  and not any( [ args.get("a" + str(i)) for i in range(3, max_supported_args) ]):
        return parseExecve_a0_a1_a2(args)

    if args.get("a0") and args.get("a1") and args.get("a2") and args.get("a3") and not any( [ args.get("a" + str(i)) for i in range(4, max_supported_args) ]):
        return parseExecve_a0_a1_a2_a3(args)


    if args.get("a0") and args.get("a1") and args.get("a2") and args.get("a3") and args.get("a4") and not any( [ args.get("a" + str(i)) for i in range(5, max_supported_args) ]):
        return parseExecve_a0_a1_a2_a3_a4(args)


    if args.get("a0") and args.get("a1") and args.get("a2") and args.get("a3") and args.get("a4") and args.get("a5") and not any( [ args.get("a" + str(i)) for i in range(6, max_supported_args) ]):
        return parseExecve_a0_a1_a2_a3_a4_a5(args)


    print("more than 4 params or none params..")
    return None

    #TODO:
    assert "a0 a1 a2... are in that order"    

    #if onyl a0,a1..aN
    SPADE_KEY = "\"command line\""
    SPADE_OP = " like "
    SPADE_VALUE = "'"
    for i,param in enumerate(args):
        SPADE_VALUE += "'" + args[param]
        SPADE_VALUE += " " if i != len(args)-1 else "%'"

    expr.constraints.append(generate_leaf(SPADE_KEY, SPADE_OP, SPADE_VALUE))

    return expr

    for  _,matchall in enumerate(Matchall):
        assert len(matchall)
        if matchall[0] == "type":
            continue

        leaf : Leaf = parseMatchallEXECVE(matchall[0], matchall[1] ) 
        expression.constraints.append(leaf)

    return expression 


def parseMatchallEXECVE(transformation, terms, negate : bool = False) -> Constraint:
    expr : Expression = Expression(join_term=Constraint.Join_term.OR, negate = negate, constraints=[])

    for term in terms:
        if transformation == "a0":
            SPADE_KEY = "\"command line\""
            SPADE_OP = " like "
            SPADE_VALUE = "'" + str(term) + "%'"
        else:
            SPADE_KEY = "\"command line\""
            SPADE_OP = " like "
            SPADE_VALUE = "'%" + str(term) + "%'"

        leaf = Leaf(str( SPADE_KEY + SPADE_OP + SPADE_VALUE))
        expr.constraints.append(leaf)

    assert expr.constraints
    return expr


def parseContains(matchall):
    
    if "|contains " not in matchall:
        return None
    #parse the fier



def type_path(matchall):
    if len(matchall) == 0:
        return False


    return any(item[0] == "type" and item[1] == "PATH" for item in matchall)



def rewrite_args_path(old_args) -> dict:
    old_args.remove(('type', 'PATH'))

    old_args = old_args[0]
    args : dict = {}
    transformation = ""
    if "|" in old_args[0]:
        transformation = old_args[0][old_args[0].index("|")+1:]
    else:
        transformation = None

    value = old_args[1]


    args["value"] = value
    args["transformation"] = transformation

    return args


def parsePath(Matchall) -> Expression: 
    if not type_path(Matchall):
        return None 

    paths : dict = rewrite_args_path(Matchall)
    assert len(paths)

    expression : Expression = Expression(join_term=Constraint.Join_term.OR, negate=False, constraints=[])
    for path in perfrom_transformation(paths):

        path = path.replace("%%", "%")            

        SPADE_KEY = "\"path\""
        if "%" in str(path):
            SPADE_OP = " like "
            SPADE_VALUE = "'" + str(path) + "'"
        else:
            SPADE_OP = " = "
            SPADE_VALUE = "'" + str(path) + "'"

        leaf = Leaf(str( SPADE_KEY + SPADE_OP + SPADE_VALUE))
        expression.constraints.append(leaf)

    assert expression.constraints

    return expression 


def parseMatchallPATH(transformation, terms) -> list:
    constraints = []
    expr : Expression = Expression(join_term=Constraint.Join_term.OR, negate=False, constraints=[])

    for term in terms:
        SPADE_KEY = "\"path\""
        if "*" in str(term):
            SPADE_OP = " like "
            SPADE_VALUE = "'" + str(term).replace("*", "%") + "'"
        else:
            SPADE_OP = " = "
            SPADE_VALUE = "'" + str(term) + "'"

        leaf = Leaf(str( SPADE_KEY + SPADE_OP + SPADE_VALUE))
        expr.constraints.append(leaf)

    assert len(constraints)
    return constraints




def type_syscall(matchall):
    if len(matchall) == 0:
        return False


    # print(matchall)
    for item in matchall:
        continue
        #TODO: bypassing for the time being
        if not isinstance(item, list):
            return False

    return any(item[0] == "type" and item[1] == "SYSCALL" for item in matchall)


def rewrite_args_syscall(old_args) -> dict:
    old_args.remove(('type', 'SYSCALL'))

    args : dict = {}
    for i,term in enumerate(old_args):
        a_i = ""
        transformation = ""
        if "|" in term[0]:
            a_i = term[0][0:term[0].index("|")]
            transformation = term[0][term[0].index("|")+1:]
        else:
            a_i = term[0]
            transformation = None

        value = term[1]


        args[a_i] = {}
        args[a_i]["value"] = value
        args[a_i]["transformation"] = transformation

    return args



def parseSyscall(Matchall: list) -> Expression:
    if not type_syscall(Matchall):
        return None

    exe_arg : dict = rewrite_args_syscall(Matchall)
    assert exe_arg


    expression : Expression = Expression(join_term=Constraint.Join_term.AND, negate=False, constraints=[])
    for arg in exe_arg:

        if arg == "comm":
            #sd
            SPADE_KEY = "\"name\""
        elif arg == "uid":
            #sdds
            SPADE_KEY = "\"uid\""
        elif arg == "exe":
            #sdds
            SPADE_KEY = "\"exe\""
        elif arg == "cwd":
            SPADE_KEY = "\"cwd\""
        elif arg == "uid":
            SPADE_KEY = "\"uid\""
        elif arg == "key":
            print("TOOD: do something with key field")
            continue
        else:
            print("parseSyscall: Not exe and not comm..")
            assert(False)


        internal_expression : Expression = Expression(join_term=Constraint.Join_term.OR, negate=False, constraints=[])
        for _arg in perfrom_transformation(exe_arg[arg]):
            #TODO:
            if "%" in str(_arg):
                SPADE_OP = " like "
                SPADE_VALUE = "'" + str(_arg) + "'"
            else:
                SPADE_OP = " = "
                SPADE_VALUE = "'" + str(_arg) + "'"

            leaf = Leaf(str( SPADE_KEY + SPADE_OP + SPADE_VALUE))
            internal_expression.constraints.append(leaf)

        expression.constraints.append(internal_expression)

    assert expression.constraints

    return expression 

def parseKeyword(Matchall : list) -> Expression:

    expression : Expression = Expression(join_term=Constraint.Join_term.OR, constraints=[])
    for arg in Matchall:
        # print(arg)
        assert(GLOBAL_SPADE_KEYWORD)

        arg = arg.replace("%%", "%")            

        SPADE_KEY = "\"" + GLOBAL_SPADE_KEYWORD + "\""
        if "%" in str(arg):
            assert(False)
            SPADE_OP = " like "
            SPADE_VALUE = "'" + str(arg) + "'"
        else:
            SPADE_OP = " like "
            SPADE_VALUE = "'%" + str(arg) + "%'"

        leaf = Leaf(str( SPADE_KEY + SPADE_OP + SPADE_VALUE))
        expression.constraints.append(leaf)

    # assert(expression.constraints)

    #TODO: KEYWORDD
    return expression


def parseMatchall(Matchall : list) -> Expression:


    _result  = parseExecve(Matchall)
    if _result:
        return _result


    _result  = parsePath(Matchall)
    if _result:
        return _result

    _result = parseSyscall(Matchall)
    if _result:
        return _result


    #keyword mode
    if GLOBAL_SPADE_KEYWORD:
        _result = parseKeyword(Matchall)
        if _result:
            return _result

    print("TODO: not execve, not path, not syscall")
    # return Expression(join_term=Constraint.Join_term.OR, constraints=[])
    return None


if __name__ == "__main__":
    main()

