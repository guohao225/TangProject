import {createStore} from "vuex";
import dataMan from "@/utils/DataMan";
import {setting} from "../setting";
const store = createStore({
    state: {
        mainData:[],
        dataList:[],

        trainRecord:[],
        operationRecord:[],
        tagVis:false,
        tagID:-1,

        findOperation: {},
        language:setting.Chinese,
        strategy:"LC"
    },
    mutations:{
        setMainData(state, data){
            data.sort((a, b)=>{return b.LC-a.LC})
            state.mainData = data
        },
        setDataList(state, data){
            data.sort((a, b)=>{return b.LC-a.LC})
            state.dataList = data
        },
        setTagVisible(state, visible){
            state.tagVis = visible
        },
        setTagID(state, id){
            state.tagID = id
        },
        updateMainData(state, data){
            dataMan.setParameter(data).then(res=>{
                let data = res.data.res
                let dataList = res.data.list
                state.mainData = data
                state.dataList = dataList
            })
        },
        setTrainRecord(state, data){
            state.trainRecord =data
        },
        setOperationRecord(state, data){
            state.operationRecord = data
        },
        setFindOperationStatus(state, data){
            state.findOperation = data
        },
        changeLanguage(state, data){
            data===1?(state.language = setting.Chinese):(state.language = setting.English)
        },
        setStrategy(state, data){
            state.strategy = data
        }
    },
    getters:{
        getMainData(state){

        }
    }
})

export default store