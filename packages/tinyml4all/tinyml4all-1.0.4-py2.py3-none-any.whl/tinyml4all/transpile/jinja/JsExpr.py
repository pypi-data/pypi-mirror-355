class JsExpr:
    """
    Javascript expression to be evaluated
    """

    def __init__(self, expr: str):
        """
        Constructor
        :param expr:
        """
        self.expr = expr.replace("\n", " ").replace("\t", " ")
