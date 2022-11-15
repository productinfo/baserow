from fractions import Fraction


def find_intermediate(p1, q1, p2, q2):
    """
    Based on `find_intermediate` in
    https://wiki.postgresql.org/wiki/User-specified_ordering_with_fractions
    """

    pl = 0
    ql = 1
    ph = 1
    qh = 0

    if p1 * q2 + 1 != p2 * q1:
        while True:
            p = pl + ph
            q = ql + qh
            if p * q1 <= q * p1:
                pl = p
                ql = q
            elif p2 * q <= q2 * p:
                ph = p
                qh = q
            else:
                return p, q
    else:
        p = p1 + p2
        q = q1 + q2

    return p, q


def find_intermediate_order(order_1, order_2) -> float:
    p1, q1 = Fraction(order_1).limit_denominator(100000000).as_integer_ratio()
    p2, q2 = Fraction(order_2).limit_denominator(100000000).as_integer_ratio()
    return float(Fraction(*find_intermediate(p1, q1, p2, q2)))
