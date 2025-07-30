from stgem import config

def get_DIFFUSION_parameters(identifier, execution_budget=None, network_type="convolution"):
    """Returns preset Diffusion test suite generator parameters according to
    the given identifier. Different initial random searches can be specified
    with a suffix like '_lhs'. The default initial random search is uniform
    random."""
    
    if execution_budget is not None and execution_budget < 1:
        raise ValueError("The execution budget must be positive.")

    if "_" in identifier:
        identifier, random_search = identifier.split("_")
        main_id = main_id.lower()
        random_search = random_search.lower()
    else:
        main_id = identifier.lower()
        random_search = "uniform"
    
    if random_search is not None and random_search not in ["uniform", "lhs"]:
        raise ValueError("Unsupported initial random search '{}'.".format(random_search))

    match main_id:
        case "default" | "arch24":
            execution_budget = 1500 if execution_budget is None else execution_budget
            random_search_proportion = 0.05
            random_search_samples = int(random_search_proportion*execution_budget)
            if random_search_samples < 1:
                raise ValueError("The execution budget is so low that initial random search has no execution budget.")

            lhs_samples = int(random_search_proportion*execution_budget) + 1

            model_sampler = "RejectionSampler"
            model_sampler_parameters = {
                "objective_coef": 0.95,
                "invalid_threshold": 100
            }

            generator_parameters = {
                "analyzer_sampling_split":          0.5,
                "training_data_sampler":            "Quantile_Sampler",
                "training_data_sampler_parameters": {
                    "bins":                    10,
                    "sample_with_replacement": False,
                    "quantile_start":          0.4,
                    "quantile_end":            0.03,
                    "zero_minimum":            True
                },
                "model_sampler":                     model_sampler,
                "model_sampler_parameters":          model_sampler_parameters
            }
            
            analyzer = "RandomForest"
            analyzer_parameters = {}
            
            backward_model = "UNet"
            backward_model_parameters = {
                "time_embedding_dim":  20,
                "residual_connection": True,
                "max_depth":           5
            }
            
            model_parameters = {
                "analyzer":                  analyzer,
                "analyzer_parameters":       analyzer_parameters,
                "backward_model":            backward_model,
                "backward_model_parameters": backward_model_parameters,
                "ddpm":                      "DDPM",
                "ddpm_parameters": {
                    "N_steps":  75,
                    "min_beta": 10**(-4),
                    "max_beta": 0.02
                },
                "ddpm_optimizer_parameters": {
                    "optimizer": "Adam",
                    "lr":        0.001
                },
                "train_settings": {
                    "epochs":     20,
                    "batch_size": 32
                }
            }
            
            tsg_parameters = {
                "execution_budget":         execution_budget,
                "random_search_proportion": random_search_proportion,
                "random_search":            random_search.lower(),
                "lhs_samples":              lhs_samples,
                "reset_each_training":      False,
                "train_delay":              1,
                "generator_parameters":     generator_parameters,
                "model_parameters":         model_parameters
            }
        case _:
            raise ValueError("Unknown identifier '{}'.".format(identifier))
        
    return tsg_parameters

