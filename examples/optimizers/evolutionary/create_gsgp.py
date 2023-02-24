from opytimizer.optimizers.evolutionary import GSGP

# One should declare a hyperparameters object based
# on the desired algorithm that will be used
params = {
    "p_reproduction": 0.25,
    "p_mutation": 0.1,
    "p_crossover": 0.2,
    "prunning_ratio": 0.0,
}

# Creates a GSGP optimizer
o = GSGP(params=params)
