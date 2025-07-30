import ml_collections




def get_MARIOtrain_config(epochs=40000, opt='Adam', sch='CosineAnnealingLR'):
    config = ml_collections.ConfigDict()
    config.epochs = epochs
    config.opt = opt
    config.sch = sch
    config.title = 'super_mario'


    config.env_name = 'SuperMarioBros-v0'
    config.iter_print = 2

    config.checkpoint = None
    config.skip_frame = 4
    config.render = True

    return config