def get_OGAN_parameters(identifier, execution_budget=None, network_type="convolution"):
    """Returns preset OGAN test suite generator parameters according to the given
    identifier. Different initial random searches can be specified
    with a suffix like '_lhs'. The default initial random search is uniform
    random."""

    if execution_budget is not None and execution_budget < 1:
        raise ValueError("The execution budget must be positive.")

    if "_" in identifier:
        identifier, random_search = identifier.split("_")
        main_id = identifier.lower()
        random_search = random_search.lower()
    else:
        main_id = identifier.lower()
        random_search = "uniform"
    
    if random_search is not None and random_search not in ["uniform", "lhs"]:
        raise ValueError("Unsupported initial random search '{}'.".format(random_search))

    match main_id:
        case "default":
            execution_budget = 300 if execution_budget is None else execution_budget
            random_search_proportion = 0.25
            random_search_samples = int(random_search_proportion*execution_budget)
            if random_search_samples < 1:
                raise ValueError("The execution budget is so low that initial random search has no execution budget.")

            lhs_samples = int(random_search_proportion*execution_budget) + 1

            model_sampler = "RejectionSampler"
            model_sampler_parameters = {
                "objective_coef": 0.95,
                "invalid_threshold": 100
            }

            generator_parameters = {
                "model_sampler": model_sampler,
                "model_sampler_parameters": model_sampler_parameters
            }

            match network_type.lower():
                case "convolution":
                    model_parameters = {
                        "optimizer": "Adam",
                        "discriminator_lr": 0.001,
                        "discriminator_betas": [0.9, 0.999],
                        "generator_lr": 0.0001,
                        "generator_betas": [0.9, 0.999],
                        "noise_batch_size": 8192,
                        "generator_loss": "MSE,Logit",
                        "discriminator_loss": "MSE,Logit",
                        "generator_mlm": "GeneratorNetwork",
                        "generator_mlm_parameters": {
                            "noise_dim": 20,
                            "hidden_neurons": [128, 128, 128],
                            "hidden_activation": "leaky_relu"
                        },
                        "discriminator_mlm": "DiscriminatorNetwork1dConv",
                        "discriminator_mlm_parameters": {
                            "feature_maps": [16, 16],
                            "kernel_sizes": [[2, 2], [2, 2]],
                            "convolution_activation": "leaky_relu",
                            "dense_neurons": 128
                        },
                        "train_settings_init": {"epochs": 1, "discriminator_epochs": 15, "generator_batch_size": 32},
                        "train_settings": {"epochs": 1, "discriminator_epochs": 15, "generator_batch_size": 32}
                    }
                case "dense":
                    model_parameters = {
                        "optimizer": "Adam",
                        "discriminator_lr": 0.001,
                        "discriminator_betas": [0.9, 0.999],
                        "generator_lr": 0.0001,
                        "generator_betas": [0.9, 0.999],
                        "noise_batch_size": 8192,
                        "generator_loss": "MSE,Logit",
                        "discriminator_loss": "MSE,Logit",
                        "generator_mlm": "GeneratorNetwork",
                        "generator_mlm_parameters": {
                            "noise_dim": 20,
                            "hidden_neurons": [128, 128, 128],
                            "hidden_activation": "leaky_relu"
                        },
                        "discriminator_mlm": "DiscriminatorNetwork",
                        "discriminator_mlm_parameters": {
                            "hidden_neurons": [128, 128, 128],
                            "hidden_activation": "leaky_relu"
                        },
                        "train_settings_init": {"epochs": 1, "discriminator_epochs": 15, "generator_batch_size": 32},
                        "train_settings": {"epochs": 1, "discriminator_epochs": 15, "generator_batch_size": 32}
                    }
                case _:
                    ValueError("Unknown network type '{}'.".format(network_type))

            tsg_parameters = {
                "execution_budget":         execution_budget,
                "random_search_proportion": random_search_proportion,
                "random_search":            random_search,
                "lhs_samples":              lhs_samples,
                "reset_each_training":      True,
                "train_delay":              1,
                "generator_parameters":     generator_parameters,
                "model_parameters":         model_parameters
            }
        case "arch23":
            if random_search != "lhs":
                raise ValueError("The initial random search is always LHS in the ARCH23 setup.")

            # Proportion of the total execution budget for the initial LHS search.
            execution_budget = 1500 if execution_budget is None else execution_budget
            random_search_proportion = 0.05
            random_search_samples = int(random_search_proportion * execution_budget)
            if random_search_samples < 1:
                raise ValueError("The execution budget is so low that initial random search has no execution budget.")

            # Probability for the 'hyperheuristic' part where OGAN test
            # generation is sometimes replaced by uniform random sampling.
            # This is chosen so that on overage 25 % of the total budget is
            # used for random sampling (this includes the initial random
            # search). When the execution budget is 1500, theta is 0.21 as in
            # the ARCH-COMP 2023 report.
            theta = round((0.25*execution_budget - random_search_samples) / (execution_budget - random_search_samples), 2)

            model_sampler = "RejectionSampler"
            model_sampler_parameters = {
                "objective_coef": 0.95,
                "invalid_threshold": 100
            }

            generator_parameters = {
                "model_sampler": model_sampler,
                "model_sampler_parameters": model_sampler_parameters
            }

            match network_type.lower():
                case "convolution":
                    model_parameters = {
                        "optimizer": "Adam",
                        "discriminator_lr": 0.001,
                        "discriminator_betas": [0.9, 0.999],
                        "generator_lr": 0.0001,
                        "generator_betas": [0.9, 0.999],
                        "noise_batch_size": 8192,
                        "generator_loss": "MSE,Logit",
                        "discriminator_loss": "MSE,Logit",
                        "generator_mlm": "GeneratorNetwork",
                        "generator_mlm_parameters": {
                            "noise_dim": 20,
                            "hidden_neurons": [128, 128, 128],
                            "hidden_activation": "leaky_relu"
                        },
                        "discriminator_mlm": "DiscriminatorNetwork1dConv",
                        "discriminator_mlm_parameters": {
                            "feature_maps": [16, 16],
                            "kernel_sizes": [[2, 2], [2, 2]],
                            "convolution_activation": "leaky_relu",
                            "dense_neurons": 128
                        },
                        "train_settings_init": {"epochs": 1, "discriminator_epochs": 15, "generator_batch_size": 32},
                        "train_settings": {"epochs": 1, "discriminator_epochs": 15, "generator_batch_size": 32}
                    }
                case "dense":
                    model_parameters = {
                        "optimizer": "Adam",
                        "discriminator_lr": 0.001,
                        "discriminator_betas": [0.9, 0.999],
                        "generator_lr": 0.0001,
                        "generator_betas": [0.9, 0.999],
                        "noise_batch_size": 8192,
                        "generator_loss": "MSE,Logit",
                        "discriminator_loss": "MSE,Logit",
                        "generator_mlm": "GeneratorNetwork",
                        "generator_mlm_parameters": {
                            "noise_dim": 20,
                            "hidden_neurons": [128, 128, 128],
                            "hidden_activation": "leaky_relu"
                        },
                        "discriminator_mlm": "DiscriminatorNetwork",
                        "discriminator_mlm_parameters": {
                            "hidden_neurons": [128, 128, 128],
                            "hidden_activation": "leaky_relu"
                        },
                        "train_settings_init": {"epochs": 1, "discriminator_epochs": 15, "generator_batch_size": 32},
                        "train_settings": {"epochs": 1, "discriminator_epochs": 15, "generator_batch_size": 32}
                    }
                case _:
                    ValueError("Unknown network type '{}'.".format(network_type))

            tsg_parameters = {
                "execution_budget":               execution_budget,
                "random_search_proportion":       0.05,
                "random_search":                  "lhs",
                "lhs_samples":                    75,
                "random_exploration_probability": theta,
                "exploration_warm_up":            30,
                "reset_each_training":            True,
                "train_delay":                    1,
                "generator_parameters":           generator_parameters,
                "model_parameters":               model_parameters
            }
        case _:
            raise ValueError("Unknown identifier '{}'.".format(identifier))
    
    # small is the same as default, but we adjust one parameter for faster execution.
    if __debug__ and config.faster_parameters:
        tsg_parameters["model_parameters"]["noise_batch_size"] = 512

    return tsg_parameters

