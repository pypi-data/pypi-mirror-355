
digits = "0123456789"
class Lexer:
	def __init__(self, text : str) -> None:
		self.text = text
		self.pos = -1
		self.char = None
		self.advance()
		
	def advance(self) -> None:
		self.pos += 1
		if len(self.text) > self.pos:
			self.char = self.text[self.pos]
		else:
			self.char = None
			
	def number(self):
		result = ""
		dot = 0
		while self.char is not None and self.char in digits + ".":
			if self.char == ".": 
				dot += 1
				if dot > 1: raise SyntaxError(f"Количество точек: {dot}. Допустимо 0 или 1")
			
			result += self.char
			self.advance()
		
		if dot == 0:
			return ("INT", int(result))
		else:
			return ("FLOAT",float(result))	
			
	def tokenize(self) -> list[tuple]:
		tokens = []
		
		while self.char is not None:
			if self.char == "+":#
				tokens.append(("PLUS","+"))
				self.advance()
				continue
			if self.char.isspace():
				self.advance()
				continue
			if self.char == '-':
				tokens.append(("MINUS","-"))
				self.advance()
				continue
			if self.char == '*':
				tokens.append(("MULTIPLY","*"))
				self.advance()
				continue
			if self.char == '/':
				tokens.append(("DIVIDE","/"))
				self.advance()
				continue
			if self.char == "(":
				tokens.append(("LPAREN","("))
				self.advance()
				continue
			if self.char == ")":
				tokens.append(("RPAREN",")"))
				self.advance()
				continue
			if self.char.isdigit():
				tokens.append(self.number())
				continue
			else:
				raise SyntaxError(f"Unexpected char: {self.char}")			
		return tokens
		
class Parser:
	def __init__(self, tokens : list):
		self.tokens = iter(tokens)
		self.token = None
		self.advance()
	
	def parse(self):
		return self.expr()
	
	def advance(self):
		self.token = next(self.tokens, None)
	
	def factor(self):
		if self.token[0]=="INT":
			tvalue=self.token[1]
			self.advance()
			return ("IntNode",tvalue)
		elif self.token[0]=="FLOAT":
			tvalue=self.token[1]
			self.advance()
			return ("FloatNode",tvalue)
		elif self.token[0] == "LPAREN":
			self.advance()
			expression = self.expr()
			
			if self.token is None or self.token[0] != "RPAREN":
				raise SyntaxError("Ожидалась закрывающая скобка ')'")
			self.advance()
			
			return expression
	def expr(self):
		left = self.term()
		
		while self.token is not None and self.token[0] in ("PLUS","MINUS"):
			op = self.token[1]
			self.advance()
			right = self.term()
			left = ("BinOpNode",left, op, right)
		return left
		
	
	def term(self):
		left = self.factor()
		
		while self.token is not None and self.token[0] in ("DIVIDE","MULTIPLY"):
			op = self.token[1]
			self.advance()
			right = self.factor()
			left = ("BinOpNode",left, op, right)
		return left
	
class Evaluator:
	def __init__(self, nodes):
		self.nodes = nodes
	
	def calc(self, node=None):
		if node is None: node = self.nodes
		
		if node[0]=="BinOpNode":
			left = self.calc(node[1])
			right = self.calc(node[3])
			op = node[2]
			if op == "+":
				return left + right
			elif op == "-":
				return left - right
			elif op == "*":
				return left * right
			elif op == "/":
				return left / right
		elif node[0] == "FloatNode" or node[0] == "IntNode":
			return node[1] 
			
class Calculator:
	def calculate(self, string):
		lexer = Lexer(string).tokenize()
		parser = Parser(lexer).parse()
		evaluator = Evaluator(parser).calc()
		return evaluator
