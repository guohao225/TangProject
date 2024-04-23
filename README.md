# 环境配置
python = 3.7  
tensorflow-gpu = 2.6  
bert4keras = 0.11.5  

# 文件说明
al_api--后端接口函数  
checkpoints -- 训练参数保存位置  
data --- 数据文件夹  
model --- 模型文件夹  
 |model.json --- 模型配置文件  
 |NerModel.py --- 模型架构文件  
procsessing --- 数据预处理文件夹  
source --- 废弃  
untils --- 公共函数  
  |Config.py --- 模型配置类，数据来源于model.json  
  |DataManger.py --- 数据加载类，数据来源于data文件夹  
  |evaluate.py --- 模型评估函数，负责计算各项指标  
web --- 前端文件夹  
app.py --- 已废弃  
server.py --- 后端启动文件  
train.py --- 训练模型  

# 启动
## 启动后台
项目拉取下来后，安装后端依赖，注意配置tensorflow-gpu的运行环境。本机环境为cudnn(v8.3)  
![image](https://github.com/guohao225/TangProject/assets/80250472/6cb63578-6800-4e31-871d-9d685e42f253)
1. 在项目开始前需要预训练参数，训练文件存在于data/NER_TRAIN/NERTRAIN.txt. 预训练的参数保存位置可以在model.json中配置，字段为“save_path”
2. 训练完成后请在srever.py文件中启动后台
如果需要使用BERT训练参数，请将下载的BERT预训练参数放到**MiniRBT-h256-pt**文件夹下，注意只支持bert4keras能加载的BERT预训练模型。
## 启动前端
1. 将项目根目录跳转到web文件夹下，运行  `npm install`
2. 安装依赖完成后，运行`npm run serve` 
