from enum import Enum
import sys

sys.setrecursionlimit(100_000)
	
class Position:
	def __init__(self, idx: int, col: int, ln: int, fn: str, ftxt: str):
		self.idx = idx
		self.col = col
		self.ln = ln
		self.fn = fn
		self.ftxt = ftxt
	
	def advance(self, current_char: str):
		self.idx += 1
		self.col += 1
		if current_char == "\n":
			self.col = 0
			self.ln += 1

	def copy(self):
		return Position(self.idx, self.col, self.ln, self.fn, self.ftxt)

class TT(Enum):
	EOF, NEWLINE, IDENTIFIER, LAMBDA, DOT, LPAREN, RPAREN, ASSIGN = range(8)

	def __str__(self):
		return super().__str__().replace("TT.", "")

class Token:
	def __init__(self, start_pos: Position, end_pos: Position, type: TT, value: str|None = None):
		self.start_pos = start_pos
		self.end_pos = end_pos
		self.type = type
		self.value = value
	
	def __repr__(self):
		return f"{self.type}" + (f":{self.value}" if self.value != None else "")

class Error:
	def __init__(self, start_pos: Position, end_pos: Position, name: str, details: str):
		self.start_pos = start_pos
		self.end_pos = end_pos
		self.name = name
		self.details = details
	
	def __str__(self):
		return f"File {self.start_pos.fn} (line {self.start_pos.ln + 1}, column {self.start_pos.col})\n\n{self.name}: {self.details}"

class UnknownCharacter(Error):
	def __init__(self, start_pos: Position, end_pos: Position, char: str):
		super().__init__(start_pos, end_pos, "Unknown Character", f"'{char}'")

class ExpectedCharacter(Error):
	def __init__(self, start_pos: Position, end_pos: Position, details: str):
		super().__init__(start_pos, end_pos, "Expected Character", details)

class InvalidSyntax(Error):
	def __init__(self, start_pos: Position, end_pos: Position, details: str):
		super().__init__(start_pos, end_pos, "Invalid Syntax", details)

class ProgramError(Error):
	def __init__(self, start_pos: Position, end_pos: Position, details: str):
		super().__init__(start_pos, end_pos, "Program Error", details)

class Lexer:
	def __init__(self, fn: str, ftxt: str):
		self.ftxt = ftxt
		self.current_char = ''
		self.pos = Position(-1, -1, 0, fn, ftxt)
		self.advance()
	
	def advance(self):
		self.pos.advance(self.current_char)
		self.current_char = self.ftxt[self.pos.idx] if self.pos.idx < len(self.ftxt) else None
	
	def make_identifier(self, start: str = ""):
		id_str: str = start
		while self.current_char != None:
			is_assign = False
			if self.current_char in "\n\r.λ@() ": break
			if self.current_char == "-": is_assign = True

			id_str += self.current_char
			self.advance()

			if self.current_char == ">" and is_assign:
				id_str = id_str[:-1]
				self.pos.idx -= 1
				self.pos.col -= 1
				self.current_char = self.ftxt[self.pos.idx]
				break
		return id_str


	def lex(self):
		tokens: list[Token] = []

		while self.current_char != None:
			start_pos = self.pos.copy()
			if self.current_char in " ":
				self.advance()
			elif self.current_char in "\n\r":
				self.advance()
				tokens.append(Token(start_pos, self.pos, TT.NEWLINE))
			elif self.current_char == "(":
				self.advance()
				tokens.append(Token(start_pos, self.pos, TT.LPAREN))
			elif self.current_char == ")":
				self.advance()
				tokens.append(Token(start_pos, self.pos, TT.RPAREN))
			elif self.current_char in "λ@":
				self.advance()
				tokens.append(Token(start_pos, self.pos, TT.LAMBDA))
			elif self.current_char == ".":
				self.advance()
				tokens.append(Token(start_pos, self.pos, TT.DOT))
			elif self.current_char == "-":
				self.advance()
				if self.current_char == ">":
					self.advance()
					tokens.append(Token(start_pos, self.pos, TT.ASSIGN))
				else:
					id_str = self.make_identifier("-")
					tokens.append(Token(start_pos, self.pos, TT.IDENTIFIER, id_str))
			else:
				id_str = self.make_identifier()
				tokens.append(Token(start_pos, self.pos, TT.IDENTIFIER, id_str))
		
		return tokens + [Token(self.pos, self.pos, TT.EOF)], None

