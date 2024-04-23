import axios from "axios";
import relations from "@/assets/relations.json"
import {ElNotification} from "element-plus";
class DataMan {
  static BASE_URL = 'http://127.0.0.1:5000'
  static COLORS = {
    other: '#E0E2E5',
    PER: '#a6d691',
    LOC: '#8fcde5',
    TIME: '#fbd379',
    BORDER: '#BEB8DC',
    lines:'#ee6c6c',
    selected: '#FF6600',
    ORG: '#fbd379',
    buttons:'#445469',
    unlabel: '#909399',
    labeled:'#5ab55a',
    suggest:'red',
    background:'',
    title:'#445469',
    titleColor:'#fff'
  }


  static getDataList() {
    return axios.get(`${DataMan.BASE_URL}/get_all_data`)
  }

  static removeData(dataName) {
    return axios.post(`${DataMan.BASE_URL}/remove_data`, {name: dataName})
  }

  static setParameter(data) {
    return axios.post(`${DataMan.BASE_URL}/init`, {data: data})
  }

  static suggestSample() {
    return axios.get(`${DataMan.BASE_URL}/get_suggest`)
  }

  static getTagSample(id) {
    return axios.post(`${DataMan.BASE_URL}/get_tag_sample`, {id: id})
  }

  static tagUpdate(data) {
    return axios.post(`${DataMan.BASE_URL}/tag_update`, {data: data})
  }

  static getNextTagSample() {
    return axios.get(`${DataMan.BASE_URL}/one_loop_tag`)
  }

  static getTrainStatus() {
    return axios.get(`${DataMan.BASE_URL}/train_status`)
  }

  static getTrainRecord() {
    return axios.get(`${DataMan.BASE_URL}/get_train_record`)
  }

  static addOperationRecords(data) {
    return axios.post(`${DataMan.BASE_URL}/insert_oper_record`, {data: data})
  }

  static getOperationRecords() {
    return axios.get(`${DataMan.BASE_URL}/get_oper_record`)
  }

  static getSampleOperationRecords(id, loop) {
    return axios.post(`${DataMan.BASE_URL}/query_record_sample`, {id: id, loop: loop})
  }

  static getLoopOperationRecords(loop) {
    return axios.post(`${DataMan.BASE_URL}/query_record_loop`, {loop: loop})
  }

  static getSampleStatistics() {
    return axios.get(`${DataMan.BASE_URL}/sample_statistics`)
  }

  static getLoopEntitys() {
    return axios.post(`${DataMan.BASE_URL}/get_all_loop_entitys`)
  }

  static operateSample(id, type) {
    return axios.post(`${DataMan.BASE_URL}/operate_sample`, {id: id, type: type})
  }

  static getSelected() {
    return axios.get(`${DataMan.BASE_URL}/get_selected_data`)
  }

  static changeModelParam(data, loopID) {
    return axios.post(`${DataMan.BASE_URL}/fine_tuning_model`, {data: data, id: loopID})
  }

  static reLabel(id) {
    return axios.post(`${DataMan.BASE_URL}/re_label`, {loop: id})
  }

  static getDicData(text) {
    return axios.post(`${DataMan.BASE_URL}/query_dic_text`, {text: text})
  }

  static getModelText(text) {
    return axios.post(`${DataMan.BASE_URL}/query_text_model`, {text: text})
  }

  static getPoemNote(text) {
    return axios.post(`${DataMan.BASE_URL}/query_note`, {text: text})
  }

  static getSelectStatus() {
    return axios.get(`${DataMan.BASE_URL}/query_select_status`)
  }

  static lookLoop(loop, config) {
    return axios.post(`${DataMan.BASE_URL}/look_loop`, {loop: loop, config: config})
  }

  static addTime(time) {
    return axios.post(`${DataMan.BASE_URL}/add_time`, {time: time})
  }

  static getPoemList() {
    return axios.get(`${DataMan.BASE_URL}/get_poem_list`)
  }

  static tagUpdateMany(data) {
    return axios.post(`${DataMan.BASE_URL}/tag_update_batch`,{data:data})
  }

  static getAllWordCloudData(){
    return axios.get(`${DataMan.BASE_URL}/get_all_entitys`)
  }
  static getLoopLabeledToUnlabel(){
    return axios.get(`${DataMan.BASE_URL}/get_loop_labeledandunlabel`)
  }
  static getAllLabelToUnlabel() {
    return axios.get(`${DataMan.BASE_URL}/get_all_labeledandunlabel`)
  }
  static getAllPERANDLOCANDTIME(){
    return axios.get(`${DataMan.BASE_URL}/get_all_PERANDLOCANDTIME`)
  }
  static getLabelTime(){
    return axios.get(`${DataMan.BASE_URL}/get_all_time_record`)
  }
  static insertTimeRecord(time){
    return axios.post(`${DataMan.BASE_URL}/insert_time`,{time:time})
  }
  static get_format_label(label, id){
    return axios.post(`${DataMan.BASE_URL}/get_format_label`, {label:label,id:id})
  }
  static timefig(a, b){
    const timeDifference = a.getTime() - b.getTime(); // 获取毫秒级时间差
    // 将毫秒转换为小时和分钟
    let minutesDifference = timeDifference / (1000 * 60) % 60;
    return minutesDifference.toFixed(4)
  }
  static getRelations(){
    return axios.get(`${DataMan.BASE_URL}/relation_types`)
  }
  static updateRelationTypes(data){
    return axios.post(`${DataMan.BASE_URL}/update_relations`, {data:data})
  }
  static getLoopSample(loop){
    return axios.post(`${DataMan.BASE_URL}/look_loop`, {loop:loop})
  }
  static getEntityNum(entity){
    return axios.post(`${DataMan.BASE_URL}/query_entity_num`, {entity:entity})
  }
  // static Relations = this.getRelations()
}


export function notice(type, msg){
  ElNotification({
    title: type.toUpperCase(),
    message: msg,
    position: 'bottom-right',
    type:type
  })
}

export default DataMan