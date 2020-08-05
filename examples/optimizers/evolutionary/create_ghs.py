from opytimizer.optimizers.evolutionary.hs import GHS

# One should declare a hyperparameters object based
# on the desired algorithm that will be used
hyperparams = {
    'HMCR': 0.7,
    'PAR_min': 0.0,
    'PAR_max': 1.0,
    'bw_min': 1.0,
    'bw_max': 10.0
}

# Creating an GHS optimizer
o = GHS(hyperparams=hyperparams)
