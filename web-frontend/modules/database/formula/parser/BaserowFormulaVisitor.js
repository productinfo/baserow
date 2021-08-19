// Generated from BaserowFormula.g4 by ANTLR 4.8
// jshint ignore: start
var antlr4 = require('antlr4/index');

// This class defines a complete generic visitor for a parse tree produced by BaserowFormula.

function BaserowFormulaVisitor() {
	antlr4.tree.ParseTreeVisitor.call(this);
	return this;
}

BaserowFormulaVisitor.prototype = Object.create(antlr4.tree.ParseTreeVisitor.prototype);
BaserowFormulaVisitor.prototype.constructor = BaserowFormulaVisitor;

// Visit a parse tree produced by BaserowFormula#root.
BaserowFormulaVisitor.prototype.visitRoot = function(ctx) {
  return this.visitChildren(ctx);
};


// Visit a parse tree produced by BaserowFormula#StringLiteral.
BaserowFormulaVisitor.prototype.visitStringLiteral = function(ctx) {
  return this.visitChildren(ctx);
};


// Visit a parse tree produced by BaserowFormula#FunctionCall.
BaserowFormulaVisitor.prototype.visitFunctionCall = function(ctx) {
  return this.visitChildren(ctx);
};


// Visit a parse tree produced by BaserowFormula#Indentifier.
BaserowFormulaVisitor.prototype.visitIndentifier = function(ctx) {
  return this.visitChildren(ctx);
};


// Visit a parse tree produced by BaserowFormula#func_name.
BaserowFormulaVisitor.prototype.visitFunc_name = function(ctx) {
  return this.visitChildren(ctx);
};


// Visit a parse tree produced by BaserowFormula#func_call.
BaserowFormulaVisitor.prototype.visitFunc_call = function(ctx) {
  return this.visitChildren(ctx);
};


// Visit a parse tree produced by BaserowFormula#identifier.
BaserowFormulaVisitor.prototype.visitIdentifier = function(ctx) {
  return this.visitChildren(ctx);
};



exports.BaserowFormulaVisitor = BaserowFormulaVisitor;