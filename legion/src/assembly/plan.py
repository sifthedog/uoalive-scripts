# Demand runs backwards from one product through what the pack already holds, and the first stage
# still missing is pressed. The product itself is counted as absent however many are in the pack:
# a keg or a clock is its own part elsewhere, and the ones already made would otherwise plan nothing.
def next_stage(stages, stock):
    product = stages[-1][0]
    demand = {product: 1}
    missing = {}

    for row, _menu, needs in reversed(stages):
        held = 0 if row == product else stock.get(row, 0)
        missing[row] = max(0, demand.get(row, 0) - held)

        for part in needs:
            demand[part] = demand.get(part, 0) + needs[part] * missing[row]

    for stage in stages:
        if missing[stage[0]] > 0:
            return stage

    return stages[-1]
