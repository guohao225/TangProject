class ModelPara():
    def __init__(self):
        self.getconfig()

    def getconfig(self):
        f = open('./model_config.cfg', 'r')
        lines = f.readlines()
        for line in lines:
            if line.startswith('#'):
                continue
            config = line.strip().split(' ')
            if config[0] != 'cnn_act':
                self.__setattr__(config[0], eval(config[1]))
            else:
                self.__setattr__(config[0], eval(config[1]) if config[1]=='None' else config[1])


CONFIG = ModelPara()