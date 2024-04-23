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