class Statements:
	def __init__(self, start_pos: Position, end_pos: Position, statements):
		self.start_pos = start_pos
		self.end_pos = end_pos
		self.statements = statements
	
	def __repr__(self):
		return "\n".join([f"{line}" for line in self.statements])

class Identifier:
	def __init__(self, start_pos: Position, end_pos: Position, name: str):
		self.start_pos = start_pos
		self.end_pos = end_pos
		self.name = name
	
	def __repr__(self):
		return self.name

class LambdaNode:
	def __init__(self, start_pos: Position, end_pos: Position, param: str, body):
		self.start_pos = start_pos
		self.end_pos = end_pos
		self.param = param
		self.body = body
	
	def __repr__(self):
		return f"λ{self.param}.{self.body}"

class ApplicationNode:
	def __init__(self, start_pos: Position, end_pos: Position, caller: Identifier|LambdaNode, param):
		self.start_pos = start_pos
		self.end_pos = end_pos
		self.caller = caller
		self.arg = param
	
	def __repr__(self):
		caller_str = f"{self.caller}"
		arg_str = f"{self.arg}"

		if isinstance(self.caller, LambdaNode):
			caller_str = f"({caller_str})"
		if isinstance(self.arg, (LambdaNode, ApplicationNode)):
			arg_str = f"({arg_str})"
		
		return f"{caller_str} {arg_str}"

class AssignmentNode:
	def __init__(self, start_pos: Position, end_pos: Position, name: str, value):
		self.start_pos = start_pos
		self.end_pos = end_pos
		self.name = name
		self.value = value
	
	def __repr__(self):
		return f"{self.value} -> {self.name}"

class ParseResult:
	def __init__(self):
		self.node = None
		self.error = None
	
	def register(self, res):
		if res.error: self.error = res.error
		return res.node
	
	def success(self, node):
		self.node = node
		return self
	
	def fail(self, error: Error):
		self.error = error
		return self

class Parser:
	def __init__(self, tokens: list[Token]):
		self.tokens = tokens
		self.idx = -1
		self.current_token = None
		self.advance()
	
	def advance(self):
		self.idx += 1
		if self.idx < len(self.tokens): self.current_token = self.tokens[self.idx]

	def parse(self):
		"""
		expr       ::= application (-> identifier)
		application ::= atom {atom}
		atom       ::= variable | abstraction | '(' expr ')'
		abstraction ::= 'λ' identifier '.' expr
		"""
		return self.statements()

	def statements(self, end: tuple[TT] = (TT.EOF, )):
		# Remove trailing newlines
		res = ParseResult()
		while self.current_token.type == TT.NEWLINE: self.advance()
		start_pos = self.current_token.start_pos

		statements = []
		while self.current_token.type not in end:
			line = res.register(self.expr())
			if res.error: return res

			statements.append(line)
			while self.current_token.type == TT.NEWLINE: self.advance()
		
		end_pos = self.current_token.end_pos
		return res.success(Statements(start_pos, end_pos, statements))
	
	def expr(self):
		res = ParseResult()

		app = res.register(self.application())
		if res.error: return res

		if self.current_token.type == TT.ASSIGN:
			self.advance()

			if self.current_token.type != TT.IDENTIFIER:
				return res.fail(InvalidSyntax(
					self.current_token.start_pos, self.current_token.end_pos, "Expected an identifier after '->'."
				))
			name = self.current_token
			self.advance()

			if self.current_token.type not in (TT.NEWLINE, TT.EOF):
				return res.fail(InvalidSyntax(
					self.current_token.start_pos, self.current_token.end_pos, "Expected a newline or EOF after assignment."
				))
			return res.success(AssignmentNode(
				app.start_pos, name.end_pos,
				name.value, app
			))
		return res.success(app)
	
	def application(self):
		res = ParseResult()
		atoms = []

		while self.current_token.type in (TT.IDENTIFIER, TT.LAMBDA, TT.LPAREN):
			atom = res.register(self.atom())
			if res.error: return res

			atoms.append(atom)

		if not atoms:
			return res.fail(InvalidSyntax(
				self.current_token.start_pos, self.current_token.end_pos,
				f"Expected an identifier, 'λ', '(', found token {self.current_token.type} instead."
			))
		
		# No need to check if the list is empty as it is guaranteed not to.
		expr = atoms[0]
		for atom in atoms[1:]:
			expr = ApplicationNode(
				expr.start_pos, atom.end_pos,
				expr, atom
			)
		return res.success(expr)
	
	def atom(self):
		res = ParseResult()
		tok = self.current_token
		self.advance()

		match tok.type:
			case TT.IDENTIFIER: return res.success(Identifier(
				tok.start_pos, tok.end_pos, tok.value
			))
			case TT.LAMBDA:
				if self.current_token.type != TT.IDENTIFIER:
					return res.fail(InvalidSyntax(
						self.current_token.start_pos, self.current_token.end_pos,
						"Expected an identifier after 'λ'."
					))
				param = self.current_token.value
				self.advance()

				if self.current_token.type != TT.DOT:
					return res.fail(InvalidSyntax(
						self.current_token.start_pos, self.current_token.end_pos,
						"Expected '.' after parameter."
					))
				self.advance()

				body = res.register(self.application())
				if res.error: return res

				return res.success(LambdaNode(
					tok.start_pos, body.end_pos, param, body
				))
			case TT.LPAREN:
				expr = res.register(self.application())
				if self.current_token.type != TT.RPAREN:
					return res.fail(InvalidSyntax(
						self.current_token.start_pos, self.current_token.end_pos,
						"Expected matching ')'."
					))
				self.advance()
				return res.success(expr)
			case _:
				return res.fail(InvalidSyntax(
					tok.start_pos, tok.end_pos,
					f"Expected an identifier, 'λ', '(', found token {tok.type} instead."
				))

