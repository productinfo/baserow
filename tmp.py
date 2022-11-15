from fractions import Fraction
from decimal import Decimal
from copy import deepcopy


rows = [
    {
        "id": 1,
        "order": float(Fraction('1/1'))
    },
    {
        "id": 2,
        "order": float(Fraction('2/1'))
    },
    {
        "id": 3,
        "order": float(Fraction('3/1'))
    },
    {
        "id": 4,
        "order": float(Fraction('4/1'))
    },
    {
        "id": 5,
        "order": float(Fraction('5/1'))
    },
    {
        "id": 6,
        "order": float(Fraction('100/1'))
    }
]


def find_intermediate(p1, q1, p2, q2):
    pl = 0
    ql = 1
    ph = 1
    qh = 0

    if p1 *q2 + 1 != p2 *q1:
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


def find_intermediate_order(order_1, order_2):
    p1, q1 = Fraction(order_1).limit_denominator(100000000).as_integer_ratio()
    p2, q2 = Fraction(order_2).limit_denominator(100000000).as_integer_ratio()
    return float(Fraction(*find_intermediate(p1, q1, p2, q2)))


def find_in_rows(rows, id):
    for index, row in enumerate(rows):
        if row['id'] == id:
            return index
    return -1


def insert_before(row_to_insert, insert_before_id):
    copy = deepcopy(rows)
    sorted(copy, key=lambda d: d['order'])
    index = find_in_rows(copy, insert_before_id)

    if index == 0:
        row_before = rows[index]
        row_after = rows[index + 1]
        new_order = find_intermediate_order(row_before['order'], row_after['order'])
        row_to_insert['order'] = rows[index]['order']
        rows[index]['order'] = new_order
    else:
        row_before = rows[index - 1]
        row_after = rows[index]
        new_order = find_intermediate_order(row_before['order'], row_after['order'])
        row_to_insert['order'] = new_order

    rows.append(row_to_insert)


insert_before({ "id": 7 }, 1)
insert_before({ "id": 8 }, 3)

print(rows)


import json
rows = sorted(rows, key=lambda d: d['order'])
print(json.dumps(rows, indent=4))


order_1 = 1.0
order_2 = 2.0
import time
s = time.time()
for i in range(1, 1000000):
    order_2 = find_intermediate_order(order_1, order_2)
    print(order_2)
print(time.time() - s)
