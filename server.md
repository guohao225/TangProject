## 句子的标签更新
标注更新接口：tag_update
    1. 获取原始的标签和实体，更新到user_lable和user_entity中
    2. 更新当前标注的实体与标签到lable和entity中
    3. 更新操作记录（未实现）
预测接口：predict_unlabeled
    该接口在每一轮中预测未标注的样本，并更新他们的标签

## 标注路径
    get_tag_sample-->tag_update
