def cost_of(product, costs, fallback):
    return costs.get(product, fallback)


def short_by(product, held, costs, fallback):
    return max(0, cost_of(product, costs, fallback) - held)
