from MT22Visitor import MT22Visitor
from MT22Parser import MT22Parser
from AST import *
from functools import reduce

class ASTGeneration(MT22Visitor):
    def visitProgram(self, ctx: MT22Parser.ProgramContext):
        decls = [decl for x in ctx.declare() for decl in (self.visitDeclare(x) if isinstance(self.visitDeclare(x), list) else [self.visitDeclare(x)])]
        return Program(decls)
    
    def visitDeclare(self, ctx: MT22Parser.DeclareContext):
        return self.visitChildren(ctx)
    
    def visitFunc_decl(self, ctx: MT22Parser.Func_declContext):
        functype = self.visitFunc_type(ctx.func_type())
        funcname = ctx.ID()[0].getText()
        paralist = self.visitPara_list(ctx.para_list()) if ctx.para_list() else []
        blockstmt = self.visitBlock_func(ctx.block_func())
        inherit = None if len(ctx.ID()) == 1 else ctx.ID()[1].getText()
        return FuncDecl(funcname, functype, paralist, inherit, blockstmt)
    
    def visitPrim_type(self, ctx: MT22Parser.Prim_typeContext):
        return (IntegerType() if ctx.INTEGER() else
        FloatType() if ctx.FLOAT() else
        StringType() if ctx.STRING() else
        BooleanType())
    
    def visitIntList(self, ctx:MT22Parser.IntListContext):
        lst = [int(x.getText()) for x in ctx.INT_LIT()]
        return lst
    
    def visitArray_type(self, ctx:MT22Parser.Array_typeContext):
        int_list = self.visitIntList(ctx.intList())
        prim_type = self.visitPrim_type(ctx.prim_type())
        return ArrayType(int_list, prim_type)
    
    
    def visitVar_type(self, ctx: MT22Parser.Var_typeContext):
        return (self.visitPrim_type(ctx.prim_type()) if ctx.prim_type() else
        AutoType() if ctx.AUTO() else
        self.visitArray_type(ctx.array_type()))
    
    def visitFunc_type(self, ctx: MT22Parser.Func_typeContext):
        return self.visitVar_type(ctx.var_type()) if ctx.var_type() else VoidType()
       
    def visitVarlist(self, ctx:MT22Parser.VarlistContext):
        lst = [x for x in ctx.ID()]
        return lst

    def visitVar_decl(self, ctx: MT22Parser.Var_declContext):
        varlist = self.visitVarlist(ctx.varlist())
        vartype = self.visitVar_type(ctx.var_type())
        initExp = [self.visitExpression(x) for x in ctx.expression()] if ctx.ASSIGN() else [None] * len(varlist)
        return [VarDecl(varlist[x].getText(), vartype, initExp[x]) for x in range(len(varlist))]
    
    def visitPara_dec(self, ctx:MT22Parser.Para_decContext):
        para_var = ctx.ID().getText()
        para_type = self.visitVar_type(ctx.var_type())
        inherit = True if ctx.INHERIT() else False
        out = True if ctx.OUT() else False
        return ParamDecl(para_var, para_type, out, inherit)
    
    def visitPara_list(self, ctx:MT22Parser.Para_listContext):
        return [self.visitPara_dec(x) for x in ctx.para_dec()]
    
    def visitExpression_list(self, ctx:MT22Parser.Expression_listContext):
        return [self.visitExpression(x) for x in ctx.expression()]
    
    def visitExpression(self, ctx:MT22Parser.ExpressionContext):
        return (BinExpr(ctx.CONCAT().getText(), self.visitExpression1(ctx.expression1()[0]), self.visitExpression1(ctx.expression1()[1])) if ctx.CONCAT() 
        else self.visitChildren(ctx))
    
    def visitExpression1(self, ctx:MT22Parser.Expression1Context):
        operators = ['EQ', 'NOT_EQ', 'LT', 'LTE', 'GT', 'GTE']
        for op_name in operators:
            if getattr(ctx, op_name)():
                op = getattr(ctx, op_name)().getText()
                left, right = (self.visitExpression2(expr) for expr in ctx.expression2())
                return BinExpr(op, left, right)
        return self.visitChildren(ctx)
    
    def visitExpression2(self, ctx:MT22Parser.Expression2Context):
        for op_name in ['AND', 'OR']:
            if getattr(ctx, op_name)():
                op = getattr(ctx, op_name)().getText()
                left = self.visitExpression2(ctx.expression2())
                right = self.visitExpression3(ctx.expression3())
                return BinExpr(op, left, right)
        return self.visitExpression3(ctx.expression3())
    
    def visitExpression3(self, ctx:MT22Parser.Expression3Context):
        return (BinExpr(ctx.ADD().getText(), self.visitExpression3(ctx.expression3()), self.visitExpression4(ctx.expression4())) if ctx.ADD() else
        BinExpr(ctx.SUB().getText(), self.visitExpression3(ctx.expression3()), self.visitExpression4(ctx.expression4())) if ctx.SUB() else
        self.visitExpression4(ctx.expression4()))
        
    def visitExpression4(self, ctx:MT22Parser.Expression4Context):
        return (BinExpr(ctx.MUL().getText(), self.visitExpression4(ctx.expression4()), self.visitExpression5(ctx.expression5())) if ctx.MUL() else
        BinExpr(ctx.DIV().getText(), self.visitExpression4(ctx.expression4()), self.visitExpression5(ctx.expression5())) if ctx.DIV() else
        BinExpr(ctx.MOD().getText(), self.visitExpression4(ctx.expression4()), self.visitExpression5(ctx.expression5())) if ctx.MOD() else
        self.visitExpression5(ctx.expression5()))
    
    def visitExpression5(self, ctx:MT22Parser.Expression5Context):
        return (UnExpr(ctx.NEGATION().getText(), self.visitExpression5(ctx.expression5())) if ctx.NEGATION() 
        else self.visitExpression6(ctx.expression6()))
    
    def visitExpression6(self, ctx:MT22Parser.Expression6Context):
        return (UnExpr(ctx.SUB().getText(), self.visitExpression6(ctx.expression6())) if ctx.SUB() 
        else self.visitExpression7(ctx.expression7()))
    
    def visitExpression7(self, ctx:MT22Parser.Expression7Context):
        return self.visitArray_Ele(ctx.array_Ele()) if ctx.array_Ele() else self.visitOperands(ctx.operands())
        
    def visitOperands(self, ctx:MT22Parser.OperandsContext):
        return (self.visitLiteral(ctx.literal()) if ctx.literal() else
        Id(ctx.ID().getText()) if ctx.ID() else
        self.visitExpression(ctx.expression()) if ctx.R_OPEN() and ctx.R_CLOSE() else
        self.visitFunc_call(ctx.func_call()) if ctx.func_call() else
        self.visitArray_literal(ctx.array_literal()))
    
    def visitLiteral(self, ctx:MT22Parser.LiteralContext):
        return (IntegerLit(int(ctx.INT_LIT().getText())) if ctx.INT_LIT() else
        (FloatLit(float('0' + ctx.FLOAT_LIT().getText())) if len(ctx.FLOAT_LIT().getText()) >= 3 and ctx.FLOAT_LIT().getText()[0] == '.' and (ctx.FLOAT_LIT().getText()[1] in 'eE') else FloatLit(float(ctx.FLOAT_LIT().getText()))) if ctx.FLOAT_LIT() else
        StringLit(ctx.STR_LIT().getText()) if ctx.STR_LIT() else
        BooleanLit(False) if ctx.FALSE() else BooleanLit(True))

    def visitArray_Ele(self, ctx:MT22Parser.Array_EleContext):
        iden = ctx.ID().getText()
        exp_list = self.visitExpression_list(ctx.expression_list())
        return ArrayCell(iden, exp_list)
    
    def visitArray_literal(self, ctx:MT22Parser.Array_literalContext):
        exp_list = self.visitExpression_list(ctx.expression_list()) if ctx.expression_list() else []
        return ArrayLit(exp_list)
    
    def visitBlock_func(self, ctx:MT22Parser.Block_funcContext):
        stmt_list = [y for x in ctx.stmt() for y in (self.visitStmt(x) if isinstance(self.visitStmt(x), list) else [self.visitStmt(x)])]
        return BlockStmt(stmt_list)
    
    def visitStmt(self, ctx:MT22Parser.StmtContext):
        return self.visitChildren(ctx)

    def visitStatement(self, ctx:MT22Parser.StatementContext):
        return (self.visitFor_stmt(ctx.for_stmt()) if ctx.for_stmt() else
        self.visitIf_stmt(ctx.if_stmt()) if ctx.if_stmt() else
        self.visitBreak_stmt(ctx.break_stmt()) if ctx.break_stmt() else
        self.visitCont_stmt(ctx.cont_stmt()) if ctx.cont_stmt() else
        self.visitReturn_stmt(ctx.return_stmt()) if ctx.return_stmt() else
        self.visitDo_while_stmt(ctx.do_while_stmt()) if ctx.do_while_stmt() else
        self.visitWhile_stmt(ctx.while_stmt()) if ctx.while_stmt() else
        self.visitCall_func(ctx.call_func()) if ctx.call_func() else
        self.visitAssign_stmt(ctx.assign_stmt()) if ctx.assign_stmt() else
        self.visitBlock_func(ctx.block_func()))

    def visitFor_stmt(self, ctx:MT22Parser.For_stmtContext):
        init = self.visitInit_stmt(ctx.init_stmt())
        cond = self.visitExpression(ctx.expression()[0])
        update = self.visitExpression(ctx.expression()[1])
        body = self.visitStatement(ctx.statement())
        return ForStmt(init, cond, update, body)
    
    def visitIf_stmt(self, ctx:MT22Parser.If_stmtContext):
        cond = self.visitExpression(ctx.expression())
        tstmt = self.visitStatement(ctx.statement()[0])
        fstmt = None if not ctx.ELSE() else self.visitStatement(ctx.statement()[1])
        return IfStmt(cond, tstmt, fstmt)

    def visitDo_while_stmt(self, ctx:MT22Parser.Do_while_stmtContext):
        body = self.visitBlock_func(ctx.block_func())
        cond = self.visitExpression(ctx.expression())
        return DoWhileStmt(cond, body)

    def visitWhile_stmt(self, ctx:MT22Parser.While_stmtContext):
        body = self.visitStatement(ctx.statement())
        cond = self.visitExpression(ctx.expression())
        return WhileStmt(cond, body)
    
    def visitBreak_stmt(self, ctx: MT22Parser.Break_stmtContext):
        return BreakStmt()
    
    def visitCont_stmt(self, ctx: MT22Parser.Cont_stmtContext):
        return ContinueStmt()
    
    def visitReturn_stmt(self, ctx:MT22Parser.Return_stmtContext):
        return ReturnStmt(self.visitExpression(ctx.expression())) if ctx.expression() else ReturnStmt()
    
    def visitCall_func(self, ctx:MT22Parser.Call_funcContext):
        func_name = ctx.ID().getText()
        arg_lst = [] if not ctx.expression_list() else self.visitExpression_list(ctx.expression_list())
        return CallStmt(func_name, arg_lst)
    
    def visitAssign_stmt(self, ctx:MT22Parser.Assign_stmtContext):
        lhs = self.visitLhs(ctx.lhs())
        rhs = self.visitExpression(ctx.expression())
        return AssignStmt(lhs, rhs)
    
    def visitLhs(self, ctx:MT22Parser.LhsContext):
        return Id(ctx.ID().getText()) if ctx.ID() else self.visitArray_Ele(ctx.array_Ele())
    
    def visitFunc_call(self, ctx:MT22Parser.Func_callContext):
        func_name = ctx.ID().getText()
        arg_lst = [] if not ctx.expression_list() else self.visitExpression_list(ctx.expression_list())
        return FuncCall(func_name, arg_lst)

    def visitInit_stmt(self, ctx:MT22Parser.Init_stmtContext):
        lhs = self.visitLhs(ctx.lhs())
        rhs = self.visitExpression(ctx.expression())
        return AssignStmt(lhs, rhs)
        