def substitute(expr, var_name: str, value):
	if isinstance(expr, Identifier):
		return value if expr.name == var_name else expr
	elif isinstance(expr, LambdaNode):
		if expr.param == var_name:
			return expr # Shadowed
		return LambdaNode(
			expr.start_pos, expr.end_pos,
			expr.param, substitute(expr.body, var_name, value)
		)
	elif isinstance(expr, ApplicationNode):
		return ApplicationNode(
			expr.start_pos, expr.end_pos,
			substitute(expr.caller, var_name, value),
			substitute(expr.arg, var_name, value)
		)

def reduce_step(expr, context):
	if isinstance(expr, Identifier):
		if expr.name in context:
			return context[expr.name]
		elif expr.name.isdigit():
			body = Identifier(None, None, "x")
			for _ in range(int(expr.name)):
				body = ApplicationNode(None, None, Identifier(None, None, "f"), body)
			return LambdaNode(None, None, "f", LambdaNode(None, None, "x", body))
		return expr
	elif isinstance(expr, ApplicationNode):
		func = reduce_step(expr.caller, context)
		arg = reduce_step(expr.arg, context)
		if isinstance(func, LambdaNode):
			return substitute(func.body, func.param, arg)
		return ApplicationNode(expr.start_pos, expr.end_pos, func, arg)
	elif isinstance(expr, LambdaNode):
		return LambdaNode(expr.start_pos, expr.end_pos, expr.param, reduce_step(expr.body, context))
	else:
		return expr

def normalize(expr, context=None):
	if context is None: context = {}
	prev = None
	while repr(expr) != repr(prev):
		prev = expr
		expr = reduce_step(expr, context)
	return expr

def decode_church(expr):
	# Assumes normalized form: λf.λx. f (f (... (f x)))
	if not isinstance(expr, LambdaNode): return None
	if not isinstance(expr.body, LambdaNode): return None

	def count_apps(e):
		if isinstance(e, Identifier) and e.name == "x":
			return 0
		if isinstance(e, ApplicationNode):
			if isinstance(e.caller, Identifier) and e.caller.name == "f":
				return 1 + count_apps(e.arg)
		return None

	return count_apps(expr.body.body)

def run(fn: str, ftxt: str, context: dict):
	lexer = Lexer(fn, ftxt)
	tokens, error = lexer.lex()
	if error: return None, error

	parser = Parser(tokens)
	ast = parser.parse()
	if ast.error: return None, ast.error

	result: str = ""
	for stmt in ast.node.statements:
		if isinstance(stmt, AssignmentNode):
			reduced = stmt.value
			context[stmt.name] = reduced
		else:
			reduced = normalize(stmt, context)
		result = reduced
	return result, None

if __name__ == "__main__":
	context = {}
	while True:
		expr = input(">>> ").strip()
		if expr == "EXIT": break

		result, error = run("<stdin>", expr, context)
		print(error if error else result)