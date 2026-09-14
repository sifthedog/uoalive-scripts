# Demand runs backwards from one product through what the pack already holds, and the first stage
# still missing is pressed. The product is never in stock, so it is the last resort.
def next_stage(stages, stock):
    demand = {stages[-1][0]: 1}
    missing = {}

    for product, _menu, needs in reversed(stages):
        missing[product] = max(0, demand.get(product, 0) - stock.get(product, 0))

        for part in needs:
            demand[part] = demand.get(part, 0) + needs[part] * missing[product]

    for stage in stages:
        if missing[stage[0]] > 0:
            return stage

    return stages[-1]