def get_WOGAN_parameters(identifier, execution_budget=None, network_type="convolution"):
    """Returns preset WOGAN test suite generator parameters according to the
    given identifier. Different initial random searches can be specified with a
    suffix like '_lhs'. The default initial random search is uniform random."""
    
    if execution_budget is not None and execution_budget < 1:
        raise ValueError("The execution budget must be positive.")

    if "_" in identifier:
        identifier, random_search = identifier.split("_")
        main_id = identifier.lower()
        random_search = random_search.lower()
    else:
        main_id = identifier.lower()
        random_search = "uniform"
    
    if random_search is not None and random_search not in ["uniform", "lhs"]:
        raise ValueError("Unsupported initial random search '{}'.".format(random_search))

    match main_id:
        case "default":
            execution_budget = 1500 if execution_budget is None else execution_budget
            random_search_proportion = 0.05
            random_search_samples = int(random_search_proportion*execution_budget)
            if random_search_samples < 1:
                raise ValueError("The execution budget is so low that initial random search has no execution budget.")

            lhs_samples = int(random_search_proportion*execution_budget) + 1

            model_sampler = "RejectionSampler"
            model_sampler_parameters = {
                "objective_coef": 0.95,
                "invalid_threshold": 100
            }

            generator_parameters = {
                "wgan_batch_size": 32,
                "model_sampler": model_sampler,
                "model_sampler_parameters": model_sampler_parameters,
                "training_data_sampler": "Quantile_Sampler",
                "training_data_sampler_parameters": {
                    "bins": 10,
                    "sample_with_replacement": False,
                    "omit_initial_empty": False,
                    "quantile_start": 0.5,
                    "quantile_end": 0.1,
                    "zero_minimum": True
                }
            }

            match network_type.lower():
                case "convolution":
                    analyzer_parameters = {
                        "optimizer": "Adam",
                        "lr": 0.0001,
                        "betas": [0, 0.9],
                        "loss": "MSE,logit",
                        "l2_regularization_coef": 0.0,
                        "analyzer_mlm": "AnalyzerNetwork_conv",
                        "analyzer_mlm_parameters": {
                            "feature_maps": [16,16],
                            "kernel_sizes": [[2,2], [2,2]],
                            "convolution_activation": "leaky_relu",
                            "dense_neurons": 128
                        }
                    }
                case "dense":
                    analyzer_parameters = {
                        "optimizer": "Adam",
                        "lr": 0.0001,
                        "betas": [0, 0.9],
                        "loss": "MSE,logit",
                        "l2_regularization_coef": 0.01,
                        "analyzer_mlm": "AnalyzerNetwork",
                        "analyzer_mlm_parameters": {
                            "hidden_neurons": [128,128],
                            "hidden_activation": "leaky_relu",
                            "batch_normalization": True,
                            "layer_normalization": False
                        }
                    }
                case _:
                    raise ValueError("Unknown network type '{}'.".format(network_type))

            model_parameters = {
                "critic_optimizer": "Adam",
                "critic_lr": 0.0001,
                "critic_betas": [0, 0.9],
                "generator_optimizer": "Adam",
                "generator_lr": 0.0001,
                "generator_betas": [0, 0.9],
                "noise_batch_size": 32,
                "gp_coefficient": 10,
                "eps": 1e-6,
                "report_wd": True,
                "analyzer": "Analyzer_NN",
                "analyzer_parameters": analyzer_parameters,
                "generator_mlm": "GeneratorNetwork",
                "generator_mlm_parameters": {
                    "noise_dim": 10,
                    "hidden_neurons": [128, 128],
                    "hidden_activation": "leaky_relu",
                    "batch_normalization": True,
                    "layer_normalization": False
                },
                "critic_mlm": "CriticNetwork",
                "critic_mlm_parameters": {
                    "hidden_neurons": [128, 128],
                    "hidden_activation": "leaky_relu",
                },
                "train_settings_init": {
                    "epochs": 2,
                    "analyzer_epochs": 10,
                    "critic_steps": 5,
                    "generator_steps": 1
                },
                "train_settings": {
                    "epochs": 2,
                    "analyzer_epochs": 10,
                    "critic_steps": 5,
                    "generator_steps": 1
                }
            }

            tsg_parameters = {
                "execution_budget":          execution_budget,
                "random_search_proportion":  random_search_proportion,
                "random_search":             random_search,
                "lhs_samples":               lhs_samples,
                "reset_each_training":       False,
                "train_delay":               3,
                "generator_parameters":      generator_parameters,
                "model_parameters":          model_parameters
            }
        case "test":
            execution_budget = 1500 if execution_budget is None else execution_budget
            random_search_proportion = 0.05
            random_search_samples = int(random_search_proportion*execution_budget)
            if random_search_samples < 1:
                raise ValueError("The execution budget is so low that initial random search has no execution budget.")

            lhs_samples = int(random_search_proportion*execution_budget) + 1

            model_sampler = "RejectionSampler"
            model_sampler_parameters = {
                "objective_coef": 0.95,
                "invalid_threshold": 100
            }

            generator_parameters = {
                "wgan_batch_size": 32,
                "model_sampler": model_sampler,
                "model_sampler_parameters": model_sampler_parameters,
                "training_data_sampler": "Quantile_Sampler",
                "training_data_sampler_parameters": {
                    "bins": 10,
                    "sample_with_replacement": False,
                    "omit_initial_empty": False,
                    "quantile_start": 0.5,
                    "quantile_end": 0.025,
                    "zero_minimum": True
                }
            }

            match network_type.lower():
                case "convolution":
                    analyzer_parameters = {
                        "optimizer": "Adam",
                        "lr": 0.0001,
                        "betas": [0, 0.9],
                        "loss": "MSE,logit",
                        "l2_regularization_coef": 0.0,
                        "analyzer_mlm": "AnalyzerNetwork_conv",
                        "analyzer_mlm_parameters": {
                            "feature_maps": [16,16],
                            "kernel_sizes": [[2,2], [2,2]],
                            "convolution_activation": "leaky_relu",
                            "dense_neurons": 128
                        }
                    }
                case "dense":
                    analyzer_parameters = {
                        "optimizer": "Adam",
                        "lr": 0.0001,
                        "betas": [0, 0.9],
                        "loss": "MSE,logit",
                        "l2_regularization_coef": 0.01,
                        "analyzer_mlm": "AnalyzerNetwork",
                        "analyzer_mlm_parameters": {
                            "hidden_neurons": [128,128],
                            "hidden_activation": "leaky_relu",
                            "batch_normalization": True,
                            "layer_normalization": False
                        }
                    }
                case _:
                    raise ValueError("Unknown network type '{}'.".format(network_type))

            model_parameters = {
                "critic_optimizer": "Adam",
                "critic_lr": 0.0001,
                "critic_betas": [0, 0.9],
                "generator_optimizer": "Adam",
                "generator_lr": 0.0001,
                "generator_betas": [0, 0.9],
                "noise_batch_size": 32,
                "gp_coefficient": 10,
                "eps": 1e-6,
                "report_wd": True,
                "analyzer": "Analyzer_NN",
                "analyzer_parameters": analyzer_parameters,
                "generator_mlm": "GeneratorNetwork",
                "generator_mlm_parameters": {
                    "noise_dim": 10,
                    "hidden_neurons": [128, 128],
                    "hidden_activation": "leaky_relu",
                    "batch_normalization": True,
                    "layer_normalization": False
                },
                "critic_mlm": "CriticNetwork",
                "critic_mlm_parameters": {
                    "hidden_neurons": [128, 128],
                    "hidden_activation": "leaky_relu",
                },
                "train_settings_init": {
                    "epochs": 2,
                    "analyzer_epochs": 10,
                    "critic_steps": 5,
                    "generator_steps": 1
                },
                "train_settings": {
                    "epochs": 2,
                    "analyzer_epochs": 10,
                    "critic_steps": 5,
                    "generator_steps": 1
                }
            }

            tsg_parameters = {
                "execution_budget":          execution_budget,
                "random_search_proportion":  random_search_proportion,
                "random_search":             random_search,
                "lhs_samples":               lhs_samples,
                "reset_each_training":       False,
                "train_delay":               3,
                "generator_parameters":      generator_parameters,
                "model_parameters":          model_parameters
            }

        case _:
            raise ValueError("Unknown identifier '{}'.".format(identifier))
        
    return tsg_parameters
